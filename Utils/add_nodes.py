import bpy
import addon_utils
from pathlib import Path

def clear_asset_status(data_block):
    """Clears the asset status of any data block (NodeTree, Material, etc.)"""
    if data_block and hasattr(data_block, "asset_data") and data_block.asset_data:
        data_block.asset_clear()
        # print(f"MaStro: Asset status cleared for {type(data_block).__name__}: '{data_block.name}'")

def clean_tree_recursive(tree, processed_trees):
    """
    Recursively scans a node tree (Geometry Nodes or Shader Nodes) 
    to clear asset status from nested groups and materials.
    """
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