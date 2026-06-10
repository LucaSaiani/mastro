from bpy.props import IntProperty, CollectionProperty

from .property_classes_custom_properties import mastro_CL_custom_property_name_list

# =============================================================================
# Scene Properties - Custom Properties
# =============================================================================
scene_props_custom_properties = [
    ("mastro_custom_property_name_list", CollectionProperty(type=mastro_CL_custom_property_name_list)),
    ("mastro_custom_property_name_list_index", IntProperty(name="Custom Property Name", default=0)),
]
