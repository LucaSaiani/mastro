from bpy.types import PropertyGroup
from bpy.props import (IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       StringProperty,
)

from ...Utils.update_attributes import *


class mastro_CL_street_name_list(PropertyGroup):
    """One street type with width, corner radius, and overlay color."""
    id: IntProperty(
           name="Id",
           description="Street name id",
           default = 0)

    name: StringProperty(
           name="Street type Name",
           description="The type name of the street",
           default="Street type",
           update=update_mastro_filter_by_street_type)

    streetWidth: FloatProperty(
        name="Street width",
        description="The width of the street",
        min=0,
        #max=99,
        precision=3,
        default = 8,
        unit='LENGTH',
        update=update_mastro_street_width)

    streetRadius: FloatProperty(
        name="Street radius",
        description="The radius of the street",
        min=0,
        #max=99,
        precision=3,
        default = 16,
        unit='LENGTH',
        update=update_mastro_street_radius)

    streetEdgeColor: FloatVectorProperty(
        name = "Color of the edges of the street to be shown in the overlay",
        subtype = "COLOR",
        size = 3,
        min = 0.0,
        max = 1.0,
        default = (1.0, 0.0, 0.0))
