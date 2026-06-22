from bpy.types import UIList


class PROPERTIES_UL_Album_Children(UIList):
    """Lists the objects parented to a MaStro album."""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            row.label(text=item.object.name, icon='OBJECT_DATA')
            row.operator(
                "object.mastro_album_remove_child",
                text="",
                icon='TRASH',
                emboss=False,
            ).object_name = item.object.name
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon='OBJECT_DATA')

    def filter_items(self, context, data, propname):
        # Hide stale entries whose object reference no longer resolves —
        # can happen if a child was deleted outside our own operators and
        # the active-object sync hasn't run yet.
        items = getattr(data, propname)
        filtered = [self.bitflag_filter_item if item.object else 0 for item in items]
        return filtered, []

    def draw_filter(self, context, layout):
        pass
