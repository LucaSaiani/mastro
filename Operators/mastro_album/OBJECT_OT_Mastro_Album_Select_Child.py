import bpy
from bpy.types import Operator
from bpy.props import StringProperty


class OBJECT_OT_Mastro_Album_Select_Child(Operator):
    """Select and activate a drawing listed under this MaStro album"""
    bl_idname = "object.mastro_album_select_child"
    bl_label = "Select Drawing"
    bl_options = {'REGISTER', 'UNDO'}

    object_name: StringProperty()

    def execute(self, context):
        obj = bpy.data.objects.get(self.object_name)
        if obj is None:
            return {'CANCELLED'}

        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        context.view_layer.objects.active = obj
        return {'FINISHED'}
