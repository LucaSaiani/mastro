import bpy
from bpy.types import Operator

from ...Utils.mastro_cad.convert_to_drawing import convert_object_to_mastro_cad


class OBJECT_OT_Convert_to_Mastro_Cad(Operator):
    bl_idname = "object.mastro_convert_to_mastro_cad"
    bl_label = "Convert to MaStro CAD"
    bl_description = "Convert the selected mesh to a MaStro CAD drawing with its attributes"

    @classmethod
    def poll(cls, context):
        if context.mode != 'OBJECT':
            return False

        active = context.active_object
        if not active or active.type != 'MESH':
            return False

        selected_objects = bpy.context.selected_objects
        selected_meshes = [obj for obj in selected_objects if obj.type == 'MESH']
        return len(selected_meshes) > 0

    def execute(self, context):
        selected_objects = bpy.context.selected_objects
        selected_meshes = [obj for obj in selected_objects if obj.type == 'MESH']

        for obj in selected_meshes:
            convert_object_to_mastro_cad(context, obj)

        return {'FINISHED'}
