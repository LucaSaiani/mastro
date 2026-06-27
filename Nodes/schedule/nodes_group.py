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

    valid_socket_type/execute/update all mirror MaStroScheduleTree's
    own (see tree.py) - a group's own body is evaluated/validated
    exactly like the main tree, just never opened as a standalone
    editor on its own."""
    bl_idname = 'MaStroScheduleGroupTreeType'
    bl_label = 'MaStro Schedule Group'
    bl_icon = 'NODETREE'

    @classmethod
    def poll(cls, context):
        return False

    @classmethod
    def valid_socket_type(cls, socket_type):
        return socket_type in socket_type_names()


# A real Blender NodeCustomGroup (the native base class for group
# nodes, confirmed against Sverchok's own SvGroupTreeNode in
# core/node_group.py, which uses the same base) rather than the usual
# MaStroScheduleTreeNode/Node mixin every other node in this package
# uses - NodeCustomGroup is what gives this node its own node_tree
# property and the native "edit this group" double-click behavior,
# neither of which a plain Node provides.
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
        if tree is None or tree.bl_idname != 'MaStroScheduleTreeType':
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

        # node.clipboard_copy/paste is Blender's own native node
        # clipboard (confirmed against Sverchok's own identical use in
        # AddGroupTreeFromSelected) - copies every currently selected
        # node, with all of its own property values, into the paste
        # buffer; pasting into a different tree (by appending it to
        # the editor's own breadcrumb path first) is the only way to
        # duplicate a node's full state without manually re-creating
        # every property by hand.
        bpy.ops.node.clipboard_copy()
        context.space_data.path.append(sub_tree)
        bpy.ops.node.clipboard_paste()
        context.space_data.path.pop()

        sub_tree_nodes = _selected_groupable_nodes(sub_tree)
        if sub_tree_nodes:
            from mathutils import Vector
            center = sum((Vector(n.location) for n in sub_tree_nodes), Vector((0.0, 0.0))) / len(sub_tree_nodes)
            for node in sub_tree_nodes:
                node.location = Vector(node.location) - center

        # Every link crossing the selection's own boundary, keyed by
        # the (node, socket) pair on the OUTSIDE of the selection - one
        # interface socket per distinct outside endpoint, the same
        # grouping Sverchok's own from_sockets/to_sockets dicts use, so
        # two links from the same outside output don't each get their
        # own redundant Group Input.
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
        # the Nth interface socket created below lines up with the Nth
        # entry iterated again right after - dict insertion order would
        # work too here (Python 3.7+), but sorting makes this not rely
        # on that incidental guarantee.
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

        # Linking order must follow the interface sockets' own order
        # (group_node.inputs[i]/outputs[i] - Blender keeps those in
        # sync with the interface automatically) - same requirement
        # Sverchok's own comment flags ("linking should be ordered from
        # first socket to last").
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

        for node in selected_nodes:
            base_tree.nodes.remove(node)

        return {'FINISHED'}


classes = (
    MaStroScheduleGroupTree,
    MaStroScheduleGroupNode,
    MASTRO_OT_Schedule_Add_Group_From_Selected,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
