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
    def _assign_flag_for(cls, data):
        """Return the assign_to_* attribute name matching the object's MaStro type."""
        if data.get("MaStro street"):
            return "assign_to_street"
        if data.get("MaStro plan"):
            return "assign_to_plan"
        if data.get("MaStro drawing"):
            return "assign_to_drawing"
        return "assign_to_mass"

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
                 "MaStro street" in data or
                 "MaStro plan" in data or
                 "MaStro drawing" in data)):
            return False
        assign_flag = cls._assign_flag_for(data)
        return any(
            p.committed and
            getattr(p, assign_flag) and
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

        assign_flag = self._assign_flag_for(obj.data)

        any_shown = False
        for attr in custom_list:
            if not getattr(attr, assign_flag): continue

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
