import bpy

from .plan_drivers import link_all_plan_drivers
from .update_plan_attributes import update_plan_attributes, plan_name_for_level
from ..mastro_preferences.get_preferences import get_prefs


def levels_missing_a_plan(levels):
    """Levels in `levels` that no existing MaStro plan is locked to (by
    mastro_bottom_level_id, not by position - see
    OBJECT_OT_Mastro_Plan_Unlock_From_Level for why id is the right check:
    an unlocked plan's FFL can drift away from its old level, so its stale
    id must not count as "this level already has a plan")."""
    occupied_ids = {
        obj.mastro_props.mastro_bottom_level_id
        for obj in bpy.data.objects
        if obj.type == "MESH" and "MaStro plan" in obj.data
    }
    return [lvl for lvl in levels if lvl.id not in occupied_ids]


def duplicate_plan_to_levels(context, source_obj, levels, link_mesh=True):
    """Duplicate source_obj once per level in `levels`, each copy locked to
    its own level. Returns the list of newly created objects.

    link_mesh=True shares source_obj.data across every copy (like Blender's
    own Alt+D): editing the walls/floors on one plan updates every plan
    sharing that mesh - intended for repeated floors that should stay in
    sync. link_mesh=False gives each copy an independent mesh.copy()
    instead, for plans that will diverge from here on."""
    modifier_name = "MaStro Plan"
    new_objects = []

    for level in levels:
        new_obj = source_obj.copy()
        new_obj.data = source_obj.data if link_mesh else source_obj.data.copy()
        context.collection.objects.link(new_obj)

        # obj.copy() also duplicates source_obj's drivers, with their
        # target.id still pointing at source_obj rather than new_obj - so
        # without this, new_obj would end up with two drivers per property:
        # the (wrongly-targeted) copied ones, plus the correct ones added
        # by link_all_plan_drivers below.
        new_obj.animation_data_clear()

        new_modifier = new_obj.modifiers.get(modifier_name)
        link_all_plan_drivers(new_obj, new_modifier)

        new_obj.mastro_props.mastro_bottom_level_id = level.id
        update_plan_attributes(context)

        if get_prefs().rename_plan_on_relock:
            new_obj.name = plan_name_for_level(level.name, new_obj.mastro_props.mastro_ffl)

        new_objects.append(new_obj)

    return new_objects
