from bpy.types import PropertyGroup
from bpy.props import (IntProperty,
                       FloatProperty,
                       StringProperty,
)


def update_level_list(self, context):
    """Keep the level list sorted by descending level, then by name.

    Skipped while a batch operation (new_item, batch_add) is writing
    several fields/items in sequence; those operators call
    sort_level_list() once themselves after all writes are done.
    """
    if context.scene.get("mastro_level_list_batch_update"):
        return
    from ...Utils.mastro_levels.sort_level_list import sort_level_list
    sort_level_list(context.scene)


class mastro_CL_level_list(PropertyGroup):
    """One project level, defined by its elevation.

    id 0 is the default "AOD" (ground/datum) level created by init_lists and
    can never be removed or edited; see PROPERTIES_OT_Level_List_Remove_Item
    and PROPERTIES_UL_Level for where that is enforced.
    """
    id: IntProperty(
        name="Id",
        description="Level id",
        default=0,
    )
    name: StringProperty(
        name="Name",
        description="The name of the level",
        default="Level",
        update=update_level_list,
    )
    level: FloatProperty(
        name="Level",
        description="Elevation of the level",
        # precision=5 so sub-millimetre elevations stay visible in the
        # compact UIList row, where Blender would otherwise round the
        # displayed value more aggressively than the stored precision.
        precision=5,
        subtype="DISTANCE",
        update=update_level_list,
    )
