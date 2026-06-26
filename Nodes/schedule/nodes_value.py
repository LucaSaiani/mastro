from bpy.types import Node
from bpy.props import FloatProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node


class MaStroScheduleValueNode(MaStroScheduleTreeNode, Node):
    """Emit a single constant number as a one-row Column, so it can feed
    a Math node's B input as a scalar (broadcast over A's rows) instead
    of requiring an actual upstream Column"""
    bl_idname = 'MaStroScheduleValue'
    bl_label = 'Value'

    value: FloatProperty(name="Value", update=update_node)

    def init(self, context):
        # No instance name ("Column" would read oddly on a node whose
        # whole point is feeding a plain number into something like
        # Table's Rows - the user's own call) - the socket TYPE is
        # still MaStroScheduleColumnSocketType (stays compatible with
        # every input that expects one, e.g. Math's A/B, Table's
        # Rows/Columns), only the label next to the output dot is empty.
        self.outputs.new('MaStroScheduleColumnSocketType', "")

    @property
    def column_label(self):
        return "Value"

    def draw_buttons(self, context, layout):
        layout.prop(self, "value", text="")

    def evaluate(self, inputs):
        return [[{self.name: self.value}]]
