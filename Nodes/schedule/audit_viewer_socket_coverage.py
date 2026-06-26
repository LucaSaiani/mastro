"""Not a registered module - run manually with
`python3 audit_viewer_socket_coverage.py` from this directory whenever a
new socket type is added, or a node is given a new output socket type.

The Viewer's input is MaStroScheduleAnySocketType (sockets.py) - it
deliberately accepts ANY of this tree's own socket types, since the
whole point of a Viewer is to display whatever a node happens to
produce. evaluate() (nodes_viewer.py) branches explicitly on
from_socket.bl_idname for the shapes that don't look like a plain list
of dict rows (Table, List, Id Key so far) - anything NOT given its own
branch falls through to the generic Column/Data-shaped code, which
calls .items()/.keys() on every element of inputs[0]. That's correct
for Data/Column (already lists of dict rows) but a real crash for any
OTHER socket type whose value isn't shaped that way - confirmed live:
Get Id Keys (a plain string) plugged into a Viewer raised "'str' object
has no attribute 'keys'" before Id Key got its own branch.

This script finds every socket type that's actually used as a real
node's output (not just declared in sockets.py - a socket type nothing
emits can never reach the Viewer in the first place) and checks whether
nodes_viewer.py's evaluate() has an explicit `from_socket.bl_idname ==
'...'` branch for it, OR is listed in GENERIC_SHAPE_EXEMPT below with a
comment explaining why the generic Column/Data code already handles it
correctly without one (e.g. Data's own rows already are plain dict
lists, identical in shape to what the generic path expects).
"""

import ast
import pathlib

# bl_idname strings explicitly confirmed to already work correctly
# falling through to the generic Column/Data-shaped code below the
# Table/List/Id Key branches in nodes_viewer.py's evaluate() - add here
# only with a comment proving the value reaching the Viewer for that
# socket type really is a plain list of dict rows (or empty), not
# something that would crash .items()/.keys() the way a bare string/
# tuple/bool does.
GENERIC_SHAPE_EXEMPT = {
    # Data's own rows are already plain {key: value} dicts - the exact
    # shape the generic path expects, no branch needed.
    "MaStroScheduleDataSocketType",
    # AttributeRef's own rows are [{"Field": ..., "Name": ...}] - also a
    # plain list of dicts, handled further down by the same generic
    # path's own special-case for "Field"/"Name" keys (see the comment
    # there), not a separate branch up top like Table/List/Id Key.
    "MaStroScheduleAttributeRefSocketType",
    # MaStroScheduleAnySocketType is the Viewer's OWN input type, never
    # a real node's output - nothing to check.
    "MaStroScheduleAnySocketType",
}


def _string_value(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _outputs_new_socket_types(tree):
    """Every bl_idname string passed to any `outputs.new(...)` call
    anywhere in this module (not scoped to a single class - init()
    methods are the only place this appears, walking the whole module
    is equivalent and simpler)."""
    types = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr == "new"):
            continue
        if not (isinstance(func.value, ast.Attribute) and func.value.attr == "outputs"):
            continue
        if not node.args:
            continue
        value = _string_value(node.args[0])
        if value is not None and value.endswith("SocketType"):
            types.add(value)
    return types


def _string_keys_or_elements(container_node):
    """String literals found as dict keys or set/list/tuple elements -
    covers `from_socket.bl_idname in {'A': ..., 'B': ...}` (a dict, keys
    checked) or `in {'A', 'B'}` (a set/list/tuple, elements checked), in
    case a future branch in nodes_viewer.py uses one of these forms
    instead of the simpler `== 'A'`/`== 'A' or == 'B'` comparisons
    every branch there uses today."""
    if isinstance(container_node, ast.Dict):
        return [_string_value(k) for k in container_node.keys]
    if isinstance(container_node, (ast.Set, ast.List, ast.Tuple)):
        return [_string_value(e) for e in container_node.elts]
    return []


def _viewer_branches(viewer_path):
    """Every bl_idname string compared against `from_socket.bl_idname`
    anywhere in nodes_viewer.py, via either `== '...'` or `in {...}`/
    `in {'...': ...}` - these are the socket types the Viewer already
    special-cases before falling through to the generic path."""
    tree = ast.parse(viewer_path.read_text())
    branches = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        left = node.left
        if not (isinstance(left, ast.Attribute) and left.attr == "bl_idname"):
            continue
        if not (isinstance(left.value, ast.Name) and left.value.id == "from_socket"):
            continue
        for op, comparator in zip(node.ops, node.comparators):
            if isinstance(op, ast.In):
                for value in _string_keys_or_elements(comparator):
                    if value is not None:
                        branches.add(value)
            else:
                value = _string_value(comparator)
                if value is not None:
                    branches.add(value)
    return branches


def main():
    here = pathlib.Path(__file__).parent
    viewer_path = here / "nodes_viewer.py"

    produced_types = set()
    for path in sorted(here.glob("*.py")):
        if path.name == "audit_viewer_socket_coverage.py":
            continue
        tree = ast.parse(path.read_text())
        produced_types |= _outputs_new_socket_types(tree)

    branches = _viewer_branches(viewer_path)

    uncovered = sorted(produced_types - branches - GENERIC_SHAPE_EXEMPT)

    print(f"=== Socket types with no Viewer branch and no GENERIC_SHAPE_EXEMPT entry: {len(uncovered)} ===")
    for bl_idname in uncovered:
        print(f"  {bl_idname}")
    print()

    if not uncovered:
        print("OK - every socket type a node actually outputs is either branched on in "
              "nodes_viewer.py's evaluate(), or confirmed exempt (generic Column/Data shape).")


if __name__ == "__main__":
    main()
