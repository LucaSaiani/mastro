"""Shared helpers for Hide Zero/Cell Prefix-Suffix/Cell Case/Cell Align
(nodes_table_hide_zero.py/nodes_table_prefix_suffix.py/nodes_table_case.py/
nodes_table_align.py) - four separate nodes, each one operation on a
Table's column(s), the user's own explicit call over a single generic
"Edit Rows" node with a dropdown: "ogni operazione è un nodo diverso",
same "one node, one job" convention as Math/Aggregate/Flatten Key
elsewhere in this tree.

All four take the same Start Column Index/End Column Index range
instead of a single Column Index - the user's own generalization:
Start==End means exactly one column (the common case), Start<End
applies the same operation to every column in that inclusive range in
one node instead of needing one node per column. Labelled "Start/End
COLUMN Index", not just "Start/End Index" - the user's own follow-up
clarification, to make clear at a glance which axis this range covers
(every one of these nodes works on columns, never rows). Align uses
column_range directly (it sets text_align, not each row's own "text");
the other three go through map_table_rows.
"""


def resolve_index(socket, value_in, fallback):
    """Same "unlinked socket always comes through as None" handling as
    Rename Header/Math/Edit Header's own Column Index - fall back to the
    inline field's own backing property explicitly when unlinked, rather
    than assuming the input holds it."""
    if not socket.is_linked:
        return fallback
    if isinstance(value_in, str):
        return int(value_in) if value_in else fallback
    rows_in = value_in or []
    if not rows_in:
        return fallback
    row_key = next((k for k in rows_in[0] if not k.startswith("_")), None)
    return int(rows_in[0].get(row_key, fallback)) if row_key else fallback


def column_range(table, start_index, end_index):
    """The (start, end) column indices to actually edit, clamped to the
    Table's real column count and to start<=end (a End Index dragged
    below Start Index - confirmed not prevented by Blender's own min=
    alone once Start Index is raised past it live - silently swaps back
    to a same-as-start, single-column range rather than editing nothing
    or raising)."""
    columns = table.get("columns", [])
    if not columns:
        return None
    end_index = max(start_index, end_index)
    start_index = max(0, start_index)
    end_index = min(len(columns) - 1, end_index)
    if start_index > end_index:
        return None
    return start_index, end_index


def map_table_rows(table, start_index, end_index, transform):
    """Returns a new Table value with `transform(text)` applied to every
    row's "text" in columns start_index..end_index (inclusive) - merges
    untouched (a merge spans whole rows of columns, not cleanly
    addressable by a column sub-range the same way; editing merge text
    is Edit Header's own job, not these nodes')."""
    bounds = column_range(table, start_index, end_index)
    if bounds is None:
        return table
    start_index, end_index = bounds

    columns = table.get("columns", [])
    new_columns = list(columns)
    for index in range(start_index, end_index + 1):
        target = columns[index]
        new_rows = [{**row, "text": transform(row.get("text", ""))} for row in target.get("rows", [])]
        new_columns[index] = {**target, "rows": new_rows}

    return {"columns": new_columns, "merges": table.get("merges", [])}
