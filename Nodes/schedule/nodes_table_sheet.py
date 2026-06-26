from bpy.types import Node
from bpy.props import StringProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node


def _update_table_or_sheet_name(self, context):
    # Same Node.label rename, and same explicit
    # _pending_execute_trees flag, as Join Tables/Join Sheets' own
    # _update_table_name/_update_sheet_name (nodes_table_join.py/
    # nodes_sheet_place.py) - see those functions' own docstrings.
    self.label = self.table_or_sheet_name
    update_node(self, context)
    from .tree import _pending_execute_trees
    _pending_execute_trees.add(self.id_data.name)


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
# (horizontally or vertically) is Join Sheets' own job
# (nodes_sheet_place.py), not this one's. Originally named "Place in
# Sheet" itself, before that name and its single-Table shape were
# reassigned to the new multi-input combining node (now called Join
# Sheets) instead - this one kept the simpler single-conversion role
# and took the more literal "Table to Sheet" name to match.
class MaStroScheduleTableSheetNode(MaStroScheduleTreeNode, Node):
    """Convert one Table into an opaque Sheet block - its header
    becomes an ordinary cell, and Cells/Header nodes can no longer
    connect to it past this point"""
    bl_idname = 'MaStroScheduleTableToSheet'
    bl_label = 'Table to Sheet'

    # Optional - same shared name property as Join Tables/Join Sheets
    # (table_or_sheet_name, see resolve_named_origin's own docstring in
    # tree.py for why it's ONE shared attribute name rather than a
    # separate one per node type) - the user's own follow-up: naming
    # the Sheet right here, at the Table->Sheet boundary, means Export
    # Excel's own sheet_items never need a name typed in a second time
    # downstream - this node's own name (if set) is what
    # resolve_named_origin finds first when walking upstream from
    # wherever this Sheet eventually ends up.
    table_or_sheet_name: StringProperty(name="Sheet Name", update=_update_table_or_sheet_name)

    def init(self, context):
        self.inputs.new('MaStroScheduleTableSocketType', "Table")
        self.inputs.new('MaStroScheduleStringSocketType', "Sheet Name").prop_name = "table_or_sheet_name"
        self.outputs.new('MaStroScheduleSheetSocketType', "Sheet")

    def evaluate(self, inputs):
        table = inputs[0] or {"columns": [], "merges": []}
        columns = []
        for column in table.get("columns", []):
            cells = [column.get("header", {"text": "", "bg": None})]
            cells.extend(column.get("rows", []))
            columns.append({"cells": cells})
        return [{"columns": columns, "merges": table.get("merges", [])}]
