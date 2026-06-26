from bpy.types import Node

from .tree import MaStroScheduleTreeNode
from .nodes_aggregate_column import _data_key


# PROTOTYPE - see the conversation that introduced this node (started
# from "how many buildings do I have", which this answers via Total with
# Id Key=Object_id, reading any one row's value - every row in the same
# group already carries the same Total).
#
# Mirrors Geometry Nodes' own Accumulate Field (confirmed against
# Blender's source, node_geo_accumulate_field.cc) exactly: Leading is the
# running total up to AND INCLUDING each row, Trailing is the running
# total up to but NOT including each row (starts at 0), Total is the
# final total for that row's own group - all three are per-row outputs
# of the same length as the input Column, not a single collapsed value,
# matching node_geo_accumulate_field.cc's AccumulateFieldInput/
# TotalFieldInput exactly (every row of a group reads the same Total,
# via accumulations.lookup(group_indices[i]) in the C++ source). With
# Id Key left unconnected, every row belongs to the same single group,
# exactly GN's own "Group ID is a single value" branch
# (group_indices.is_single()) - a deliberately valid, common choice
# here (a single running total over every row), not a state to avoid,
# unlike Aggregate/Group Into List/Flatten Key where an unset key means
# nothing to do at all.
#
# With an Id Key connected (e.g. Object_id), the running total resets to
# 0 every time the key's value changes from the previous row to this
# one - NOT a full re-group like Aggregate/Group Into List/Flatten Key
# (which gather every row sharing a key together first, regardless of
# row order). Accumulate deliberately keeps row order untouched and
# only tracks "has the key changed since the last row", matching GN's
# own row-order-preserving behavior (the C++ source's group_indices[i]
# lookup walks rows in their existing order, never re-sorting/
# re-grouping them) - rows with the same key value but not adjacent
# (e.g. interleaved with a different object's rows) would NOT
# accumulate together. This matches every other Column-producing node
# in this tree, which already emits rows already naturally grouped by
# key (e.g. Evaluate Attribute's own per-object, per-level row order) -
# Group Into List's own dict-based grouping (nodes_groupby_column.py) is
# the tool for ungrouped/interleaved data.
#
# Id Key is the same socket type Get Id Keys emits (nodes_id_keys.py) -
# no internal search-popup fallback when unconnected, the user's own
# call: this socket is now the ONLY way to set it (leaving it
# unconnected is itself the valid "(none)" choice, see above).
class MaStroScheduleAccumulateNode(MaStroScheduleTreeNode, Node):
    """Running total of a Column's values, row by row - Leading
    (inclusive), Trailing (exclusive) and Total (the final value for
    that row's own group) - optionally resetting at every change of the
    chosen id key"""
    bl_idname = 'MaStroScheduleAccumulate'
    bl_label = 'Accumulate'

    def init(self, context):
        self.inputs.new('MaStroScheduleColumnSocketType', "Column")
        self.inputs.new('MaStroScheduleIdKeySocketType', "Id Key")
        self.outputs.new('MaStroScheduleColumnSocketType', "Leading")
        self.outputs.new('MaStroScheduleColumnSocketType', "Trailing")
        self.outputs.new('MaStroScheduleColumnSocketType', "Total")

    @property
    def column_label(self):
        if "Column" not in self.inputs:
            return ""
        from .tree import upstream_attr
        return upstream_attr(self.inputs["Column"], "column_label")

    def evaluate(self, inputs):
        rows = inputs[0] or []
        group_key = inputs[1]
        if not rows:
            return [[], [], []]

        data_key = _data_key(rows[0])
        leading_rows, trailing_rows, total_rows = [], [], []

        # Same "the key changed since the last row" reset as GN's own
        # group_indices[i] lookup - see this class's own docstring for
        # why this preserves row order instead of re-grouping.
        current_key = object()  # sentinel never equal to any real value
        accumulation = 0.0
        group_start_index = 0

        def _numeric(value):
            try:
                return float(value)
            except (TypeError, ValueError):
                return 0.0

        for i, row in enumerate(rows):
            key_value = row.get(group_key) if group_key else None
            if key_value != current_key:
                current_key = key_value
                accumulation = 0.0
                group_start_index = i

            trailing_rows.append({**row, data_key: accumulation})
            accumulation += _numeric(row.get(data_key))
            leading_rows.append({**row, data_key: accumulation})

            # Total isn't known for a group until its LAST row has been
            # walked - every row's own Total dict is appended now (with
            # a placeholder value), then patched in place once the
            # group's final accumulation is known (mirrors GN's own
            # two-pass shape: TotalFieldInput's loop also only finishes
            # accumulating a group before its second loop reads
            # accumulations.lookup() back out for every row of it).
            total_rows.append({**row, data_key: accumulation})
            is_last_row = i + 1 == len(rows)
            next_key_changes = group_key and not is_last_row and rows[i + 1].get(group_key) != current_key
            if is_last_row or next_key_changes:
                for j in range(group_start_index, i + 1):
                    total_rows[j][data_key] = accumulation

        return [leading_rows, trailing_rows, total_rows]
