"""
Run this script in Blender's Text Editor (with mastroAssets.blend open)
or via: blender mastroAssets.blend --background --python export_nodes.py

Output: export_nodes.json in the same folder as the .blend file.
"""

import bpy
import json
import os


def socket_info(socket):
    info = {
        "name": socket.name,
        "type": socket.type,
    }
    # Try to get default value
    if hasattr(socket, "default_value"):
        try:
            val = socket.default_value
            if hasattr(val, "to_list"):
                info["default"] = val.to_list()
            elif hasattr(val, "__iter__") and not isinstance(val, str):
                info["default"] = list(val)
            else:
                info["default"] = val
        except Exception:
            pass
    # Subtype / enum items
    if hasattr(socket, "enum_items"):
        try:
            info["enum_items"] = [i.identifier for i in socket.enum_items]
        except Exception:
            pass
    return info


def node_group_info(ng):
    inputs = []
    outputs = []

    # Blender 4.x uses ng.interface.items_tree
    if hasattr(ng, "interface") and hasattr(ng.interface, "items_tree"):
        # Build panel map: panel index -> panel name
        # items_tree is ordered; panels contain the sockets that follow them until the next panel
        current_panel = None
        for item in ng.interface.items_tree:
            if item.item_type == 'PANEL':
                current_panel = item.name
            elif item.item_type == 'SOCKET':
                entry = {
                    "name": item.name,
                    "type": item.socket_type,
                    "description": getattr(item, "description", ""),
                    "panel": current_panel,
                }
                if hasattr(item, "default_value"):
                    try:
                        val = item.default_value
                        if hasattr(val, "to_list"):
                            entry["default"] = val.to_list()
                        elif hasattr(val, "__iter__") and not isinstance(val, str):
                            entry["default"] = list(val)
                        elif isinstance(val, (int, float, bool, str)):
                            entry["default"] = val
                        else:
                            entry["default"] = repr(val)
                    except Exception:
                        pass
                if item.in_out == 'INPUT':
                    inputs.append(entry)
                else:
                    outputs.append(entry)
    # Blender 3.x fallback
    elif hasattr(ng, "inputs") and hasattr(ng, "outputs"):
        for s in ng.inputs:
            inputs.append(socket_info(s))
        for s in ng.outputs:
            outputs.append(socket_info(s))

    return {
        "name": ng.name,
        "description": getattr(ng, "description", ""),
        "inputs": inputs,
        "outputs": outputs,
    }


# Build a map: node group name -> set of node group names that contain it
def find_ng_dependencies(node_groups):
    """Returns dict: ng_name -> set of ng_names that directly use it as a node."""
    used_by = {}  # ng_name -> set of parent ng_names
    for ng in node_groups:
        for node in ng.nodes:
            child_ng = None
            for attr in ('node_tree', 'node_group', 'group'):
                candidate = getattr(node, attr, None)
                if candidate is not None and hasattr(candidate, 'name'):
                    child_ng = candidate
                    break
            if child_ng:
                used_by.setdefault(child_ng.name, set()).add(ng.name)
    return used_by

ng_internal_deps = find_ng_dependencies(bpy.data.node_groups)

# Recursively find all top-level objects that use a node group (directly or transitively)
def find_top_level_users(ng_name, ng_internal_deps, ng_to_objects_direct, visited=None):
    if visited is None:
        visited = set()
    if ng_name in visited:
        return []
    visited.add(ng_name)
    results = list(ng_to_objects_direct.get(ng_name, []))
    for parent_ng in ng_internal_deps.get(ng_name, set()):
        results.extend(find_top_level_users(parent_ng, ng_internal_deps, ng_to_objects_direct, visited))
    return results

# Build direct object usage map
ng_to_objects_direct = {}
for obj in bpy.data.objects:
    for mod in obj.modifiers:
        if mod.type == 'NODES' and mod.node_group:
            ng_name = mod.node_group.name
            collections = [c.name for c in bpy.data.collections if obj.name in c.objects]
            ng_to_objects_direct.setdefault(ng_name, []).append({
                "object": obj.name,
                "collections": collections,
            })

# Also track which node groups directly contain this one
ng_to_parent_ngs = ng_internal_deps

data = {}
for ng in bpy.data.node_groups:
    if ng.type != 'GEOMETRY':
        continue
    info = node_group_info(ng)
    # Direct object usage (transitive)
    all_usages = find_top_level_users(ng.name, ng_internal_deps, ng_to_objects_direct)
    # Deduplicate by object name
    seen = set()
    unique_usages = []
    for u in all_usages:
        if u["object"] not in seen:
            seen.add(u["object"])
            unique_usages.append(u)
    info["used_by"] = unique_usages
    # Direct parent node groups (immediate, not transitive)
    info["used_in_node_groups"] = sorted(ng_to_parent_ngs.get(ng.name, set()))
    data[ng.name] = info

out_path = os.path.join(os.path.dirname(bpy.data.filepath), "export_nodes.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Exported {len(data)} node groups to {out_path}")
