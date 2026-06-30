import bpy
from bpy.types import Node

from .tree import MaStroScheduleTreeNode


def _id_key_signature(row):
    """A hashable signature built from EVERY id key present on `row`
    (every key starting with "_" - same convention _data_key/_id_keys
    already use elsewhere, e.g. nodes_aggregate_column.py/
    nodes_id_keys.py), sorted by key name so the same combination of
    id keys always produces the same signature regardless of dict
    insertion order. Duplicated from nodes_merge_list.py's own
    identical helper rather than imported - same reasoning as
    nodes_id_keys.py's own _id_keys duplication, avoiding an import
    cycle between sibling node modules."""
    return tuple(sorted((k, row[k]) for k in row if k.startswith("_")))


# Combines several Columns (already sharing the same outer identity -
# e.g. all already filtered/grouped down to one Object, the common
# case right after Item from List/inside a For Each List body) into
# one Column whose own rows carry every input's own data attributes
# together. Merge List's own (nodes_merge_list.py) "outer key, inner
# rows" two-level merge, with the outer level dropped - that level
# only ever mattered for combining whole LISTS (multiple Group Into
# List outputs, one group per Object); once already down to a single
# Object's own Column, there's nothing left to group by at the outer
# level, only the SAME inner-row merge Merge List's own inner loop
# already does (_id_key_signature below, unchanged from there).
#
# The user's own design call, after noticing Aggregate's own "Id Key
# to Group" input was redundant inside a loop already grouped by
# Object (every row already shares the same _Object, so re-passing
# Object_id to Aggregate just to group by it again added nothing) -
# rather than extending Aggregate itself to accept multiple Columns
# directly (considered and rejected: Aggregate would then be doing two
# jobs, merging AND aggregating, instead of one), a separate node
# mirrors Merge List's own "one node, one job" shape: Merge Column
# merges, an ordinary Aggregate (unchanged, still a single Column
# input) aggregates whatever Merge Column hands it - composable, same
# as Merge List -> For Each List already is.
#
# Rows present in one input but missing from another (e.g. Area has a
# row Use doesn't) are padded with None for whatever attributes that
# row never had - never dropped, mirroring Merge List's own identical
# rule (itself mirroring Join Tables/Join Sheets' own "missing data is
# padded, not discarded" rule, nodes_table_join.py).
class MaStroScheduleMergeColumnNode(MaStroScheduleTreeNode, Node):
    """Combine several Columns (already sharing the same outer
    identity, e.g. one Object's own rows) into one, merging rows
    together by every id key they share"""
    bl_idname = 'MaStroScheduleMergeColumn'
    bl_label = 'Merge Column'

    def init(self, context):
        # use_multi_input is a constructor-only argument - see Join
        # Tables' own init() (nodes_table_join.py) for the confirmed
        # RNA source detail.
        self.inputs.new('MaStroScheduleColumnSocketType', "Column", use_multi_input=True)
        self.outputs.new('MaStroScheduleColumnSocketType', "Column")

    @property
    def column_label(self):
        # Mirrors Merge List's own column_label (nodes_merge_list.py) -
        # delegates to the FIRST linked Column input, since every input
        # is assumed to share the same outer identity already.
        socket = self.inputs["Column"]
        if not socket.links:
            return ""
        from .tree import upstream_attr
        return upstream_attr(socket.links[0].from_socket, "column_label")

    def evaluate(self, inputs):
        columns = inputs[0] or []
        if not columns:
            return [[]]

        # Rows keyed by their own FULL id-key signature
        # (_id_key_signature above) - same "first-seen order" merge as
        # Merge List's own inner loop, just without an outer "key"
        # level to merge within first.
        merged_by_match = {}
        order = []
        for column in columns:
            for row in column or []:
                match_key = _id_key_signature(row)
                if match_key not in merged_by_match:
                    merged_by_match[match_key] = {}
                    order.append(match_key)
                merged_by_match[match_key].update(row)

        return [[merged_by_match[match_key] for match_key in order]]


classes = (
    MaStroScheduleMergeColumnNode,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
