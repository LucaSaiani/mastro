from bpy.types import Node
from bpy.props import EnumProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node
from .nodes_aggregate_column import OPERATION_ITEMS, _data_key


# Pivots a Column: one chosen id key (Row Key) becomes every result
# row's own identity, another (Column Key) has its distinct values
# turned into separate DATA keys - the user's own framing, inspired by
# KNIME's own Pivoting node: "_Floor in righe, ogni valore distinto di
# _UnitType come colonna, aggregando i valori che cadono nella stessa
# cella". Produces a Multi Column (sockets.py:MaStroScheduleMultiColumnSocket),
# never a plain Column - the result has MORE THAN ONE data key per row
# (one per distinct Column Key value), which breaks every existing
# Column-consuming node's own "exactly one data key, found by
# exclusion" assumption (see that socket's own module comment in
# sockets.py for the fuller reasoning, including the Blender 5.0
# socket-shape parallel that confirmed a fixed, separate type is the
# right call here rather than overloading Column).
#
# Every result row carries every data key found across the WHOLE
# Column, not just the ones that occurred for that particular Row Key
# value - filled with the Operation's own "empty" value (0 for Sum/
# Count/Average, None for Mode/-, see _aggregate below) where a given
# Row Key/Column Key combination never actually occurred - the user's
# own explicit call, so every row has the exact same shape.
class MaStroSchedulePivotNode(MaStroScheduleTreeNode, Node):
    """Pivot a Column: one id key becomes each row's own identity,
    another's distinct values become separate data columns, aggregating
    whatever falls into the same cell"""
    bl_idname = 'MaStroSchedulePivot'
    bl_label = 'Pivot'

    operation: EnumProperty(name="Operation", items=OPERATION_ITEMS, default='SUM', update=update_node)

    def init(self, context):
        self.inputs.new('MaStroScheduleColumnSocketType', "Column")
        self.inputs.new('MaStroScheduleIdKeySocketType', "Row Key")
        self.inputs.new('MaStroScheduleIdKeySocketType', "Column Key")
        self.outputs.new('MaStroScheduleMultiColumnSocketType', "Multi Column")

    def draw_buttons(self, context, layout):
        layout.prop(self, "operation", text="")

    def evaluate(self, inputs):
        rows = inputs[0] or []
        row_key = inputs[1]
        column_key = inputs[2]
        if not row_key or not column_key or not rows:
            return [{"id_keys": [], "data_keys": [], "rows": []}]

        data_key = _data_key(rows[0])

        # First pass: collect every distinct Column Key value (in
        # first-seen order, not sorted - same "order of appearance"
        # convention Aggregate's own group order already follows) -
        # these become this Multi Column's own data_keys, the same
        # set for every result row regardless of which Row Key/Column
        # Key combinations actually occurred.
        column_values = []
        seen_columns = set()
        row_order = []
        seen_rows = set()
        # group_id -> {column_value: [values]}
        groups = {}
        for row in rows:
            row_id = row.get(row_key)
            col_id = row.get(column_key)
            if col_id not in seen_columns:
                seen_columns.add(col_id)
                column_values.append(col_id)
            if row_id not in seen_rows:
                seen_rows.add(row_id)
                row_order.append(row_id)
            groups.setdefault(row_id, {}).setdefault(col_id, []).append(row.get(data_key))

        result_rows = []
        for row_id in row_order:
            new_row = {row_key: row_id}
            for col_id in column_values:
                values = groups.get(row_id, {}).get(col_id, [])
                new_row[str(col_id)] = self._aggregate(values)
            result_rows.append(new_row)

        return [{
            "id_keys": [row_key],
            "data_keys": [str(c) for c in column_values],
            "rows": result_rows,
        }]

    def _aggregate(self, values):
        # Same operation set/shape as Aggregate's own _aggregate
        # (nodes_aggregate_column.py) - duplicated rather than shared,
        # since Aggregate's own version is a bound method on a
        # different class; not worth a shared free function for this
        # short a body.
        if self.operation == 'NONE':
            return values[0] if values else None
        if self.operation == 'COUNT':
            return len(values)
        if self.operation == 'MODE':
            from collections import Counter
            counts = Counter(values)
            return max(counts, key=counts.get) if counts else None
        numbers = []
        for value in values:
            try:
                numbers.append(float(value))
            except (TypeError, ValueError):
                pass
        if self.operation == 'AVERAGE':
            return sum(numbers) / len(numbers) if numbers else 0.0
        return sum(numbers)
