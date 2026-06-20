from bpy.types import UIList


class MASTRO_UL_Print_Sets(UIList):
    bl_idname = "MASTRO_UL_Print_Sets"

    def draw_item(self, context, layout, data, item, icon,
                  active_data, active_propname, index):
        row = layout.row(align=True)
        row.prop(item, "name", text="", emboss=False)

    def filter_items(self, context, data, propname):
        items = getattr(data, propname)
        return [self.bitflag_filter_item] * len(items), []

    def draw_filter(self, context, layout):
        pass


class MASTRO_UL_Print_Set_Params(UIList):
    bl_idname = "MASTRO_UL_Print_Set_Params"

    def draw_item(self, context, layout, data, item, icon,
                  active_data, active_propname, index):
        row = layout.row(align=True)
        row.prop(item, "param_name", text="")
        row.prop(item, "group", text="Group")
        row.prop(item, "total", text="Total")
        row.prop(item, "calc", text="")
        icon = 'SORT_DESC' if item.sort_desc else 'SORT_ASC'
        row.prop(item, "sort_desc", text="", icon=icon, toggle=True)
        row.separator()

    def filter_items(self, context, data, propname):
        items = getattr(data, propname)
        return [self.bitflag_filter_item] * len(items), []

    def draw_filter(self, context, layout):
        pass
