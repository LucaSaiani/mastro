from bpy.props import PointerProperty

from .property_classes_constraints import mastro_CL_constraint_XY_settings

# =============================================================================
# Scene Pointer Properties - Constraints
# =============================================================================
scene_pointer_props_constraints = [
    ("mastro_constraint_xy_setting", PointerProperty(type=mastro_CL_constraint_XY_settings)),
]
