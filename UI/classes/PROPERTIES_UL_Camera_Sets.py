import bpy
from bpy.types import UIList


class PROPERTIES_UL_Camera_Sets(UIList):
    bl_idname = "PROPERTIES_UL_Camera_Sets"

    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):
        row = layout.row(align=True)
        if item.is_default:
            row.label(text="", icon='LOCKED')
        else:
            row.label(text="", icon='NONE')
        row.prop(item, "name", text="", emboss=False)
        row.label(text=str(len(item.cameras)), icon='CAMERA_DATA')
