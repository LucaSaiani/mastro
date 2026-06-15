from bpy.types import Node
from bpy.props import StringProperty, EnumProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node


class MaStroScheduleMathNode(MaStroScheduleTreeNode, Node):
    """Combine two columns of the same table with an arithmetic operation,
    adding the result as a new column"""
    bl_idname = 'MaStroScheduleMath'
    bl_label = 'Math'

    column_a: StringProperty(name="Column A", update=update_node)
    column_b: StringProperty(name="Column B", update=update_node)
    operation: EnumProperty(
        name="Operation",
        items=[
            ('ADD', "Add", "A + B"),
            ('SUBTRACT', "Subtract", "A - B"),
            ('MULTIPLY', "Multiply", "A * B"),
            ('DIVIDE', "Divide", "A / B"),
        ],
        default='ADD',
        update=update_node,
    )
    output_name: StringProperty(name="Output Name", default="Result", update=update_node)

    def init(self, context):
        self.inputs.new('MaStroScheduleDataSocketType', "Data")
        self.outputs.new('MaStroScheduleDataSocketType', "Data")

    def draw_buttons(self, context, layout):
        layout.prop(self, "column_a")
        layout.prop(self, "column_b")
        layout.prop(self, "operation")
        layout.prop(self, "output_name")

    def evaluate(self, inputs):
        rows = inputs[0] or []
        out_key = self.output_name or "Result"

        result = []
        for row in rows:
            new_row = dict(row)
            try:
                a = float(row.get(self.column_a, 0))
                b = float(row.get(self.column_b, 0))
                if self.operation == 'ADD':
                    value = a + b
                elif self.operation == 'SUBTRACT':
                    value = a - b
                elif self.operation == 'MULTIPLY':
                    value = a * b
                else:
                    value = a / b if b else 0
            except (TypeError, ValueError):
                value = 0
            new_row[out_key] = value
            result.append(new_row)

        return [result]
