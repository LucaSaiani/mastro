from bpy.types import Node
from bpy.props import EnumProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node


OPERATION_ITEMS = [
    ('NONE', "-", "Group only - keep any one row's value as-is, with nothing actually aggregated"),
    ('SUM', "Sum", "Sum the column's values within each group"),
    ('COUNT', "Count", "Count the rows in each group"),
    ('AVERAGE', "Average", "Average the column's values within each group"),
    ('MODE', "Mode", "The most frequently occurring value within each group"),
]


def _data_key(row):
    for key in row.keys():
        if not key.startswith("_"):
            return key
    return None


# PROTOTYPE - see the conversation that introduced this node for the
# design discussion.
#
# Aggregates a Column down to one row per distinct value of the chosen
# `group_key` id key, DROPPING every other id key entirely - "total per
# Object" means group_key=_Object, and the result no longer carries
# _Face/_Level at all, just _Object and the aggregated value. This is
# the opposite of Flatten Key (nodes_flatten_key.py), which instead
# drops only the chosen key and KEEPS every other one - the two cover
# the two parallel cases the user described: a flat "total per Object"
# regardless of how many Face/Level rows feed into each Object (this
# node), versus a step-by-step cascade like Plot -> Block -> Use ->
# Level where each step needs to keep peeling away one key at a time
# while the others survive to the next step (Flatten Key, chained).
#
# Id Key is the same socket type Get Id Keys emits (sockets.py:
# MaStroScheduleIdKeySocket, nodes_id_keys.py) - the user's own ask: the
# choice of which id key to group by used to be hardcoded into a search-
# popup built fresh by each of Aggregate/Group Into List/Accumulate,
# instead of one shared, dynamic "what id keys exist on this Column"
# node whose output can be wired to several of them at once. No
# internal search-popup fallback when unconnected - the user's own
# follow-up call, once Get Id Keys existed: this socket is now the ONLY
# way to set it, never both a socket and a node-local picker at the
# same time.
#
# Deliberately NOT the abandoned WIP Group By/Aggregate
# (nodes_groupby.py/nodes_aggregate.py, both still WIP and built against
# the old Data model before this Column model existed) - the user's own
# call: "ignora quello che c'è in wip... spesso non è generalizzabile",
# that earlier attempt mirrored one Excel-macro example without ever
# discussing the general problem this one is built from.
class MaStroScheduleAggregateColumnNode(MaStroScheduleTreeNode, Node):
    """Aggregate a Column down to one row per distinct value of the
    chosen id key, dropping every other id key - e.g. Id Key=Object_id
    gives one row per object, regardless of how many Face/Level rows
    fed into it"""
    bl_idname = 'MaStroScheduleAggregateColumn'
    bl_label = 'Aggregate'

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
        group_key = inputs[1]
        if not group_key or not rows:
            return [rows]

        data_key = _data_key(rows[0])
        groups = {}
        order = []
        for row in rows:
            group_id = row.get(group_key)
            if group_id not in groups:
                groups[group_id] = []
                order.append(group_id)
            groups[group_id].append(row.get(data_key))

        result = []
        for group_id in order:
            result.append({group_key: group_id, data_key: self._aggregate(groups[group_id])})
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
