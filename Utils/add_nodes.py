import bpy
import addon_utils
from pathlib import Path
# import mastro nodes in the file

def add_nodes():
    for mod in addon_utils.modules():
        if mod.bl_info['name'] == 'MaStro':
            my_addon_path = Path(mod.__file__).parent.resolve()
            break

    # my_addon_path = Path(bpy.utils.user_resource('EXTENSIONS'))
    blend_file_path = my_addon_path / "mastro.blend"
    # if not os.path.isdir(blend_file_path): blend_file_path = my_addon_path / "vscode_development/mastro/mastro.blend"
    inner_path = "NodeTree"
    
    geoNodes_list = ("MaStro Mass", "MaStro Block", "MaStro Street", "MaStro Dimension")

    for group in geoNodes_list:
        if group not in bpy.data.node_groups:
            bpy.ops.wm.link(
                filepath=str(blend_file_path / inner_path / group),
                directory=str(blend_file_path / inner_path),
                filename = group
                )   