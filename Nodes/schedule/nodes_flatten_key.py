from bpy.types import Node
from bpy.props import EnumProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node
from .nodes_aggregate_column import OPERATION_ITEMS, _data_key
from .nodes_id_keys import _id_keys


# PROTOTYPE - see the conversation that introduced this node for the
# design discussion (the Plot -> Block -> Use -> Level cascading case).
#
# The mirror image of Aggregate (nodes_aggregate_column.py): Aggregate
# keeps ONE chosen id key and drops every other one; Flatten Key drops
# ONE chosen id key and KEEPS every other one. Rows are merged together
# only if they agree on every id key OTHER than the chosen Id Key - that
# key itself is the one allowed to differ, since it's the one being
# collapsed away.
#
# This is what makes chaining work for a real case like Plot -> Block ->
# Use -> Level: Flatten Key(Id Key=_Level) merges rows that agree on
# _Object/_Block/_Plot/_Use, summing across _Level - the result still
# carries _Object/_Block/_Plot/_Use (just not _Level anymore), so a
# second Flatten Key(Id Key=_Use) chained after it has something left to
# flatten, and so on down the chain - one id key consumed per node,
# mirroring the user's own VBA for-loop nesting one level at a time,
# with each step's own partial totals still available by reading that
# step's output directly (rather than only the final, fully collapsed
# result).
#
# Id Key is the same socket type Get Id Keys emits (nodes_id_keys.py) -
# no internal search-popup fallback when unconnected, the user's own
# call: this socket is now the ONLY way to set it.
class MaStroScheduleFlattenKeyNode(MaStroScheduleTreeNode, Node):
    """Collapse a Column's rows that share every id key except the
    chosen one, dropping that one key while keeping the rest - chain
    several of these to aggregate across multiple keys, one at a time
    (e.g. Level, then Use, then Block), keeping each step's own partial
    totals available"""
    bl_idname = 'MaStroScheduleFlattenKey'
    bl_label = 'Flatten Key'

    operation: EnumProperty(name="Operation", items=OPERATION_ITEMS, default='SUM', update=update_node)

    def init(self, context):
        self.inputs.new('MaStroScheduleColumnSocketType', "Column")
        self.inputs.new('MaStroScheduleIdKeySocketType', "Id Key")
        self.outputs.new('MaStroScheduleColumnSocketType', "Column")

    @property
    def column_label(self):
        if "Column" not in self.inputs:
            return ""
        from .tree import upstream_attr
        return upstream_attr(self.inputs["Column"], "column_label")

    def draw_buttons(self, context, layout):
        layout.prop(self, "operation", text="")

    def evaluate(self, inputs):
        rows = inputs[0] or []
        flatten_key = inputs[1]
        if not flatten_key or not rows:
            return [rows]

        data_key = _data_key(rows[0])
        groups = {}
        order = []
        for row in rows:
            # The grouping identity is every id key EXCEPT flatten_key -
            # see this class's module-level docstring for why that's the
            # one key allowed to differ within a group.
            remaining_keys = [k for k in _id_keys(row) if k != flatten_key]
            group_id = tuple(row.get(k) for k in remaining_keys)
            if group_id not in groups:
                new_row = {k: row.get(k) for k in remaining_keys}
                groups[group_id] = {"row": new_row, "values": []}
                order.append(group_id)
            groups[group_id]["values"].append(row.get(data_key))

        result = []
        for group_id in order:
            group = groups[group_id]
            new_row = dict(group["row"])
            new_row[data_key] = self._aggregate(group["values"])
            result.append(new_row)
        return [result]

    def _aggregate(self, values):
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
