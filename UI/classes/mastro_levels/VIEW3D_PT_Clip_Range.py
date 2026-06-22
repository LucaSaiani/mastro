import bpy

from ....Utils.mastro_levels.clip_range import (
    is_top_bottom_ortho, get_view_side, is_clip_range_unlimited,
)


def _draw_clip_range(self, context):
    """Appended to Blender's native View3D 'View' panel (next to Lens /
    Clip Start / Clip End), since the clip range only makes sense as part
    of that panel - not as a standalone MaStro panel."""
    space = context.space_data
    if space is None or space.type != 'VIEW_3D':
        return
    region_3d = space.region_3d
    if not is_top_bottom_ortho(region_3d):
        return

    scene = context.scene
    if not scene.mastro_level_set_list:
        return

    side = get_view_side(region_3d)
    is_bottom = side == "bottom"

    layout = self.layout
    layout.separator()
    layout.label(text="Clip Range")
    layout.prop(scene, f"mastro_clip_range_set_id_{side}", text="Set")

    # "Unlimited" pushes the far clip plane out, which - given the
    # current/count model in clip_range.py - extends towards the bottom
    # of the list (lower elevations) in Top view, or towards the top of
    # the list (higher elevations) in Bottom view. Placing the button on
    # that same side of the list visually matches which direction it
    # extends, with no gap so it reads as part of the same control.
    unlimited = is_clip_range_unlimited(scene, side)

    if is_bottom:
        layout.operator("mastro_clip_range.unlimited", icon='ARROW_LEFTRIGHT', depress=unlimited)

    row = layout.row()
    row.template_list("PROPERTIES_UL_Clip_Range_Levels", "clip_range_levels", scene,
                       "mastro_level_list", scene, f"mastro_clip_range_list_index_{side}", rows=4)
    col = row.column(align=True)
    # mastro_level_list is sorted by descending level (see sort_level_list),
    # so a higher elevation sits at a *lower* list index: the "up" arrow
    # (towards higher levels) must shift by -1, "down" by +1.
    col.operator("mastro_clip_range.shift", icon='TRIA_UP', text="").direction = -1
    col.operator("mastro_clip_range.shift", icon='TRIA_DOWN', text="").direction = 1

    if not is_bottom:
        layout.operator("mastro_clip_range.unlimited", icon='ARROW_LEFTRIGHT', depress=unlimited)


def register():
    bpy.types.VIEW3D_PT_view3d_properties.append(_draw_clip_range)


def unregister():
    bpy.types.VIEW3D_PT_view3d_properties.remove(_draw_clip_range)
