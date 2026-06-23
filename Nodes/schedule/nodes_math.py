import math

from bpy.types import Node
from bpy.props import EnumProperty, IntProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node, get_available_columns_items


class MaStroScheduleMathNode(MaStroScheduleTreeNode, Node):
    """Round, floor or ceil a column to the given number of digits, adding
    the result as a new column. Minimal incremental rebuild of the old
    superseded Math node (nodes_math_superseded.py, no longer registered,
    kept as a reference for the feature set still to be ported over: the
    other 16 operations and A/B broadcasting)"""
    bl_idname = 'MaStroScheduleMath'
    bl_label = 'Math'

    column: EnumProperty(
        name="Column",
        items=lambda self, context: get_available_columns_items(self, 0),
        update=update_node,
    )
    operation: EnumProperty(
        name="Operation",
        items=[
            ('ROUND', "Round", "Round to the given number of digits"),
            ('FLOOR', "Floor", "The largest integer smaller than or equal to the value"),
            ('CEIL', "Ceil", "The smallest integer greater than or equal to the value"),
        ],
        default='ROUND',
        update=update_node,
    )
    digits: IntProperty(name="Digits", default=2, min=0, update=update_node)

    def init(self, context):
        self.inputs.new('MaStroScheduleDataSocketType', "Data")
        self.outputs.new('MaStroScheduleDataSocketType', "Data")

    def draw_buttons(self, context, layout):
        layout.prop(self, "column")
        layout.prop(self, "operation")
        if self.operation == 'ROUND':
            layout.prop(self, "digits")

    def _compute(self, value):
        if self.operation == 'ROUND':
            return round(value, self.digits)
        elif self.operation == 'FLOOR':
            return math.floor(value)
        elif self.operation == 'CEIL':
            return math.ceil(value)
        return value

    def evaluate(self, inputs):
        rows = inputs[0] or []
        result = []
        for row in rows:
            new_row = dict(row)
            try:
                value = self._compute(float(row.get(self.column, 0)))
            except (TypeError, ValueError):
                value = 0.0
            new_row["Result"] = value
            result.append(new_row)
        return [result]
