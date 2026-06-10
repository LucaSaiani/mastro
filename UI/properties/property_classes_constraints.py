from bpy.types import PropertyGroup
from bpy.props import BoolProperty


class mastro_CL_constraint_XY_settings(PropertyGroup):
    """Scene-level toggle for the XY translation/rotation constraint operators."""
    constraint_xy_on: BoolProperty(
        name = 'XY constraints',
        default = False,
        description = 'Toggle XY constraint behaviour globally'
    )
