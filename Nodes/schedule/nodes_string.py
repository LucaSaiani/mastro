from bpy.types import Node
from bpy.props import StringProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node


class MaStroScheduleStringNode(MaStroScheduleTreeNode, Node):
    """Emit a single constant string as a one-row table, so it can feed a
    Header node's Name input as a reusable, possibly shared, column name"""
    bl_idname = 'MaStroScheduleString'
    bl_label = 'String ?'

    value: StringProperty(name="Value", update=update_node)

    def init(self, context):
        self.outputs.new('MaStroScheduleDataSocketType', "Data")

    def draw_buttons(self, context, layout):
        layout.prop(self, "value", text="")

    def evaluate(self, inputs):
        return [[{"Value": self.value}]]
