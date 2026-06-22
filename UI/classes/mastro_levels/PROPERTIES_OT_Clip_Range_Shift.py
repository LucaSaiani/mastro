from bpy.types import Operator
from bpy.props import IntProperty

from ....Utils.mastro_levels.clip_range import (
    shift_clip_range, update_clip_from_selection, is_bottom_ortho,
)


class PROPERTIES_OT_Clip_Range_Shift(Operator):
    """Move the selected clip range up or down by one level per click"""
    bl_idname = "mastro_clip_range.shift"
    bl_label = "Shift Clip Range"
    bl_options = {'REGISTER', 'UNDO'}

    direction: IntProperty(default=1)  # +1 (up) or -1 (down) list-positions per click

    def execute(self, context):
        space = getattr(context, "space_data", None)
        is_bottom = space is not None and space.type == 'VIEW_3D' and is_bottom_ortho(space.region_3d)
        shift_clip_range(context.scene, self.direction, is_bottom)
        update_clip_from_selection(context)
        for area in context.screen.areas:
            area.tag_redraw()
        return {'FINISHED'}
