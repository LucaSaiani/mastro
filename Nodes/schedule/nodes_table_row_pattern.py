from bpy.types import Node
from bpy.props import IntProperty, FloatVectorProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node, is_socket_active
from .table_text_edit_shared import resolve_index, column_range


# Alternates two background/text colour pairs across EVERY data row, no
# row index needed - the user's own explicit distinction from Row
# Colour ("row colour and row pattern. il pattern si applica a tutte le
# row senza dover indicare quale"). Loosely the Schedule equivalent of
# Excel's own alternating-row-colour table styles (the reference image
# the user attached) - except this tree only ever offers two plain
# colour pairs to alternate between, not a gallery of preset templates
# the way Excel does ("noi però scegliamo tra due colori, non come
# excel che ti presenta dei template"). Text colour added alongside
# background colour for each of the two - the user's own explicit
# call: "se abbiamo il colore per il background avremo anche il colore
# per il testo" - same pairing Row Colour/Edit Header/Edit Cell already
# have.
#
# Never touches the header - same rule as every other cell-editing node
# in this tree (Hide Zero/Cell Prefix-Suffix/Cell Case/Cell Align/Row
# Colour/Edit Cell): "L'header dovrebbe sempre essere escluso da tutte
# le operazioni sulle celle". The first data row (Excel-style row 2 -
# see nodes_viewer.py's row-number overlay/nodes_table_edit_cell.py's
# own comment, row 1 is always the header) always gets the A pair, the
# next gets the B pair, the next the A pair again, and so on - a fixed,
# not user-configurable, starting colour; swapping which pair starts is
# just swapping the A/B inputs.
class MaStroScheduleTableRowPatternNode(MaStroScheduleTreeNode, Node):
    """Alternate two background/text colour pairs across every data
    row, in one or more columns of a Table"""
    bl_idname = 'MaStroScheduleTableRowPattern'
    bl_label = 'Row Pattern'

    start_index: IntProperty(
        name="Start Column Index", default=0, min=0, update=update_node,
        description="First column to apply this to - equal to End Column Index for just one column",
    )
    end_index: IntProperty(
        name="End Column Index", default=0, min=0, update=update_node,
        description="Last column to apply this to (inclusive) - equal to Start Column Index for just one column",
    )
    bg_colour_a: FloatVectorProperty(name="Background Colour A", subtype='COLOR', size=3, min=0.0, max=1.0,
                                      default=(0.18, 0.18, 0.18), update=update_node)
    text_colour_a: FloatVectorProperty(name="Text Colour A", subtype='COLOR', size=3, min=0.0, max=1.0,
                                        default=(1.0, 1.0, 1.0), update=update_node)
    bg_colour_b: FloatVectorProperty(name="Background Colour B", subtype='COLOR', size=3, min=0.0, max=1.0,
                                      default=(0.12, 0.12, 0.12), update=update_node)
    text_colour_b: FloatVectorProperty(name="Text Colour B", subtype='COLOR', size=3, min=0.0, max=1.0,
                                        default=(1.0, 1.0, 1.0), update=update_node)

    def init(self, context):
        self.inputs.new('MaStroScheduleTableSocketType', "Table")
        self.inputs.new('MaStroScheduleColumnSocketType', "Start Column Index").prop_name = "start_index"
        self.inputs.new('MaStroScheduleColumnSocketType', "End Column Index").prop_name = "end_index"
        self.inputs.new('MaStroScheduleColorSocketType', "Background Colour A").prop_name = "bg_colour_a"
        self.inputs.new('MaStroScheduleColorSocketType', "Text Colour A").prop_name = "text_colour_a"
        self.inputs.new('MaStroScheduleColorSocketType', "Background Colour B").prop_name = "bg_colour_b"
        self.inputs.new('MaStroScheduleColorSocketType', "Text Colour B").prop_name = "text_colour_b"
        self.outputs.new('MaStroScheduleTableSocketType', "Table")

    def evaluate(self, inputs):
        table = inputs[0] or {"columns": [], "merges": []}
        start_index = resolve_index(self.inputs["Start Column Index"], inputs[1], self.start_index)
        end_index = resolve_index(self.inputs["End Column Index"], inputs[2], self.end_index)
        bg_colour_a = inputs[3] if is_socket_active(self.inputs["Background Colour A"]) else tuple(self.bg_colour_a)
        text_colour_a = inputs[4] if is_socket_active(self.inputs["Text Colour A"]) else tuple(self.text_colour_a)
        bg_colour_b = inputs[5] if is_socket_active(self.inputs["Background Colour B"]) else tuple(self.bg_colour_b)
        text_colour_b = inputs[6] if is_socket_active(self.inputs["Text Colour B"]) else tuple(self.text_colour_b)

        bounds = column_range(table, start_index, end_index)
        if bounds is None:
            return [table]
        start_index, end_index = bounds

        columns = table.get("columns", [])
        new_columns = list(columns)
        for col_idx in range(start_index, end_index + 1):
            target = columns[col_idx]
            new_rows = [
                {
                    **row,
                    "bg": bg_colour_a if row_idx % 2 == 0 else bg_colour_b,
                    "text_color": text_colour_a if row_idx % 2 == 0 else text_colour_b,
                }
                for row_idx, row in enumerate(target.get("rows", []))
            ]
            new_columns[col_idx] = {**target, "rows": new_rows}

        return [{"columns": new_columns, "merges": table.get("merges", [])}]
