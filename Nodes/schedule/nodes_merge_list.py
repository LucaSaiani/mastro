import bpy
from bpy.types import Node

from .tree import MaStroScheduleTreeNode


def _id_key_signature(row):
    """A hashable signature built from EVERY id key present on `row`
    (every key starting with "_" - same convention _data_key/_id_keys
    already use elsewhere, e.g. nodes_aggregate_column.py/
    nodes_id_keys.py), sorted by key name so the same combination of
    id keys always produces the same signature regardless of dict
    insertion order."""
    return tuple(sorted((k, row[k]) for k in row if k.startswith("_")))


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
# that and doesn't try to).
#
# Inner rows within each matched group are matched by EVERY id key
# present on them together (_id_key_signature above), not a single
# chosen Id Key - the user's own explicit correction after a single-
# key version (e.g. just _Face) was confirmed live to silently
# collapse rows: a building with multiple _Level rows sharing the same
# _Face value all matched the SAME inner key and overwrote each other,
# losing every level but the last one merged. A combined signature of
# every id key at once (_Object handled separately as the outer key,
# but _Face+_Level+... together here) only matches rows that truly
# represent the same underlying element - no single key to choose
# (right or wrong), no collision possible between rows that are
# actually distinct. A row present in one input's own group but
# missing from another (e.g. Area has a row Use doesn't) is padded
# with None for whatever attributes that row never had - never
# dropped, mirroring Join Tables/Join Sheets' own "missing data is
# padded, not discarded" rule (nodes_table_join.py).
#
# Each input's own data attribute keeps whatever distinct node.name
# Evaluate Attribute gave it (e.g. "Evaluate Attribute"/"Evaluate
# Attribute.001", never the chosen attribute's own user-facing name
# like "area"/"use" - see that node's own module comment for why:
# node.name is guaranteed unique, exactly so two merged Columns never
# collide on the same dict key the way two equally-named "area"
# columns could) - so a merged row ends up with BOTH distinct keys
# side by side rather than one overwriting the other. The Viewer's own
# evaluate() (nodes_viewer.py) was extended alongside this node to
# relabel each one individually back to its own readable
# column_label when more than one data key shows up in the same row -
# confirmed live as a real, separate bug before that fix: relabeling
# every data key to one borrowed label collapsed two genuinely
# different attributes onto the same visible column name, silently
# losing one of them.
class MaStroScheduleMergeListNode(MaStroScheduleTreeNode, Node):
    """Combine several Lists (grouped by the same outer key) into one,
    merging each group's own inner rows together by every id key they
    share"""
    bl_idname = 'MaStroScheduleMergeList'
    bl_label = 'Merge List'

    def init(self, context):
        # use_multi_input is a constructor-only argument - see Join
        # Tables' own init() (nodes_table_join.py) for the confirmed
        # RNA source detail.
        self.inputs.new('MaStroScheduleListSocketType', "List", use_multi_input=True)
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
        if not lists:
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
                # inner rows for THIS input's own group, keyed by the
                # FULL id-key signature of each row (_id_key_signature
                # above) - same "first-seen order" convention as the
                # outer keys, kept per input so a row present in an
                # earlier input but missing here doesn't accidentally
                # inherit this input's own ordering.
                inner_by_match = merged_by_key[key]
                for row in group.get("rows", []):
                    inner_key = _id_key_signature(row)
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
