from bpy.props import PointerProperty

from .property_classes_pdf import mastro_CL_pdf_scene_props

# =============================================================================
# Scene Pointer Properties - PDF
# =============================================================================
scene_pointer_props_pdf = [
    ("mastro_pdf_props", PointerProperty(type=mastro_CL_pdf_scene_props)),
]
