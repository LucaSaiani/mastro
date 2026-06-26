from bpy.types import Node
from bpy.props import CollectionProperty, IntProperty

from .tree import MaStroScheduleTreeNode, resolve_origin_node
from .execution import get_node_table
from .properties import MaStro_schedule_join_table_item


def _link_key(from_node, output_index):
    """A stable string identity for one connection into Join Tables' own
    multi-input socket - NOT the NodeLink object itself (not a stable
    Python identity across redraws/undo) and NOT just from_node.name
    (the same node could have more than one output, or appear linked
    more than once via different outputs) - from_node.name plus which
    of its OWN outputs feeds this connection is the smallest thing that
    actually disambiguates every real case."""
    return f"{from_node.name}::{output_index}"


def _header_text(table):
    """The first column's own header text in a Table value (see
    sockets.py:MaStroScheduleTableSocket for the shape) - an empty
    string if there are no columns at all, or the header has no text
    (the UIList itself is what shows "(empty)" for that case, see
    MASTRO_UL_schedule_join_tables.draw_item in operators.py). Purely
    cosmetic, used only to label Join Tables' own ordering UIList - the
    user's own explicit call: "individuiamo le tabelle in base al loro
    header. se in input abbiamo una tabella di tabelle, vale il primo
    header trovato" (i.e. only the FIRST column's header, never anything
    past it, even if other columns disagree)."""
    columns = table.get("columns", []) if table else []
    if not columns:
        return ""
    return columns[0].get("header", {}).get("text", "")


# Concatenates several Tables side by side (more columns) - the user's
# own explicit ask: "facciamo un nodo join tables? prende in input
# multipli le tables, le unisce o orizzontalmente o verticalmente".
# Vertical stacking was REMOVED after a live test surfaced a real
# design question it can't answer cleanly: stacking whole Tables means
# every Table after the first has its own header text just... dropped
# (the result has ONE header per column, never several) - confirmed
# live as a real surprise ("vertical si mangia l'header"), not just a
# bug to patch. The user's own conclusion: that case belongs to a
# different concept ("Sheet" - a Table converted via Table to Sheet
# into an opaque block of plain cells with no header concept at all,
# combined - horizontally OR vertically - by Place in Sheet
# (nodes_sheet_place.py), which keeps every block's own former header
# intact as an ordinary cell rather than needing to choose between
# them) rather than forcing it into this node, which stays
# horizontal-only, where there's no such ambiguity (every column
# already carries its own header, nothing to choose between). A real
# Blender multi-input socket (use_multi_input=True) - resolved by
# execution.py:eval_node into a LIST of values (one per link), a
# deliberate core change made specifically for this node (see that
# function's own comment for why every other, non multi-input socket
# in this tree is entirely unaffected by it).
#
# The join ORDER is controlled by table_items (a UIList the user can
# reorder with Up/Down, see MASTRO_OT_Schedule_Join_Tables_Move in
# operators.py) - deliberately NOT the order links happen to have
# (Blender's own multi_input_sort_id IS readable from Python, but its
# own C++ source comment warns "for historical reasons, larger ids
# come before lower ids", an ordering quirk that's easy to get backwards)
# - the user's own explicit call: "l'ordine lo gestiamo all'interno del
# nodo, non in base a come entriamo nel nodo".
# table_items is re-synced against the socket's actual links from
# tree.py's own polling timer (new links appended at the end, removed
# links dropped, existing ones left exactly where the user put them) -
# NOT from draw_buttons (see _sync_table_items's own docstring for why
# that's disallowed) - see _sync_table_items below.
#
# Mismatched row/column counts between the Tables being joined are
# padded with blank cells rather than dropped - the user's own explicit
# call: "adatti riempimento con celle vuote. ricorda che il lavoro sulle
# table è puramente grafico. la coerenza dei dati deve essere garantita
# a monte nelle columns" - Table has no obligation to validate anything,
# only to render predictably.
#
# Each Table is assumed to already be positioned where the user wants it
# in the final result (e.g. via a future Translate Table node upstream,
# padding its own rows/columns with blank cells to shift it) - this node
# does no translation of its own, it only concatenates whatever arrives
# as-is, in table_items' own order.
class MaStroScheduleTableJoinNode(MaStroScheduleTreeNode, Node):
    """Join several Tables side by side, in an order set by this
    node's own list (not by link order)"""
    bl_idname = 'MaStroScheduleTableJoin'
    bl_label = 'Join Tables'

    table_items: CollectionProperty(type=MaStro_schedule_join_table_item)
    active_table_index: IntProperty()

    def init(self, context):
        # use_multi_input is a constructor-only argument (confirmed
        # against Blender's own RNA source, rna_Node_inputs_new in
        # rna_nodetree.cc) - it can't be set on an existing socket
        # afterward, only at creation time here.
        self.inputs.new('MaStroScheduleTableSocketType', "Table", use_multi_input=True)
        self.outputs.new('MaStroScheduleTableSocketType', "Table")

    def _sync_table_items(self):
        """Rebuilds the set of link_keys table_items tracks to exactly
        match the Table input's current links, preserving the existing
        ORDER of any link_key already present (new links are appended
        at the end, in whatever order socket.links happens to report -
        the user re-orders from there if it doesn't match what they
        want; removed links are dropped from wherever they were)."""
        socket = self.inputs["Table"]
        current_keys = []
        labels_by_key = {}
        for link in socket.links:
            # A muted link is treated as if it doesn't exist at all -
            # the user's own explicit call: the Table it feeds
            # disappears entirely from this list, not just from the
            # join result (same "unplugged in spirit" treatment as the
            # mismatch/reroute-failure cases right below).
            if link.is_muted:
                continue
            # Both the KEY identifying this entry AND the label shown
            # for it come from resolve_origin_node (walks back through
            # any transparent single-input Table operator - Move Sheet,
            # Edit Cell, ... - to the real origin) - the user's own
            # explicit call ("per me la label è quella del nodo
            # [origine]"): the label names the same node the key
            # tracks, not whatever value happens to be flowing through
            # right now (which can differ from the origin's own value
            # when an operator in between is muted) - identity and its
            # displayed name are the same thing, on purpose. See
            # resolve_origin_node's own docstring for the full story/bug
            # this fixes.
            origin_node, origin_socket = resolve_origin_node(link)
            if origin_node is None:
                continue
            try:
                output_index = list(origin_node.outputs).index(origin_socket)
            except ValueError:
                continue
            key = _link_key(origin_node, output_index)
            current_keys.append(key)
            table = get_node_table(self.id_data.name, origin_node.name)
            labels_by_key[key] = _header_text(table[output_index] if table else None)

        existing_keys = [item.link_key for item in self.table_items]
        # Drop entries whose link no longer exists, back to front so
        # removing by index doesn't shift the ones still to be checked.
        for index in reversed(range(len(self.table_items))):
            if existing_keys[index] not in current_keys:
                self.table_items.remove(index)
        # Append entries for any link not already tracked - new links
        # always join the order at the end, never inserted in the
        # middle of whatever order the user already set.
        tracked_keys = {item.link_key for item in self.table_items}
        for key in current_keys:
            if key not in tracked_keys:
                item = self.table_items.add()
                item.link_key = key
                tracked_keys.add(key)
        # Labels can change every evaluate() (e.g. the upstream Column's
        # own header text changed) even when the set of links didn't -
        # refreshed unconditionally on every sync, not just when an
        # entry is added.
        for item in self.table_items:
            item.label = labels_by_key.get(item.link_key, "")

    def draw_buttons(self, context, layout):
        # _sync_table_items() must NOT be called from here - confirmed
        # live: table_items.add() raised "Writing to ID classes in
        # this context is not allowed" the moment a Table was linked
        # in, the same restriction tree.py's update()/draw_buttons
        # already document for other writes. The sync instead runs
        # from tree.py's own polling timer (_poll_pending_trees, the
        # same one mark_mismatched_links uses) - this method only
        # reads whatever table_items already holds from the last poll.
        # Same row/template_list/column(align=True) layout every native
        # Blender list with Add/Remove/Move buttons uses (confirmed
        # against bl_ui/properties_data_mesh.py's own Vertex Groups/UV
        # Maps panels) - the buttons sit in their own column NEXT TO
        # the list, not stacked below it, matching the user's own
        # explicit call ("i pulsanti per muovere non sotto ma di fianco
        # come per tutte le altre ui").
        row = layout.row()
        row.template_list(
            "MASTRO_UL_schedule_join_tables", "", self, "table_items", self, "active_table_index", rows=4,
        )
        col = row.column(align=True)
        op = col.operator("mastro_schedule.join_tables_move", icon='TRIA_UP', text="")
        op.node_name = self.name
        op.direction = 'UP'
        op = col.operator("mastro_schedule.join_tables_move", icon='TRIA_DOWN', text="")
        op.node_name = self.name
        op.direction = 'DOWN'

    @staticmethod
    def _row_count(table):
        columns = table.get("columns", [])
        if not columns:
            return 0
        return max(len(column.get("rows", [])) for column in columns)

    @staticmethod
    def _blank_row():
        return {"text": "", "bg": None}

    def _join_horizontal(self, tables):
        """Side by side: every Table's own columns appended in order,
        each column's row list padded with blank rows up to the tallest
        Table in the join - so every column ends up the same height,
        even though the Tables it came from didn't agree."""
        row_count = max((self._row_count(t) for t in tables), default=0)
        columns = []
        for table in tables:
            for column in table.get("columns", []):
                rows = list(column.get("rows", []))
                rows.extend(self._blank_row() for _ in range(row_count - len(rows)))
                columns.append({**column, "rows": rows})
        return {"columns": columns, "merges": []}

    def evaluate(self, inputs):
        # inputs[0] is a LIST here, not a single Table - the Table
        # input is multi-input (see init()), and execution.py:eval_node
        # resolves a multi-input socket into one value per link, in
        # socket.links' own order (not table_items' own order - that
        # reordering happens here, by link_key, not upstream).
        tables_by_key = {}
        socket = self.inputs["Table"]
        for link, value in zip(socket.links, inputs[0] or []):
            # Same "disappears entirely" treatment as _sync_table_items'
            # own is_muted check above - a muted link contributes
            # nothing to the join, not even an empty Table occupying a
            # slot.
            if link.is_muted:
                continue
            # Same identity resolution as _sync_table_items' own key
            # (resolve_origin_node, not resolve_through_reroutes) - see
            # that method's own comment, and resolve_origin_node's own
            # docstring, for why: this key must match exactly what
            # table_items itself tracks, or the join order built from
            # table_items below would never line up with this dict's
            # own keys.
            origin_node, origin_socket = resolve_origin_node(link)
            if origin_node is None:
                continue
            try:
                output_index = list(origin_node.outputs).index(origin_socket)
            except ValueError:
                continue
            tables_by_key[_link_key(origin_node, output_index)] = value or {"columns": [], "merges": []}

        # table_items' own order (the user's own custom ordering, see
        # this class's module-level docstring) - a link_key with no
        # entry yet (this evaluate() ran before the polling timer's own
        # next _sync_table_items pass, e.g. right after a new link is
        # made) falls back to whatever order socket.links itself has,
        # appended after every already-ordered Table.
        ordered_keys = [item.link_key for item in self.table_items if item.link_key in tables_by_key]
        for key in tables_by_key:
            if key not in ordered_keys:
                ordered_keys.append(key)
        tables = [tables_by_key[key] for key in ordered_keys]

        if not tables:
            return [{"columns": [], "merges": []}]
        return [self._join_horizontal(tables)]
