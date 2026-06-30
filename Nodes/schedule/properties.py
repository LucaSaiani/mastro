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
    # Set on a header cell by Edit Header/Table primitive; on a row cell
    # by Cell Align (nodes_table_align.py) - both write the same field
    # on this shared PropertyGroup.
    text_align: StringProperty(name="Text Align", default="LEFT")


class MaStro_schedule_table_column(PropertyGroup):
    """One column of a Viewer Table - a header cell plus its own
    positional list of row cells, independent of every other column's
    row count (see the module-level comment above
    sockets.py:MaStroScheduleTableSocket for why Table columns don't
    share row identity)."""
    header: PointerProperty(type=MaStro_schedule_table_cell)
    rows: CollectionProperty(type=MaStro_schedule_table_cell)


class MaStro_schedule_join_table_item(PropertyGroup):
    """One entry in Join Tables' own ordering UIList
    (nodes_table_join.py) - one per Table currently linked into its
    multi-input socket. link_key identifies WHICH link this entry
    tracks (not the link object itself - NodeLink isn't a stable
    Python identity across redraws/undo the way this needs), so the
    list can be re-synced against the socket's actual links (from
    tree.py's own polling timer, see _sync_table_items's own docstring
    for why not from draw_buttons) without losing the user's own
    custom ordering when nothing about the links themselves changed.
    label is purely cosmetic - the
    first header text found in that Table, stored as an empty string
    if it has none (the UIList itself, not this PropertyGroup, is what
    shows "(empty)" for that case - see
    MASTRO_UL_schedule_join_tables.draw_item in operators.py), shown
    read-only in the list so the user can tell which entry is which."""
    link_key: StringProperty()
    label: StringProperty(name="Table")


class MaStro_schedule_group_by_item(PropertyGroup):
    """One entry in Aggregate's own group-by ordering UIList
    (nodes_aggregate_column.py) - one per Id Key OR Attribute Name
    currently linked into its two separate multi-input sockets (kept
    as two real sockets, not one generic Any socket, for simpler
    validation - the user's own explicit call), merged into ONE
    ordered list here so Id Keys and Attributes can be freely
    interleaved (e.g. group by Floor then Use, or Use then Floor -
    the user's own explicit ask: which order they're wired/listed in
    changes the grouping's own nesting order, like a multi-column
    Excel pivot).

    kind ('KEY' or 'ATTRIBUTE') says which of the two sockets this
    entry came from, since link_key alone (see
    MaStro_schedule_join_table_item's own docstring for why link
    identity needs a stable string, not the NodeLink object itself)
    isn't enough to tell them apart once merged into one list - the
    two sockets' own links are independently numbered, so a KEY entry
    and an ATTRIBUTE entry can share the same link_position by
    coincidence."""
    kind: StringProperty()
    link_key: StringProperty()
    label: StringProperty(name="Group By")


class MaStro_schedule_export_sheet_item(PropertyGroup):
    """One entry in Export Excel's own ordering UIList
    (nodes_excel_export.py) - one per Sheet currently linked into its
    multi-input socket. Deliberately NOT MaStro_schedule_join_table_item
    (the same-shaped PropertyGroup Join Tables/Join Sheets already
    share) - the user's own explicit call: those two nodes have no use
    for update_mode/start_cell, so giving them those fields anyway just
    to reuse one PropertyGroup would leave dead properties sitting on
    unrelated nodes. link_key/label work exactly like Join Tables' own
    table_items (see that PropertyGroup's own docstring) - the rest are
    this node's own per-Sheet export settings, editable directly in the
    UIList (see MASTRO_UL_schedule_export_sheets.draw_item in
    operators.py)."""
    link_key: StringProperty()
    # The actual Excel sheet name written by export_sheets()
    # (nodes_excel_export.py) - no separate editable sheet_name field
    # here anymore (the user's own explicit removal, once Table to
    # Sheet/Join Tables/Join Sheets all gained their own
    # table_or_sheet_name): renaming happens once, upstream, at
    # whichever node produced/combined this Sheet, not a second time on
    # this list too. Falls back to "Sheet {N}" (this entry's own
    # 1-based position) if even that's blank.
    label: StringProperty(name="Sheet")
    # Off (the default): REPLACE - the existing sheet (if the workbook
    # being written to already has one with this name) is wiped
    # entirely before writing. On: UPDATE - only the rectangle at
    # row>=start_cell's row AND column>=start_cell's column is cleared
    # first - the user's own explicit design, to let an Excel sheet
    # keep its own pre-existing content above/to the left of where
    # this export writes (e.g. a title block or notes column the user
    # added by hand in Excel itself, never touched by this node).
    # Reworked from an EnumProperty into this single boolean - the
    # user's own explicit call, so the UIList can simply disable
    # start_cell (rather than hide/show it) when this is off, with one
    # custom toggle icon instead of a dropdown (see this PropertyGroup's
    # own update_icon class var note in operators.py's draw_item).
    update_mode: BoolProperty(name="Update", default=False)
    # An Excel-style cell reference (e.g. "B3") - only read (and only
    # editable in the UIList) when update_mode is on. Validated/parsed
    # by nodes_excel_export.py's own _parse_cell_ref, not here (a
    # PropertyGroup string field has no
    # validation hook of its own worth using for this).
    start_cell: StringProperty(name="Start Cell", default="A1")


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
