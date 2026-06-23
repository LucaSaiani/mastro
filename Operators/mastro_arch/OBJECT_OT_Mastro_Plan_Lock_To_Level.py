import bpy
from bpy.types import Operator

from ...Utils.mastro_arch.plan_drivers import link_all_plan_drivers, unlink_all_plan_drivers
from ...Utils.mastro_arch.update_plan_attributes import update_plan_attributes, plan_name_for_level
from ...Utils.mastro_levels.clip_range import active_clip_range_level_id
from ...Utils.mastro_preferences.get_preferences import get_prefs


class OBJECT_OT_Mastro_Plan_Unlock_From_Level(Operator):
    """Unlock a MaStro plan from its level: removes the FFL/height drivers
    so the user can set the modifier's inputs manually. Z and height keep
    whatever value they last had.

    mastro_bottom_level_id is reset to -1 ("no level"): once unlocked, FFL
    can be hand-edited and drift away from any level's actual elevation, so
    keeping the old id around would make the plan look like it still
    belongs to that level - confusing update_plan_attributes (if re-locked
    through some other path) and, more immediately, the "one plan per
    level" duplicate check used when batch-creating plans across a level
    set (see OBJECT_OT_Mastro_Plan_Duplicate_To_Levels)."""
    bl_idname = "object.mastro_plan_unlock_from_level"
    bl_label = "Unlock from Level"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.object
        modifier = obj.modifiers.get("MaStro Plan")
        if modifier is None or modifier.node_group is None:
            return {'CANCELLED'}

        obj.mastro_props.mastro_lock_to_level = False
        obj.mastro_props.mastro_bottom_level_id = -1
        unlink_all_plan_drivers(obj, modifier)

        return {'FINISHED'}


class OBJECT_OT_Mastro_Plan_Lock_To_Level(Operator):
    """Lock a MaStro plan to a level: links the FFL/height drivers to
    obj.mastro_props and recomputes Z and height from the level list.

    level_id selects which level becomes the new bottom level; -1 (the
    default) means "whichever level is active in the Clip Range right now"."""
    bl_idname = "object.mastro_plan_lock_to_level"
    bl_label = "Lock to Level"
    bl_options = {'REGISTER', 'UNDO'}

    level_id: bpy.props.IntProperty(name="Level Id", default=-1)

    def execute(self, context):
        obj = context.object
        modifier = obj.modifiers.get("MaStro Plan")
        if modifier is None or modifier.node_group is None:
            return {'CANCELLED'}

        level_id = self.level_id
        if level_id == -1:
            level_id = active_clip_range_level_id(context)
        if level_id is None:
            return {'CANCELLED'}

        obj.mastro_props.mastro_bottom_level_id = level_id
        obj.mastro_props.mastro_lock_to_level = True

        # modifier.properties.inputs is only populated after Blender syncs the
        # modifier with the node group interface; force that sync now so
        # link_all_plan_drivers can find every input socket (see
        # OBJECT_OT_Add_Mastro_Plan, which has the same requirement).
        context.view_layer.update()

        link_all_plan_drivers(obj, modifier)
        update_plan_attributes(context)

        if get_prefs().rename_plan_on_relock:
            level = next((lvl for lvl in context.scene.mastro_level_list
                          if lvl.id == level_id), None)
            if level is not None:
                obj.name = plan_name_for_level(level.name, obj.mastro_props.mastro_ffl)

        return {'FINISHED'}
