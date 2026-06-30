import bpy
from bpy.types import Node
from bpy.props import IntProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node, is_socket_active


# Removes one row from a Sheet ENTIRELY - every row below it shifts up
# by one position - unlike Hide Zero/Cell Prefix-Suffix/.../Edit
# Header's own column edits (table_text_edit_shared.py), which only
# ever change a cell's own text/style in place, never the Table/Sheet's
# own shape. The user's own concrete need: Table to Sheet
# (nodes_table_sheet.py) converts a column's own header into an
# ordinary cell rather than a separate concept (a Sheet has no header
# at all, see sockets.py:MaStroScheduleTableSocket's own module
# comment) - removing what USED TO BE a header now means removing
# that cell's own row outright, not just blanking its text the way
# Edit Header already can for a real Table column.
#
# Built at the SHEET level, not Table - the user's own explicit call:
# a Table's own header/rows split has no row to "remove" the same way
# (its header lives in a separate slot from rows, not row 0 of a flat
# list) - Separate Columns (nodes_column_separate.py) already covers
# the analogous "drop a whole column" case at the Column level instead.
class MaStroScheduleSheetRemoveRowNode(MaStroScheduleTreeNode, Node):
    """Remove one row from a Sheet by index - every row below it shifts
    up by one position"""
    bl_idname = 'MaStroScheduleSheetRemoveRow'
    bl_label = 'Remove Row'

    row_index: IntProperty(name="Row Index", default=0, min=0, update=update_node)

    def init(self, context):
        self.inputs.new('MaStroScheduleSheetSocketType', "Sheet")
        self.inputs.new('MaStroScheduleColumnSocketType', "Row Index").prop_name = "row_index"
        self.outputs.new('MaStroScheduleSheetSocketType', "Sheet")

    @staticmethod
    def _resolve_index(socket, value_in, fallback):
        # Same "unlinked socket always comes through as None" handling
        # as every other index-taking node in this tree (Hide Zero/Edit
        # Header/Item from List/...) - fall back to the inline field's
        # own backing property explicitly when unlinked.
        if not is_socket_active(socket):
            return fallback
        if isinstance(value_in, str):
            return int(value_in) if value_in else fallback
        rows_in = value_in or []
        if not rows_in:
            return fallback
        row_key = next((k for k in rows_in[0] if not k.startswith("_")), None)
        return int(rows_in[0].get(row_key, fallback)) if row_key else fallback

    def evaluate(self, inputs):
        sheet = inputs[0] or {"columns": [], "merges": []}
        columns = sheet.get("columns", [])
        if not columns:
            return [sheet]

        index = self._resolve_index(self.inputs["Row Index"], inputs[1], self.row_index)
        row_count = max((len(c.get("cells", [])) for c in columns), default=0)
        if index < 0 or index >= row_count:
            return [sheet]

        new_columns = []
        for column in columns:
            cells = list(column.get("cells", []))
            if index < len(cells):
                del cells[index]
            new_columns.append({**column, "cells": cells})

        # Merges spanning the removed row are dropped entirely (the
        # same "no longer a coherent region once part of what it
        # covered no longer exists" call Edit Header's own Unjoin
        # already makes for a removed merge) - merges entirely BELOW
        # the removed row shift up by one to follow their own cells;
        # merges entirely ABOVE are untouched. A merge straddling the
        # removed row (start_row < index < end_row) shrinks by one
        # row instead of being dropped - it still covers a coherent
        # region once that one row is gone, just a shorter one.
        new_merges = []
        for merge in sheet.get("merges", []):
            start_row = merge.get("start_row", 0)
            end_row = merge.get("end_row", 0)
            if start_row == index and end_row == index:
                continue
            new_merge = dict(merge)
            if start_row > index:
                new_merge["start_row"] = start_row - 1
            if end_row >= index:
                new_merge["end_row"] = end_row - 1
            new_merges.append(new_merge)

        return [{"columns": new_columns, "merges": new_merges}]


classes = (
    MaStroScheduleSheetRemoveRowNode,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
