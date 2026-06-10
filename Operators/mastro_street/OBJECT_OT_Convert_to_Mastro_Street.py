import bpy
from bpy.types import Operator

from ...Utils.mastro_street.add_attributes_street import add_street_attributes
from ...Utils.add_nodes import add_nodes, add_materials
from ..mastro_custom_properties.OBJECT_OT_Update_Mastro_Custom_Properties import add_custom_properties_to_object


class OBJECT_OT_Convert_to_Mastro_Street(Operator):
    bl_idname = "object.mastro_convert_to_mastro_street"
    bl_label = "Convert to MaStro Street"
    bl_description = "Convert the selected mesh to a MaStro street with its attributes"

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
            add_street_attributes(obj)
            add_custom_properties_to_object(obj, is_street=True)

        add_nodes()
        add_materials()
        return {'FINISHED'}
