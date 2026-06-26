from bpy.types import Node
from bpy.props import IntProperty, StringProperty, FloatVectorProperty, EnumProperty, BoolProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node, is_socket_active
from .nodes_table_edit_header import ALIGNMENT_ITEMS, _mark_touched


# Edits one single DATA cell in a Table (text, background, text colour
# and alignment) - Edit Header's own logic, generalized from "row 0 of
# one column" to "any one data row, any column", since a copy of Edit
# Header was the user's own explicit starting point ("copierei Edit
# Header"). Never touches the header (row 0) - the user's own explicit
# call, same rule as every other cell-editing node in this tree (Hide
# Zero/Cell Prefix-Suffix/Cell Case/Cell Align/Row Colour): "L'header
# dovrebbe sempre essere escluso da tutte le operazioni sulle celle...
# anche edit cell non deve toccare l'header. per quello c'è edit
# header" - editing a header's own text/style stays Edit Header's job
# exclusively. Row Index follows Excel's own convention (the row
# overlay's own ref labels mirror this too, see nodes_viewer.py) - row
# 1 is always the header, so the first DATA row is row 2, not row 1 -
# the user's own explicit call ahead of a future Excel export: "la
# prima cell è A1... noi rappresentiamo A1 come la prima cella dopo
# l'header. Non sarebbe meglio quella cella fosse A2?" Same convention
# as Row Colour/Row Pattern.
#
# No Unjoin, unlike Edit Header - the user's own call: no node in this
# tree produces a merge anywhere but row 0 (Table primitive's Join
# Header) yet, and this node can't reach row 0 at all, so there's no
# real "is this cell covered by some merge" case to handle here at all.
class MaStroScheduleTableEditCellNode(MaStroScheduleTreeNode, Node):
    """Edit one single data cell in a Table, by row and column index -
    text, alignment, background and text colour"""
    bl_idname = 'MaStroScheduleTableEditCell'
    bl_label = 'Edit Cell'

    row_index: IntProperty(name="Row Index", default=2, min=2, update=update_node)
    column_index: IntProperty(name="Column Index", default=0, min=0, update=update_node)
    string_value: StringProperty(name="String", update=update_node)
    bg_value: FloatVectorProperty(name="Background Colour", subtype='COLOR', size=3, min=0.0, max=1.0,
                                   default=(0.18, 0.18, 0.18), update=_mark_touched("has_bg"))
    text_colour_value: FloatVectorProperty(
        name="Text Colour", subtype='COLOR', size=3, min=0.0, max=1.0, default=(1.0, 1.0, 1.0),
        update=_mark_touched("has_text_colour"))
    has_bg: BoolProperty(default=False)
    has_text_colour: BoolProperty(default=False)
    alignment: EnumProperty(name="Alignment", items=ALIGNMENT_ITEMS, default='LEFT',
                             update=_mark_touched("has_alignment"))
    has_alignment: BoolProperty(default=False)

    def init(self, context):
        self.inputs.new('MaStroScheduleTableSocketType', "Table")
        self.inputs.new('MaStroScheduleColumnSocketType', "Row Index").prop_name = "row_index"
        self.inputs.new('MaStroScheduleColumnSocketType', "Column Index").prop_name = "column_index"
        self.inputs.new('MaStroScheduleStringSocketType', "String").prop_name = "string_value"
        self.inputs.new('MaStroScheduleColorSocketType', "Background Colour").prop_name = "bg_value"
        self.inputs.new('MaStroScheduleColorSocketType', "Text Colour").prop_name = "text_colour_value"
        self.outputs.new('MaStroScheduleTableSocketType', "Table")

    def draw_buttons(self, context, layout):
        layout.prop(self, "alignment", text="")

    @staticmethod
    def _resolve_scalar(socket, value_in, fallback, cast):
        if not is_socket_active(socket):
            return fallback
        if isinstance(value_in, str):
            return cast(value_in) if value_in else fallback
        rows_in = value_in or []
        if not rows_in:
            return fallback
        row_key = next((k for k in rows_in[0] if not k.startswith("_")), None)
        return cast(rows_in[0].get(row_key, fallback)) if row_key else fallback

    def evaluate(self, inputs):
        table = inputs[0] or {"columns": [], "merges": []}
        row_index = self._resolve_scalar(self.inputs["Row Index"], inputs[1], self.row_index, int)
        # Clamped to 2, not just gated on it - min=2 on the property
        # itself only blocks typing a smaller number into the inline
        # field; a linked node (e.g. a Value node set to 1) can still
        # send a smaller value straight through. The user's own
        # explicit call: row 1 (the header) must never be reachable from
        # this node regardless of where Row Index's value came from.
        row_index = max(2, row_index)
        col_index = self._resolve_scalar(self.inputs["Column Index"], inputs[2], self.column_index, int)

        string_socket = self.inputs["String"]
        if is_socket_active(string_socket):
            new_text = inputs[3] or ""
            has_text = True
        else:
            new_text = self.string_value
            has_text = bool(new_text)

        bg_socket = self.inputs["Background Colour"]
        if is_socket_active(bg_socket):
            new_bg = inputs[4]
            has_bg = True
        else:
            new_bg = tuple(self.bg_value)
            has_bg = self.has_bg
        text_colour_socket = self.inputs["Text Colour"]
        if is_socket_active(text_colour_socket):
            new_text_colour = inputs[5]
            has_text_colour = True
        else:
            new_text_colour = tuple(self.text_colour_value)
            has_text_colour = self.has_text_colour

        columns = list(table.get("columns", []))
        # row_index - 2, not - 1: row_index follows the Excel-style
        # convention where row 1 is always the header (see this class's
        # own module-level comment) - the Table's own "rows" list has
        # no header entry at all, so its first DATA row (list index 0)
        # corresponds to row_index 2.
        if row_index >= 2 and 0 <= col_index < len(columns):
            column = columns[col_index]
            rows = list(column.get("rows", []))
            data_index = row_index - 2
            if data_index < len(rows):
                new_row = dict(rows[data_index])
                if has_text:
                    new_row["text"] = new_text
                if has_bg:
                    new_row["bg"] = new_bg
                if has_text_colour:
                    new_row["text_color"] = new_text_colour
                if self.has_alignment:
                    new_row["text_align"] = self.alignment
                rows[data_index] = new_row
                columns[col_index] = {**column, "rows": rows}

        return [{"columns": columns, "merges": table.get("merges", [])}]
