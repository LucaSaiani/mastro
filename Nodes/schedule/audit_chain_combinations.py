"""Not a registered module - run manually with
`python3 audit_chain_combinations.py` from this directory.

Static-only (no bpy, no Blender, no evaluate() calls) - lists every
node-to-node CONNECTION that's actually constructible in the editor
(output socket type of node A matches an input socket type of node B),
then chains those up to MAX_DEPTH deep, to get a sense of how many
distinct node chains exist among nodes that share a socket type at all.
Doesn't run any of them - this only enumerates what's CONSTRUCTIBLE, as
a starting point for picking specific chains worth checking by hand in
Blender (this codebase's existing convention - see feedback_no_headless_verify
memory: actual runtime verification stays the user's job, not a headless
script's).

Most node pairs share no socket type at all (e.g. nothing with a Table
output can ever feed something expecting a Column input - Blender's own
socket type system already rules that out before this script needs to)
- this is exactly why a naive "all N nodes x all N nodes" combinatorial
count would wildly overstate the real number: only pairs that ACTUALLY
share a socket type are ever counted here.
"""

import ast
import pathlib

MAX_DEPTH = 3


def _string_value(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _bl_idname(class_node):
    for item in class_node.body:
        if isinstance(item, ast.Assign) and len(item.targets) == 1:
            target = item.targets[0]
            if isinstance(target, ast.Name) and target.id == "bl_idname":
                return _string_value(item.value)
    return None


def _socket_calls(class_node, attr_name):
    """Every bl_idname string passed to `self.<attr_name>.new(...)`
    inside this class's methods (init(), mainly, but anywhere a node
    happens to add sockets from - some do it in update_sockets() too)."""
    types = []
    for node in ast.walk(class_node):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr == "new"):
            continue
        if not (isinstance(func.value, ast.Attribute) and func.value.attr == attr_name):
            continue
        if not node.args:
            continue
        value = _string_value(node.args[0])
        if value is not None and value.endswith("SocketType"):
            types.append(value)
    return types


def _collect_nodes(here):
    """{bl_idname: {"label": class_name, "inputs": [...], "outputs": [...]}}
    for every Node subclass found across every module in this directory."""
    nodes = {}
    for path in sorted(here.glob("*.py")):
        if path.name.startswith("audit_"):
            continue
        tree = ast.parse(path.read_text())
        for class_node in ast.walk(tree):
            if not isinstance(class_node, ast.ClassDef):
                continue
            bl_idname = _bl_idname(class_node)
            if bl_idname is None:
                continue
            inputs = _socket_calls(class_node, "inputs")
            outputs = _socket_calls(class_node, "outputs")
            if not inputs and not outputs:
                continue
            nodes[bl_idname] = {
                "label": class_node.name,
                "file": path.name,
                "inputs": inputs,
                "outputs": outputs,
            }
    return nodes


def _build_edges(nodes):
    """(from_bl_idname, to_bl_idname) pairs where some output socket of
    `from` shares a type with some input socket of `to` - the actual
    constructible connections, self-loops included (a node feeding
    another instance of itself, e.g. Math -> Math, is a real, common
    chain)."""
    edges = []
    for from_id, from_node in nodes.items():
        from_types = set(from_node["outputs"])
        if not from_types:
            continue
        for to_id, to_node in nodes.items():
            to_types = set(to_node["inputs"])
            if from_types & to_types:
                edges.append((from_id, to_id))
    return edges


def _chains(edges, max_depth):
    """All node-id chains [n1, n2, ..., nk] with 2 <= k <= max_depth+1,
    where each consecutive pair is a real edge - built depth-first,
    revisiting the same node within one chain IS allowed (e.g. Math ->
    Math -> Math is a real, constructible chain a user could build)."""
    adjacency = {}
    for from_id, to_id in edges:
        adjacency.setdefault(from_id, []).append(to_id)

    all_chains = []

    def extend(chain):
        all_chains.append(list(chain))
        if len(chain) > max_depth:
            return
        for next_id in adjacency.get(chain[-1], []):
            extend(chain + [next_id])

    for start_id in adjacency:
        extend([start_id])
    return [c for c in all_chains if len(c) >= 2]


def main():
    here = pathlib.Path(__file__).parent
    nodes = _collect_nodes(here)
    edges = _build_edges(nodes)
    chains = _chains(edges, MAX_DEPTH)

    print(f"Nodes with at least one Schedule socket: {len(nodes)}")
    print(f"Constructible direct connections (A -> B sharing a socket type): {len(edges)}")
    print(f"Chains up to depth {MAX_DEPTH + 1} nodes: {len(chains)}")
    print()
    print("Sample of the longest chains found:")
    chains.sort(key=len, reverse=True)
    for chain in chains[:15]:
        labels = " -> ".join(nodes[bl_idname]["label"] for bl_idname in chain)
        print(f"  {labels}")


if __name__ == "__main__":
    main()
