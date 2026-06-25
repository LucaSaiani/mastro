import math

from bpy.types import Node
from bpy.props import EnumProperty, IntProperty, FloatProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node


# operations that only use Column A - the B input socket is hidden for
# these (see update_sockets) rather than just left wired but unused.
UNARY_OPERATIONS = {
    'SQRT', 'INVERSE_SQRT', 'ABSOLUTE', 'EXPONENT',
    'ROUND', 'FLOOR', 'CEIL', 'TRUNCATE',
}

# Round/Truncate take a digit count - Floor/Ceil always produce a whole
# number, so `digits` doesn't apply to them.
DIGITS_OPERATIONS = {'ROUND', 'TRUNCATE'}

OPERATION_ITEMS = [
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
    ('TRUNCATE', "Truncate", "Cut off A after the given number of digits, without rounding"),
]

OPERATION_LABELS = {identifier: label for identifier, label, _ in OPERATION_ITEMS}


def _on_operation_changed(self, context):
    self.update_sockets()
    update_node(self, context)


# Single-Column math, ported from the old Table-based Math node
# (nodes_math_superseded.py, no longer registered) onto the Column model:
# a Column always has exactly one data key, this node's own upstream
# node.name, found by elimination against the id keys (_Object/_Face/
# _Edge/_Vertex/_Level) - same as Evaluate Attribute's. The result keeps
# A's key/identity (this is a transformation of A, not a new Column), so
# its `column_label` carries through unchanged too. Not called `label` -
# bpy.types.Node already has a native `label` attribute (the node's own
# custom display label, unrelated to this), and a same-named Python
# @property doesn't reliably override it.
#
# B (for binary operations) is a second Column input, broadcasting like
# the old superseded node did: a single-row B applies to every row of A;
# otherwise B must have the same number of rows as A, matched by position
# (not by id keys - there's no guarantee both Columns share the same
# id-key shape, e.g. one from Field=Face and the other from Field=Object).
class MaStroScheduleMathNode(MaStroScheduleTreeNode, Node):
    """Combine a Column with a constant or a second Column using a
    mathematical operation, in place"""
    bl_idname = 'MaStroScheduleMath'
    bl_label = 'Math'

    # update=update_node on both - these are STATIC-items/plain
    # properties, not dynamic, so they don't carry the RecursionError
    # risk a dynamic-items EnumProperty did (see nodes_attribute.py's
    # history) - without update= here, changing either property never
    # flags this tree for the poller (tree.py:_pending_execute_trees) to
    # re-evaluate, so the Viewer doesn't refresh (confirmed live).
    operation: EnumProperty(
        name="Operation",
        items=OPERATION_ITEMS,
        default='ADD',
        update=_on_operation_changed,
    )
    # max=5: the user's call - there's no real-world need for this
    # node's inputs (areas, heights, counts) to ever need more than 5
    # decimal digits of precision.
    digits: IntProperty(name="Digits", default=2, min=0, max=5, update=update_node)
    # Backing values for A/B's inline numeric fields (NodeSocket.prop_name,
    # see sockets.py:MaStroScheduleColumnSocket.draw) - shown on the socket
    # itself only while that socket is unlinked, the same native Blender
    # mechanism its own socket types (e.g. NodeSocketFloat) use, not
    # something specific to this node. Lets the node do plain arithmetic
    # on typed-in numbers with no Column wired in at all, instead of
    # always needing an upstream Column or a separate Value node.
    value_a: FloatProperty(name="A", update=update_node)
    value_b: FloatProperty(name="B", update=update_node)

    def init(self, context):
        self.inputs.new('MaStroScheduleColumnSocketType', "A").prop_name = "value_a"
        self.inputs.new('MaStroScheduleColumnSocketType', "B").prop_name = "value_b"
        self.outputs.new('MaStroScheduleColumnSocketType', "Number Column")
        self.update_sockets()

    def update_sockets(self):
        # "B" can be momentarily absent - confirmed live as a
        # 'bpy_prop_collection[key]: key "A" not found' (sic, same shape
        # for "B") warning right after a copy/paste: Blender restores
        # this node's properties (operation, which carries
        # update=_on_operation_changed) before init() has necessarily
        # finished rebuilding its sockets on the pasted copy, so
        # update_sockets() can run against a node that doesn't have "B"
        # (or even "A") yet.
        if "B" in self.inputs:
            self.inputs["B"].hide = self.operation in UNARY_OPERATIONS

    def draw_label(self):
        # Mirrors Geometry Nodes/Sverchok's Math node: the node's own
        # display name follows the chosen operation, instead of staying
        # a fixed "Math" regardless of what it actually does.
        return OPERATION_LABELS[self.operation]

    @property
    def column_label(self):
        """Mirrors A's label unchanged - see this class's docstring for
        why Math doesn't get its own identity."""
        if "A" not in self.inputs:
            return ""
        from .tree import upstream_attr
        return upstream_attr(self.inputs["A"], "column_label")

    def draw_buttons(self, context, layout):
        layout.prop(self, "operation", text="")
        if self.operation in DIGITS_OPERATIONS:
            layout.prop(self, "digits")

    def _data_key(self, row):
        for key in row.keys():
            if not key.startswith("_"):
                return key
        return None

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
            # round(a, 0) still returns a float (173.0, not 173) - plain
            # round(a) (no digits arg) is the one that returns an actual
            # int, same as FLOOR/CEIL already do. Without this, a
            # 0-digit Round would display as "173.0" instead of "173".
            if self.digits == 0:
                return round(a)
            return round(a, self.digits)
        elif op == 'FLOOR':
            return math.floor(a)
        elif op == 'CEIL':
            return math.ceil(a)
        elif op == 'TRUNCATE':
            # Cut off after `digits` decimal places without rounding -
            # math.trunc alone only handles digits=0 (whole numbers);
            # shifting by 10**digits, truncating, then shifting back
            # drops the unwanted decimals instead of rounding them, the
            # actual difference from ROUND (e.g. 1.999 truncated to 2
            # digits is 1.99, not 2.0). At digits=0 the shift is a no-op
            # (factor=1), so math.trunc alone already returns a plain
            # int - no float division needed there.
            if self.digits == 0:
                return math.trunc(a)
            factor = 10 ** self.digits
            return math.trunc(a * factor) / factor
        return a

    def evaluate(self, inputs):
        unary = self.operation in UNARY_OPERATIONS
        # An unlinked socket has no Column behind it - its inline numeric
        # field (value_a/value_b, drawn via prop_name when unlinked) takes
        # over instead, as a synthetic one-row Column with this node's own
        # name as the data key, so the rest of evaluate() (which only
        # knows how to deal with Columns) doesn't need a separate code
        # path for the "typed-in constant" case.
        # "A"/"B" not existing yet (mid copy-paste, see update_sockets'
        # comment) means there's nothing to evaluate against - fall back
        # to the typed-in constant rather than indexing a socket that
        # isn't there.
        a_linked = "A" in self.inputs and self.inputs["A"].is_linked
        b_linked = "B" in self.inputs and self.inputs["B"].is_linked
        rows_a = inputs[0] if a_linked else [{self.name: self.value_a}]
        rows_a = rows_a or []
        rows_b = inputs[1] if b_linked else [{self.name: self.value_b}]
        rows_b = rows_b or []
        broadcast = len(rows_b) == 1

        if not unary and rows_b and len(rows_b) != len(rows_a) and not broadcast:
            error = ValueError(
                f"Column B has {len(rows_b)} rows, expected 1 (broadcast) "
                f"or {len(rows_a)} (matching A)"
            )
            # short_message: what the Viewer-adjacent overlay draws above
            # the erroring node (nodes_viewer.py:_draw_evaluation_errors) -
            # the full exception text above is too long to read comfortably
            # at node-editor zoom, the node-tree position already tells the
            # user which node failed.
            error.short_message = "A and B length mismatch"
            raise error

        # Equal row counts alone doesn't mean row i of A and row i of B
        # are the same entity - e.g. A from Field=Face and B from
        # Field=Object can happen to have the same number of rows by pure
        # coincidence. Checking the id keys (_Object/_Face/_Edge/_Vertex/
        # _Level) catch this: if they don't match row-for-row, pairing
        # them positionally anyway would silently combine unrelated rows
        # instead of failing loudly. Skipped entirely for the single-row
        # broadcast case - a one-row B has no per-row identity to match,
        # it's a constant by design (see Value node, or B's own inline
        # field - neither carries an id key at all, so this comparison
        # would always fail them otherwise).
        if not unary and rows_b and not broadcast:
            for i, (row_a, row_b) in enumerate(zip(rows_a, rows_b)):
                ids_a = {k: v for k, v in row_a.items() if k.startswith("_")}
                ids_b = {k: v for k, v in row_b.items() if k.startswith("_")}
                if ids_a != ids_b:
                    error = ValueError(
                        f"Row {i} of A and B don't refer to the same entity "
                        f"(A: {ids_a}, B: {ids_b}) - can't combine rows "
                        f"positionally otherwise"
                    )
                    error.short_message = "A and B rows don't match"
                    raise error

        result = []
        for i, row in enumerate(rows_a):
            # A column-less row (the synthetic constant from an unlinked
            # A) has only this node's own name as its single key, with no
            # id keys to carry through - dict(row) below still does the
            # right thing for it, same as for a real Column's row.
            new_row = dict(row)
            key = self._data_key(row)
            if key is not None:
                try:
                    a = float(row.get(key, 0))
                    if unary:
                        b = 0.0
                    else:
                        b_row = rows_b[0] if broadcast else rows_b[i] if rows_b else {}
                        b_key = self._data_key(b_row) if b_row else None
                        b = float(b_row.get(b_key, 0)) if b_key else 0.0
                    new_row[key] = self._compute(a, b)
                except (TypeError, ValueError):
                    new_row[key] = 0.0
            result.append(new_row)
        return [result]
