import math

from bpy.types import Node
from bpy.props import EnumProperty, IntProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node


# Minimal incremental rebuild of the old superseded Math node
# (nodes_math_superseded.py, no longer registered, kept as a reference for
# the feature set still to be ported over: the other 16 operations and
# two-Column A/B operations).
#
# Takes a single Column - there's nothing to pick (no `column`
# EnumProperty like the old Table-based version had): a Column always has
# exactly one data key, this node's own upstream node.name, found by
# elimination against the id keys (_Object/_Face/_Edge/_Vertex/_Level).
# The result keeps that same key/identity - this is a transformation of
# the same Column, not a new one - so its `column_label` (read from the
# upstream node, same as Evaluate Attribute's) carries through unchanged
# too. Not called `label` - bpy.types.Node already has a native `label`
# attribute (the node's own custom display label, unrelated to this), and
# a same-named Python @property doesn't reliably override it.
class MaStroScheduleMathNode(MaStroScheduleTreeNode, Node):
    """Round, floor, ceil or truncate a Column's value, in place"""
    bl_idname = 'MaStroScheduleMath'
    bl_label = 'Math'

    # update=update_node on both - this is a STATIC-items EnumProperty
    # and a plain IntProperty, neither dynamic, so they don't carry the
    # RecursionError risk a dynamic-items EnumProperty did (see
    # nodes_attribute.py's history) - without update= here, changing
    # either property never flags this tree for the poller
    # (Nodes/schedule/tree.py:_pending_execute_trees) to re-evaluate,
    # so the Viewer doesn't refresh - confirmed live, most noticeably
    # when dragging `digits` quickly (each change was simply never
    # queued for a re-run at all).
    operation: EnumProperty(
        name="Operation",
        items=[
            ('ROUND', "Round", "Round to the given number of digits"),
            ('FLOOR', "Floor", "The largest integer smaller than or equal to the value"),
            ('CEIL', "Ceil", "The smallest integer greater than or equal to the value"),
            ('TRUNCATE', "Truncate", "Cut off after the given number of digits, without rounding"),
        ],
        default='ROUND',
        update=update_node,
    )
    # Only Round/Truncate have a meaningful digit count - Floor/Ceil
    # always produce a whole number, so `digits` doesn't apply to them
    # (draw_buttons only shows it for ROUND/TRUNCATE). max=5: the user's
    # call - there's no real-world need for this node's inputs (areas,
    # heights, counts) to ever need more than 5 decimal digits of
    # precision.
    digits: IntProperty(name="Digits", default=2, min=0, max=5, update=update_node)

    def init(self, context):
        self.inputs.new('MaStroScheduleColumnSocketType', "Column")
        self.outputs.new('MaStroScheduleColumnSocketType', "Column")

    @property
    def column_label(self):
        """Mirrors the upstream Column's label unchanged - see this
        class's docstring for why Math doesn't get its own identity."""
        from .tree import upstream_attr
        return upstream_attr(self.inputs["Column"], "column_label")

    def draw_buttons(self, context, layout):
        layout.prop(self, "operation")
        if self.operation in ('ROUND', 'TRUNCATE'):
            layout.prop(self, "digits")

    def _data_key(self, row):
        for key in row.keys():
            if not key.startswith("_"):
                return key
        return None

    def _compute(self, value):
        if self.operation == 'ROUND':
            # round(value, 0) still returns a float (173.0, not 173) -
            # plain round(value) (no digits arg) is the one that returns
            # an actual int, same as FLOOR/CEIL below already do. Without
            # this, a 0-digit Round would display as "173.0" instead of
            # "173".
            if self.digits == 0:
                return round(value)
            return round(value, self.digits)
        elif self.operation == 'FLOOR':
            return math.floor(value)
        elif self.operation == 'CEIL':
            return math.ceil(value)
        elif self.operation == 'TRUNCATE':
            # Cut off after `digits` decimal places without rounding -
            # math.trunc alone only handles digits=0 (whole numbers);
            # shifting by 10**digits, truncating, then shifting back
            # drops the unwanted decimals instead of rounding them, the
            # actual difference from ROUND (e.g. 1.999 truncated to 2
            # digits is 1.99, not 2.0). At digits=0 the shift is a no-op
            # (factor=1), so math.trunc alone already returns a plain
            # int - no float division needed there.
            if self.digits == 0:
                return math.trunc(value)
            factor = 10 ** self.digits
            return math.trunc(value * factor) / factor
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
