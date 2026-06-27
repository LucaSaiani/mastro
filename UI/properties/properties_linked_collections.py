from bpy.props import PointerProperty

from .property_classes_linked_collections import mastro_CL_linked_collections_props

# =============================================================================
# Scene Pointer Properties - Linked Collections Manager
# =============================================================================
scene_pointer_props_linked_collections = [
    ("mastro_linked_collections_props", PointerProperty(type=mastro_CL_linked_collections_props)),
]
