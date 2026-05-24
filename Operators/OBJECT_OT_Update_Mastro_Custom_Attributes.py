import bpy
from bpy.types import Operator


def add_custom_properties_to_object(obj, is_street=False):
    """Add committed scene custom properties to a single newly created MaStro object."""
    scene = bpy.context.scene
    is_mass = not is_street
    for attr in scene.mastro_custom_property_name_list:
        if not attr.committed:                       continue
        if is_mass   and not attr.assign_to_mass:   continue
        if is_street and not attr.assign_to_street: continue
        key = f"mastro_custom_{attr.id}"
        if attr.property_type == 'INT':
            obj[key] = attr.default_int
        elif attr.property_type == 'FLOAT':
            obj[key] = attr.default_float
        elif attr.property_type == 'BOOL':
            obj[key] = attr.default_bool
        elif attr.property_type == 'STRING':
            obj[key] = attr.default_string


class OBJECT_OT_Update_Mastro_Custom_Attributes(Operator):
    '''Add or update custom properties on all MaStro objects in the scene'''
    bl_idname = "object.update_mastro_custom_attributes"
    bl_label = "Update Custom Properties"
    bl_options = {'REGISTER', 'UNDO'}

    attribute_to_update: bpy.props.StringProperty(name="Property to update")
    attribute_id:        bpy.props.IntProperty(name="Property id", default=-1)
    remove:              bpy.props.BoolProperty(name="Remove", default=False)

    def execute(self, context):
        scene = context.scene
        custom_list = scene.mastro_custom_property_name_list

        if self.attribute_id >= 0:
            attrs = [a for a in custom_list if a.id == self.attribute_id]
        else:
            attrs = list(custom_list)

        for obj in bpy.data.objects:
            if obj.type != 'MESH' or "MaStro object" not in obj.data:
                continue
            is_street = bool(obj.data.get("MaStro street"))
            is_mass   = not is_street

            if self.attribute_to_update == "mass"   and not is_mass:   continue
            if self.attribute_to_update == "street" and not is_street: continue

            for attr in attrs:
                key = f"mastro_custom_{attr.id}"

                if self.remove:
                    if key in obj:
                        del obj[key]
                else:
                    if is_mass   and not attr.assign_to_mass:   continue
                    if is_street and not attr.assign_to_street: continue

                    if attr.property_type == 'INT':
                        obj[key] = obj.get(key, attr.default_int)
                    elif attr.property_type == 'FLOAT':
                        obj[key] = obj.get(key, attr.default_float)
                    elif attr.property_type == 'BOOL':
                        obj[key] = obj.get(key, attr.default_bool)
                    elif attr.property_type == 'STRING':
                        obj[key] = obj.get(key, attr.default_string)

        if not self.remove:
            for attr in attrs:
                attr.committed = True

        return {'FINISHED'}


class OBJECT_OT_Remove_Mastro_Custom_Attribute(Operator):
    '''Remove a custom property from all MaStro objects of the given type'''
    bl_idname  = "object.mastro_remove_custom_attribute"
    bl_label   = "Remove Custom Property"
    bl_options = {'REGISTER', 'UNDO'}

    attribute_id:  bpy.props.IntProperty()
    object_type:   bpy.props.StringProperty()  # 'mass' or 'street'

    def invoke(self, context, event):
        attr = next((a for a in context.scene.mastro_custom_property_name_list
                     if a.id == self.attribute_id), None)
        name = attr.name if attr else f"id {self.attribute_id}"
        self.bl_label = f"Remove \"{name}\" from all {self.object_type} objects?"
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        bpy.ops.object.update_mastro_custom_attributes(
            attribute_to_update=self.object_type,
            attribute_id=self.attribute_id,
            remove=True)
        custom_list = context.scene.mastro_custom_property_name_list
        idx = next((i for i, a in enumerate(custom_list) if a.id == self.attribute_id), None)
        if idx is not None:
            custom_list.remove(idx)
            context.scene.mastro_custom_property_name_list_index = max(0, idx - 1)
        for area in context.screen.areas:
            area.tag_redraw()
        return {'FINISHED'}
