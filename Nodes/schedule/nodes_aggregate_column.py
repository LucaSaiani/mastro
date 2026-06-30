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
# Deliberately NOT the abandoned WIP Group By (nodes_groupby.py, still
# WIP and built against the old Data model before this Column model
# existed) - the user's own call: "ignora quello che c'è in wip...
# spesso non è generalizzabile", that earlier attempt mirrored one
# Excel-macro example without ever discussing the general problem this
# one is built from. The equally superseded Aggregate
# (nodes_aggregate.py) was removed outright once confirmed redundant
# with this node.
class MaStroScheduleAggregateColumnNode(MaStroScheduleTreeNode, Node):
    """Aggregate a Column down to one row per distinct value of the
    chosen id key, dropping every other id key - e.g. Id Key=Object_id
    gives one row per object, regardless of how many Face/Level rows
    fed into it"""
    bl_idname = 'MaStroScheduleAggregateColumn'
    bl_label = 'Aggregate'

    operation: EnumProperty(name="Operation", items=OPERATION_ITEMS, default='SUM', update=update_node)

    # Same MaStroScheduleAttributeRefSocketType Named Attribute itself
    # outputs (nodes_attribute.py) - optional, left unwired in the
    # common case (a Column with exactly one data key, found by
    # exclusion via _data_key as always). Added once a Column with
    # MORE than one data key at once became possible (Merge List,
    # nodes_merge_list.py) and confirmed live as a real, silent bug:
    # _data_key always picked the SAME first key by exclusion
    # regardless of which one the user actually wanted, with no way to
    # choose - two separate Aggregate nodes meant to total Area and
    # Use respectively both silently aggregated the same one. Named
    # Attribute's own available_attribute_names (nodes_attribute.py)
    # was extended to recognize this node as a second kind of
    # consumer (reading the Column's own already-present data keys,
    # not a MaStro object's mesh attributes) - one shared picker node
    # covers both cases, the user's own explicit design call, rather
    # than a second dedicated node for this one.
    def init(self, context):
        self.inputs.new('MaStroScheduleColumnSocketType', "Column")
        self.inputs.new('MaStroScheduleIdKeySocketType', "Id Key")
        self.inputs.new('MaStroScheduleAttributeRefSocketType', "Attribute Name")
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
        attribute_ref = inputs[2] or []
        if not group_key or not rows:
            return [rows]

        # Attribute (the optional explicit choice) wins when wired and
        # actually present in this Column's own rows - falls back to
        # the old by-exclusion behavior otherwise, covering both "left
        # unwired entirely" (the common single-data-key case) and "the
        # chosen name doesn't match anything here" (e.g. picked against
        # a different upstream Column before this one was rewired) -
        # the same "don't silently produce nothing, fall back to
        # something reasonable" spirit Math/Header's own
        # _data_key-style fallbacks already follow.
        chosen_name = attribute_ref[0].get("Name") if attribute_ref else None
        if chosen_name and chosen_name in rows[0]:
            data_key = chosen_name
        else:
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
