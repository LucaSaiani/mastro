from bpy.props import PointerProperty

from .property_classes_print import mastro_CL_print_scene_props

# =============================================================================
# Scene Pointer Properties - Print
# =============================================================================
scene_pointer_props_print = [
    ("mastro_print_props", PointerProperty(type=mastro_CL_print_scene_props)),
]
