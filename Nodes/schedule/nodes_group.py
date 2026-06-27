import bpy
from bpy.types import NodeTree, NodeCustomGroup, Operator

from .sockets import socket_type_names


class MaStroScheduleGroupTree(NodeTree):
    """A MaStro Schedule sub-tree used as a Group node's own body - kept
    as its own dedicated tree class, separate from MaStroScheduleTree
    (the main editor's own tree type), the same way Sverchok keeps a
    dedicated SvGroupTree apart from SverchCustomTreeType
    (core/node_group.py) - mirrors that split rather than reusing the
    main tree type directly, so a group's own body never shows up as a
    selectable option in the node editor's own tree-type dropdown
    (poll() below returns False for exactly that reason: "only for
    inner usage", Sverchok's own words for the identical restriction).

    valid_socket_type mirrors MaStroScheduleTree's own (see tree.py)."""
    bl_idname = 'MaStroScheduleGroupTreeType'
    bl_label = 'MaStro Schedule Group'
    bl_icon = 'NODETREE'

    @classmethod
    def poll(cls, context):
        return False

    @classmethod
    def valid_socket_type(cls, socket_type):
        return socket_type in socket_type_names()

    def update(self):
        # Confirmed live as a real gap otherwise: editing this tree's
        # own interface (e.g. dragging a new link into Group Input/
        # Output, which silently adds a matching socket) never showed
        # up on the Group node back in the main tree - "Group Selected"
        # only builds that node's own inputs/outputs ONCE, at creation
        # time (see MASTRO_OT_Schedule_Add_Group_From_Selected), with
        # nothing keeping them in sync afterward. Sverchok's own
        # SvGroupTree.update() (core/node_group.py) hits the identical
        # gap and re-syncs from there too - mirrored here, just without
        # that version's own context.space_data.path bookkeeping (not
        # needed: every Group node anywhere referencing this tree gets
        # re-synced, not only the one on the currently open path).
        #
        # "building" (a custom ID property, same guard pattern as
        # Sverchok's own "init_tree" check) skips this entirely while
        # "Group Selected" is still constructing a brand new group -
        # every interface.new_socket() call that operator makes while
        # building the new group's own boundary sockets ALSO triggers
        # this update() (Blender fires it on any interface change, not
        # just ones made interactively), and _sync_group_node_sockets
        # reading the interface mid-construction (before every socket
        # the operator means to add is actually there yet) would settle
        # on a temporary, incomplete state - wasted work at best. The
        # operator removes "building" only once it has finished linking
        # everything, so this update() runs (at most) once more right
        # after, syncing the final, settled interface - never in the
        # middle of construction. (An earlier version of
        # _sync_group_node_sockets unconditionally cleared and rebuilt
        # every socket on every call, which made this guard load-bearing
        # for a much worse reason too - dropping every existing link,
        # not just stale state - see that function's own docstring for
        # why it no longer works that way.)
        if self.get("building"):
            return
        # Also searches MaStroScheduleGroupTreeType, not just the main
        # tree - a Group node referencing this tree can itself live
        # inside ANOTHER Group's own body (nested groups), not only in
        # the outermost MaStroScheduleTree.
        for tree in bpy.data.node_groups:
            if tree.bl_idname not in ('MaStroScheduleTreeType', 'MaStroScheduleGroupTreeType'):
                continue
            for node in tree.nodes:
                if node.bl_idname == MaStroScheduleGroupNode.bl_idname and node.node_tree == self:
                    _sync_group_node_sockets(node)


# A real Blender NodeCustomGroup (the native base class for group
# nodes, confirmed against Sverchok's own SvGroupTreeNode in
# core/node_group.py, which uses the same base) rather than the usual
# MaStroScheduleTreeNode/Node mixin every other node in this package
# uses - NodeCustomGroup is what gives this node its own node_tree
# property. Tab/double-click navigation into the group's own body is
# NOT native for a custom NodeCustomGroup (Blender's own node.group_edit
# is hardcoded to only the 4 standard tree types, same restriction as
# Ctrl+G, see tree.py's own valid_socket_type comment) - covered
# instead by our own Tab keymap (mastro_schedule.enter_exit_group, see
# Keymaps/keymap.py), so no on-node "Edit" button is needed here.
class MaStroScheduleGroupNode(NodeCustomGroup):
    """Run a group of nodes as one reusable unit"""
    bl_idname = 'MaStroScheduleGroupNodeType'
    bl_label = 'Group'

    @classmethod
    def poll(cls, context):
        return True


def _selected_groupable_nodes(tree):
    """Every selected node, excluding Group Input/Output themselves
    (re-grouping a boundary node makes no sense) - same exclusion as
    Sverchok's own filter_selected_nodes (core/node_group.py)."""
    return [n for n in tree.nodes if n.select and n.bl_idname not in {'NodeGroupInput', 'NodeGroupOutput'}]


def _would_create_cycle(tree, selected_names):
    """True if grouping the current selection would require a link
    that skips over an unselected node and comes back into the
    selection further downstream - same check Sverchok's own
    can_be_grouped (core/node_group.py) makes, reimplemented here
    without that function's own Tree() helper class (no equivalent in
    this package): a plain BFS from every unselected node directly
    downstream of a selected one, looking for a path back into the
    selection. If such a path exists, the group's own single boundary
    (one Group Input crossing, one Group Output crossing) can't
    represent the connection - the unselected node would need to
    appear on BOTH sides of the group at once."""
    selected = set(selected_names)

    def downstream_unselected_starts():
        starts = set()
        for node in tree.nodes:
            if node.name not in selected:
                continue
            for socket in node.outputs:
                for link in socket.links:
                    if link.to_node.name not in selected:
                        starts.add(link.to_node.name)
        return starts

    for start_name in downstream_unselected_starts():
        seen = {start_name}
        queue = [start_name]
        while queue:
            current_name = queue.pop()
            if current_name in selected:
                return True
            current_node = tree.nodes.get(current_name)
            if current_node is None:
                continue
            for socket in current_node.outputs:
                for link in socket.links:
                    next_name = link.to_node.name
                    if next_name not in seen:
                        seen.add(next_name)
                        queue.append(next_name)
    return False


def _new_tree_socket(tree, bl_idname, name, in_out):
    """tree.interface.new_socket - the Blender 4.0+ Node Group
    interface API (confirmed against Blender's own startup scripts,
    bl_operators/node.py's own interface.new_socket calls) - no legacy
    tree.inputs/tree.outputs branch needed, unlike Sverchok's own
    new_tree_socket (which still supports pre-4.0 Blender)."""
    return tree.interface.new_socket(name, in_out=in_out, socket_type=bl_idname)


def _sync_group_node_sockets(group_node):
    """Rebuild group_node's own inputs/outputs to match its node_tree's
    own interface exactly, one socket per interface item, in the
    interface's own order - called once right after "Group Selected"
    creates a brand new group (see that operator's own comment for why
    this step is needed at all: node_tree alone never gives a
    NodeCustomGroup its own sockets), and again from
    MaStroScheduleGroupTree.update() any time the interface itself
    changes afterward (e.g. a new link dragged into Group Input/Output
    inside the group's own body, silently adding a matching interface
    socket) - confirmed live as a real gap otherwise: a socket added
    that way never showed up on the Group node back in the main tree.

    A real diff against interface_socket.identifier (a stable id
    Blender assigns to each interface socket, confirmed against
    Blender's own RNA source for tree.interface.new_socket/
    NodeTreeInterfaceSocket) - NOT an unconditional rebuild. Confirmed
    live as a real, serious bug with an earlier, simpler version of
    this function that always did group_node.inputs.clear()/
    outputs.clear() then rebuilt everything from scratch: every single
    call (and update() fires far more often than the interface actually
    changes - a nested group's own construction alone triggers well
    over a dozen calls, see MaStroScheduleGroupTree.update()'s own
    "building" guard) dropped EVERY existing link on the Group node,
    not just on whatever socket had actually changed - adding even one
    new socket to an otherwise-unchanged interface disconnected the
    entire group from the rest of the graph, confirmed live exactly
    this way. This version instead: removes only the sockets whose own
    identifier no longer exists in the interface (their own links go
    with them, unavoidably - nothing to preserve, the socket itself is
    gone); adds only brand new ones (matching by identifier) at the
    correct position via socket.move(); and otherwise touches nothing,
    so a socket whose identifier is still present - and the link sitting
    on it - is never touched."""
    node_tree = group_node.node_tree
    for in_out, node_sockets in (('INPUT', group_node.inputs), ('OUTPUT', group_node.outputs)):
        expected = [
            s for s in node_tree.interface.items_tree
            if s.item_type == 'SOCKET' and s.in_out == in_out
        ]
        expected_ids = {s.identifier for s in expected}
        # Remove first - same "drop what no longer belongs, in reverse
        # so removing by index never shifts what's still to be
        # checked" pattern used elsewhere in this package (e.g.
        # nodes_table_join.py's own _sync_table_items).
        for socket in list(node_sockets):
            if socket.identifier not in expected_ids:
                node_sockets.remove(socket)
        existing_ids = {s.identifier for s in node_sockets}
        for index, interface_socket in enumerate(expected):
            if interface_socket.identifier not in existing_ids:
                node_sockets.new(
                    interface_socket.bl_socket_idname, interface_socket.name,
                    identifier=interface_socket.identifier,
                )
                node_sockets.move(len(node_sockets) - 1, index)


class MASTRO_OT_Schedule_Enter_Exit_Group(Operator):
    """Tab's own target inside a MaStro Schedule editor: enters the
    active node's own Group body if it has one, otherwise steps back
    out one level if currently inside a Group - mirrors Sverchok's own
    EnterExitGroupNodes (ui/nodeview_keymaps.py), bound to Tab the same
    way there (no bl_label/description needed beyond what the keymap
    entry itself implies - this is never meant to be found in a menu,
    only pressed)."""
    bl_idname = "mastro_schedule.enter_exit_group"
    bl_label = "Enter/Exit Group"

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space is not None and getattr(space, "tree_type", None) in (
            'MaStroScheduleTreeType', 'MaStroScheduleGroupTreeType',
        )

    def execute(self, context):
        node = context.active_node
        if node is not None and node.bl_idname == MaStroScheduleGroupNode.bl_idname and node.node_tree is not None:
            context.space_data.path.append(node.node_tree, node=node)
        elif len(context.space_data.path) > 1:
            context.space_data.path.pop()
        return {'FINISHED'}


class MASTRO_OT_Schedule_Add_Group_From_Selected(Operator):
    """Move the selected nodes into a new Group, reconnecting every
    link that crossed the selection's own boundary - mirrors
    Sverchok's own AddGroupTreeFromSelected (core/node_group.py), see
    that operator's own docstring for the full step list this follows.
    Built for the Schedule's future For Each node (see issue #15): a
    loop's own body needs to be a Group, and a group has to come from
    somewhere - this is that "somewhere"."""
    bl_idname = "mastro_schedule.add_group_from_selected"
    bl_label = "Group Selected"
    bl_description = "Move the selected nodes into a new Group"

    @classmethod
    def poll(cls, context):
        space = context.space_data
        if not space or not getattr(space, "path", None):
            return False
        tree = space.path[-1].node_tree
        # Also allowed one level deep inside another Group's own body
        # (MaStroScheduleGroupTreeType) - nesting groups works exactly
        # the same way either way (execute() below only ever reads
        # space.path[-1].node_tree, whichever kind it actually is), no
        # reason for this poll() to single out the main tree only.
        if tree is None or tree.bl_idname not in ('MaStroScheduleTreeType', 'MaStroScheduleGroupTreeType'):
            return False
        return bool(_selected_groupable_nodes(tree))

    def execute(self, context):
        base_tree = context.space_data.path[-1].node_tree
        selected_nodes = _selected_groupable_nodes(base_tree)
        selected_names = {n.name for n in selected_nodes}

        if _would_create_cycle(base_tree, selected_names):
            self.report({'WARNING'}, "Current selection can't be grouped (would create a cycle)")
            return {'CANCELLED'}

        # Deselect any Group Input/Output that happened to be selected
        # too - same as Sverchok's own equivalent line: they're never
        # copied into the new sub-tree (filtered out by
        # _selected_groupable_nodes above already), but clipboard_copy
        # below copies whatever is selected, so they must not stay
        # selected either.
        for node in base_tree.nodes:
            if node.select and node.bl_idname in {'NodeGroupInput', 'NodeGroupOutput'}:
                node.select = False

        sub_tree = bpy.data.node_groups.new('MaStro Schedule Group', MaStroScheduleGroupTree.bl_idname)
        sub_tree.use_fake_user = True
        # See MaStroScheduleGroupTree.update()'s own comment for why
        # this guard exists at all - removed in a try/finally below so
        # it's never left behind even if something here raises partway
        # through. base_tree gets the same guard - confirmed live as a
        # real bug otherwise when grouping INSIDE another Group's own
        # body: every node/link change made to base_tree while building
        # the new nested group (e.g. base_tree.nodes.new() for the new
        # Group node itself) also fires base_tree's own update(), which
        # - if base_tree is itself a MaStroScheduleGroupTree, not the
        # main tree - re-synced ITS OWN Group node back in whatever
        # tree contains IT, wiping out that outer Group's own links to
        # the rest of the graph in the process. Harmless to always set
        # this even when base_tree is the main MaStroScheduleTree
        # (which has no such update()-driven guard check at all).
        base_tree["building"] = True
        sub_tree["building"] = True

        try:
            # node.clipboard_copy/paste is Blender's own native node
            # clipboard (confirmed against Sverchok's own identical use
            # in AddGroupTreeFromSelected) - copies every currently
            # selected node, with all of its own property values, into
            # the paste buffer; pasting into a different tree (by
            # appending it to the editor's own breadcrumb path first)
            # is the only way to duplicate a node's full state without
            # manually re-creating every property by hand.
            bpy.ops.node.clipboard_copy()
            context.space_data.path.append(sub_tree)
            bpy.ops.node.clipboard_paste()
            context.space_data.path.pop()

            sub_tree_nodes = _selected_groupable_nodes(sub_tree)
            if sub_tree_nodes:
                from mathutils import Vector
                center = sum(
                    (Vector(n.location) for n in sub_tree_nodes), Vector((0.0, 0.0))
                ) / len(sub_tree_nodes)
                for node in sub_tree_nodes:
                    node.location = Vector(node.location) - center

            # Every link crossing the selection's own boundary, keyed by
            # the (node, socket) pair on the OUTSIDE of the selection -
            # one interface socket per distinct outside endpoint, the
            # same grouping Sverchok's own from_sockets/to_sockets dicts
            # use, so two links from the same outside output don't each
            # get their own redundant Group Input.
            from collections import defaultdict
            incoming = defaultdict(list)  # (from_node_name, from_socket_id) -> [to_node_name, to_socket_id), ...]
            outgoing = defaultdict(list)  # (to_node_name, to_socket_id) -> [(from_node_name, from_socket_id), ...]
            for node in selected_nodes:
                for socket in node.inputs:
                    for link in socket.links:
                        if link.from_node.name not in selected_names:
                            key = (link.from_node.name, link.from_socket.identifier)
                            incoming[key].append((node.name, socket.identifier))
                for socket in node.outputs:
                    for link in socket.links:
                        if link.to_node.name not in selected_names:
                            key = (link.to_node.name, link.to_socket.identifier)
                            outgoing[key].append((node.name, socket.identifier))

            input_node = sub_tree.nodes.new('NodeGroupInput')
            output_node = sub_tree.nodes.new('NodeGroupOutput')
            if sub_tree_nodes:
                min_x = min(n.location[0] for n in sub_tree_nodes)
                max_x = max(n.location[0] for n in sub_tree_nodes)
            else:
                min_x = max_x = 0.0
            input_node.location = (min_x - 250, 0)
            output_node.location = (max_x + 250, 0)

            group_node = base_tree.nodes.new(MaStroScheduleGroupNode.bl_idname)
            group_node.select = False
            if selected_nodes:
                from mathutils import Vector
                group_node.location = sum(
                    (Vector(n.location) for n in selected_nodes), Vector((0.0, 0.0))
                ) / len(selected_nodes)
            group_node.node_tree = sub_tree

            # Build the new sockets in a stable order (sorted by key) so
            # the Nth interface socket created below lines up with the
            # Nth entry iterated again right after - dict insertion
            # order would work too here (Python 3.7+), but sorting
            # makes this not rely on that incidental guarantee.
            incoming_keys = sorted(incoming.keys())
            outgoing_keys = sorted(outgoing.keys())

            for from_node_name, from_socket_id in incoming_keys:
                from_node = base_tree.nodes[from_node_name]
                from_socket = next(s for s in from_node.outputs if s.identifier == from_socket_id)
                _new_tree_socket(sub_tree, from_socket.bl_idname, from_socket.name, 'INPUT')
            for to_node_name, to_socket_id in outgoing_keys:
                to_node = base_tree.nodes[to_node_name]
                to_socket = next(s for s in to_node.inputs if s.identifier == to_socket_id)
                _new_tree_socket(sub_tree, to_socket.bl_idname, to_socket.name, 'OUTPUT')

            # group_node.node_tree = sub_tree alone does NOT give the
            # group node its own inputs/outputs - confirmed live as a
            # real bug ("IndexError: ... index 0 out of range, size 0"
            # on group_node.inputs[0] right below) - see
            # _sync_group_node_sockets's own docstring for why this
            # needs to be explicit at all, and why it's also called
            # again later from MaStroScheduleGroupTree.update() to stay
            # in sync from then on.
            _sync_group_node_sockets(group_node)

            # Linking order must follow the interface sockets' own order
            # (group_node.inputs[i]/outputs[i], freshly built above in
            # exactly incoming_keys/outgoing_keys' own order) - same
            # requirement Sverchok's own comment flags ("linking should
            # be ordered from first socket to last").
            for i, (from_node_name, from_socket_id) in enumerate(incoming_keys):
                from_node = base_tree.nodes[from_node_name]
                from_socket = next(s for s in from_node.outputs if s.identifier == from_socket_id)
                base_tree.links.new(group_node.inputs[i], from_socket)
                for to_node_name, to_socket_id in incoming[(from_node_name, from_socket_id)]:
                    inner_node = sub_tree.nodes[to_node_name]
                    inner_socket = next(s for s in inner_node.inputs if s.identifier == to_socket_id)
                    sub_tree.links.new(inner_socket, input_node.outputs[i])
            for i, (to_node_name, to_socket_id) in enumerate(outgoing_keys):
                to_node = base_tree.nodes[to_node_name]
                to_socket = next(s for s in to_node.inputs if s.identifier == to_socket_id)
                base_tree.links.new(to_socket, group_node.outputs[i])
                for from_node_name, from_socket_id in outgoing[(to_node_name, to_socket_id)]:
                    inner_node = sub_tree.nodes[from_node_name]
                    inner_socket = next(s for s in inner_node.outputs if s.identifier == from_socket_id)
                    sub_tree.links.new(output_node.inputs[i], inner_socket)
        finally:
            del sub_tree["building"]
            del base_tree["building"]

        for node in selected_nodes:
            base_tree.nodes.remove(node)

        # Straight into the new group's own body, the same way
        # Sverchok's own AddGroupTreeFromSelected ends by calling its
        # own edit_group_tree - landing back on the now-empty outer
        # tree (with nothing left selected, the group still showing as
        # a single collapsed node) would be a strange place to leave
        # the user right after "Group Selected" specifically asked to
        # build a group's own contents.
        context.space_data.path.append(sub_tree, node=group_node)

        return {'FINISHED'}


class MASTRO_OT_Schedule_Ungroup(Operator):
    """Move a Group node's own nodes back into the tree containing it,
    reconnecting every link that crossed the group's own boundary, and
    delete the now-empty Group node - the reverse of "Group Selected"
    (see that operator's own docstring). Mirrors Sverchok's own
    UngroupGroupTree (core/node_group.py), simplified: no Frame
    handling (Group Selected itself never copies Frames into a new
    group either, see its own docstring, so there are none to restore
    here)."""
    bl_idname = "mastro_schedule.ungroup"
    bl_label = "Ungroup"
    bl_description = "Move this Group's own nodes back into the tree containing it"

    @classmethod
    def poll(cls, context):
        node = context.active_node
        return node is not None and node.bl_idname == MaStroScheduleGroupNode.bl_idname and node.node_tree is not None

    def execute(self, context):
        group_node = context.active_node
        sub_tree = group_node.node_tree
        base_tree = context.space_data.path[-1].node_tree

        sub_tree_nodes = [
            n for n in sub_tree.nodes if n.bl_idname not in ('NodeGroupInput', 'NodeGroupOutput')
        ]
        # No selection to copy at all (an empty group) - just remove
        # the Group node itself, nothing to paste back.
        if not sub_tree_nodes:
            base_tree.nodes.remove(group_node)
            return {'FINISHED'}

        for node in sub_tree.nodes:
            node.select = node in sub_tree_nodes
            # Same "this will be copied within the nodes" marker
            # Sverchok's own UngroupGroupTree relies on (a custom ID
            # property survives clipboard_copy/paste, confirmed live -
            # used right below to map each pasted copy in base_tree
            # back to the original node it came from inside sub_tree,
            # the only way to know which outside link should reconnect
            # to which copy once both sit in the same tree).
            if node in sub_tree_nodes:
                node["sub_node_name"] = node.name

        # node.clipboard_copy/paste is the same native node clipboard
        # "Group Selected" itself uses (see that operator's own
        # comment) - this time copying OUT of sub_tree, into base_tree,
        # the exact reverse direction.
        context.space_data.path.append(sub_tree, node=group_node)
        bpy.ops.node.clipboard_copy()
        context.space_data.path.pop()
        bpy.ops.node.clipboard_paste()

        pasted_nodes = [n for n in base_tree.nodes if n.select]
        from mathutils import Vector
        center = sum((Vector(n.location) for n in pasted_nodes), Vector((0.0, 0.0))) / len(pasted_nodes)
        for node in pasted_nodes:
            node.location = Vector(node.location) - center + Vector(group_node.location)

        # sub_node_name -> the pasted copy that came from it, the
        # twin-mapping Sverchok's own UngroupGroupTree builds the same
        # way (there as a full Tree() structure, here as a plain dict -
        # nothing here needs that structure's own extra bookkeeping).
        twin_by_sub_node_name = {n["sub_node_name"]: n for n in pasted_nodes}

        # Every link crossing INTO the group (Group Input's own outputs
        # feeding some inner node) - reconnect the outside source
        # straight to the pasted copy's own matching input, skipping
        # the (now redundant) Group Input node entirely.
        for input_node in sub_tree.nodes:
            if input_node.bl_idname != 'NodeGroupInput':
                continue
            for i, output_socket in enumerate(input_node.outputs):
                if i >= len(group_node.inputs) or not group_node.inputs[i].is_linked:
                    continue
                outside_link = group_node.inputs[i].links[0]
                for link in output_socket.links:
                    inner_node = twin_by_sub_node_name.get(link.to_node.name)
                    if inner_node is None:
                        continue
                    inner_socket = inner_node.inputs[list(link.to_node.inputs).index(link.to_socket)]
                    base_tree.links.new(inner_socket, outside_link.from_socket)

        # Every link crossing OUT of the group (some inner node feeding
        # Group Output's own inputs) - same reconnect, the other
        # direction.
        for output_node in sub_tree.nodes:
            if output_node.bl_idname != 'NodeGroupOutput':
                continue
            for i, input_socket in enumerate(output_node.inputs):
                if i >= len(group_node.outputs) or not group_node.outputs[i].is_linked:
                    continue
                for outside_link in group_node.outputs[i].links:
                    for link in input_socket.links:
                        inner_node = twin_by_sub_node_name.get(link.from_node.name)
                        if inner_node is None:
                            continue
                        inner_socket = inner_node.outputs[list(link.from_node.outputs).index(link.from_socket)]
                        base_tree.links.new(outside_link.to_socket, inner_socket)

        for node in pasted_nodes:
            del node["sub_node_name"]
        base_tree.nodes.remove(group_node)

        return {'FINISHED'}


classes = (
    MaStroScheduleGroupTree,
    MaStroScheduleGroupNode,
    MASTRO_OT_Schedule_Enter_Exit_Group,
    MASTRO_OT_Schedule_Add_Group_From_Selected,
    MASTRO_OT_Schedule_Ungroup,
)


# KNOWN ISSUE (not fixed here, see this comment for why): Node
# Wrangler's own "Reset Nodes" (scripts/addons_core/node_wrangler/
# operators/reset_selected.py:NODE_OT_reset_selected) crashes if run on
# a MaStroScheduleGroupNode - confirmed live, IndexError in
# connect_sockets() at that file's own line 107. Root cause: that
# operator recreates the node via node_tree.nodes.new(node.bl_idname)
# (giving a fresh NodeCustomGroup with no node_tree assigned, hence no
# sockets at all) then reconnects every old link by the SAME index it
# had before. Node Wrangler already has a node_ignore set that skips
# Blender's own native group nodes (CompositorNodeGroup/
# GeometryNodeGroup/ShaderNodeGroup) for exactly this reason - adding
# our own bl_idname to that set (a monkey-patch, since it's someone
# else's class) was tried and abandoned: NODE_OT_reset_selected isn't
# registered in bpy.types until Node Wrangler itself is enabled, which
# can happen at any point during a session, independently of and after
# this addon's own register() - reliably catching that moment would
# need an open-ended retry (e.g. a persistent timer, re-checking
# forever in case the user disables/re-enables Node Wrangler later too)
# for a problem that only bites if Node Wrangler's "Reset Nodes" is
# pointed at our own Group node specifically - not worth that ongoing
# cost. Living with the known crash (Node Wrangler is a third-party
# addon we don't otherwise depend on) rather than carrying that
# complexity.


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
