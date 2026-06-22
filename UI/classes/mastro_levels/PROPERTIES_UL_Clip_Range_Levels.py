import bpy
from bpy.types import UIList

from ....Utils.mastro_levels.clip_range import (
    get_active_clip_range_set, get_set_levels, is_clip_range_unlimited,
)


class PROPERTIES_UL_Clip_Range_Levels(UIList):
    """Levels belonging to the set chosen for the viewport clip range
    (scene.mastro_clip_range_set_id), each with a checkbox toggling whether
    it's included in the contiguous clip range (see in_clip_range).

    The checkboxes are disabled while Unlimited is active, since the
    selection is then driven entirely by the active level and the list
    bounds (see toggle_unlimited_clip_range).
    """

    use_filter_show: bpy.props.BoolProperty(default=False)

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            row.label(text=f"{item.level:.3f}")
            row.label(text=item.name)

            sub = row.row(align=True)
            sub.alignment = 'RIGHT'
            sub.enabled = not is_clip_range_unlimited(context.scene)
            check_icon = 'HIDE_OFF' if item.in_clip_range else 'HIDE_ON'
            sub.prop(item, "in_clip_range", text="", icon=check_icon, emboss=False)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="")

    def draw_filter(self, context, layout):
        pass

    def filter_items(self, context, data, propname):
        items = getattr(data, propname)
        scene = context.scene
        level_set = get_active_clip_range_set(scene)
        member_ids = {lvl.id for lvl in get_set_levels(scene, level_set)}

        flt_flags = [
            self.bitflag_filter_item if item.id in member_ids else 0
            for item in items
        ]
        return flt_flags, []
