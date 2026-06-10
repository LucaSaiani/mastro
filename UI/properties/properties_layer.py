from bpy.props import PointerProperty

from .property_classes_layer import mastro_CL_layer_manager_props

# =============================================================================
# Scene Pointer Properties - Layer Manager
# =============================================================================
scene_pointer_props_layer = [
    ("mastro_layer_manager_props", PointerProperty(type=mastro_CL_layer_manager_props)),
]
