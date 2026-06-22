from bpy.types import UIList


class PROPERTIES_UL_Level(UIList):
    """UIList for the project level list: id, level, name."""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            split = layout.split(factor=0.2)
            split.label(text=f"Id: {item.id}")
            split2 = split.split(factor=0.45)
            # The default AOD level (id 0) is fixed at level 0 and cannot be
            # renamed, so its level/name fields are greyed out here too.
            sub = split2.row()
            sub.enabled = item.id != 0
            sub.prop(item, "level", text="")
            row = split2.row(align=True)
            row.enabled = item.id != 0
            row.prop(item, "name", text="", emboss=False)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="")

    def filter_items(self, context, data, propname):
        items = getattr(data, propname)
        return [self.bitflag_filter_item] * len(items), []

    def draw_filter(self, context, layout):
        pass
