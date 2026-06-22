from bpy.props import (IntProperty,
                       BoolProperty,
                       CollectionProperty,
)

from .property_classes_levels import mastro_CL_level_list, mastro_CL_level_set

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
]
