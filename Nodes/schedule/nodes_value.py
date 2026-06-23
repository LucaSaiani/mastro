from bpy.types import Node
from bpy.props import FloatProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node


class MaStroScheduleValueNode(MaStroScheduleTreeNode, Node):
    """Emit a single constant number as a one-row table, so it can feed a
    Math node's A/B input as a scalar (broadcast over the other operand's
    rows) instead of requiring a column on the main table"""
    bl_idname = 'MaStroScheduleValue'
    bl_label = 'Value'

    value: FloatProperty(name="Value", update=update_node)

    def init(self, context):
        self.outputs.new('MaStroScheduleDataSocketType', "Data")

    def draw_buttons(self, context, layout):
        layout.prop(self, "value", text="")

    def evaluate(self, inputs):
        return [[{"Value": self.value}]]
