import bpy
from bpy.types import Node

from .tree import MaStroScheduleTreeNode


# Combines several Lists (e.g. multiple Group Into List outputs, each
# grouping the same underlying data by the same OUTER id key - see
# nodes_groupby_column.py's own docstring for List's shape, {"key":
# ..., "rows": [...]}) into one List whose own inner rows carry every
# input's own data attributes together - the user's own design,
# worked out from a real limitation found testing For Each List
# (issue #15): Aggregate (and every other Column-consuming node) only
# ever processes ONE data attribute per row (found by exclusion, see
# nodes_aggregate_column.py:_data_key) - if a Column has both Area and
# Use, only one gets used, the other silently ignored. There was no
# way to process both inside the same loop. Merge List is built
# BEFORE a For Each, as its own separate, Viewer-inspectable step
# (the user's own explicit preference over a For Each-level
# multi-input - a dedicated node's own result can be checked with the
# Viewer before it ever reaches a loop, the same debugging-friendliness
# this whole node set already leans on).
#
# Outer groups are matched across every input List by their own "key"
# (the same id key value every input List's own Group Into List was
# grouped by - assumed to already be the SAME outer key across every
# input, e.g. all grouped by _Object; this node has no way to verify
# that and doesn't try to). Inner rows within each matched group are
# then matched against each other by Match Key (an explicit Id Key
# input, e.g. _Level) - NOT by position, the user's own deliberate
# call: row order within a group isn't guaranteed to agree across
# different input Lists, an implicit positional match would silently
# misalign data the moment it didn't. A row present in one input's own
# group but missing from another (e.g. Area has a _Level=2 row, Use
# doesn't) is padded with None for whatever attributes that row never
# had - never dropped, mirroring Join Tables/Join Sheets' own "missing
# data is padded, not discarded" rule (nodes_table_join.py).
class MaStroScheduleMergeListNode(MaStroScheduleTreeNode, Node):
    """Combine several Lists (grouped by the same outer key) into one,
    merging each group's own inner rows together by a chosen id key"""
    bl_idname = 'MaStroScheduleMergeList'
    bl_label = 'Merge List'

    def init(self, context):
        # use_multi_input is a constructor-only argument - see Join
        # Tables' own init() (nodes_table_join.py) for the confirmed
        # RNA source detail.
        self.inputs.new('MaStroScheduleListSocketType', "List", use_multi_input=True)
        self.inputs.new('MaStroScheduleIdKeySocketType', "Match Key")
        self.outputs.new('MaStroScheduleListSocketType', "List")

    @property
    def column_label(self):
        # Mirrors Group Into List's own column_label (nodes_groupby_column.py) -
        # delegates to the FIRST linked List input, since every input is
        # assumed to share the same outer key/identity already.
        socket = self.inputs["List"]
        if not socket.links:
            return ""
        from .tree import upstream_attr
        return upstream_attr(socket.links[0].from_socket, "column_label")

    def evaluate(self, inputs):
        lists = inputs[0] or []
        match_key = inputs[1]
        if not lists or not match_key:
            return [[]]

        # Outer groups, keyed by their own "key" - merged in the order
        # the first non-empty input List established (first-seen
        # order), every other input's own matching group folded into
        # it as it's found.
        merged_by_key = {}
        order = []
        for one_list in lists:
            for group in one_list or []:
                key = group.get("key")
                if key not in merged_by_key:
                    merged_by_key[key] = {}
                    order.append(key)
                # inner rows for THIS input's own group, keyed by
                # match_key's own value - same "first-seen order"
                # convention as the outer keys, kept per input so a
                # row present in an earlier input but missing here
                # doesn't accidentally inherit this input's own
                # ordering.
                inner_by_match = merged_by_key[key]
                for row in group.get("rows", []):
                    inner_key = row.get(match_key)
                    if inner_key not in inner_by_match:
                        inner_by_match[inner_key] = {}
                    inner_by_match[inner_key].update(row)

        result = []
        for key in order:
            rows = list(merged_by_key[key].values())
            result.append({"key": key, "rows": rows})
        return [result]


classes = (
    MaStroScheduleMergeListNode,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
