import bpy
from bpy.types import UIList, Operator
from ...properties.property_classes_cad import STANDARD_PENS


# ── Pen UIList ────────────────────────────────────────────────────────────────

class PREFERENCES_UL_MaStroCad_All_Pens(UIList):
    """Preferences UIList — standard pens only, enable toggle and colour editing."""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            split = layout.split(factor=0.12)
            split.label(text="Id: %d" % item.pen_id)
            rest = split.split(factor=0.25)
            sub = rest.row()
            sub.enabled = False
            sub.prop(item, "thickness", text="")
            row = rest.row(align=True)
            row.prop(item, "color", text="")
            row.prop(item, "enabled", text="")
            row.operator("mastrocad.reset_pen_color", text="", icon='LOOP_BACK').index = index
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text=f"{item.thickness:.2f}")

    def draw_filter(self, context, layout):
        pass

    def filter_items(self, context, data, propname):
        items = getattr(data, propname)
        flags = [self.bitflag_filter_item if item.locked else 0 for item in items]
        return flags, []


class PREFERENCES_OT_MaStroCad_Reset_Pen_Color(Operator):
    """Reset a standard pen colour to its default value."""
    bl_idname = "mastrocad.reset_pen_color"
    bl_label  = "Reset Colour"
    bl_options = {'REGISTER', 'UNDO'}

    index: bpy.props.IntProperty()

    def execute(self, context):
        pens = context.scene.mastro_cad_pens
        if not (0 <= self.index < len(pens)):
            return {'CANCELLED'}
        pen = pens[self.index]
        w = round(pen.thickness, 4)
        for data in STANDARD_PENS:
            if round(data["thickness"], 4) == w:
                pen.color = data["color"]
                break
        return {'FINISHED'}
