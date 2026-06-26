from bpy.types import Node

from .tree import MaStroScheduleTreeNode


# The boundary between Table (header/rows split, still editable by any
# Cells/Header node - Edit Cell, Row Colour, Edit Header, ...) and Sheet
# (no header concept at all, opaque from here on - see sockets.py:
# MaStroScheduleSheetSocket for the full shape/story). Table to Sheet
# actually RESTRUCTURES the data, unlike a pure type-change boundary -
# each column's separate "header"/"rows" becomes one flat "cells" list
# (header first, then every row, in that order) - the user's own
# explicit correction: "per sheet tutto è cell, non ci sono headers".
# Merges pass through unchanged - Sheet only erases the header/row
# DISTINCTION, not row 0's still-meaningful position as the visual top
# (a merge spanning row 0 still spans what's now cells[0], same
# coordinates as before). No position/offset inputs here, and no
# multi-input either - this node converts exactly ONE Table at a time;
# combining several already-converted Sheet blocks together
# (horizontally or vertically) is Place in Sheet's own job
# (nodes_sheet_place.py), not this one's. Originally named "Place in
# Sheet" itself, before that name and its single-Table shape were
# reassigned to the new multi-input combining node instead - this one
# kept the simpler single-conversion role and took the more literal
# "Table to Sheet" name to match.
class MaStroScheduleTableSheetNode(MaStroScheduleTreeNode, Node):
    """Convert one Table into an opaque Sheet block - its header
    becomes an ordinary cell, and Cells/Header nodes can no longer
    connect to it past this point"""
    bl_idname = 'MaStroScheduleTableToSheet'
    bl_label = 'Table to Sheet'

    def init(self, context):
        self.inputs.new('MaStroScheduleTableSocketType', "Table")
        self.outputs.new('MaStroScheduleSheetSocketType', "Sheet")

    def evaluate(self, inputs):
        table = inputs[0] or {"columns": [], "merges": []}
        columns = []
        for column in table.get("columns", []):
            cells = [column.get("header", {"text": "", "bg": None})]
            cells.extend(column.get("rows", []))
            columns.append({"cells": cells})
        return [{"columns": columns, "merges": table.get("merges", [])}]
