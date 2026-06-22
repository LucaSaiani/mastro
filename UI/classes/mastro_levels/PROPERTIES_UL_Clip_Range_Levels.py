import bpy
from bpy.types import UIList

from ....Utils.mastro_levels.clip_range import (
    get_active_clip_range_set, get_set_levels, is_clip_range_unlimited,
    is_top_bottom_ortho, get_view_side,
)


def _side_from_context(context):
    """"top" or "bottom" matching context.space_data's view, or None if
    it's not a Top/Bottom ortho VIEW_3D (then there's nothing to show)."""
    space = getattr(context, "space_data", None)
    if space is None or space.type != 'VIEW_3D' or not is_top_bottom_ortho(space.region_3d):
        return None
    return get_view_side(space.region_3d)


class PROPERTIES_UL_Clip_Range_Levels(UIList):
    """Levels belonging to the set chosen for the viewport clip range on
    the active viewport's side (scene.mastro_clip_range_set_id_top or
    _bottom), each with a checkbox toggling whether it's included in the
    contiguous clip range (see in_clip_range).

    The checkboxes are disabled while Unlimited is active, since the
    selection is then driven entirely by the active level and the list
    bounds (see toggle_unlimited_clip_range).
    """

    use_filter_show: bpy.props.BoolProperty(default=False)

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            side = _side_from_context(context)

            # Explicit +/- sign and the scene's length unit (e.g. "m"),
            # rather than a bare number, so it's clear at a glance whether
            # a level is above or below AOD (elevation 0).
            # precision=4 because bpy.utils.units.to_string rounds before
            # trimming trailing zeros, so 3 ends up dropping the last
            # displayed digit in some cases - 4 reliably keeps 3 decimals.
            unit_system = context.scene.unit_settings.system
            level_text = bpy.utils.units.to_string(unit_system, 'LENGTH', item.level, precision=4)
            if item.level > 0:
                level_text = "+" + level_text

            row = layout.row(align=True)
            row.label(text=level_text)
            row.label(text=item.name)

            sub = row.row(align=True)
            sub.alignment = 'RIGHT'
            sub.enabled = side is not None and not is_clip_range_unlimited(context.scene, side)
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
        side = _side_from_context(context)
        if side is None:
            return [0] * len(items), []

        level_set = get_active_clip_range_set(scene, side)
        member_ids = {lvl.id for lvl in get_set_levels(scene, level_set)}

        flt_flags = [
            self.bitflag_filter_item if item.id in member_ids else 0
            for item in items
        ]
        return flt_flags, []
