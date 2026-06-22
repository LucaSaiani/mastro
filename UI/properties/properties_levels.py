from bpy.props import (IntProperty,
                       BoolProperty,
                       EnumProperty,
                       CollectionProperty,
)

from .property_classes_levels import mastro_CL_level_list, mastro_CL_level_set
from ...Utils.mastro_levels.clip_range import get_level_set_enum_items

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
    )),
    ("mastro_clip_range_set_id_bottom", EnumProperty(
        name="Set",
        description="Level set used to define the Bottom view's clip range",
        items=get_level_set_enum_items,
    )),
    # Independent from mastro_level_list_index (used by the Levels and
    # Sets-members lists) so highlighting the clip range's top level in
    # the View panel doesn't change the active row shown in those other,
    # unrelated UILists.
    ("mastro_clip_range_list_index_top", IntProperty(name="Clip Range Level (Top)", default=0)),
    ("mastro_clip_range_list_index_bottom", IntProperty(name="Clip Range Level (Bottom)", default=0)),
]
