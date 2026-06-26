import bpy
from bpy.types import NodeTree

# Names of trees whose update() was called since the last poll - see
# update() and _poll_pending_trees below for why this is a flag checked by
# a persistent timer, rather than execute() running directly from update().
_pending_execute_trees = set()


def _poll_pending_trees():
    """Persistent timer (registered once in register(), like
    Timers/monitor_view_rotation.py's viewport monitor - never re-registered
    per update() call): runs execute() for any tree MaStroScheduleTree.update()
    flagged since the last poll, on Blender's own schedule rather than
    synchronously inside update() itself. See update()'s docstring for why
    that distinction is required. Returns 0.1 (seconds until next poll),
    matching monitor_view_rotation's interval.

    Also runs mark_mismatched_links here, not from draw_buttons: Blender
    raises `AttributeError: Writing to ID classes in this context is not
    allowed` when a NodeLink/Node property (is_valid, use_custom_color,
    color, ...) is written from inside a UI draw call - confirmed live
    (the exact error this fixes). Sverchok's equivalent
    (`core/update_system.py`'s `e.socket.links[0].is_valid = False`) is
    likewise called from its task-runner timer (`core/tasks.py`), never
    from a node's `draw_buttons` - same constraint, same fix shape.

    Join Tables' own table_items sync (nodes_table_join.py) hit the
    exact same error - confirmed live, table_items.add() from inside
    draw_buttons raised "Writing to ID classes in this context is not
    allowed" the moment a Table was actually linked in (a passive
    redraw, e.g. the window's own idle-timer redraw, not a user action,
    is what reaches draw_buttons in the disallowed context) - moved
    here for the same reason mark_mismatched_links already is. Place in
    Sheet (nodes_sheet_place.py) reuses the exact same table_items
    machinery for its own multi-input Sheet socket, so its sync is
    polled here too; Export Excel (nodes_excel_export.py) has its own
    sheet_items/_sync_sheet_items, same shape, same reason. One side
    effect: both _sync_table_items()/_sync_sheet_items() read each
    linked Table/Sheet's own label text from the evaluation cache
    (get_node_table) BEFORE tree.execute() runs below, so the label
    shown in any of these node's own list is always one poll (0.1s)
    stale relative to whatever just changed - purely cosmetic (the
    join/place/export itself always reads the freshly computed value,
    only the list's own label lags), not worth reordering for.

    Export Excel never writes from here - it only ever exports
    manually, via its own button (see that node's own module comment
    for why an auto-export-from-here option was tried and removed)."""
    if _pending_execute_trees:
        pending = list(_pending_execute_trees)
        _pending_execute_trees.clear()
        for tree_name in pending:
            tree = bpy.data.node_groups.get(tree_name)
            if tree is None:
                continue
            for node in tree.nodes:
                if isinstance(node, MaStroScheduleTreeNode):
                    mark_mismatched_links(node)
                if node.bl_idname in ('MaStroScheduleTableJoin', 'MaStroScheduleSheetPlace'):
                    node._sync_table_items()
                if node.bl_idname == 'MaStroScheduleExcelExport':
                    node._sync_sheet_items()
            try:
                tree.execute()
            except Exception as exc:
                print(f"MaStro Schedule: execution error: {exc}")
            _mark_evaluation_errors(tree)
    return 0.1


def _mark_evaluation_errors(tree):
    """Color red any node whose evaluate() raised during the execute()
    call just above (tracked in execution.py:_evaluation_errors, keyed by
    tree/node name), and clear that color off every other node - the
    same way mark_mismatched_links colors a single bad link instead of
    leaving an exception to surface only as a console print or, worse,
    only on a manual Refresh click (see MASTRO_OT_Schedule_Force_Refresh,
    which has no try/except of its own and would otherwise show a
    blocking Blender error popup there but nothing during auto-refresh -
    this makes the two paths behave the same way). Same write-from-the-
    poller constraint as mark_mismatched_links - see that function's
    docstring."""
    from .execution import _evaluation_errors
    errors = _evaluation_errors.get(tree.name, {})
    for node in tree.nodes:
        if not isinstance(node, MaStroScheduleTreeNode):
            continue
        has_error = node.name in errors
        if node.use_custom_color != has_error:
            node.use_custom_color = has_error
        if has_error:
            node.color = (0.6, 0.1, 0.1)


def start_polling():
    if not bpy.app.timers.is_registered(_poll_pending_trees):
        # persistent=True: without it Blender silently unregisters this
        # timer on every new file / file load (see monitor_view_rotation.py
        # for the same gotcha), which would make the tree stop
        # auto-refreshing in any file opened after the addon's register().
        bpy.app.timers.register(_poll_pending_trees, persistent=True)


def stop_polling():
    if bpy.app.timers.is_registered(_poll_pending_trees):
        bpy.app.timers.unregister(_poll_pending_trees)


def resolve_through_reroutes(link):
    """Given a NodeLink, follow it back through any chain of native
    Blender NodeReroute nodes AND muted nodes to the real (from_node,
    from_socket) that actually produces the value - or (None, None) if
    the chain dead-ends without ever reaching a real one (a reroute or
    muted node with nothing plugged into the input it bypasses to).

    Dragging a link in this tree's editor with Shift+RMB always creates
    a native `NodeReroute` (confirmed live - Blender's drag-to-insert
    operator hard-codes that type, there's no way to make it create our
    own MaStroScheduleRerouteNode instead), which has its own native
    socket type (not one of ours), so naively reading
    `link.from_socket.bl_idname` on a link coming out of one would always
    look like a mismatch. Mirrors Sverchok's approach (it doesn't have
    its own reroute type either - it accepts the native NodeReroute as-is,
    `core/update_system.py:_remove_reroutes()`, walking straight through
    any reroute chain rather than evaluating/validating them as real
    nodes) rather than trying to recolor/replace the native reroute,
    which would mean writing node structure from inside NodeTree.update()
    - the same place that, mishandled, caused this tree's RecursionError
    (see update()'s docstring below).

    A muted node is walked through the same way, always via its FIRST
    input regardless of socket type (the user's own call: "il mute, a
    logica, vuol dire che connette il primo input con il primo output,
    ignorando quello che sta in mezzo... va sempre sul primo input") -
    this is the ONLY mute-bypass mechanism in this tree (an earlier
    version also had eval_node apply a `mastro_internal_links`
    same-bl_idname pairing per node, but that's now removed: every
    consumer of resolve_through_reroutes - eval_node, mark_mismatched_links,
    is_node_valid, upstream_attr - already resolves straight through a
    muted node to the real upstream socket, so a node with no outputs of
    its own being muted is the only case this doesn't cover, and that
    case has no real use - a muted Viewer just draws nothing, which is
    already correct). Resolving via first-input deliberately allows
    surfacing a TYPE CHANGE across the muted node (e.g. Column to Table:
    muting it lets something downstream see the original Column again,
    not a default-shaped empty Table) - the existing bl_idname mismatch
    check in eval_node/mark_mismatched_links then correctly flags that
    as invalid if whatever's downstream actually required a Table."""
    from_socket = link.from_socket
    from_node = link.from_node
    while True:
        if from_node.bl_idname == 'NodeReroute':
            next_input = from_node.inputs[0]
        elif getattr(from_node, "mute", False) and from_node.inputs:
            next_input = from_node.inputs[0]
        else:
            break
        if not next_input.is_linked or not next_input.links:
            return None, None
        inner_link = next_input.links[0]
        from_socket = inner_link.from_socket
        from_node = inner_link.from_node
    return from_node, from_socket


def resolve_origin_node(link):
    """Given a NodeLink feeding a Table/Sheet multi-input socket (Join
    Tables/Join Sheets, see nodes_table_join.py/nodes_sheet_place.py),
    walk back through every "transparent" single-input Table/Sheet
    operator (Move Sheet, Edit Cell, Row Colour, Cell Align, ...) to the
    real origin node that actually CREATED this Table/Sheet (a
    primitive like Table Primitive/Sheet Primitive/Column to Table/
    Table to Sheet, or another multi-input node like Join Tables/Place
    in Sheet itself) - or (None, None) if the chain dead-ends.

    Exists so the join/place order tracked by table_items'
    own link_key (_link_key in nodes_table_join.py/nodes_sheet_place.py)
    stays stable across the user editing an operator chain feeding into
    the join (e.g. muting Move Sheet, or inserting/removing an Edit
    Cell) - the user's own explicit framing: "quello per cui facciamo
    join sono le tabelle e le sheet, eventualmente modificate da
    operatori, ma sempre quelle sheet e tabelle sono... il nodo join per
    stabilire l'id va fino alla prima table/sheet che incontra".
    Confirmed live as a real bug before this existed: muting Move Sheet
    (a node with one Sheet input and one Sheet output) made
    resolve_through_reroutes correctly resolve straight past it to the
    Sheet Primitive behind it - correct for VALUE resolution, but it
    silently changed the (from_node, output_index) pair _link_key keys
    table_items by, making the entry look like a brand new connection
    each time, losing its position in the user's own custom order.

    A node only counts as "transparent" here if it has EXACTLY one
    Table/Sheet input socket, of the SAME socket type as its (single)
    Table/Sheet output - any node that combines several Tables/Sheets
    (multi-input, e.g. Join Tables/Join Sheets) or changes the type
    altogether (e.g. Table to Sheet: Table in, Sheet out) is treated as
    an origin in its own right, never walked through. mute is
    irrelevant here on purpose - unlike resolve_through_reroutes (which
    exists specifically to resolve VALUES around a muted node), this
    walks the same chain whether muted or not, since the user's own
    framing is about identity, not value."""
    from_node = link.from_node
    from_socket = link.from_socket
    while True:
        # Confirmed live as a real bug otherwise: a multi-input socket
        # (Join Tables/Join Sheets' own Table/Sheet input) still
        # counts as exactly ONE declared input socket here, even with
        # several real links feeding it - without explicitly excluding
        # is_multi_input sockets, Join Sheets looked "transparent"
        # by this same shape test, and got walked straight through to
        # whichever ONE of its own several inputs happened to be
        # link.from_socket's own upstream, silently dropping every
        # other Sheet it was supposed to combine (Export Excel ended
        # up exporting only one of the Sheets Join Sheets actually
        # merged, ignoring its own join order entirely).
        table_sheet_inputs = [
            s for s in from_node.inputs
            if s.bl_idname in ('MaStroScheduleTableSocketType', 'MaStroScheduleSheetSocketType')
            and not s.is_multi_input
        ]
        if len(table_sheet_inputs) != 1 or table_sheet_inputs[0].bl_idname != from_socket.bl_idname:
            break
        next_input = table_sheet_inputs[0]
        if not next_input.is_linked or not next_input.links:
            return None, None
        inner_link = next_input.links[0]
        from_socket = inner_link.from_socket
        from_node = inner_link.from_node
    return from_node, from_socket


def resolve_named_origin(origin_node):
    """Given the (origin_node, ...) resolve_origin_node already
    returned, walks FURTHER upstream - through Table to Sheet's own
    type change included, unlike resolve_origin_node itself - looking
    for the first node carrying a non-empty table_or_sheet_name (Join
    Tables/Join Sheets' own shared optional name property - ONE
    attribute name for both, the user's own explicit simplification,
    so this walk never needs to guess which of "table_name"/
    "sheet_name" to check at each node it's currently looking at - it
    could be either kind of node depending how many Table<->Sheet type
    changes happen to sit in between). Returns that name, or "" if the
    walk runs out (hits another multi-input node with no name of its
    own, or a node with no further single Table/Sheet input to follow)
    without ever finding one.

    Exists because resolve_origin_node's own type-change boundary
    (Table to Sheet: Table in, Sheet out) is the right place to stop
    for IDENTITY (a Sheet's own identity is not the Table that made
    it) but the wrong place to stop for a NAME someone set further
    upstream - confirmed live as a real gap: Join Tables -> Table to
    Sheet -> Join Sheets never saw Join Tables' own
    table_or_sheet_name at all, since Table to Sheet (which has no
    name of its own) was as far as the lookup went, leaving the user
    staring at a meaningless fallback label ("D", one of the joined
    Table's own column headers) with no way to tell what it actually
    referred to. The user's own explicit call: keep walking past a
    type change too, but ONLY for the name, not for table_items' own
    link_key (which must stay exactly as stable as resolve_origin_node
    already makes it - this function is purely an extra read on top,
    never changes what counts as this entry's own identity)."""
    node = origin_node
    while node is not None:
        name = getattr(node, "table_or_sheet_name", "")
        if name:
            return name
        table_sheet_inputs = [
            s for s in node.inputs
            if s.bl_idname in ('MaStroScheduleTableSocketType', 'MaStroScheduleSheetSocketType')
            and not s.is_multi_input
        ]
        if len(table_sheet_inputs) != 1:
            return ""
        next_input = table_sheet_inputs[0]
        if not next_input.is_linked or not next_input.links:
            return ""
        node, _socket = resolve_through_reroutes(next_input.links[0])
    return ""


def upstream_attr(socket, attr_name, default=""):
    """Read `attr_name` off the real node feeding `socket`, resolving
    through any native NodeReroute chain first (see
    resolve_through_reroutes) - the common case behind every
    `column_label`/`name_value`-style lookup in this tree (Evaluate
    Attribute, Math, ...): "what's the upstream node, ignoring any
    Reroute in between, and what does it say". Returns `default` if the
    socket isn't linked, the link is muted (a muted link must behave
    like the socket isn't linked at all - see execution.py:
    is_socket_active's own docstring for the fuller story), the chain
    dead-ends, or the resolved node doesn't have that attribute at
    all."""
    if not socket.is_linked or not socket.links or socket.links[0].is_muted:
        return default
    from_node, _from_socket = resolve_through_reroutes(socket.links[0])
    if from_node is None:
        return default
    return getattr(from_node, attr_name, default)


def input_link_ok(socket):
    """A linked input is "ok" if its link's socket type matches (no
    mismatch) - an unlinked socket is judged separately by the caller,
    since whether that's acceptable depends on whether the input is
    optional. MaStroScheduleAnySocketType (the Viewer's input) is always
    "ok" regardless of what's linked - see mark_mismatched_links."""
    if not socket.is_linked or not socket.links:
        return True
    if socket.bl_idname == 'MaStroScheduleAnySocketType':
        return True
    _from_node, from_socket = resolve_through_reroutes(socket.links[0])
    if from_socket is None:
        return False
    return from_socket.bl_idname == socket.bl_idname


def mark_mismatched_links(node):
    """Set NodeLink.is_valid (a native Blender property - Blender itself
    draws an invalid link in red) on each of this node's input links,
    reflecting whether that specific link's socket types actually match.
    More precise than coloring the whole node: the user sees exactly
    which link is wrong, not just that something in the node is.

    Modeled on Sverchok (github.com/nortikin/sverchok,
    core/update_system.py: `e.socket.links[0].is_valid = False`), which
    sets this from its update-system task runner (core/tasks.py, a
    persistent timer) - i.e. during/after actual execution, not from
    inside NodeTree.update() and not from a node's draw_buttons either.
    Only ever called from _poll_pending_trees here - first tried from
    draw_buttons (a normal redraw, not update()'s Blender-internal
    topology-change event), but that raised a different, separate
    error: `AttributeError: Writing to ID classes in this context is not
    allowed` - Blender forbids writing any ID-owned property (a NodeLink
    is owned by its NodeTree) from inside a UI draw call, confirmed
    live. The persistent-timer poller is allowed to write it; update()
    and draw_buttons both are not, for two unrelated reasons."""
    for socket in node.inputs:
        if not socket.is_linked or not socket.links:
            continue
        # MaStroScheduleAnySocketType (the Viewer's input) deliberately
        # accepts any other MaStro Schedule socket type - it carries no
        # structural guarantee by design, so a from_socket/to_socket
        # bl_idname mismatch here is expected, not an error.
        if socket.bl_idname == 'MaStroScheduleAnySocketType':
            continue
        link = socket.links[0]
        _from_node, from_socket = resolve_through_reroutes(link)
        ok = from_socket is not None and from_socket.bl_idname == socket.bl_idname
        if link.is_valid != ok:
            link.is_valid = ok


def is_node_valid(node):
    """A node is valid if walking backwards from each of its *required*
    inputs (every input not listed in `optional_inputs`) reaches an actual
    source node (one with no inputs of its own - today, Input Mesh
    All/Selected) through a chain of correctly-typed links and locally
    valid nodes the whole way. An optional input left unlinked doesn't
    block this; if it IS linked, it's held to the same standard as a
    required one.

    This deliberately does NOT require reaching a sink/Viewer downstream -
    matching how Geometry Nodes lets a Named Attribute node populate its
    field list as soon as it's wired to *something* carrying geometry,
    without needing the whole chain to reach the Group Output first.

    Computed fresh every call, from current topology only - NEVER cached
    in a node property (see MaStroScheduleTree.update()'s docstring for
    why writing node properties from update() is unsafe)."""
    valid = {}

    def visit(n):
        if n.name in valid:
            return valid[n.name]
        valid[n.name] = False  # tentative, guards against link cycles
        if not n.inputs:
            result = True
        else:
            optional = getattr(n, "optional_inputs", frozenset())
            result = True
            for socket in n.inputs:
                if not input_link_ok(socket):
                    result = False
                    break
                if not socket.is_linked:
                    if socket.name not in optional:
                        result = False
                        break
                    continue
                from_node, _from_socket = resolve_through_reroutes(socket.links[0])
                if from_node is None or not visit(from_node):
                    result = False
                    break
        valid[n.name] = result
        return result

    return visit(node)


class MaStroScheduleTree(NodeTree):
    """MaStro Schedule node tree: build quantity-takeoff tables from the MaStro model"""
    bl_idname = 'MaStroScheduleTreeType'
    bl_label = "MaStro Schedule Editor"
    # NodeTree.bl_icon only accepts Blender's native icon enum, not a
    # custom icon loaded via bpy.utils.previews (confirmed against
    # Blender's dev tracker, T85213) - a custom icon (Icons/schedule.svg,
    # a copy of mass.svg meant to be edited separately) is usable
    # elsewhere in this addon's UI (icon_value=icons.icon_id("schedule"),
    # e.g. in a menu or panel) but not here.
    bl_icon = 'NODETREE'

    def execute(self):
        from .execution import evaluate_tree
        evaluate_tree(self)

    def update(self):
        # update() must never write any node property and must never call
        # execute() synchronously: it runs while Blender is still mid-way
        # through a topology change (e.g. creating a node/link, before
        # things have settled), and execute() -> evaluate_tree calls
        # evaluate() on every reachable node, which can read node
        # properties or trigger dynamic-EnumProperty items callbacks -
        # doing that here re-enters Blender's own update machinery before
        # this call returns, recursing into a real RecursionError
        # (confirmed by isolating this in headless Blender, and matching a
        # known Blender community report - forum.blender.org, Jacques
        # Lucke/Josephbburg, 2020). A *new* one-shot timer registered here
        # (tried first) didn't fix it either - registering a timer from
        # inside an event Blender is still processing can still run before
        # that event settles. The fix that held up: follow the same
        # pattern as Timers/monitor_view_rotation.py's viewport monitor -
        # one *persistent* timer registered once in register() (see
        # start_polling below), never re-registered per update() call.
        # update() only flags this tree as needing a refresh; the timer
        # picks it up on its own next poll, fully outside whatever
        # Blender-internal event called update().
        _pending_execute_trees.add(self.name)


class MaStroScheduleTreeNode:
    """Mixin shared by all nodes of the MaStro Schedule tree"""

    # Names of input sockets a subclass allows to be left unlinked without
    # invalidating the node (it has its own fallback for that case, e.g.
    # Header's "Name", which falls back to a typed-in string). Absent here
    # means "all inputs are required" - override on the subclass to opt in.
    optional_inputs = frozenset()

    @classmethod
    def poll(cls, ntree):
        return ntree.bl_idname == 'MaStroScheduleTreeType'

    @property
    def is_valid(self):
        """Whether this node's required inputs all trace back, through
        correctly-typed links and locally valid nodes, to a real source
        node (no inputs of its own - Input Mesh All/Selected). Computed
        fresh on every access - see is_node_valid above for why this is
        never a stored property."""
        return is_node_valid(self)

    def evaluate(self, inputs):
        """Return a list of output values, one per output socket.

        `inputs` is a list of values, one per input socket (None if unlinked).
        Each value is a list of row dicts (a table).
        """
        return []
