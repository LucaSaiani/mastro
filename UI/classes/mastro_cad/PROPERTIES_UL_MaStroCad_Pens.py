import bpy
from bpy.types import UIList


class PROPERTIES_UL_MaStroCad_Pens(UIList):
    """Scene UIList — shows only active pens. No enable toggle."""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            split = layout.split(factor=0.12)
            split.label(text="Id: %d" % item.pen_id)
            rest = split.split(factor=0.25)
            sub = rest.row()
            sub.enabled = not item.locked
            sub.prop(item, "thickness", text="")
            row = rest.row(align=True)
            row.prop(item, "color", text="")
            row.prop(item, "fixed_colour", text="", icon='RESTRICT_COLOR_ON' if item.fixed_colour else 'RESTRICT_COLOR_OFF')
            row.label(text="", icon='LOCKED' if item.locked else 'BLANK1')
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text=f"{item.thickness:.2f}")

    def draw_filter(self, context, layout):
        pass

    def filter_items(self, context, data, propname):
        items = getattr(data, propname)
        flags = [self.bitflag_filter_item] * len(items)
        for i, item in enumerate(items):
            if not item.enabled:
                flags[i] &= ~self.bitflag_filter_item
        return flags, []
