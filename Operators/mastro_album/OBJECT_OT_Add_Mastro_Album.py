import bpy
from bpy.types import Operator
from bpy_extras.object_utils import AddObjectHelper, object_data_add


class OBJECT_OT_Add_Mastro_Album(Operator, AddObjectHelper):
    """Add a MaStro album"""
    bl_idname = "object.mastro_add_mastro_album"
    bl_label = "Album"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = object_data_add(context, None, operator=self, name="MaStro album")
        obj.empty_display_type = 'PLAIN_AXES'

        obj["MaStro object"] = True
        obj["MaStro album"] = True

        return {'FINISHED'}
