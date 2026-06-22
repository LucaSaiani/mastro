from bpy.props import (IntProperty,
                       BoolProperty,
                       EnumProperty,
                       CollectionProperty,
)

from .property_classes_levels import mastro_CL_level_list, mastro_CL_level_set
from ...Utils.mastro_levels.clip_range import get_level_set_enum_items


# bpy's update= callback signature is fixed at (self, context); the "top"
# vs "bottom" distinction can't be injected as an extra argument, so each
# property needs its own thin wrapper around the shared implementation.
def _on_clip_range_set_changed_top(self, context):
    _on_clip_range_set_changed(context, "top")


def _on_clip_range_set_changed_bottom(self, context):
    _on_clip_range_set_changed(context, "bottom")


def _on_clip_range_set_changed(context, side):
    from ...Utils.mastro_levels.clip_range import (
        reset_clip_range_for_set_change, update_clip_from_selection,
    )
    reset_clip_range_for_set_change(context.scene, side)
    update_clip_from_selection(context)


# Same per-side wrapper reason as _on_clip_range_set_changed_top/_bottom above.
def _on_clip_range_active_level_changed_top(self, context):
    _on_clip_range_active_level_changed(context, "top")


def _on_clip_range_active_level_changed_bottom(self, context):
    _on_clip_range_active_level_changed(context, "bottom")


def _on_clip_range_active_level_changed(context, side):
    """Lets clicking a row in the View panel's clip-range UIList set the
    active level directly, instead of only being reachable via the
    Shift Up/Down arrow operators (see set_active_level_by_index)."""
    from ...Utils.mastro_levels.clip_range import (
        set_active_level_by_index, update_clip_from_selection,
    )
    index = getattr(context.scene, f"mastro_clip_range_list_index_{side}")
    if set_active_level_by_index(context.scene, side, index):
        update_clip_from_selection(context)

# =============================================================================
# Scene Properties - Levels
# =============================================================================
scene_props_levels = [
    ("mastro_level_list", CollectionProperty(type=mastro_CL_level_list)),
    ("mastro_level_list_index", IntProperty(name="Level", default=0)),

    ("mastro_level_set_list", CollectionProperty(type=mastro_CL_level_set)),
    ("mastro_level_set_list_index", IntProperty(name="Level Set", default=0)),
    ("mastro_level_set_filter_members_only", BoolProperty(
        name="Show assigned only",
        default=False,
        description="Show only levels assigned to the active set",
    )),

    # Duplicated per side (Top/Bottom ortho view) rather than shared, so a
    # Top viewport and a Bottom viewport open at the same time each keep
    # their own chosen set, range and active level - see clip_range.py,
    # where every clip-range function takes an explicit `side` ("top" or
    # "bottom") and reads/writes the matching suffixed property/id-property.
    #
    # Independent from mastro_level_set_list_index (the Sets panel's
    # selection) so picking a set here for clip planes doesn't change
    # what the Sets panel is showing, and vice versa.
    ("mastro_clip_range_set_id_top", EnumProperty(
        name="Set",
        description="Level set used to define the Top view's clip range",
        items=get_level_set_enum_items,
        update=_on_clip_range_set_changed_top,
    )),
    ("mastro_clip_range_set_id_bottom", EnumProperty(
        name="Set",
        description="Level set used to define the Bottom view's clip range",
        items=get_level_set_enum_items,
        update=_on_clip_range_set_changed_bottom,
    )),
    # Independent from mastro_level_list_index (used by the Levels and
    # Sets-members lists) so highlighting the clip range's top level in
    # the View panel doesn't change the active row shown in those other,
    # unrelated UILists.
    ("mastro_clip_range_list_index_top", IntProperty(
        name="Clip Range Level (Top)", default=0,
        update=_on_clip_range_active_level_changed_top,
    )),
    ("mastro_clip_range_list_index_bottom", IntProperty(
        name="Clip Range Level (Bottom)", default=0,
        update=_on_clip_range_active_level_changed_bottom,
    )),
]
