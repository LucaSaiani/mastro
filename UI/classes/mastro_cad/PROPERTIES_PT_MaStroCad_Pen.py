import bpy
from bpy.types import Panel, Operator
from ...properties.property_classes_cad import _insert_pen_sorted


class PROPERTIES_OT_MaStroCad_Add_Pen(Operator):
    """Add a custom pen, inserted in thickness order. Duplicate widths are not allowed."""
    bl_idname = "mastrocad.add_pen"
    bl_label  = "Add Pen"
    bl_options = {'REGISTER', 'UNDO'}

    thickness: bpy.props.FloatProperty(name="Thickness (mm)", min=0.01, max=10.0, default=0.25)
    color: bpy.props.FloatVectorProperty(name="Colour", subtype='COLOR', size=4,
                                         min=0.0, max=1.0, default=(0.5, 0.5, 0.5, 1.0))

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        item = _insert_pen_sorted(
            context.scene.mastro_cad_pens,
            self.thickness, self.color, enabled=True, locked=False,
        )
        if item is None:
            self.report({'WARNING'}, f"A pen with width {self.thickness:.2f} mm already exists")
            return {'CANCELLED'}
        return {'FINISHED'}


class PROPERTIES_OT_MaStroCad_Remove_Pen(Operator):
    """Remove the selected custom pen (locked pens cannot be removed)."""
    bl_idname = "mastrocad.remove_pen"
    bl_label  = "Remove Pen"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        pens  = scene.mastro_cad_pens
        idx   = scene.mastro_cad_pen_index
        if not (0 <= idx < len(pens)):
            return {'CANCELLED'}
        if pens[idx].locked:
            self.report({'WARNING'}, "Standard pens cannot be removed")
            return {'CANCELLED'}
        removed_id = pens[idx].pen_id
        pens.remove(idx)
        scene.mastro_cad_pen_index = max(0, idx - 1)
        # Reassign layers that referenced the removed pen to the smallest available pen.
        valid_ids = {p.pen_id for p in pens if p.enabled}
        if valid_ids:
            fallback = min(valid_ids)
            for layer in scene.mastro_cad_layers:
                if layer.pen_id == removed_id:
                    layer.pen_id = fallback
        return {'FINISHED'}


class PROPERTIES_PT_MaStroCad_Drawing(Panel):
    """Scene → MaStro → Drawing — parent panel for all drawing settings."""
    bl_space_type  = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_label       = "Drawing"
    bl_parent_id   = "PROPERTIES_PT_Mastro_Project_Data"
    bl_options     = {'DEFAULT_CLOSED'}
    bl_order       = 10
    bl_context     = "scene"

    def draw(self, context):
        pass


class PROPERTIES_PT_MaStroCad_Pens(Panel):
    """Scene → MaStro → Drawing → Pens."""
    bl_space_type  = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_label       = "Pens"
    bl_parent_id   = "PROPERTIES_PT_MaStroCad_Drawing"
    bl_options     = {'DEFAULT_CLOSED'}
    bl_context     = "scene"

    def draw(self, context):
        scene  = context.scene
        layout = self.layout

        row = layout.row()
        row.template_list(
            "PROPERTIES_UL_MaStroCad_Pens", "",
            scene, "mastro_cad_pens",
            scene, "mastro_cad_pen_index",
            rows=6,
        )
        col = row.column(align=True)
        col.operator("mastrocad.add_pen",    icon='ADD',    text="")
        col.operator("mastrocad.remove_pen", icon='REMOVE', text="")
