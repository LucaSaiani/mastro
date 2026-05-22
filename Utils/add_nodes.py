import bpy
import addon_utils
from pathlib import Path
from .get_preferences import get_prefs

def clear_asset_status(data_block):
    """Clear the asset status of a data block. Appended node groups are marked as assets,
    which causes them to appear in the asset browser and interfere with searches."""
    if data_block and hasattr(data_block, "asset_data") and data_block.asset_data:
        data_block.asset_clear()
        # print(f"MaStro: Asset status cleared for {type(data_block).__name__}: '{data_block.name}'")

def clean_tree_recursive(tree, processed_trees):
    """Recursively clear asset status from a node tree and all nested groups/materials.
    The processed_trees set prevents re-visiting shared node groups."""
    if not tree or tree in processed_trees:
        return
    
    processed_trees.add(tree)
    clear_asset_status(tree)

    for node in tree.nodes:
        # 1. Handle Nested Groups (both Geometry and Shader groups)
        if node.type in {'GROUP', 'SHADER_NODE_GROUP'} and node.node_tree:
            clean_tree_recursive(node.node_tree, processed_trees)
        
        # 2. Handle Materials found in Geometry Nodes
        if hasattr(node, "material") and node.material:
            mat = node.material
            clear_asset_status(mat)
            if mat.node_tree: # Scan the material's internal nodes
                clean_tree_recursive(mat.node_tree, processed_trees)
            
        # 3. Handle Material inputs (default values in sockets)
        for socket in node.inputs:
            if socket.type == 'MATERIAL' and socket.default_value:
                mat = socket.default_value
                clear_asset_status(mat)
                if mat.node_tree:
                    clean_tree_recursive(mat.node_tree, processed_trees)

def _deduplicate_node_group(canonical_name):
    """Replace all uses of '<canonical_name>.001', '.002', … with the canonical
    group and remove the duplicates."""
    import re
    canonical = bpy.data.node_groups.get(canonical_name)
    if canonical is None:
        return
    pattern = re.compile(r"^" + re.escape(canonical_name) + r"\.\d+$")
    duplicates = [ng for ng in bpy.data.node_groups if pattern.match(ng.name)]
    if not duplicates:
        return
    for dup in duplicates:
        for tree in bpy.data.node_groups:
            for node in tree.nodes:
                if node.type == 'GROUP' and node.node_tree == dup:
                    node.node_tree = canonical
        for mat in bpy.data.materials:
            if mat.node_tree:
                for node in mat.node_tree.nodes:
                    if node.type == 'GROUP' and node.node_tree == dup:
                        node.node_tree = canonical
        bpy.data.node_groups.remove(dup)


def add_materials():
    """Append MaStro materials from mastro.blend in a single load call so shared
    node groups (e.g. Section RGB) are not duplicated."""
    mastro_path = None
    for mod in addon_utils.modules():
        if mod.bl_info.get('name') == 'MaStro':
            mastro_path = Path(mod.__file__).parent.resolve()
            break

    if not mastro_path:
        return

    blend_file     = str(mastro_path / "mastro.blend")
    mats_to_import = {"MaStro Mass", "MaStro Mass Floor", "MaStro Section Colour", "MaStro Shadow Colour"}
    ngs_to_import  = {"Section RGB", "Shadow RGB"}

    try:
        with bpy.data.libraries.load(blend_file) as (data_from, data_to):
            # Import node groups first so materials find them already present.
            data_to.node_groups = [
                name for name in data_from.node_groups
                if name in ngs_to_import and name not in bpy.data.node_groups
            ]
            data_to.materials = [
                name for name in data_from.materials
                if name in mats_to_import and name not in bpy.data.materials
            ]
        # Deduplicate: if a canonical group and a numbered copy both exist,
        # reroute all nodes pointing at the copy to the canonical and remove it.
        _deduplicate_node_group("Section RGB")
        _deduplicate_node_group("Shadow RGB")

        processed = set()
        for ng in data_to.node_groups:
            if ng:
                clean_tree_recursive(ng, processed)
        for mat in data_to.materials:
            if mat:
                clear_asset_status(mat)
                if mat.node_tree:
                    clean_tree_recursive(mat.node_tree, processed)
        apply_section_color(get_prefs().section_color)
        apply_shadow_color(get_prefs().shadow_color)
    except Exception as e:
        print(f"MaStro Error (add_materials): {e}")


def apply_section_color(color):
    """Push an RGB value into the 'Section RGB' node group."""
    ng = bpy.data.node_groups.get("Section RGB")
    if ng is None:
        return
    node = ng.nodes.get("RGB")
    if node:
        node.outputs[0].default_value = (color[0], color[1], color[2], 1.0)
    mat = bpy.data.materials.get("MaStro Section Colour")
    if mat:
        mat.diffuse_color = (color[0], color[1], color[2], 1.0)


def apply_shadow_color(color):
    """Push an RGB value into the 'Shadow RGB' node group."""
    ng = bpy.data.node_groups.get("Shadow RGB")
    if ng is None:
        return
    node = ng.nodes.get("RGB")
    if node:
        node.outputs[0].default_value = (color[0], color[1], color[2], 1.0)
    mat = bpy.data.materials.get("MaStro Shadow Colour")
    if mat:
        mat.diffuse_color = (color[0], color[1], color[2], 1.0)


def add_nodes():
    """Main function to append nodes and clean all dependencies."""
    # Locate the MaStro addon path
    mastro_path = None
    for mod in addon_utils.modules():
        if mod.bl_info.get('name') == 'MaStro':
            mastro_path = Path(mod.__file__).parent.resolve()
            break

    if not mastro_path:
        print("Error: 'MaStro' addon not found.")
        return

    blend_file = str(mastro_path / "mastro.blend")
    nodes_to_import = {"MaStro Mass", "MaStro Block", "MaStro Street", "MaStro Dimension"}

    try:
        # Append node groups
        with bpy.data.libraries.load(blend_file) as (data_from, data_to):
            data_to.node_groups = [
                name for name in data_from.node_groups 
                if name in nodes_to_import and name not in bpy.data.node_groups
            ]
        
        # Start the recursive cleaning process
        processed_trees = set()
        for group in data_to.node_groups:
            if group:
                clean_tree_recursive(group, processed_trees)

    except Exception as e:
        print(f"MaStro Error: {e}")




# import bpy
# import addon_utils
# from pathlib import Path
# # import mastro nodes in the file

# def add_nodes():
#     for mod in addon_utils.modules():
#         if mod.bl_info['name'] == 'MaStro':
#             my_addon_path = Path(mod.__file__).parent.resolve()
#             break

#     # my_addon_path = Path(bpy.utils.user_resource('EXTENSIONS'))
#     blend_file_path = my_addon_path / "mastro.blend"
#     # if not os.path.isdir(blend_file_path): blend_file_path = my_addon_path / "vscode_development/mastro/mastro.blend"
#     inner_path = "NodeTree"
    
#     geoNodes_list = ("MaStro Mass", "MaStro Block", "MaStro Street", "MaStro Dimension")

#     for group in geoNodes_list:
#         if group not in bpy.data.node_groups:
#             bpy.ops.wm.link(
#                 filepath=str(blend_file_path / inner_path / group),
#                 directory=str(blend_file_path / inner_path),
#                 filename = group
#                 )   