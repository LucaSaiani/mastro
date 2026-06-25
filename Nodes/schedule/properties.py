from bpy.types import PropertyGroup
from bpy.props import (
    StringProperty, CollectionProperty, BoolProperty, IntProperty,
    FloatVectorProperty, PointerProperty,
)


class MaStro_schedule_key_item(PropertyGroup):
    """One column name used by the Group By node"""
    name: StringProperty(name="Column")


class MaStro_schedule_cell(PropertyGroup):
    """One cell of a Viewer table row"""
    name: StringProperty(name="Column")
    value: StringProperty(name="Value")


class MaStro_schedule_row(PropertyGroup):
    """One row of a Viewer table"""
    cells: CollectionProperty(type=MaStro_schedule_cell)
    is_subtotal: BoolProperty(name="Subtotal", default=False)
    level: IntProperty(name="Level", default=0)


class MaStro_schedule_table_cell(PropertyGroup):
    """One cell of a Viewer Table column (either its header or one of its
    rows) - separate from MaStro_schedule_cell, which is keyed by column
    name (a Column/Data row is a flat dict); a Table cell instead just
    holds its own text/style, positional within its column's own list."""
    text: StringProperty(name="Text")
    # bg/text_color: set on a header cell by Edit Header
    # (nodes_table_edit_header.py); row cells have these too (shared
    # PropertyGroup) but nothing writes them on a row yet - unused there
    # until a node that edits row style exists. Stored as plain RGB
    # triplets rather than reusing bpy.types.Theme color types, since
    # there's no upstream theme value to assign them from.
    has_bg: BoolProperty(name="Has Background Override", default=False)
    bg: FloatVectorProperty(name="Background", subtype='COLOR', size=3, default=(0.0, 0.0, 0.0))
    has_text_color: BoolProperty(name="Has Text Color Override", default=False)
    text_color: FloatVectorProperty(name="Text Color", subtype='COLOR', size=3, default=(1.0, 1.0, 1.0))
    # No has_text_align flag, unlike bg/text_color above - LEFT is
    # already this Viewer's existing default behavior (the fixed 4px
    # inset from the cell's left edge every cell used before alignment
    # existed at all), so there's no separate "unset" state to track.
    text_align: StringProperty(name="Text Align", default="LEFT")


class MaStro_schedule_table_column(PropertyGroup):
    """One column of a Viewer Table - a header cell plus its own
    positional list of row cells, independent of every other column's
    row count (see the module-level comment above
    sockets.py:MaStroScheduleTableSocket for why Table columns don't
    share row identity)."""
    header: PointerProperty(type=MaStro_schedule_table_cell)
    rows: CollectionProperty(type=MaStro_schedule_table_cell)


class MaStro_schedule_table_merge(PropertyGroup):
    """One merged-cell region of a Viewer Table (see the module-level
    comment above sockets.py:MaStroScheduleTableSocket) - row/column
    coordinates plus its own cell content, the same shape a future Excel
    export would feed straight into openpyxl/xlsxwriter's own
    merge_cells(). Reuses MaStro_schedule_table_cell for content (text/
    bg/text_color) rather than duplicating those fields here."""
    start_row: IntProperty(default=0)
    start_col: IntProperty(default=0)
    end_row: IntProperty(default=0)
    end_col: IntProperty(default=0)
    cell: PointerProperty(type=MaStro_schedule_table_cell)
