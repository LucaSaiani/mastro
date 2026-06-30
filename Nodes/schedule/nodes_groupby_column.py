from bpy.types import Node
from bpy.props import IntProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node, is_socket_active


# PROTOTYPE - see the conversation that introduced this node for the
# design discussion (Object -> per-object list of rows, each then
# group-able again by Level, picked apart one group at a time with Item
# from List below, before any future "loop" node automates walking every
# group instead of needing one Item from List per value).
#
# Unlike Aggregate/Flatten Key (nodes_aggregate_column.py/
# nodes_flatten_key.py), which both immediately collapse each group down
# to a single aggregated value, Group Into List keeps every group's
# original rows fully intact (still carrying every id key except the
# chosen Id Key, untouched) - nothing is aggregated here at all. This is
# what lets a group be grouped again afterwards (e.g. group by Object,
# then within one chosen object's own rows, group again by Level)
# instead of having already thrown away the detail Aggregate/Flatten Key
# would have collapsed. The trade-off the user explicitly accepted
# choosing this over Aggregate/Flatten Key being "good enough": this
# produces a List, a new shape (sockets.py:MaStroScheduleListSocket)
# nothing else in this tree's Column-based nodes consumes yet except
# Item from List below - getting back to a plain Column (so Aggregate/
# Math/Viewer/... can work on it again) always goes through that node
# first. Named "Group Into List", not "Group By" - the user's own call:
# the result is a List, not a Column, the name should say so rather than
# reading the same as Aggregate's own (very different) grouping.
#
# Id Key is the same socket type Get Id Keys emits (nodes_id_keys.py) -
# no internal search-popup fallback when unconnected, the user's own
# call: this socket is now the ONLY way to set it.
class MaStroScheduleGroupByColumnNode(MaStroScheduleTreeNode, Node):
    """Group a Column's rows by the chosen id key into a List of groups,
    each keeping its full, unaggregated list of rows - pick one group out
    with Item from List to keep working on it (e.g. group it again by a
    different key)"""
    bl_idname = 'MaStroScheduleGroupByColumn'
    bl_label = 'Group Column by Key'

    def init(self, context):
        self.inputs.new('MaStroScheduleColumnSocketType', "Column")
        self.inputs.new('MaStroScheduleIdKeySocketType', "Id Key")
        self.outputs.new('MaStroScheduleListSocketType', "List")

    @property
    def column_label(self):
        # Mirrors A's label unchanged (same reasoning as Math's own
        # column_label) - a List still carries the SAME underlying
        # Column data inside each group's "rows", just regrouped, not
        # given a new identity. Read by Item from List below, which has
        # no "Column" input of its own to delegate to directly (only
        # "List") - it instead reads THIS property off whatever node
        # produced its List input.
        if "Column" not in self.inputs:
            return ""
        from .tree import upstream_attr
        return upstream_attr(self.inputs["Column"], "column_label")

    def evaluate(self, inputs):
        rows = inputs[0] or []
        group_key = inputs[1]
        if not group_key or not rows:
            return [[]]

        groups = {}
        order = []
        for row in rows:
            group_id = row.get(group_key)
            if group_id not in groups:
                groups[group_id] = []
                order.append(group_id)
            groups[group_id].append(row)

        return [[{"key": group_id, "rows": groups[group_id]} for group_id in order]]


# Resolves a List (the output of Group Into List above) down to one
# chosen group's own rows, as an ordinary Column again - picked by a
# plain index, not by the group's key value, the user's own explicit
# call: an index stays valid across a rename of whatever the key's
# underlying value is (e.g. an object renamed in the scene), whereas a
# value-based picker (the same search-popup mechanism Aggregate/Group
# Into List's own key pickers use) would silently break/repoint to a
# different group the moment that value changed. The trade-off accepted
# along with that: the index is only as stable as the ORDER groups come
# out of Group Into List in, which mirrors the order rows arrived in the
# original Column (first appearance, see Group Into List's own
# evaluate() above) - stable as long as upstream row order doesn't
# change (e.g. no objects added/removed from the scene), not guaranteed
# otherwise.
class MaStroScheduleItemFromListNode(MaStroScheduleTreeNode, Node):
    """Pick one group out of a List by its position, returning that
    group's own rows as a Column again"""
    bl_idname = 'MaStroScheduleItemFromList'
    bl_label = 'Item from List'

    index: IntProperty(name="Index", default=0, min=0, update=update_node)

    def init(self, context):
        self.inputs.new('MaStroScheduleListSocketType', "List")
        self.inputs.new('MaStroScheduleColumnSocketType', "Index").prop_name = "index"
        self.outputs.new('MaStroScheduleColumnSocketType', "Column")

    @property
    def column_label(self):
        # No "Column" input to delegate to directly here, unlike
        # Math/Aggregate/Flatten Key - "List" is the only upstream input,
        # so this reads column_label off WHATEVER NODE produced that
        # List (e.g. Group Into List, which itself mirrors its own
        # Column input's label - see that class's own column_label
        # above) rather than a socket named "Column" that doesn't exist
        # on this node.
        if "List" not in self.inputs:
            return ""
        from .tree import upstream_attr
        return upstream_attr(self.inputs["List"], "column_label")

    def evaluate(self, inputs):
        groups = inputs[0] or []
        index = self._resolve_index(inputs[1])
        if not groups or index < 0 or index >= len(groups):
            return [[]]
        return [groups[index]["rows"]]

    def _resolve_index(self, value_in):
        # Same "unlinked socket always comes through as None" handling
        # as Rename Header/Math - fall back to the inline field's own
        # backing property explicitly when unlinked.
        if not is_socket_active(self.inputs["Index"]):
            return self.index
        if isinstance(value_in, (int, float)):
            return int(value_in)
        rows_in = value_in or []
        if not rows_in:
            return self.index
        row_key = next((k for k in rows_in[0] if not k.startswith("_")), None)
        return int(rows_in[0].get(row_key, self.index)) if row_key else self.index


# Counts the elements of a List - e.g. wired after Group Into List(key=
# Object_id) to answer "how many distinct objects/buildings are there"
# as a single number (the question that started this whole conversation:
# "se volessi sapere quanti edifici ho"). A Column with exactly one row,
# this node's own name as the data key, no id keys at all - the same
# "single constant" shape Value/Integer/String already use for their
# own one-row Columns, since a count has no per-row identity of its own
# to carry.
class MaStroScheduleListLengthNode(MaStroScheduleTreeNode, Node):
    """The number of groups in a List, as a one-row Column"""
    bl_idname = 'MaStroScheduleListLength'
    bl_label = 'List Length'

    def init(self, context):
        self.inputs.new('MaStroScheduleListSocketType', "List")
        self.outputs.new('MaStroScheduleColumnSocketType', "Column")

    @property
    def column_label(self):
        # Same fixed-name-by-default pattern as Value/Integer/String/
        # Colour (the user's own call, confirmed: those defaults are
        # wanted, not a gap to close) - missing here was an oversight,
        # not a deliberate "stay blank" choice the way Rename Header's
        # own empty-String case is.
        return "Length"

    def evaluate(self, inputs):
        groups = inputs[0] or []
        return [[{self.name: len(groups)}]]
