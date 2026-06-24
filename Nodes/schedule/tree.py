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
    from a node's `draw_buttons` - same constraint, same fix shape."""
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
            try:
                tree.execute()
            except Exception as exc:
                print(f"MaStro Schedule: execution error: {exc}")
    return 0.1


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
    Blender NodeReroute nodes to the real (from_node, from_socket) that
    actually produces the value - or (None, None) if the chain dead-ends
    without ever reaching a non-reroute node (a reroute with nothing
    plugged into its own input).

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
    (see update()'s docstring below)."""
    from_socket = link.from_socket
    from_node = link.from_node
    while from_node.bl_idname == 'NodeReroute':
        reroute_input = from_node.inputs[0]
        if not reroute_input.is_linked or not reroute_input.links:
            return None, None
        inner_link = reroute_input.links[0]
        from_socket = inner_link.from_socket
        from_node = inner_link.from_node
    return from_node, from_socket


def upstream_attr(socket, attr_name, default=""):
    """Read `attr_name` off the real node feeding `socket`, resolving
    through any native NodeReroute chain first (see
    resolve_through_reroutes) - the common case behind every
    `column_label`/`name_value`-style lookup in this tree (Evaluate
    Attribute, Math, ...): "what's the upstream node, ignoring any
    Reroute in between, and what does it say". Returns `default` if the
    socket isn't linked, the chain dead-ends, or the resolved node
    doesn't have that attribute at all."""
    if not socket.is_linked or not socket.links:
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
    bl_label = "MaStro Schedule"
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
