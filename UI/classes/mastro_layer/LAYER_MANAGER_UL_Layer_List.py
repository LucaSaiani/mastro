import bpy
from bpy.types import UIList


class LAYER_MANAGER_UL_Layer_List(UIList):
    """UIList showing view-layer shadow slots; supports inline rename."""
    bl_idname = "LAYER_MANAGER_UL_layer_list"

    def draw_item(self, context, layout, data, item, icon,
                  active_data, active_propname, index):
        layout.prop(item, "name", text="", emboss=False)
