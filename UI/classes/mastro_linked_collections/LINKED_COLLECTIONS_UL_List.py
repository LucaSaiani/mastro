from bpy.types import UIList


_STATUS_ICON = {
    'LOADED': 'CHECKBOX_HLT',
    'UNLOADED': 'CHECKBOX_DEHLT',
    'BROKEN': 'ERROR',
}


class LINKED_COLLECTIONS_UL_List(UIList):
    """UIList showing collections registered in the mastro Linked Collections manager."""
    bl_idname = "LINKED_COLLECTIONS_UL_List"

    def draw_item(self, context, layout, data, item, icon,
                  active_data, active_propname, index):
        row = layout.row(align=True)
        row.label(text="", icon=_STATUS_ICON.get(item.status, 'QUESTION'))
        row.label(text=item.collection_name)
