from bpy.types import Node
from bpy.props import IntProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node
from .table_text_edit_shared import resolve_index, map_table_rows


def _is_zero_text(text):
    """True if `text` is exactly what _cell_text (nodes_viewer.py) would
    have produced for a literal 0/0.0 - "0" (an int) or "0.00" (a float,
    always formatted to 2 decimal places). Not a generic numeric parse
    of arbitrary text (e.g. "0.0" typed by some other node, or "00") -
    this only needs to recognize the exact shapes this tree's own nodes
    actually produce for a real zero, not every conceivable spelling of
    zero a human or another tool might write."""
    return text == "0" or text == "0.00"


# Replaces a Table column's text with "" wherever it's exactly zero -
# the user's own explicit call, after reverting an earlier global
# "hide zero values" preference (nodes_viewer.py's _cell_text used to
# do this tree-wide, with an is_id_key escape hatch for Object/Face/
# Level - that kept needing more escape hatches every time a new
# legitimate-zero case showed up, e.g. Evaluate Attribute's own
# "floor"). A real node instead, placed explicitly where it's wanted
# (e.g. right after Column to Table, for an undercroft floor's area).
#
# Works on Table (text), not Column (numbers) - the user's own explicit
# call: a Column's own data is still meant to be computed on downstream
# (Math, Aggregate, ...), where a 0 is a real number, not "nothing to
# show" - only once it's purely visual text (past Column to Table) does
# "hide this specific zero" become a presentation choice rather than a
# data one.
class MaStroScheduleTableHideZeroNode(MaStroScheduleTreeNode, Node):
    """Hide zero values (replace with blank) in one or more columns of a
    Table"""
    bl_idname = 'MaStroScheduleTableHideZero'
    bl_label = 'Hide Zero'

    start_index: IntProperty(name="Start Index", default=0, min=0, update=update_node)
    end_index: IntProperty(name="End Index", default=0, min=0, update=update_node)

    def init(self, context):
        self.inputs.new('MaStroScheduleTableSocketType', "Table")
        self.inputs.new('MaStroScheduleColumnSocketType', "Start Index").prop_name = "start_index"
        self.inputs.new('MaStroScheduleColumnSocketType', "End Index").prop_name = "end_index"
        self.outputs.new('MaStroScheduleTableSocketType', "Table")

    def evaluate(self, inputs):
        table = inputs[0] or {"columns": [], "merges": []}
        start_index = resolve_index(self.inputs["Start Index"], inputs[1], self.start_index)
        end_index = resolve_index(self.inputs["End Index"], inputs[2], self.end_index)
        return [map_table_rows(
            table, start_index, end_index,
            lambda text: "" if _is_zero_text(text) else text,
        )]
