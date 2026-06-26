from bpy.types import Node
from bpy.props import IntProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node, is_socket_active


# Moves a Sheet by INSERTING blank cells/columns ahead of it - never by
# subtracting or shifting existing content out, the user's own explicit
# design for how Sheet "movement" works at all: "di fatto aggiunge
# celle vuote, ampliando la dimensione della tabella... per fare in
# negativo, tipo spostare in su, lo si fa spostando in giù (aggiungendo
# righe vuote) l'altra tabella" - i.e. there is no real negative offset
# anywhere in this system; "moving A up relative to B" is done by
# moving B down instead, never by giving A a negative Row Offset (this
# node's own min=0 enforces that there's nothing to misuse here).
#
# Row Offset/Column Offset are independent - both at once moves
# diagonally in one node, the user's own explicit call (a single node
# with two offsets, rather than two separate horizontal/vertical move
# nodes) to avoid needing two chained nodes for a diagonal move.
#
# Inserted cells are always transparent (bg=None) - same convention as
# Place in Sheet's own padding cells (nodes_sheet_place.py) in this
# same Sheet world, and Join Tables' own padding cells
# (nodes_table_join.py) in the separate Table world - the user's own
# reversal of an earlier call ("aggiungi il background anche qui"): a
# per-node Background Colour was useful as a visual guide for an
# otherwise-invisible move, but left every node that inserts padding
# cells disagreeing about their color, making "is this cell padding or
# real content" impossible to tell at a glance. Use Sheet Background
# (nodes_sheet_background.py) right after this node instead for the
# same visual-guide effect, with every kind of Sheet padding cell
# (Move Sheet's own, or Place in Sheet's) uniformly colorable in one
# place: it colors every cell still at bg=None, exactly what this node
# (and Place in Sheet) always leave behind.
#
# Existing merges are translated along with everything else (their
# start_row/start_col/end_row/end_col coordinates shift by the same
# offsets) - the user's own explicit anticipation of this need before
# this node was even built: "comunque sarà necessario traslare le
# coordinate delle celle" once any node moves a Sheet's content around.
class MaStroScheduleSheetMoveNode(MaStroScheduleTreeNode, Node):
    """Move a Sheet by inserting blank rows/columns ahead of it"""
    bl_idname = 'MaStroScheduleSheetMove'
    bl_label = 'Move Sheet'

    # Backing values for every inline field below (NodeSocket.prop_name,
    # same mechanism as Sheet Primitive's own column_count/row_count) -
    # editable directly on the socket while unlinked, read from the
    # actual linked node's output instead once something is plugged in.
    # min=0, not allowing negative offsets at all - see this class's own
    # module comment for why there's no such thing as a negative move
    # in this system.
    row_offset: IntProperty(name="Row Offset", default=0, min=0, update=update_node)
    column_offset: IntProperty(name="Column Offset", default=0, min=0, update=update_node)

    def init(self, context):
        self.inputs.new('MaStroScheduleSheetSocketType', "Sheet")
        self.inputs.new('MaStroScheduleColumnSocketType', "Row Offset").prop_name = "row_offset"
        self.inputs.new('MaStroScheduleColumnSocketType', "Column Offset").prop_name = "column_offset"
        self.outputs.new('MaStroScheduleSheetSocketType', "Sheet")

    @staticmethod
    def _resolve_count(socket, rows_in, fallback):
        # Same resolution shape as Sheet Primitive's own _resolve_count.
        if not is_socket_active(socket):
            return fallback
        rows_in = rows_in or []
        if not rows_in:
            return 0
        row_key = next((k for k in rows_in[0] if not k.startswith("_")), None)
        return int(rows_in[0].get(row_key, 0)) if row_key else 0

    def evaluate(self, inputs):
        sheet = inputs[0] or {"columns": [], "merges": []}
        # No clamping beyond min=0 on the properties (UI-only, same as
        # every other primitive's own _resolve_count) - a negative
        # value reaching here through a linked socket on purpose is
        # used as-is, same "the user's own call" rule Table Primitive's
        # column_count/row_count already follow.
        row_offset = self._resolve_count(self.inputs["Row Offset"], inputs[1], self.row_offset)
        column_offset = self._resolve_count(self.inputs["Column Offset"], inputs[2], self.column_offset)

        existing_columns = sheet.get("columns", [])
        row_count = max((len(c.get("cells", [])) for c in existing_columns), default=0) + row_offset

        def blank_cell():
            # Always transparent - see this class's own module comment
            # for why (Sheet Background is the dedicated tool for
            # coloring this afterward, not this node).
            return {"text": "", "bg": None}

        moved_columns = []
        # column_offset blank columns inserted AHEAD of every existing
        # one - each as tall as the moved result ends up being (every
        # column in a Sheet must stay the same height, the same
        # invariant Join Tables' own horizontal join already
        # maintains).
        for _ in range(column_offset):
            moved_columns.append({"cells": [blank_cell() for _ in range(row_count)]})
        for column in existing_columns:
            cells = [blank_cell() for _ in range(row_offset)]
            cells.extend(column.get("cells", []))
            moved_columns.append({"cells": cells})

        moved_merges = []
        for merge in sheet.get("merges", []):
            moved_merges.append({
                **merge,
                "start_row": merge.get("start_row", 0) + row_offset,
                "start_col": merge.get("start_col", 0) + column_offset,
                "end_row": merge.get("end_row", 0) + row_offset,
                "end_col": merge.get("end_col", 0) + column_offset,
            })

        return [{"columns": moved_columns, "merges": moved_merges}]
