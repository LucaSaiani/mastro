from bpy.types import Operator

from ....Utils.mastro_levels.clip_range import (
    toggle_unlimited_clip_range, update_clip_from_selection, is_top_bottom_ortho, get_view_side,
)


class PROPERTIES_OT_Clip_Range_Unlimited(Operator):
    """Toggle Unlimited: extend the clip range to cover every level from
    the active one to the far end of the list. Re-pressing restores the
    selection that was active before Unlimited was turned on"""
    bl_idname = "mastro_clip_range.unlimited"
    bl_label = "Unlimited"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        space = getattr(context, "space_data", None)
        if space is None or space.type != 'VIEW_3D' or not is_top_bottom_ortho(space.region_3d):
            return {'CANCELLED'}
        side = get_view_side(space.region_3d)
        toggle_unlimited_clip_range(context.scene, side)
        update_clip_from_selection(context)
        for area in context.screen.areas:
            area.tag_redraw()
        return {'FINISHED'}
