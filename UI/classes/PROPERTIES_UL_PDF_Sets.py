from bpy.types import UIList


class PROPERTIES_UL_PDF_Sets(UIList):
    bl_idname = "PROPERTIES_UL_PDF_Sets"

    def draw_item(self, context, layout, data, item, icon,
                  active_data, active_propname, index):
        row = layout.row(align=True)
        row.label(text="", icon='DOCUMENTS')
        row.prop(item, "name", text="", emboss=False)

        sub = row.row(align=True)
        sub.alignment = 'RIGHT'
        bind_icon = 'LINKED' if item.bind_pages else 'UNLINKED'
        sub.prop(item, "bind_pages", text="", icon=bind_icon, emboss=False)
        sub.label(text=str(len(item.frames)))
