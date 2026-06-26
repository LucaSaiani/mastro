"""Shared Sheet-reading logic - the ONE place that knows how to read a
Sheet value (see sockets.py:MaStroScheduleSheetSocket for its
{"columns": [{"cells": [...]}], "merges": [...]} shape), used by both
nodes_viewer.py (to display a Sheet) and excel_export_shared.py (to
write one to .xlsx) - kept in its own neutral module rather than
having the Viewer depend on excel_export_shared.py (or vice versa),
and rather than each keeping its own separate interpretation of the
same shape, which could silently drift apart from each other over
time."""


def sheet_to_table_shape(sheet):
    """A Sheet's own columns are {"cells": [cell, cell, ...]} - a flat
    list, no header/row split (see MaStroScheduleSheetSocket's own
    docstring for why: every position in a Sheet is just an ordinary
    cell). Table's own shape instead expects {"header": {...}, "rows":
    [...]} per column. This converts one into the other - cells[0]
    becomes "header" (still drawn/written at the visual top, same as
    before becoming a Sheet), cells[1:] become "rows" - purely a
    presentational reshaping for code that already knows how to read
    Table's own shape (the Viewer's own _evaluate_table, or
    excel_export_shared.write_sheet), NOT a sign that Sheet itself has
    a header concept again."""
    return {
        "columns": [
            {"header": (column.get("cells") or [{"text": "", "bg": None}])[0],
             "rows": (column.get("cells") or [{}])[1:]}
            for column in sheet.get("columns", [])
        ],
        "merges": sheet.get("merges", []),
    }
