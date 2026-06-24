import math

from bpy.types import Node
from bpy.props import EnumProperty, IntProperty

from .tree import MaStroScheduleTreeNode


class MaStroScheduleMathNode(MaStroScheduleTreeNode, Node):
    """Round, floor or ceil a Column's value, in place. Minimal
    incremental rebuild of the old superseded Math node
    (nodes_math_superseded.py, no longer registered, kept as a reference
    for the feature set still to be ported over: the other 16 operations
    and two-Column A/B operations).

    Takes a single Column - there's nothing to pick (no `column`
    EnumProperty like the old Table-based version had): a Column always
    has exactly one data key, this node's own upstream node.name, found
    by elimination against the id keys (_Object/_Face/_Edge/_Vertex/
    _Level). The result keeps that same key/identity - this is a
    transformation of the same Column, not a new one - so its `label`
    (read from the upstream node, same as Evaluate Attribute's) carries
    through unchanged too."""
    bl_idname = 'MaStroScheduleMath'
    bl_label = 'Math'

    operation: EnumProperty(
        name="Operation",
        items=[
            ('ROUND', "Round", "Round to the given number of digits"),
            ('FLOOR', "Floor", "The largest integer smaller than or equal to the value"),
            ('CEIL', "Ceil", "The smallest integer greater than or equal to the value"),
        ],
        default='ROUND',
    )
    digits: IntProperty(name="Digits", default=2, min=0)

    def init(self, context):
        self.inputs.new('MaStroScheduleColumnSocketType', "Column")
        self.outputs.new('MaStroScheduleColumnSocketType', "Column")

    @property
    def label(self):
        """Mirrors the upstream Column's label unchanged - see this
        class's docstring for why Math doesn't get its own identity."""
        socket = self.inputs["Column"]
        if not socket.is_linked or not socket.links:
            return ""
        return getattr(socket.links[0].from_node, "label", "")

    def draw_buttons(self, context, layout):
        layout.prop(self, "operation")
        if self.operation == 'ROUND':
            layout.prop(self, "digits")

    def _data_key(self, row):
        for key in row.keys():
            if not key.startswith("_"):
                return key
        return None

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
            key = self._data_key(row)
            if key is not None:
                try:
                    new_row[key] = self._compute(float(row.get(key, 0)))
                except (TypeError, ValueError):
                    new_row[key] = 0.0
            result.append(new_row)
        return [result]
