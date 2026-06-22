from bpy.types import UIList


class PROPERTIES_UL_Level_Set(UIList):
    """UIList for the list of level sets."""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            row.label(text="", icon='ALIGN_JUSTIFY')
            # The "All Levels" set (id 0) always contains every level, so
            # its name is fixed and its member count is read from
            # mastro_level_list instead of its own (empty) levels collection.
            if item.id == 0:
                row.label(text=item.name)
                count = len(context.scene.mastro_level_list)
            else:
                row.prop(item, "name", text="", emboss=False)
                count = len(item.levels)

            sub = row.row(align=True)
            sub.alignment = 'RIGHT'
            sub.label(text=str(count))
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="")

    def filter_items(self, context, data, propname):
        items = getattr(data, propname)
        return [self.bitflag_filter_item] * len(items), []

    def draw_filter(self, context, layout):
        pass
