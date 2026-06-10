from bpy.props import (IntProperty,
                       FloatProperty,
                       EnumProperty,
                       CollectionProperty,
)

from ...Utils.get_names_from_list import get_names_from_list
from ...Utils.update_attributes import update_attributes_street
from .property_classes_street import mastro_CL_street_name_list

# =============================================================================
# Scene Properties - Street
# =============================================================================
scene_props_street = [
    ("mastro_attribute_street_id", IntProperty(name="Street Id", default=0)),
    ("mastro_attribute_street_width", FloatProperty(
        name="Street width", default=8, precision=3, subtype="DISTANCE"
    )),
    ("mastro_attribute_street_radius", FloatProperty(
        name="Street radius", default=18, precision=3, subtype="DISTANCE"
    )),

    ("mastro_street_name_list", CollectionProperty(type=mastro_CL_street_name_list)),
    ("mastro_street_name_list_index", IntProperty(name="Street Name", default=0)),
    ("mastro_street_names", EnumProperty(
        name="Street List", description="Street type assigned to the selected edge",
        items=lambda self, context: get_names_from_list(context.scene, context, "mastro_street_name_list"),
        update=update_attributes_street
    )),
]
