from bpy.types import Node
from bpy.props import StringProperty, EnumProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node, get_available_columns_items


class MaStroScheduleFilterNode(MaStroScheduleTreeNode, Node):
    """Keep only the rows where the given column equals the given value
    (equivalent to the VBA getUniqueOfSelection/SumByCriteria filter)"""
    bl_idname = 'MaStroScheduleFilter'
    bl_label = 'Filter'

    # TODO (still WIP, see menus.py): `column` has the same shape that
    # caused a real RecursionError on Get Attribute Names - a permanent
    # dynamic-items EnumProperty on the node itself, read inside
    # evaluate(). When this node graduates out of WIP, migrate it to the
    # StringProperty + search-popup-operator pattern (see
    # nodes_attribute.py: MASTRO_OT_Schedule_Pick_Attribute_Name,
    # name_value) instead of fixing it in place now - see
    # project_schedule_nodes_roadmap memory, "Filter/GroupBy/Aggregate/
    # Header/... are all still in the WIP Add-menu category".
    column: EnumProperty(
        name="Column",
        items=lambda self, context: get_available_columns_items(self),
        update=update_node,
    )
    value: StringProperty(name="Value", update=update_node)

    def init(self, context):
        self.inputs.new('MaStroScheduleDataSocketType', "Data")
        self.outputs.new('MaStroScheduleDataSocketType', "Data")

    def draw_buttons(self, context, layout):
        layout.prop(self, "column")
        layout.prop(self, "value")

    def evaluate(self, inputs):
        rows = inputs[0] or []
        column, value = self.column, self.value
        return [[row for row in rows if str(row.get(column, "")) == value]]
