import math

from bpy.types import Node
from bpy.props import EnumProperty, IntProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node, get_available_columns_items

# operations that only use Column A
UNARY_OPERATIONS = {
    'SQRT', 'INVERSE_SQRT', 'ABSOLUTE', 'EXPONENT',
    'ROUND', 'FLOOR', 'CEIL', 'TRUNCATE',
}


class MaStroScheduleMathSupersededNode(MaStroScheduleTreeNode, Node):
    """SUPERSEDED - not registered. Kept only as a reference for the
    feature set still to be ported, incrementally, into the new minimal
    MaStroScheduleMath (nodes_math.py): the other 16 operations beyond
    Round/Floor/Ceil, and A/B broadcasting between two tables. The
    replacement uses Node.inputs[...].hide to actually hide socket B for
    unary operations, instead of just leaving it wired but unused.

    Combine a column from table A with a column from table B (or a
    constant from a Value node) using a mathematical operation, producing a
    table with one new column per row of A. If B has a single row, its value
    is broadcast to every row of A; otherwise A and B must have the same
    number of rows"""
    bl_idname = 'MaStroScheduleMathSuperseded'
    bl_label = 'Math (superseded)'

    column_a: EnumProperty(
        name="Column A",
        items=lambda self, context: get_available_columns_items(self, 0),
        update=update_node,
    )
    column_b: EnumProperty(
        name="Column B",
        items=lambda self, context: get_available_columns_items(self, 1),
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
    def init(self, context):
        self.inputs.new('MaStroScheduleDataSocketType', "A")
        self.inputs.new('MaStroScheduleDataSocketType', "B")
        self.outputs.new('MaStroScheduleDataSocketType', "Data")

    def draw_buttons(self, context, layout):
        layout.prop(self, "operation")
        layout.prop(self, "column_a", text="A")
        if self.operation not in UNARY_OPERATIONS:
            layout.prop(self, "column_b", text="B")
        if self.operation == 'ROUND':
            layout.prop(self, "round_digits")

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
        rows_a = inputs[0] or []
        rows_b = inputs[1] or []
        out_key = "Result"
        unary = self.operation in UNARY_OPERATIONS

        if not unary and rows_b and len(rows_b) != len(rows_a) and len(rows_b) != 1:
            raise ValueError(
                f"Math node '{self.name}': table B has {len(rows_b)} rows, "
                f"expected 1 (broadcast) or {len(rows_a)} (matching A)"
            )

        result = []
        for i, row in enumerate(rows_a):
            new_row = dict(row)
            try:
                a = float(row.get(self.column_a, 0))
                if unary:
                    b = 0.0
                else:
                    b_row = rows_b[0] if len(rows_b) == 1 else rows_b[i] if rows_b else {}
                    b = float(b_row.get(self.column_b, 0))
                value = self._compute(a, b)
            except (TypeError, ValueError):
                value = 0.0
            new_row[out_key] = value
            result.append(new_row)

        return [result]
