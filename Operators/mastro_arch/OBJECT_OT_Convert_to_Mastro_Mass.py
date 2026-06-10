import bpy
from bpy.types import Operator

from ...Utils.mastro_arch.add_attributes_mass import add_mass_attributes
from ...Utils.add_nodes import add_nodes, add_materials
from ..mastro_custom_properties.OBJECT_OT_Update_Mastro_Custom_Properties import add_custom_properties_to_object


class OBJECT_OT_Convert_to_Mastro_Mass(Operator):
    bl_idname = "object.mastro_convert_to_mastro_mass"
    bl_label = "Convert to MaStro Mass"
    bl_description = "Convert the selected mesh to a MaStro mass with its attributes"

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
            add_mass_attributes(obj, "MaStro mass")
            add_custom_properties_to_object(obj, is_street=False)

        add_nodes()
        add_materials()
        return {'FINISHED'}
