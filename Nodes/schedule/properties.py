from bpy.types import PropertyGroup
from bpy.props import StringProperty, CollectionProperty


class MaStro_schedule_key_item(PropertyGroup):
    """One column name used by the Group By node"""
    name: StringProperty(name="Column")


class MaStro_schedule_cell(PropertyGroup):
    """One cell of a Viewer table row"""
    name: StringProperty(name="Column")
    value: StringProperty(name="Value")


class MaStro_schedule_row(PropertyGroup):
    """One row of a Viewer table"""
    cells: CollectionProperty(type=MaStro_schedule_cell)
