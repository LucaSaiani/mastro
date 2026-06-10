from bpy.types import PropertyGroup
from bpy.props import (IntProperty,
                       FloatProperty,
                       BoolProperty,
                       StringProperty,
                       CollectionProperty,
                       EnumProperty,
)

from ...Utils.update_attributes import *


class mastro_CL_custom_property_string_name_list(PropertyGroup):
    """One string option within a STRING custom property."""
    id: IntProperty(
           name="Id",
           description="The string option id",
           default=0)
    name: StringProperty(
           name="Name",
           description="The string option name",
           default="")


class mastro_CL_custom_property_name_list(PropertyGroup):
    """Defines a custom property shared by all MaStro objects in the scene.
    Each entry in the scene list corresponds to one custom property slot.
    The property is stored as a custom property on every MaStro object,
    keyed by the entry name with a leading underscore (e.g. "_My Property").
    property_type determines which value, min, max, step and precision
    fields are active; the others are ignored at runtime.
    """
    id: IntProperty(name="Id", default=0)

    previous_name: StringProperty(name="Previous Name", default="")

    name: StringProperty(
        name="Name",
        default="Custom Property",
        update=rename_custom_property_key)

    property_type: EnumProperty(
        name="Type",
        items=[
            ('INT',    "Integer", ""),
            ('FLOAT',  "Float",   ""),
            ('BOOL',   "Boolean", ""),
            ('STRING', "String",  ""),
        ],
        default='INT')

    default_int:    IntProperty(name="Default", default=0)
    default_float:  FloatProperty(name="Default", default=0.0)
    default_bool:   BoolProperty(name="Default", default=False)

    min_int:   IntProperty(name="Min")
    max_int:   IntProperty(name="Max", default=1)
    min_float: FloatProperty(name="Min", default=0.0)
    max_float: FloatProperty(name="Max", default=1.0)

    step_int:       IntProperty(name="Step", default=1)
    step_float:     FloatProperty(name="Step", default=0.1)
    precision_float: IntProperty(name="Precision", default=3)

    description: StringProperty(name="Description", default="")

    assign_to_mass   : BoolProperty(name="Assign to Mass/Block", default=True)
    assign_to_street : BoolProperty(name="Assign to Street",     default=True)

    committed: BoolProperty(name="Committed", default=False)

    string_options      : CollectionProperty(type=mastro_CL_custom_property_string_name_list)
    string_options_index: IntProperty(name="String Option", default=0)
