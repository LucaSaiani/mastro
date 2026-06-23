import bpy
from bpy.types import Operator

from ...Utils.mastro_arch.duplicate_plan_to_levels import duplicate_plan_to_levels, levels_missing_a_plan
from ...Utils.mastro_levels.clip_range import active_clip_range_side_or_top, get_active_clip_range_set, get_set_levels


class OBJECT_OT_Mastro_Plan_Duplicate_To_Levels(Operator):
    """Duplicate the active MaStro plan once per level in the active Clip
    Range's level set, skipping levels that already have a plan locked to
    them. Reusable wherever plans need to be propagated across levels - the
    initial "duplicate to set" option on Add Plan (see OBJECT_OT_Add_Mastro_Plan)
    and any future manual "duplicate to other levels" command both go
    through this same operator."""
    bl_idname = "object.mastro_plan_duplicate_to_levels"
    bl_label = "Duplicate Plan to Levels"
    bl_options = {'REGISTER', 'UNDO'}

    link_mesh: bpy.props.BoolProperty(
        name="Link Mesh",
        description="Share the same mesh data across every duplicated plan, "
                    "like repeated floors that should stay in sync, instead "
                    "of giving each its own independent copy",
        default=True,
    )

    def execute(self, context):
        source_obj = context.object
        if source_obj is None or source_obj.type != "MESH" or "MaStro plan" not in source_obj.data:
            return {'CANCELLED'}

        side = active_clip_range_side_or_top(context)
        level_set = get_active_clip_range_set(context.scene, side)
        levels = get_set_levels(context.scene, level_set)
        levels = levels_missing_a_plan(levels)
        if not levels:
            return {'CANCELLED'}

        new_objects = duplicate_plan_to_levels(context, source_obj, levels, self.link_mesh)

        bpy.ops.object.select_all(action='DESELECT')
        for obj in new_objects:
            obj.select_set(True)
        context.view_layer.objects.active = new_objects[-1]

        return {'FINISHED'}
