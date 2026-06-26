import bpy

from .tree import resolve_through_reroutes

# Cache of the last evaluated tables, keyed by tree name then node name.
# Used by the Viewer node to read the table produced by its input node.
_schedule_cache = {}

# Nodes whose evaluate() raised on the last run, keyed by tree name then
# node name, holding the exception message - read by
# tree.py:_poll_pending_trees to color the node red, the same way
# mark_mismatched_links colors a mismatched link (see that function's
# docstring for why this can only be written from the persistent-timer
# poller, never from update() or draw_buttons).
_evaluation_errors = {}


def tag_redraw_node_editors():
    """Force every visible Node Editor area to redraw, so a POST_VIEW
    overlay (e.g. the Viewer's table) reflects a freshly re-evaluated tree
    immediately, instead of waiting for the next incidental redraw (pan,
    zoom, ...)."""
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'NODE_EDITOR':
                area.tag_redraw()


def update_node(self, context):
    """Property update callback: re-run the tree this node belongs to."""
    tree = self.id_data
    if hasattr(tree, "execute"):
        tree.execute()
    tag_redraw_node_editors()


def get_node_table(tree_name, node_name):
    return _schedule_cache.get(tree_name, {}).get(node_name)


def linked_table(node, input_index=0):
    """Resolve the table feeding `node`'s input at `input_index` from the
    evaluation cache, but only if the link's socket types actually match -
    same check as evaluate_tree/eval_node's execution gate, duplicated here
    because UI callbacks (EnumProperty items, draw_buttons) read the cache
    directly and run on their own schedule (e.g. mid-drag while a link is
    being formed), not synchronized with when tree.update()/eval_node ran.
    Each caller must validate locally instead of trusting a stale/instable
    centralized pass - that's what the old prototype's per-node checkLink()
    did before reading/writing anything, and what broke when validation was
    only centralized in MaStroScheduleTree.update()."""
    socket = node.inputs[input_index]
    if not socket.is_linked or not socket.links:
        return None
    link = socket.links[0]
    # Same native-NodeReroute resolution as eval_node/mark_mismatched_links/
    # is_node_valid (tree.py:resolve_through_reroutes) - without this, a
    # Reroute (always created by Shift+RMB drag, with its own native socket
    # type) between a source and this node made this function see a
    # bl_idname mismatch and always return None, even though the real
    # upstream socket type matched fine. Confirmed live: Get Attribute
    # Names showed no attributes for any Field once a Reroute sat between
    # it and its Data source.
    from_node, from_socket = resolve_through_reroutes(link)
    if from_node is None or from_socket.bl_idname != socket.bl_idname:
        return None
    table = get_node_table(node.id_data.name, from_node.name)
    if not table:
        return None
    try:
        output_index = list(from_node.outputs).index(from_socket)
    except ValueError:
        return None
    return table[output_index]


def leaves(item):
    """Recursively flatten a (possibly nested) Group By item down to its
    leaf rows, descending through every level of "_members" """
    if isinstance(item, dict) and "_members" in item:
        result = []
        for member in item["_members"]:
            result.extend(leaves(member))
        return result
    return [item]


# Blender requires a persistent reference to the strings returned by a
# dynamic EnumProperty items callback, keyed by (node name, input index) to
# avoid crashes from garbage-collected enum items.
_available_columns_cache = {}


def get_available_columns_items(node, input_index=0):
    """Build the EnumProperty items list of column names available on the
    table feeding `node`'s input at `input_index`, for column-picker
    dropdowns."""
    names = []
    table = linked_table(node, input_index)
    if table:
        for item in table:
            for row in leaves(item):
                for key in row.keys():
                    if not key.startswith("_") and key not in names:
                        names.append(key)

    cache_key = (node.name, input_index)
    items = [(name, name, "") for name in names] or [("", "(no columns)", "")]
    _available_columns_cache[cache_key] = items
    return _available_columns_cache[cache_key]


def evaluate_tree(tree):
    """Topologically evaluate the tree, caching each visited node's output
    values (a list of tables, one per output socket).

    Only walks backwards from real sink nodes - those with no outputs of
    their own at all (currently just the Viewer) - instead of evaluating
    every node in the tree unconditionally. A node not yet wired up to any
    Viewer (e.g. while building a chain, or one left dangling) is not
    evaluated and its dropdowns stay empty until it's connected all the way
    to a Viewer - this is a deliberate trade-off, not a bug: the
    alternative (treating any node with an unlinked output as a "tip") was
    tried and reverted because it still evaluates fully orphaned nodes that
    were never connected to anything, which is the actual case this exists
    to avoid (see the depsgraph-warning-spam case this was built for)."""
    cache = {}

    def eval_node(node):
        if node.name in cache:
            return cache[node.name]

        def resolve_link_value(socket, link):
            # Dragging a link with Shift+RMB always creates a native
            # NodeReroute (confirmed live - no way to make Blender's
            # drag-to-insert operator create our own reroute node
            # instead), which has its own native socket type, not one
            # of ours - resolve_through_reroutes walks straight
            # through any such chain to the real producing node/
            # socket, the same way tree.py's mark_mismatched_links/
            # input_link_ok/is_node_valid do (see that function's
            # docstring in tree.py for why, mirroring Sverchok's
            # equivalent handling of the native NodeReroute).
            from_node, from_socket = resolve_through_reroutes(link)
            # A link between mismatched socket types is flagged (the
            # node gets colored, see tree.py) but deliberately left in
            # place so the user can see and fix it - it must not feed a
            # value through though, the same way the old prototype's
            # checkLink() gated execution and cleared the output instead
            # of running on a mismatched input. MaStroScheduleAnySocketType
            # (the Viewer's input) deliberately accepts any other MaStro
            # Schedule socket type by design (see sockets.py) - its
            # bl_idname never matches the from_socket's, so it must be
            # exempted here the same way tree.py's mark_mismatched_links/
            # input_link_ok already are, or the Viewer would always get
            # None instead of its actual input (confirmed live).
            if from_node is None or (
                    socket.bl_idname != 'MaStroScheduleAnySocketType'
                    and from_socket.bl_idname != socket.bl_idname):
                return None
            outputs = eval_node(from_node)
            try:
                index = list(from_node.outputs).index(from_socket)
                return outputs[index]
            except (ValueError, IndexError):
                return None

        input_values = []
        for socket in node.inputs:
            # A multi-input socket (Join Tables' own Table input, see
            # nodes_table_join.py) gets a LIST of values - one per link,
            # in socket.links' own order - instead of the single value
            # every other (non multi-input) socket gets. Every node
            # written before this one has no multi-input sockets at
            # all, so this branch never changes their behavior - only a
            # node that actually sets use_multi_input=True on an input
            # socket opts into receiving a list here.
            if getattr(socket, "is_multi_input", False):
                input_values.append([resolve_link_value(socket, link) for link in socket.links])
                continue
            value = None
            if socket.is_linked:
                value = resolve_link_value(socket, socket.links[0])
            input_values.append(value)

        tree_errors = _evaluation_errors.setdefault(tree.name, {})
        try:
            result = node.evaluate(input_values) if hasattr(node, "evaluate") else []
            tree_errors.pop(node.name, None)
        except Exception as exc:
            # short_message (set by nodes that want a compact overlay
            # text, e.g. nodes_math.py) is preferred over the exception's
            # own message - the full text is often too long to read
            # comfortably at node-editor zoom; falling back to str(exc)
            # covers any node that doesn't bother setting one.
            tree_errors[node.name] = getattr(exc, "short_message", None) or str(exc)
            result = []
        cache[node.name] = result
        return result

    for node in tree.nodes:
        if not node.outputs:
            eval_node(node)

    _schedule_cache[tree.name] = cache
    return cache
