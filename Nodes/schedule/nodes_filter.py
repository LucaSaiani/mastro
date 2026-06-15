from bpy.types import Node
from bpy.props import StringProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node


class MaStroScheduleFilterNode(MaStroScheduleTreeNode, Node):
    """Keep only the rows where the given column equals the given value
    (equivalent to the VBA getUniqueOfSelection/SumByCriteria filter)"""
    bl_idname = 'MaStroScheduleFilter'
    bl_label = 'Filter'

    column: StringProperty(name="Column", update=update_node)
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
