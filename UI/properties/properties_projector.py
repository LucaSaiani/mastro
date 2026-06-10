from bpy.props import PointerProperty

from .property_classes_projector import (mastro_CL_projector_properties,
                                          mastro_CL_projector_scene_props,
)

# =============================================================================
# Camera Pointer Properties - Projector
# =============================================================================
camera_props_projector = [
    ("mastro_projector_cl", PointerProperty(type=mastro_CL_projector_properties)),
]

# =============================================================================
# Scene Pointer Properties - Projector
# =============================================================================
scene_pointer_props_projector = [
    ("mastro_projector_props", PointerProperty(type=mastro_CL_projector_scene_props)),
]
