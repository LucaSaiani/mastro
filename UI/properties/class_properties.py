import bpy 
from bpy.types import IntProperty, BoolProperty

# Defines class for custom properties
class mastroAddonProperties(bpy.types.PropertyGroup):
    mastro_block_attribute: bpy.props.IntProperty(
        name="MaStro Block Attribute",
        default=1,
        min=1,
        description="Block name"
    )
    
    mastro_building_attribute: bpy.props.IntProperty(
        name="MaStro Building Attribute",
        default=1,
        min=1,
        description="Building name"
    )
    
class constraintXYSettings(bpy.types.PropertyGroup):
    """Property Group for all xy constraint scene properties"""
    constraint_xy_on: bpy.props.BoolProperty(
        name = 'XY constraints',
        default = False,
        description = 'Toggle XY constraint behaviour globally'
    )