import bpy
from bpy.types import UIList


class PROPERTIES_UL_Camera_Sets(UIList):
    bl_idname = "PROPERTIES_UL_Camera_Sets"

    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):
        row = layout.row(align=True)

        # Column 1: collection icon + set name
        row.label(text="", icon='DOCUMENTS')
        row.prop(item, "name", text="", emboss=False)

        # Right: camera count
        sub = row.row(align=True)
        sub.alignment = 'RIGHT'
        sub.label(text=str(len(item.cameras)))
