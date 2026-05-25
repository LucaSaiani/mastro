import bpy
from bpy.types import Panel


class VIEW3D_PT_Mastro_Custom_Properties(Panel):
    """Sidebar panel showing custom properties for the active MaStro object."""
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "MaStro"
    bl_label       = "Custom Properties"
    bl_order       = 99

    @classmethod
    def poll(cls, context):
        obj = context.object
        if obj is None or obj.type != 'MESH':
            return False
        data = obj.data
        if obj.mode == 'EDIT':
            return False
        if not ("MaStro object" in data and
                ("MaStro mass" in data or
                 "MaStro block" in data or
                 "MaStro street" in data)):
            return False
        is_street = bool(data.get("MaStro street"))
        is_mass   = not is_street
        return any(
            p.committed and
            (is_mass   and p.assign_to_mass or
             is_street and p.assign_to_street) and
            f"_{p.name}" in obj
            for p in context.scene.mastro_custom_property_name_list
        )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        obj        = context.object
        scene      = context.scene
        custom_list = scene.mastro_custom_property_name_list

        if not custom_list:
            layout.label(text="No custom properties defined.", icon='INFO')
            return

        is_street = bool(obj.data.get("MaStro street"))
        is_mass   = not is_street

        any_shown = False
        for attr in custom_list:
            if is_mass   and not attr.assign_to_mass:   continue
            if is_street and not attr.assign_to_street: continue

            key = f"_{attr.name}"
            if key not in obj:
                continue

            if attr.property_type == 'STRING':
                enum_name = f"mastro_string_enum_{attr.id}"
                if hasattr(scene, enum_name):
                    layout.prop(scene, enum_name, text=attr.name)
                else:
                    layout.label(text=f"{attr.name}: not committed")
            else:
                layout.prop(obj, f'["{key}"]', text=attr.name)
            any_shown = True

        if not any_shown:
            layout.label(text="No custom properties assigned.", icon='INFO')
