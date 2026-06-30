from bpy.types import Node, Operator
from bpy.props import EnumProperty, StringProperty

from .tree import MaStroScheduleTreeNode, downstream_main_inputs
from .execution import update_node
from .nodes_viewer import _header_text


def _id_keys(row):
    """The id keys of a Column row - everything that starts with "_"
    (_Object, _Face/_Edge/_Vertex/_Level/...). Duplicated from
    nodes_aggregate_column.py's identical helper rather than imported -
    this module is meant to be importable by every id-key-consuming node
    (Aggregate/Group Into List/Accumulate) without creating an import
    cycle back into nodes_aggregate_column.py, which itself now imports
    from here instead (see that module's own picker, now superseded by
    this node's output where wired)."""
    return [k for k in row.keys() if k.startswith("_")]


def _resolve_node(tree_name, node_name):
    import bpy
    tree = bpy.data.node_groups.get(tree_name)
    if tree is None:
        return None
    return tree.nodes.get(node_name)


def _id_keys_for_socket(node, socket):
    """The distinct id keys available on whatever feeds `socket`, in
    first-appearance order. Walks EVERY one of socket's own links, not
    just the first - confirmed live as a real gap with an earlier
    version of this function (delegating straight to execution.py's
    own linked_table, which only ever reads link[0]): a multi-input
    socket (e.g. Merge List's own "List", nodes_merge_list.py) only had
    its FIRST connected List's own keys considered, silently missing
    whatever the others carried.

    Handles BOTH a Column socket (rows are plain {key: value, ...}
    dicts, id keys read directly off each one) and a List socket (rows
    are {"key": ..., "rows": [...]} groups - see Group Into List/Merge
    List's own docstrings for that shape - the real id-keyed rows are
    nested one level down, inside each group's own "rows") - confirmed
    live as a real, separate bug otherwise: Merge List's own "List"
    input was always read as if it carried plain Column rows, so
    _id_keys found nothing (a List group's own top-level keys are just
    "key"/"rows", neither starting with "_") even when the List's own
    inner rows had real id keys to offer."""
    from .tree import resolve_through_reroutes
    from .execution import get_node_table

    keys = []
    if not socket.is_linked:
        return keys
    is_list_socket = socket.bl_idname == 'MaStroScheduleListSocketType'
    for link in socket.links:
        if link.is_muted:
            continue
        from_node, from_socket = resolve_through_reroutes(link)
        if from_node is None or from_socket.bl_idname != socket.bl_idname:
            continue
        table = get_node_table(node.id_data.name, from_node.name)
        if not table:
            continue
        try:
            output_index = list(from_node.outputs).index(from_socket)
        except ValueError:
            continue
        value = table[output_index] or []
        if is_list_socket:
            rows = [row for group in value for row in group.get("rows", [])]
        else:
            rows = value
        for row in rows:
            for key in _id_keys(row):
                if key not in keys:
                    keys.append(key)
    return keys


def available_id_keys(get_id_keys_node):
    """The id keys available to pick from this Id Keys node's own
    output, found by walking FORWARD to whatever real node(s) consume
    it (downstream_main_inputs, tree.py) and reading each one's own
    main data input - NOT a Column this node carries itself (removed -
    see this module's own docstring for why a second, independently-
    wired input was a real, silent mismatch risk). If more than one
    consumer is wired (the same Id Keys feeding e.g. both Group
    Into List AND Merge List's own Match Key), only keys common to
    EVERY consumer's own data are offered - a key that isn't actually
    present everywhere this picker's result will be used isn't a safe
    choice.

    KNOWN LIMITATION (not solved here): only reads ONE level upstream
    of each consumer - if a consumer's own main input is itself fed by
    another node that ALSO needs an Id Key to produce anything (e.g.
    Merge List fed by a Group Into List that hasn't been given its own
    key yet), that upstream node's own output is empty until ITS key is
    picked, so this sees no rows and offers no keys at all - confirmed
    live as a real circular-dependency gap. Worked around for now by
    keeping the single-level case (the common one - a consumer wired
    directly to a Column/List that already has real data, e.g. Group
    Into List or Aggregate on a Column straight from Evaluate
    Attribute) fully working, while a chain through more than one
    key-dependent node isn't - see issue tracker for the open
    follow-up."""
    pairs = downstream_main_inputs(get_id_keys_node.outputs["Id Key"], 'MaStroScheduleIdKeySocketType')
    if not pairs:
        return []
    common = None
    for consumer, socket in pairs:
        keys = set(_id_keys_for_socket(consumer, socket))
        common = keys if common is None else (common & keys)
    if not common:
        return []
    # Order: first-appearance order from the FIRST consumer found,
    # filtered down to the common set - arbitrary but stable/
    # deterministic (pairs' own order is socket.links' own order,
    # unaffected by set intersection's lack of inherent ordering).
    first_consumer, first_socket = pairs[0]
    ordered = _id_keys_for_socket(first_consumer, first_socket)
    return [k for k in ordered if k in common]


def _pick_id_key_items(operator_self, context):
    """Module-level, not a method - see nodes_attribute.py's
    _pick_attribute_name_items docstring for why."""
    node = _resolve_node(operator_self.tree_name, operator_self.node_name)
    if node is None:
        return [("", "(node not found)", "")]
    keys = available_id_keys(node)
    return [(key, _header_text(key), "") for key in keys] or [("", "(no id keys)", "")]


class MASTRO_OT_Schedule_Pick_Id_Key(Operator):
    """Pick an id key"""
    bl_idname = "node.mastro_schedule_pick_id_key"
    bl_label = "Pick Id Key"
    bl_options = {'INTERNAL', 'REGISTER'}
    bl_property = "option"

    tree_name: StringProperty()
    node_name: StringProperty()
    option: EnumProperty(items=_pick_id_key_items)

    def execute(self, context):
        node = _resolve_node(self.tree_name, self.node_name)
        if node is not None:
            node.key_value = self.option
            update_node(node, context)
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {'FINISHED'}


# Mirrors Named Attribute (nodes_attribute.py) exactly, one level
# down: that node lists attribute NAMES available on the objects feeding
# Data (read dynamically, not hardcoded), to be picked and fed to
# Evaluate Attribute; this one lists ID KEYS available on the rows of a
# Column (_Object, _Face/_Edge/_Vertex/_Level/...), to be picked and fed
# to Aggregate/Flatten Key/Group Into List/Accumulate's own "Id Key"
# input - replacing the search-popup each of those used to build
# internally, hardcoded against their own first input, with one shared
# node whose output can be wired to several of them at once (the user's
# own explicit ask).
#
# No Column input of its own (removed - see available_id_keys' own
# docstring for why) - confirmed live as a real, silent bug otherwise:
# nothing stopped wiring this node's own Column input to a DIFFERENT
# upstream Column than the one actually feeding whatever consumes this
# node's own Id Key output (e.g. two separate Evaluate Attribute
# branches, Area and Use, each with its own Column - picking the wrong
# one here showed a plausible-looking key list whenever both branches
# happened to share the same id keys, with no indication anything was
# wrong). This node instead looks FORWARD to its own consumer(s) and
# reads each one's own main input directly - there's only one Column/
# List relationship to keep in sync now, the one already wired into
# the real consuming node.
class MaStroScheduleGetIdKeysNode(MaStroScheduleTreeNode, Node):
    """List the id keys available on whatever this node's own Id Key
    output is wired into - pick one with the button to feed it to
    Aggregate/Flatten Key/Group Into List/Merge List/Accumulate's own
    Id Key input"""
    bl_idname = 'MaStroScheduleGetIdKeys'
    bl_label = 'Id Keys'

    # key_value is a plain StringProperty written by
    # MASTRO_OT_Schedule_Pick_Id_Key's search popup, not a dynamic
    # EnumProperty on the node itself - same RecursionError-avoidance
    # reasoning as nodes_attribute.py's name_value/Pick_Attribute_Name.
    key_value: StringProperty(name="Key", update=update_node)

    def init(self, context):
        self.outputs.new('MaStroScheduleIdKeySocketType', "Id Key")

    def draw_buttons(self, context, layout):
        op = layout.operator(
            "node.mastro_schedule_pick_id_key",
            text=_header_text(self.key_value) if self.key_value else "(pick a key)",
        )
        op.tree_name = self.id_data.name
        op.node_name = self.name

    def evaluate(self, inputs):
        return [self.key_value]
