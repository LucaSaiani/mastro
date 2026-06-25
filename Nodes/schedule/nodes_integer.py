from bpy.types import Node
from bpy.props import IntProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node


class MaStroScheduleIntegerNode(MaStroScheduleTreeNode, Node):
    """Emit a single constant whole number as a one-row Column, so it can
    feed a Math node's B input as a scalar (broadcast over A's rows)
    instead of requiring an actual upstream Column"""
    bl_idname = 'MaStroScheduleInteger'
    bl_label = 'Integer'

    value: IntProperty(name="Value", update=update_node)

    def init(self, context):
        # No instance name - see nodes_value.py's identical change for
        # why (the socket TYPE is unaffected, only its visible label).
        self.outputs.new('MaStroScheduleColumnSocketType', "")

    @property
    def column_label(self):
        return "Integer"

    def draw_buttons(self, context, layout):
        layout.prop(self, "value", text="")

    def evaluate(self, inputs):
        return [[{self.name: self.value}]]
