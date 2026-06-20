import math

from bpy.types import Node
from bpy.props import StringProperty, EnumProperty, IntProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node, get_available_columns_items

# operations that only use Column A
UNARY_OPERATIONS = {
    'SQRT', 'INVERSE_SQRT', 'ABSOLUTE', 'EXPONENT',
    'ROUND', 'FLOOR', 'CEIL', 'TRUNCATE',
}


class MaStroScheduleMathNode(MaStroScheduleTreeNode, Node):
    """Combine one or two columns of the same table (row or group) with a
    mathematical operation, adding the result as a new column/field"""
    bl_idname = 'MaStroScheduleMath'
    bl_label = 'Math'

    column_a: EnumProperty(
        name="Column A",
        items=lambda self, context: get_available_columns_items(self),
        update=update_node,
    )
    column_b: EnumProperty(
        name="Column B",
        items=lambda self, context: get_available_columns_items(self),
        update=update_node,
    )
    round_digits: IntProperty(name="Digits", default=0, min=0, update=update_node)
    operation: EnumProperty(
        name="Operation",
        items=[
            ('ADD', "Add", "A + B"),
            ('SUBTRACT', "Subtract", "A - B"),
            ('MULTIPLY', "Multiply", "A * B"),
            ('DIVIDE', "Divide", "A / B"),
            ('POWER', "Power", "A power B"),
            ('LOGARITHM', "Logarithm", "Logarithm A base B"),
            ('MINIMUM', "Minimum", "The minimum of A and B"),
            ('MAXIMUM', "Maximum", "The maximum of A and B"),
            ('LESS_THAN', "Less Than", "1 if A < B else 0"),
            ('GREATER_THAN', "Greater Than", "1 if A > B else 0"),
            ('COMPARE', "Compare", "1 if A == B else 0"),
            ('SQRT', "Square Root", "Square root of A"),
            ('INVERSE_SQRT', "Inverse Square Root", "1 / square root of A"),
            ('ABSOLUTE', "Absolute", "Magnitude of A"),
            ('EXPONENT', "Exponent", "exp(A)"),
            ('ROUND', "Round", "Round A to the given number of digits"),
            ('FLOOR', "Floor", "The largest integer smaller than or equal to A"),
            ('CEIL', "Ceil", "The smallest integer greater than or equal to A"),
            ('TRUNCATE', "Truncate", "The integer part of A, removing fractional digits"),
        ],
        default='ADD',
        update=update_node,
    )
    output_name: StringProperty(name="Output Name", default="Result", update=update_node)

    def init(self, context):
        self.inputs.new('MaStroScheduleDataSocketType', "Data")
        self.outputs.new('MaStroScheduleDataSocketType', "Data")

    def draw_buttons(self, context, layout):
        layout.prop(self, "operation")
        layout.prop(self, "column_a", text="A")
        if self.operation not in UNARY_OPERATIONS:
            layout.prop(self, "column_b", text="B")
        if self.operation == 'ROUND':
            layout.prop(self, "round_digits")
        layout.prop(self, "output_name")

    def _compute(self, a, b):
        op = self.operation
        if op == 'ADD':
            return a + b
        elif op == 'SUBTRACT':
            return a - b
        elif op == 'MULTIPLY':
            return a * b
        elif op == 'DIVIDE':
            return a / b if b else 0.0
        elif op == 'POWER':
            return a ** b
        elif op == 'LOGARITHM':
            return math.log(a, b) if a > 0 and b > 0 and b != 1 else 0.0
        elif op == 'MINIMUM':
            return min(a, b)
        elif op == 'MAXIMUM':
            return max(a, b)
        elif op == 'LESS_THAN':
            return 1.0 if a < b else 0.0
        elif op == 'GREATER_THAN':
            return 1.0 if a > b else 0.0
        elif op == 'COMPARE':
            return 1.0 if math.isclose(a, b, abs_tol=1e-9) else 0.0
        elif op == 'SQRT':
            return math.sqrt(a) if a >= 0 else 0.0
        elif op == 'INVERSE_SQRT':
            return 1.0 / math.sqrt(a) if a > 0 else 0.0
        elif op == 'ABSOLUTE':
            return abs(a)
        elif op == 'EXPONENT':
            return math.exp(a)
        elif op == 'ROUND':
            return round(a, self.round_digits)
        elif op == 'FLOOR':
            return math.floor(a)
        elif op == 'CEIL':
            return math.ceil(a)
        elif op == 'TRUNCATE':
            return math.trunc(a)
        return 0.0

    def evaluate(self, inputs):
        rows = inputs[0] or []
        out_key = self.output_name or "Result"

        result = []
        for row in rows:
            new_row = dict(row)
            try:
                a = float(row.get(self.column_a, 0))
                b = 0.0 if self.operation in UNARY_OPERATIONS else float(row.get(self.column_b, 0))
                value = self._compute(a, b)
            except (TypeError, ValueError):
                value = 0.0
            new_row[out_key] = value
            result.append(new_row)

        return [result]
