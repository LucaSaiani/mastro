from bpy.types import Node
from bpy.props import BoolProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node


# Same role Value/Integer/String/Colour play for their own data types,
# for true/false instead - feeds e.g. a Table primitive's Join Header
# input (nodes_table_primitive.py).
class MaStroScheduleBooleanNode(MaStroScheduleTreeNode, Node):
    """Emit a single constant true/false value"""
    bl_idname = 'MaStroScheduleBoolean'
    bl_label = 'Boolean'

    value: BoolProperty(name="Value", update=update_node)

    def init(self, context):
        self.outputs.new('MaStroScheduleBooleanSocketType', "")

    def draw_buttons(self, context, layout):
        # text="Boolean" not "" - matches Geometry Nodes' own Boolean
        # node, which labels its checkbox the same way rather than
        # leaving it bare.
        layout.prop(self, "value", text="Boolean")

    def evaluate(self, inputs):
        return [self.value]
