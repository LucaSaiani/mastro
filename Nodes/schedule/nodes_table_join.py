from bpy.types import Node
from bpy.props import CollectionProperty, IntProperty, StringProperty

from .tree import MaStroScheduleTreeNode, resolve_origin_node, resolve_named_origin
from .execution import update_node, get_node_table
from .properties import MaStro_schedule_join_table_item


def _update_table_name(self, context):
    # Same Node.label rename, and same explicit
    # _pending_execute_trees flag, as Join Sheets' own
    # _update_sheet_name (nodes_sheet_place.py) - see that function's
    # own docstring for why the flag is needed (update_node() alone
    # never makes a downstream node's own _sync_table_items re-run).
    self.label = self.table_or_sheet_name
    update_node(self, context)
    from .tree import _pending_execute_trees
    _pending_execute_trees.add(self.id_data.name)


def _link_key(from_node, output_index, link_position):
    """A stable string identity for one connection into Join Tables' own
    multi-input socket - NOT the NodeLink object itself (not a stable
    Python identity across redraws/undo) and NOT just
    from_node.name::output_index (confirmed live as a real bug: the
    SAME Table plugged in twice - or once directly, once through a
    transparent operator like Edit Cell, both resolving to the same
    origin - collapsed into a single table_items entry, since both
    links resolved to an identical key). link_position (this link's
    own index within socket.links, see _sync_table_items/evaluate's
    own callers) disambiguates that case - stable as long as the user
    doesn't rewire the links into a different order, which is the same
    stability resolve_origin_node already only promises for everything
    else (see that function's own docstring)."""
    return f"{from_node.name}::{output_index}::{link_position}"


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


def _origin_label(origin_node, table):
    """origin_node's own table_or_sheet_name (this node's own optional name,
    see MaStroScheduleTableJoinNode.table_or_sheet_name) takes priority over
    _header_text's first-column-header fallback - same fix/reasoning
    as Export Excel's own _origin_label (nodes_excel_export.py): a
    Join Tables' combined result downstream showed up labeled after
    one of its own column headers (e.g. "D"), meaningless for a node
    whose whole job is combining several Tables, not being any one of
    them.

    If origin_node itself has no name, resolve_named_origin walks
    FURTHER upstream looking for one - confirmed live as a real gap
    otherwise: Join Tables -> Table to Sheet -> Join Sheets never saw
    Join Tables' own table_or_sheet_name at all, since Table to Sheet (origin_node
    here, a type-change boundary resolve_origin_node correctly stops
    at for IDENTITY) has no name of its own to check. See
    resolve_named_origin's own docstring in tree.py for why this is a
    separate walk from resolve_origin_node's, only for the displayed
    name, never for table_items' own link_key.

    _header_text's own fallback still reads table - origin_node's own
    table (the thing resolve_origin_node/_link_key are actually keyed
    by), not whatever node resolve_named_origin happened to walk
    past - the user's own explicit call to keep that part unchanged."""
    custom_name = getattr(origin_node, "table_or_sheet_name", "") or resolve_named_origin(origin_node)
    if custom_name:
        return custom_name
    return _header_text(table)


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
# combined - horizontally OR vertically - by Join Sheets
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
    # Optional - left blank, this node's own label downstream (any
    # future Table-reading equivalent of Export Excel's own
    # sheet_items, see nodes_excel_export.py's own _origin_label) falls
    # back to the first column's own header text, which can read as
    # meaningless for a node whose whole job is combining several
    # Tables into one (confirmed live as a real case: a Table joined
    # then converted to a Sheet showed up downstream labeled "D" - one
    # of its own column headers, not a name for the combined result
    # itself). Same shared property name as Join Sheets'/Table to
    # Sheet's own table_or_sheet_name (see resolve_named_origin's own
    # docstring in tree.py for why it's one shared name rather than a
    # separate one per node type).
    table_or_sheet_name: StringProperty(name="Table Name", update=_update_table_name)

    def init(self, context):
        # use_multi_input is a constructor-only argument (confirmed
        # against Blender's own RNA source, rna_Node_inputs_new in
        # rna_nodetree.cc) - it can't be set on an existing socket
        # afterward, only at creation time here.
        self.inputs.new('MaStroScheduleTableSocketType', "Table", use_multi_input=True)
        self.inputs.new('MaStroScheduleStringSocketType', "Table Name").prop_name = "table_or_sheet_name"
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
        for link_position, link in enumerate(socket.links):
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
            key = _link_key(origin_node, output_index, link_position)
            current_keys.append(key)
            table = get_node_table(self.id_data.name, origin_node.name)
            labels_by_key[key] = _origin_label(origin_node, table[output_index] if table else None)

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
        for link_position, (link, value) in enumerate(zip(socket.links, inputs[0] or [])):
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
            tables_by_key[_link_key(origin_node, output_index, link_position)] = value or {"columns": [], "merges": []}

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
