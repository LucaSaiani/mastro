from bpy.types import Node
from bpy.props import StringProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node


# Same role Value/Integer play for numbers, for text instead - feeds a
# Rename Header node's String input (nodes_header.py), so the same name
# can be typed once and shared across several Rename Header nodes
# instead of retyping it on each.
class MaStroScheduleStringNode(MaStroScheduleTreeNode, Node):
    """Emit a single constant string"""
    bl_idname = 'MaStroScheduleString'
    bl_label = 'String'

    value: StringProperty(name="Value", update=update_node)

    def init(self, context):
        self.outputs.new('MaStroScheduleStringSocketType', "String")

    def draw_buttons(self, context, layout):
        layout.prop(self, "value", text="")

    def evaluate(self, inputs):
        return [self.value]
