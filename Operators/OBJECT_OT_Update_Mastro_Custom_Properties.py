import bpy
from bpy.types import Operator


def add_custom_properties_to_object(obj, is_street=False):
    """Add committed scene custom properties to a single newly created MaStro object."""
    scene = bpy.context.scene
    is_mass = not is_street
    for prop in scene.mastro_custom_property_name_list:
        if not prop.committed:                        continue
        if is_mass   and not prop.assign_to_mass:    continue
        if is_street and not prop.assign_to_street:  continue
        key = f"mastro_custom_{prop.id}"
        if prop.property_type == 'INT':
            obj[key] = prop.default_int
        elif prop.property_type == 'FLOAT':
            obj[key] = prop.default_float
        elif prop.property_type == 'BOOL':
            obj[key] = prop.default_bool
        elif prop.property_type == 'STRING':
            obj[key] = prop.default_string


class OBJECT_OT_Update_Mastro_Custom_Properties(Operator):
    '''Add or update custom properties on all MaStro objects in the scene'''
    bl_idname = "object.update_mastro_custom_properties"
    bl_label  = "Update Custom Properties"
    bl_options = {'REGISTER', 'UNDO'}

    property_to_update: bpy.props.StringProperty(name="Property to update")
    property_id:        bpy.props.IntProperty(name="Property id", default=-1)
    remove:             bpy.props.BoolProperty(name="Remove", default=False)

    def execute(self, context):
        scene = context.scene
        custom_list = scene.mastro_custom_property_name_list

        if self.property_id >= 0:
            props = [p for p in custom_list if p.id == self.property_id]
        else:
            props = list(custom_list)

        for obj in bpy.data.objects:
            if obj.type != 'MESH' or "MaStro object" not in obj.data:
                continue
            is_street = bool(obj.data.get("MaStro street"))
            is_mass   = not is_street

            if self.property_to_update == "mass"   and not is_mass:   continue
            if self.property_to_update == "street" and not is_street: continue

            for prop in props:
                key = f"mastro_custom_{prop.id}"

                if self.remove:
                    if key in obj:
                        del obj[key]
                else:
                    if is_mass   and not prop.assign_to_mass:   continue
                    if is_street and not prop.assign_to_street: continue

                    if prop.property_type == 'INT':
                        obj[key] = obj.get(key, prop.default_int)
                    elif prop.property_type == 'FLOAT':
                        obj[key] = obj.get(key, prop.default_float)
                    elif prop.property_type == 'BOOL':
                        obj[key] = obj.get(key, prop.default_bool)
                    elif prop.property_type == 'STRING':
                        obj[key] = obj.get(key, prop.default_string)

        if not self.remove:
            for prop in props:
                prop.committed = True

        for area in bpy.context.screen.areas:
            area.tag_redraw()
        return {'FINISHED'}


class OBJECT_OT_Remove_Mastro_Custom_Property(Operator):
    '''Remove a custom property from all MaStro objects of the given type'''
    bl_idname  = "object.mastro_remove_custom_property"
    bl_label   = "Remove Custom Property"
    bl_options = {'REGISTER', 'UNDO'}

    property_id: bpy.props.IntProperty()
    object_type: bpy.props.StringProperty()  # 'mass', 'street', or 'all'

    def invoke(self, context, event):
        prop = next((p for p in context.scene.mastro_custom_property_name_list
                     if p.id == self.property_id), None)
        name = prop.name if prop else f"id {self.property_id}"
        self.bl_label = f"Remove \"{name}\" from all {self.object_type} objects?"
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        bpy.ops.object.update_mastro_custom_properties(
            property_to_update=self.object_type,
            property_id=self.property_id,
            remove=True)
        custom_list = context.scene.mastro_custom_property_name_list
        idx = next((i for i, p in enumerate(custom_list) if p.id == self.property_id), None)
        if idx is not None:
            custom_list.remove(idx)
            context.scene.mastro_custom_property_name_list_index = max(0, idx - 1)
        for area in context.screen.areas:
            area.tag_redraw()
        return {'FINISHED'}
