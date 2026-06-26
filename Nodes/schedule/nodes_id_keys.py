from bpy.types import Node, Operator
from bpy.props import EnumProperty, StringProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node, linked_table
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


def available_id_keys(node, input_index=0):
    """The distinct id keys available on the Column feeding `node`'s
    input at `input_index`, in first-appearance order - shared by Get Id
    Keys' own picker and every other node that used to hardcode this
    same lookup against its own input (Aggregate/Flatten Key/Group Into
    List/Accumulate, before this node existed to make the list dynamic
    instead - the user's own call: "non dovrebbe essere hardcoded e
    dovrebbe essere ottenuto in modo analogo a get attribute name")."""
    table = linked_table(node, input_index) or []
    keys = []
    for row in table:
        for key in _id_keys(row):
            if key not in keys:
                keys.append(key)
    return keys


def _pick_id_key_items(operator_self, context):
    """Module-level, not a method - see nodes_attribute.py's
    _pick_attribute_name_items docstring for why."""
    node = _resolve_node(operator_self.tree_name, operator_self.node_name)
    if node is None:
        return [("", "(node not found)", "")]
    keys = available_id_keys(node, 0)
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


# Mirrors Get Attribute Names (nodes_attribute.py) exactly, one level
# down: that node lists attribute NAMES available on the objects feeding
# Data (read dynamically, not hardcoded), to be picked and fed to
# Evaluate Attribute; this one lists ID KEYS available on the rows of a
# Column (_Object, _Face/_Edge/_Vertex/_Level/...), to be picked and fed
# to Aggregate/Flatten Key/Group Into List/Accumulate's own "Id Key"
# input - replacing the search-popup each of those used to build
# internally, hardcoded against their own first input, with one shared
# node whose output can be wired to several of them at once (the user's
# own explicit ask).
class MaStroScheduleGetIdKeysNode(MaStroScheduleTreeNode, Node):
    """List the id keys available on the Column feeding this node's
    Column input - pick one with the button to feed it to Aggregate/
    Flatten Key/Group Into List/Accumulate's own Id Key input"""
    bl_idname = 'MaStroScheduleGetIdKeys'
    bl_label = 'Get Id Keys'

    # key_value is a plain StringProperty written by
    # MASTRO_OT_Schedule_Pick_Id_Key's search popup, not a dynamic
    # EnumProperty on the node itself - same RecursionError-avoidance
    # reasoning as nodes_attribute.py's name_value/Pick_Attribute_Name.
    key_value: StringProperty(name="Key", update=update_node)

    def init(self, context):
        self.inputs.new('MaStroScheduleColumnSocketType', "Column")
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
