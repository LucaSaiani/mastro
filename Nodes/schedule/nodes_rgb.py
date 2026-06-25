from bpy.types import Node
from bpy.props import FloatVectorProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node


# Same role Value/Integer/String play for numbers/text, for color
# instead - feeds e.g. an Edit Header/Table primitive's Background or
# Text Colour input (nodes_table_edit_header.py/nodes_table_primitive.py).
class MaStroScheduleColourNode(MaStroScheduleTreeNode, Node):
    """Emit a single constant color"""
    bl_idname = 'MaStroScheduleColour'
    bl_label = 'Colour'

    value: FloatVectorProperty(name="Color", subtype='COLOR', size=3, min=0.0, max=1.0,
                                default=(0.8, 0.8, 0.8), update=update_node)

    def init(self, context):
        self.outputs.new('MaStroScheduleColorSocketType', "Color")

    def draw_buttons(self, context, layout):
        layout.prop(self, "value", text="")

    def evaluate(self, inputs):
        return [tuple(self.value)]
