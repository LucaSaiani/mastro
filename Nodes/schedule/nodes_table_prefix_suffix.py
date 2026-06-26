from bpy.types import Node
from bpy.props import IntProperty, StringProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node
from .table_text_edit_shared import resolve_index, map_table_rows


# Prepends/appends fixed text to a Table column's own text - both in one
# node rather than two (the user's own explicit grouping: "Hide Zero,
# prefix e suffix assieme") - e.g. a "m²" suffix on an area column, or a
# "Floor " prefix on a floor index. Empty text (the default for both)
# leaves the column untouched on that side - this node added to a chain
# with nothing typed into either field is a no-op, not an error.
class MaStroScheduleTablePrefixSuffixNode(MaStroScheduleTreeNode, Node):
    """Add a fixed prefix and/or suffix to one or more columns of a
    Table"""
    bl_idname = 'MaStroScheduleTablePrefixSuffix'
    bl_label = 'Cell Prefix / Suffix'

    prefix: StringProperty(name="Prefix", update=update_node)
    suffix: StringProperty(name="Suffix", update=update_node)
    start_index: IntProperty(name="Start Index", default=0, min=0, update=update_node)
    end_index: IntProperty(name="End Index", default=0, min=0, update=update_node)

    def init(self, context):
        self.inputs.new('MaStroScheduleTableSocketType', "Table")
        self.inputs.new('MaStroScheduleStringSocketType', "Prefix").prop_name = "prefix"
        self.inputs.new('MaStroScheduleStringSocketType', "Suffix").prop_name = "suffix"
        self.inputs.new('MaStroScheduleColumnSocketType', "Start Index").prop_name = "start_index"
        self.inputs.new('MaStroScheduleColumnSocketType', "End Index").prop_name = "end_index"
        self.outputs.new('MaStroScheduleTableSocketType', "Table")

    def evaluate(self, inputs):
        table = inputs[0] or {"columns": [], "merges": []}
        prefix = inputs[1] if self.inputs["Prefix"].is_linked else self.prefix
        suffix = inputs[2] if self.inputs["Suffix"].is_linked else self.suffix
        start_index = resolve_index(self.inputs["Start Index"], inputs[3], self.start_index)
        end_index = resolve_index(self.inputs["End Index"], inputs[4], self.end_index)
        # Leaves an already-empty cell empty - the user's own explicit
        # call: a cell blanked by Hide Zero upstream (or genuinely empty
        # to begin with) should stay blank, not become "m²" with
        # nothing in front of it. Only a non-empty cell gets wrapped.
        return [map_table_rows(
            table, start_index, end_index,
            lambda text: f"{prefix}{text}{suffix}" if text else text,
        )]
