import bpy
from bpy.types import Node
from bpy.props import FloatProperty, PointerProperty

from .tree import MaStroScheduleTreeNode, resolve_through_reroutes
from .execution import update_node
from .nodes_group import MaStroScheduleGroupTree


# Runs a Group Tree's own nodes once per element of a List, the
# Schedule's equivalent of Python's `for x in items` (NOT `while` -
# always processes every element, length known upfront from the input
# List, no early exit - see issue #15's own design discussion for why
# this distinction matters: a condition can affect what ONE iteration
# produces, never whether the loop as a whole keeps going).
#
# NOT a MaStroScheduleGroupNode/NodeCustomGroup - deliberately a plain
# node (MaStroScheduleTreeNode/Node mixin, like Pivot or Aggregate)
# with body_tree as an ordinary PointerProperty instead. A
# NodeCustomGroup's own external sockets are expected to mirror its
# body's own interface 1:1 (exactly what nodes_group.py's own
# _sync_group_node_sockets enforces for a plain Group) - For Each's own
# external sockets (a List, Start, Step) are NOT a 1:1 mirror of its
# body's own interface (a single Column + Counter per iteration, plus
# an optional accumulator pair) - fighting that built-in assumption
# would cost more than building this node's own external shape from
# scratch.
#
# The body's own interface is FIXED and built automatically at
# creation time (Column + Counter on the Group Input side, Result +
# Accumulator In/Out on the Group Output side) - unlike a plain Group
# (whose interface grows from whatever the user links via "Group
# Selected"), the user never builds this interface by hand, only the
# loop body logic that reads from/writes to it.
class MaStroScheduleForEachNode(MaStroScheduleTreeNode, Node):
    """Run a Group's own nodes once per element of a List, collecting
    each iteration's own result into a new List"""
    bl_idname = 'MaStroScheduleForEach'
    bl_label = 'For Each List'
    bl_width_default = 160

    # bpy.types.NodeTree (the generic base type, always already
    # registered by Blender itself) - NOT MaStroScheduleGroupTree
    # directly. PointerProperty(type=X) needs X's own bl_rna to already
    # exist at the moment Python evaluates THIS class's own body, which
    # happens at IMPORT time (before __init__.py calls anyone's
    # register() - every addon's imports run top-to-bottom first,
    # confirmed live: MaStroScheduleGroupTree's own bl_rna wasn't ready
    # yet here, a PointerProperty registration error). The generic base
    # type sidesteps that ordering problem entirely - it's always
    # already registered, by Blender, before any addon's own code runs
    # at all. poll= below is what actually keeps this restricted to our
    # own MaStroScheduleGroupTree in practice (mirrors Sverchok's own
    # SvGroupTreeNode.nested_tree_filter, core/node_group.py) - not
    # that the user ever picks this by hand anyway (_build_body always
    # sets it directly), but it keeps the property's own intent honest
    # rather than silently accepting any NodeTree subclass.
    body_tree: PointerProperty(
        type=bpy.types.NodeTree,
        poll=lambda self, tree: tree.bl_idname == 'MaStroScheduleGroupTreeType',
    )
    # Counter = start + index*step, the per-iteration position value
    # fed into the body's own Group Input alongside the current
    # element - NOT something the user wires in from outside (every
    # other input here is a List/Column), set directly on this node
    # the same way Math's own A/B constants are - default 0/1 makes it
    # behave like a plain position index in the common case, but
    # configurable for real counters too (e.g. starting at 100,
    # incrementing by 10).
    start: FloatProperty(name="Start", default=0.0, update=update_node)
    step: FloatProperty(name="Step", default=1.0, update=update_node)

    def init(self, context):
        self.inputs.new('MaStroScheduleListSocketType', "List")
        # Optional - read by the loop body via the body's own second
        # Group Input/Output pair (see _build_body below) only if the
        # user actually wires something into it; left unlinked, the
        # accumulator simply keeps emitting this same starting value
        # back out unchanged every iteration (nothing for the body to
        # carry forward), and the node behaves like a plain map.
        self.inputs.new('MaStroScheduleColumnSocketType', "Accumulator")
        self.outputs.new('MaStroScheduleListSocketType', "List")
        self.outputs.new('MaStroScheduleColumnSocketType', "Accumulator")
        self.body_tree = _build_body(self)

    @property
    def column_label(self):
        # Same upstream-delegation pattern Group Into List's own
        # column_label follows (nodes_groupby_column.py) - the result
        # produced by the loop's own body lives inside body_tree, not
        # reachable here statically (it depends on whatever the user
        # builds inside, which can change freely), so this falls back
        # to the input List's own label instead - "whatever this loop
        # is iterating over", close enough for the Viewer/picker
        # headers this exists for.
        if "List" not in self.inputs:
            return ""
        from .tree import upstream_attr
        return upstream_attr(self.inputs["List"], "column_label")

    def draw_buttons(self, context, layout):
        layout.prop(self, "start")
        layout.prop(self, "step")

    def evaluate(self, inputs):
        from .execution import is_socket_active

        elements = inputs[0] or []
        accumulator_in = inputs[1]
        if not self.body_tree or not elements:
            return [[], accumulator_in if is_socket_active(self.inputs["Accumulator"]) else None]

        accumulator = accumulator_in if is_socket_active(self.inputs["Accumulator"]) else None
        result_elements = []
        for index, element in enumerate(elements):
            counter = [{"Counter": self.start + index * self.step}]
            outputs = _evaluate_body(self.body_tree, element.get("rows"), counter, accumulator)
            result_elements.append({"key": element.get("key"), "rows": outputs[0]})
            if outputs[1] is not None:
                accumulator = outputs[1]

        return [result_elements, accumulator]


def _build_body(for_each_node):
    """Creates a brand new MaStroScheduleGroupTree with the loop's own
    FIXED interface already in place - Column (the current element's
    own rows) and Counter on the Group Input side, Result and
    Accumulator In/Out on the Group Output side. Mirrors
    nodes_group.py's own "Group Selected" in spirit (same node tree
    type, same "building" guard against MaStroScheduleGroupTree.update()
    firing mid-construction - see that module's own comments for why),
    but builds a fixed shape instead of one inferred from the user's
    own link choices."""
    body_tree = bpy.data.node_groups.new('MaStro Schedule For Each Body', MaStroScheduleGroupTree.bl_idname)
    body_tree.use_fake_user = True
    body_tree["building"] = True
    try:
        input_node = body_tree.nodes.new('NodeGroupInput')
        input_node.location = (-300, 0)
        output_node = body_tree.nodes.new('NodeGroupOutput')
        output_node.location = (300, 0)

        body_tree.interface.new_socket("Column", in_out='INPUT', socket_type='MaStroScheduleColumnSocketType')
        body_tree.interface.new_socket("Counter", in_out='INPUT', socket_type='MaStroScheduleColumnSocketType')
        body_tree.interface.new_socket(
            "Accumulator In", in_out='INPUT', socket_type='MaStroScheduleColumnSocketType',
        )
        body_tree.interface.new_socket("Result", in_out='OUTPUT', socket_type='MaStroScheduleColumnSocketType')
        body_tree.interface.new_socket(
            "Accumulator Out", in_out='OUTPUT', socket_type='MaStroScheduleColumnSocketType',
        )

        # Default wiring, not an empty body - the user's own observation:
        # an unwired Group Input/Output left every iteration producing
        # nothing at all, an unhelpful starting point. Column straight
        # to Result (the identity/no-op case - the loop simply passes
        # each element's own rows through unchanged until the user
        # builds real logic in between) and Accumulator In straight to
        # Accumulator Out (carries it forward unmodified by default,
        # the correct behavior for a user who never intends to touch it
        # at all). Counter is left unwired - no single "obvious" default
        # destination for it (unlike Column/Accumulator, nothing already
        # existing on Group Output expects to receive it specifically).
        body_tree.links.new(output_node.inputs["Result"], input_node.outputs["Column"])
        body_tree.links.new(output_node.inputs["Accumulator Out"], input_node.outputs["Accumulator In"])
    finally:
        del body_tree["building"]
    return body_tree


def _evaluate_subtree(tree, cache, eval_node):
    """Forces every node in `tree` to evaluate, not just nodes
    reachable from a sink (execution.py:evaluate_tree's own behavior,
    appropriate for the MAIN tree where only Viewer-connected work
    should run at all) - a loop body's own Group Output is never a
    "sink with no outputs" the way a Viewer is, so evaluate_tree's own
    walk would never reach it on its own. Returns nothing - eval_node
    itself is the one populating cache as it goes, this just has to
    visit every node at least once so anything not on Group Output's
    own input chain (e.g. a dead-end branch) still raises whatever
    error it would on the main tree too, surfaced the same way."""
    for node in tree.nodes:
        eval_node(node)


def _evaluate_body(body_tree, column_rows, counter_rows, accumulator_rows):
    """Runs body_tree's own nodes exactly once, with a fresh cache (so
    a second call - the next loop iteration - never sees a previous
    iteration's own cached results) and the current iteration's own
    values fed in at Group Input. A small, LOCAL, dedicated evaluator -
    deliberately NOT a shared function extracted from execution.py's
    own eval_node (a closure private to evaluate_tree, used by every
    existing node in the system) - see issue #15's own design comment
    for why: a subtle mistake in extracting/parameterizing that shared
    logic risks silently breaking evaluation for nodes that work fine
    today, for a benefit that only serves this one new node. A bug in
    this local copy can't touch anything else.

    Mirrors eval_node's own per-node try/except (execution.py) for the
    same resilience the rest of this package already has everywhere
    else - a node failing during one iteration doesn't stop the whole
    tree (or the whole loop), it produces an empty result for that one
    node only - no red overlay for it specifically though (unlike
    execution.py's own _evaluation_errors, nothing here writes to that
    shared, main-tree-only error map, since body_tree is never drawn/
    polled the way the main tree is - a future refinement, not
    attempted here)."""
    cache = {}

    def resolve_link_value(socket, link):
        if link.is_muted:
            return None
        from_node, from_socket = resolve_through_reroutes(link)
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

    def eval_node(node):
        if node.name in cache:
            return cache[node.name]

        if node.bl_idname == 'NodeGroupInput':
            cache[node.name] = [column_rows, counter_rows, accumulator_rows]
            return cache[node.name]

        input_values = []
        for socket in node.inputs:
            if getattr(socket, "is_multi_input", False):
                input_values.append([resolve_link_value(socket, link) for link in socket.links])
                continue
            value = None
            if socket.is_linked:
                value = resolve_link_value(socket, socket.links[0])
            input_values.append(value)

        if node.bl_idname == 'NodeGroupOutput':
            # NodeGroupOutput is a native Blender node, not one of
            # ours - it has no evaluate() of its own to call (confirmed
            # live as a real bug: hasattr(node, "evaluate") was False,
            # so this branch's own result silently stayed [] regardless
            # of what was actually linked in). Its own "result" IS
            # simply whatever arrived on its inputs, already resolved
            # above - nothing left to compute.
            cache[node.name] = input_values
            return input_values

        try:
            result = node.evaluate(input_values) if hasattr(node, "evaluate") else []
        except Exception:
            result = []
        cache[node.name] = result
        return result

    _evaluate_subtree(body_tree, cache, eval_node)

    # Written into the SAME global cache execution.py's own
    # linked_table/get_node_table read from (keyed by tree name then
    # node name, exactly like evaluate_tree's own _schedule_cache,
    # confirmed against that function's own assignment) - confirmed
    # live as a real, serious usability bug otherwise: every picker
    # node that reads available columns this way (Get Id Keys,
    # Category Lookup, Math's own EnumProperty items, ...) stayed
    # permanently empty inside a loop body, since body_tree never
    # otherwise goes through evaluate_tree at all - this is the only
    # place that ever runs it. Last iteration's own values win (this
    # cache is naturally overwritten every call) - good enough for a
    # picker's own dropdown, which only needs to see WHICH columns
    # exist, not every iteration's own actual values.
    from .execution import _schedule_cache, tag_redraw_node_editors
    _schedule_cache[body_tree.name] = cache
    tag_redraw_node_editors()

    output_node = next((n for n in body_tree.nodes if n.bl_idname == 'NodeGroupOutput'), None)
    if output_node is None:
        return [None, None]
    values = eval_node(output_node)
    result = values[0] if len(values) > 0 else None
    accumulator_out = values[1] if len(values) > 1 else None
    return [result, accumulator_out]


classes = (
    MaStroScheduleForEachNode,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
