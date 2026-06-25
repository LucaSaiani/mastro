import bpy
import bmesh

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


def extract_mesh_rows(objs):
    """Build the schedule table rows (one per floor/level) for the given
    MaStro mass objects, decoding the per-face BMesh attribute layers
    written by add_mass_attributes()."""
    rows = []

    use_names = {u.id: u.name for u in bpy.context.scene.mastro_use_name_list}
    typology_names = {t.id: t.name for t in bpy.context.scene.mastro_typology_name_list}
    block_names = {b.id: b.name for b in bpy.context.scene.mastro_block_name_list}
    building_names = {b.id: b.name for b in bpy.context.scene.mastro_building_name_list}

    for obj in objs:
        block_name = block_names.get(obj.mastro_props.mastro_block_attribute, "")
        building_name = building_names.get(obj.mastro_props.mastro_building_attribute, "")

        bm = bmesh.new()
        bm.from_mesh(obj.data)

        bm_typology = bm.faces.layers.int["mastro_typology_id"]
        bm_use_A = bm.faces.layers.int["mastro_list_use_id_A"]
        bm_use_B = bm.faces.layers.int["mastro_list_use_id_B"]
        bm_storeys = bm.faces.layers.int["mastro_number_of_storeys"]
        bm_storey_A = bm.faces.layers.int["mastro_list_storey_A"]
        bm_storey_B = bm.faces.layers.int["mastro_list_storey_B"]
        bm_height_A = bm.faces.layers.int["mastro_list_height_A"]
        bm_height_B = bm.faces.layers.int["mastro_list_height_B"]
        bm_height_C = bm.faces.layers.int["mastro_list_height_C"]
        bm_height_D = bm.faces.layers.int["mastro_list_height_D"]
        bm_height_E = bm.faces.layers.int["mastro_list_height_E"]
        bm_undercroft = bm.faces.layers.int["mastro_undercroft"]

        for f in bm.faces:
            storeys = f[bm_storeys]
            typology_name = typology_names.get(f[bm_typology], "")
            area_total = round(f.calc_area(), 2)

            # Parallel-digit-string encoding: each "_A"/"_B"/... layer holds
            # one digit position per use/storey-group across the whole
            # face, prefixed with "1" to avoid leading zeros being dropped.
            # Stripping that "1" and zipping the strings char-by-char turns
            # each position back into a "group" (e.g. one storey-group's
            # use+storeys+height), simpler in plain Python than the
            # log10/power-of-ten digit extraction used on the Geometry
            # Nodes side, where strings aren't practical to slice.
            storey_A_digits = str(f[bm_storey_A])[1:]
            storey_B_digits = str(f[bm_storey_B])[1:]
            use_A_digits = str(f[bm_use_A])[1:]
            use_B_digits = str(f[bm_use_B])[1:]
            height_A_digits = str(f[bm_height_A])[1:]
            height_B_digits = str(f[bm_height_B])[1:]
            height_C_digits = str(f[bm_height_C])[1:]
            height_D_digits = str(f[bm_height_D])[1:]
            height_E_digits = str(f[bm_height_E])[1:]

            storey_group = 0
            group_index = 0
            for level in range(storeys):
                storey_A = int(storey_A_digits[group_index])
                storey_B = int(storey_B_digits[group_index])

                use_A = int(use_A_digits[group_index])
                use_B = int(use_B_digits[group_index])
                use_name = use_names.get(use_A * 10 + use_B, "")

                height_A = int(height_A_digits[group_index])
                height_B = int(height_B_digits[group_index])
                height_C = int(height_C_digits[group_index])
                height_D = int(height_D_digits[group_index])
                height_E = int(height_E_digits[group_index])
                height = height_A * 10 + height_B + height_C * 0.1 + height_D * 0.01 + height_E * 0.001

                # mastro_undercroft stores a plain count of floors from the
                # bottom that are undercroft (e.g. 3 means levels 0,1,2 are
                # undercroft) - not a per-level digit like use/storey/height.
                undercroft = level < f[bm_undercroft]
                area = 0 if undercroft else area_total

                storey_group_new = storey_A * 10 + storey_B + storey_group
                if storey_group_new == level + 1:
                    storey_group = storey_group_new
                    group_index += 1

                rows.append({
                    "_Object": obj.name,
                    "Block": block_name,
                    "Building": building_name,
                    "Typology": typology_name,
                    "Use": use_name,
                    "Storey": storey_group_new,
                    "Height": height,
                    "Undercroft": undercroft,
                    "Area": area,
                    "_Level": level,
                    "_Face": f.index,
                })

        bm.free()

    return rows


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

        input_values = []
        for socket in node.inputs:
            value = None
            if socket.is_linked:
                link = socket.links[0]
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
                    input_values.append(None)
                    continue
                outputs = eval_node(from_node)
                try:
                    index = list(from_node.outputs).index(from_socket)
                    value = outputs[index]
                except (ValueError, IndexError):
                    value = None
            input_values.append(value)

        tree_errors = _evaluation_errors.setdefault(tree.name, {})
        if node.mute:
            # Muted: bypass evaluate() entirely and pass each input
            # straight through to an output, instead of running the
            # node's own logic on a "disabled" node - node.mute only
            # changes how Blender draws the node, it does nothing to
            # execution on its own (confirmed live: outputs kept
            # reflecting evaluate()'s result even while muted, before
            # this). Mirrors Sverchok's approach
            # (core/update_system.py:_remove_muted_nodes, node_tree.py:
            # Node.internal_links/sv_internal_links): which input maps to
            # which output defaults to positional pairing (Blender's own
            # Node.internal_links - first input to first output, etc.),
            # overridable per node type via a `mastro_internal_links`
            # property the same way Sverchok lets a node override
            # sv_internal_links when the default pairing doesn't fit
            # (e.g. Math: A should pass through, not B).
            tree_errors.pop(node.name, None)
            result = [None] * len(node.outputs)
            pairs = (node.mastro_internal_links if hasattr(node, "mastro_internal_links")
                     else [(link.from_socket, link.to_socket) for link in node.internal_links])
            for in_socket, out_socket in pairs:
                try:
                    in_index = list(node.inputs).index(in_socket)
                    out_index = list(node.outputs).index(out_socket)
                except ValueError:
                    continue
                result[out_index] = input_values[in_index]
            cache[node.name] = result
            return result

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
