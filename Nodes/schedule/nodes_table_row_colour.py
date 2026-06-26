from bpy.types import Node
from bpy.props import IntProperty, FloatVectorProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node
from .table_text_edit_shared import resolve_index


# Sets the background AND text colour of one row, across EVERY column -
# the row equivalent of Edit Header's own Background Colour/Text
# Colour (which only ever touch a column's header cell). No Start/End
# Column Index, unlike Hide Zero/Cell Prefix-Suffix/Cell Case/Cell
# Align - the user's own explicit call, after a follow-up question
# ("non capisco gli input di row colour: cosa fanno start e end? non
# basta row index?"): a typical colored row spans the whole Table (the
# common spreadsheet case), and nothing about a single-row operation
# makes "color only some of this row's columns" an obviously useful
# case to support, unlike the other four nodes' own column-range case.
# Text Colour added alongside Background Colour - the user's own
# explicit call: "se abbiamo il colore per il background avremo anche
# il colore per il testo" - same pairing Edit Header/Edit Cell already
# have. The header itself is never touched by this node either, same
# as those four - the user's own explicit call: "L'header dovrebbe
# sempre essere escluso da tutte le operazioni sulle celle" - editing a
# header's own colour stays Edit Header's job. Row Index follows
# Excel's own convention (see nodes_viewer.py's row-number overlay and
# nodes_table_edit_cell.py's own identical comment) - row 1 is always
# the header, so the first DATA row is row 2, never row 1.
class MaStroScheduleTableRowColourNode(MaStroScheduleTreeNode, Node):
    """Set the background and text colour of one entire data row of a
    Table"""
    bl_idname = 'MaStroScheduleTableRowColour'
    bl_label = 'Row Colour'

    row_index: IntProperty(name="Row Index", default=2, min=2, update=update_node)
    bg_colour: FloatVectorProperty(name="Background Colour", subtype='COLOR', size=3, min=0.0, max=1.0,
                                    default=(0.18, 0.18, 0.18), update=update_node)
    text_colour: FloatVectorProperty(name="Text Colour", subtype='COLOR', size=3, min=0.0, max=1.0,
                                      default=(1.0, 1.0, 1.0), update=update_node)

    def init(self, context):
        self.inputs.new('MaStroScheduleTableSocketType', "Table")
        self.inputs.new('MaStroScheduleColumnSocketType', "Row Index").prop_name = "row_index"
        self.inputs.new('MaStroScheduleColorSocketType', "Background Colour").prop_name = "bg_colour"
        self.inputs.new('MaStroScheduleColorSocketType', "Text Colour").prop_name = "text_colour"
        self.outputs.new('MaStroScheduleTableSocketType', "Table")

    def evaluate(self, inputs):
        table = inputs[0] or {"columns": [], "merges": []}
        row_index = resolve_index(self.inputs["Row Index"], inputs[1], self.row_index)
        # Clamped to 2, not just gated on it - min=2 on the property
        # itself only blocks typing a smaller number into the inline
        # field; a linked node can still send a smaller value straight
        # through. The user's own explicit call: row 1 (the header)
        # must never be reachable from this node regardless of where
        # Row Index's value came from.
        row_index = max(2, row_index)
        bg_colour = inputs[2] if self.inputs["Background Colour"].is_linked else tuple(self.bg_colour)
        text_colour = inputs[3] if self.inputs["Text Colour"].is_linked else tuple(self.text_colour)

        # row_index - 2, not - 1: see this class's own module-level
        # comment - row_index 2 is the first entry of "rows" (list
        # index 0), since "rows" has no header entry of its own.
        data_index = row_index - 2
        columns = table.get("columns", [])
        new_columns = list(columns)
        for col_idx, target in enumerate(columns):
            rows = target.get("rows", [])
            if data_index >= len(rows):
                continue
            new_rows = list(rows)
            new_rows[data_index] = {**rows[data_index], "bg": bg_colour, "text_color": text_colour}
            new_columns[col_idx] = {**target, "rows": new_rows}

        return [{"columns": new_columns, "merges": table.get("merges", [])}]
