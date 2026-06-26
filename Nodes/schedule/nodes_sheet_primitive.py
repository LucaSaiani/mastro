from bpy.types import Node
from bpy.props import IntProperty, FloatVectorProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node, is_socket_active


# A Sheet with no upstream at all - the same primitive role
# nodes_column_primitive.py's Column and nodes_table_primitive.py's
# Table play, just for Sheet (see those files' own docstrings). No
# Title/Join Header/Alignment here, unlike Table Primitive - Sheet has
# no header concept at all (see sockets.py:MaStroScheduleSheetSocket's
# own docstring), so every one of its cells is created equal: same
# blank text, same Background Colour/Text Colour, no row singled out
# for special treatment the way Table Primitive's row 0 always is.
# Columns/Rows here means the Sheet's own TOTAL cell count per column -
# not "rows below the header" the way Table Primitive's Rows field
# means (Table always has an implicit header at row 0 on top of
# whatever Rows says; Sheet has nothing implicit to add on top).
class MaStroScheduleSheetPrimitiveNode(MaStroScheduleTreeNode, Node):
    """Create an empty Sheet with the given number of columns and rows,
    every cell identical (no header)"""
    bl_idname = 'MaStroScheduleSheetPrimitive'
    bl_label = 'Sheet'

    # Backing values for every inline field below (NodeSocket.prop_name,
    # same mechanism as Table Primitive's own column_count/row_count) -
    # editable directly on the socket while unlinked, read from the
    # actual linked node's output instead once something is plugged in.
    column_count: IntProperty(name="Columns", default=3, min=1, update=update_node)
    row_count: IntProperty(name="Rows", default=2, min=1, update=update_node)
    bg_value: FloatVectorProperty(name="Background Colour", subtype='COLOR', size=3,
                                   min=0.0, max=1.0, default=(0.18, 0.18, 0.18), update=update_node)
    text_colour_value: FloatVectorProperty(name="Text Colour", subtype='COLOR', size=3,
                                            min=0.0, max=1.0, default=(1.0, 1.0, 1.0), update=update_node)

    def init(self, context):
        self.inputs.new('MaStroScheduleColumnSocketType', "Columns").prop_name = "column_count"
        self.inputs.new('MaStroScheduleColumnSocketType', "Rows").prop_name = "row_count"
        self.inputs.new('MaStroScheduleColorSocketType', "Background Colour").prop_name = "bg_value"
        self.inputs.new('MaStroScheduleColorSocketType', "Text Colour").prop_name = "text_colour_value"
        self.outputs.new('MaStroScheduleSheetSocketType', "Sheet")

    @staticmethod
    def _resolve_count(socket, rows_in, fallback):
        # Same resolution shape as Table Primitive's own _resolve_count.
        if not is_socket_active(socket):
            return fallback
        rows_in = rows_in or []
        if not rows_in:
            return 0
        row_key = next((k for k in rows_in[0] if not k.startswith("_")), None)
        return int(rows_in[0].get(row_key, 0)) if row_key else 0

    @staticmethod
    def _resolve_color(socket, value_in, fallback):
        if not is_socket_active(socket):
            return tuple(fallback)
        return tuple(value_in) if value_in else tuple(fallback)

    def evaluate(self, inputs):
        column_count = self._resolve_count(self.inputs["Columns"], inputs[0], self.column_count)
        row_count = self._resolve_count(self.inputs["Rows"], inputs[1], self.row_count)
        bg = self._resolve_color(self.inputs["Background Colour"], inputs[2], self.bg_value)
        text_colour = self._resolve_color(self.inputs["Text Colour"], inputs[3], self.text_colour_value)

        columns = []
        for _ in range(column_count):
            cells = [{"text": "", "bg": bg, "text_color": text_colour} for _ in range(row_count)]
            columns.append({"cells": cells})

        return [{"columns": columns, "merges": []}]
