from bpy.types import PropertyGroup
from bpy.props import (IntProperty,
                       StringProperty,
)

# ------------------------------
# Generic Properties
# ------------------------------
class mastro_CL_name_with_id(PropertyGroup):
    """Generic (name, id) pair used for single-item current-selection trackers."""
    id: IntProperty(
        name="Id",
        description="Name id",
        default = 0)

    name: StringProperty(
        name="Name",
        description="Name",
        default = "")
