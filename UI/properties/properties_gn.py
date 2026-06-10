from bpy.props import PointerProperty

from .property_classes_gn import mastro_CL_Sticky_Note

# =============================================================================
# Node Frame Pointer Properties - Geometry Nodes
# =============================================================================
node_frame_props_gn = [
    ("mastro_sticky_note_props", PointerProperty(type=mastro_CL_Sticky_Note)),
]
