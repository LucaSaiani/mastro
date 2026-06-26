from bpy.types import Node
from bpy.props import EnumProperty, CollectionProperty, IntProperty, StringProperty

from .tree import MaStroScheduleTreeNode, resolve_origin_node, resolve_named_origin
from .execution import update_node, get_node_table
from .properties import MaStro_schedule_join_table_item


def _update_sheet_name(self, context):
    # Mirrors the node's own displayed title to table_or_sheet_name
    # whenever it's non-empty - Node.label (a real, native Blender
    # property, confirmed in rna_nodetree.cc) is shown in the title
    # bar INSTEAD of bl_label once set, exactly the bonus the user
    # asked for: naming a Join Sheets' own combined result also
    # renames the node itself in the editor, not just whatever reads
    # table_or_sheet_name downstream (Export Excel's own _origin_label
    # fallback, see that module's own comment for the other half of
    # this).
    self.label = self.table_or_sheet_name
    update_node(self, context)
    # Confirmed live as a real bug otherwise: update_node() runs
    # tree.execute() directly (recomputing every evaluate(), including
    # any downstream Join Sheets/Export Excel's own), but does NOT go
    # through the polling timer - and _sync_table_items/
    # _sync_sheet_items (the methods that actually copy this label
    # into a downstream node's own table_items/sheet_items, see
    # nodes_table_join.py's/nodes_excel_export.py's own docstrings)
    # only ever run from that timer, never from evaluate(). Without
    # this, a Join Sheets feeding another Join Sheets (or Export
    # Excel) kept showing the OLD label until something else
    # (re-wiring a link) happened to flag the tree for the timer by
    # some other path. See tree.py's own _pending_execute_trees for
    # what this set actually drives.
    from .tree import _pending_execute_trees
    _pending_execute_trees.add(self.id_data.name)


def _link_key(from_node, output_index, link_position):
    """Same stable string identity as Join Tables' own _link_key
    (nodes_table_join.py) - see that function's own docstring,
    including why link_position (this link's own index within
    socket.links) is part of the key now too."""
    return f"{from_node.name}::{output_index}::{link_position}"


def _label_text(sheet):
    """The first column's own first cell text in a Sheet value (see
    sockets.py:MaStroScheduleSheetSocket for the shape) - an empty
    string if there are no columns/cells at all. Purely cosmetic, used
    only to label this node's own ordering UIList - mirrors Join
    Tables' own _header_text (nodes_table_join.py), just reading
    cells[0] instead of a separate header dict, since Sheet has no
    such thing (every position is just a cell, see
    MaStroScheduleSheetSocket's own docstring)."""
    columns = sheet.get("columns", []) if sheet else []
    if not columns:
        return ""
    cells = columns[0].get("cells", [])
    return cells[0].get("text", "") if cells else ""


def _origin_label(origin_node, sheet):
    """origin_node's own table_or_sheet_name takes priority over
    _label_text's first-cell-text fallback - same mechanism as Export
    Excel's own _origin_label/Join Tables' own _origin_label
    (nodes_excel_export.py/nodes_table_join.py). If origin_node itself
    has no name, resolve_named_origin walks FURTHER upstream looking
    for one (e.g. a Join Tables' own table_or_sheet_name, several
    nodes back through Table to Sheet's own type change) - see that
    function's own docstring in tree.py for why this is a separate
    walk from resolve_origin_node's, only for the displayed name,
    never for table_items' own link_key. _label_text's own fallback
    still reads sheet - origin_node's own sheet (the thing
    resolve_origin_node/_link_key are actually keyed by), not whatever
    node resolve_named_origin happened to walk past."""
    custom_name = getattr(origin_node, "table_or_sheet_name", "") or resolve_named_origin(origin_node)
    if custom_name:
        return custom_name
    return _label_text(sheet)


# Combines several Sheet blocks into one, side by side (more columns)
# or stacked (more rows) - the user's own clarification: this node
# absorbs the role originally meant for a separate "Join Sheets" node,
# taking over the "Place in Sheet" name itself (the node that used to
# do a single Table->Sheet conversion kept that simpler role but was
# renamed to Table to Sheet, see nodes_table_sheet.py's own module
# comment for that history). Accepts only Sheet inputs, never Table
# directly - the user's own explicit call, to keep the type boundary
# clean rather than silently converting Table on this node's behalf
# (every Table must go through Table to Sheet first).
#
# Unlike Join Tables (horizontal-only, see nodes_table_join.py's own
# module comment for why), this node supports BOTH directions - Sheet
# has no header to lose/choose between when stacking vertically (the
# entire reason Sheet exists in the first place), so there's no
# equivalent ambiguity here.
#
# Same real Blender multi-input socket (use_multi_input=True),
# reorderable UIList (table_items, reusing the exact same
# MaStro_schedule_join_table_item/MASTRO_UL_schedule_join_tables/
# MASTRO_OT_Schedule_Join_Tables_Move Join Tables already has - nothing
# about that machinery is Table-specific, it just tracks links/labels
# by a generic key), and polling-timer sync (see _sync_table_items'
# own docstring, and tree.py's _poll_pending_trees) as Join Tables -
# all for the exact same reasons documented there.
#
# Mismatched row/column counts between the Sheets being combined are
# padded with blank cells rather than dropped - same "purely graphical,
# no data guarantees" rule Join Tables already follows.
#
# Each Sheet is assumed to already be positioned where the user wants
# it (e.g. via Move Sheet upstream, nodes_sheet_move.py) - this node
# does no translation of its own, it only concatenates whatever
# arrives as-is, in table_items' own order.
class MaStroScheduleSheetPlaceNode(MaStroScheduleTreeNode, Node):
    """Combine several Sheet blocks side by side or stacked, in an
    order set by this node's own list (not by link order)"""
    bl_idname = 'MaStroScheduleSheetPlace'
    bl_label = 'Join Sheets'

    direction: EnumProperty(
        name="Direction",
        items=[
            ('HORIZONTAL', "Horizontal", "Place every Sheet's columns side by side"),
            ('VERTICAL', "Vertical", "Stack every Sheet's cells on top of each other"),
        ],
        default='HORIZONTAL',
        update=update_node,
    )
    table_items: CollectionProperty(type=MaStro_schedule_join_table_item)
    active_table_index: IntProperty()
    # Optional - left blank, this node's own label downstream
    # (Export Excel's own sheet_items, see that node's own
    # _sync_sheet_items) falls back to the first cell text found in
    # whichever linked Sheet happens to be first, which reads as
    # meaningless for a node whose whole job is combining several
    # Sheets into one ("(empty)" in the user's own screenshot, the
    # exact case this exists to fix) - set once, it names the combined
    # result itself, not any one of the Sheets that went into it.
    table_or_sheet_name: StringProperty(name="Sheet Name", update=_update_sheet_name)

    def init(self, context):
        # use_multi_input is a constructor-only argument - see Join
        # Tables' own init() for the confirmed RNA source detail.
        self.inputs.new('MaStroScheduleSheetSocketType', "Sheet", use_multi_input=True)
        self.inputs.new('MaStroScheduleStringSocketType', "Sheet Name").prop_name = "table_or_sheet_name"
        self.outputs.new('MaStroScheduleSheetSocketType', "Sheet")

    def _sync_table_items(self):
        """Same sync logic as Join Tables' own _sync_table_items
        (nodes_table_join.py) - see that method's own docstring. Must
        NOT be called from draw_buttons (same "Writing to ID classes in
        this context is not allowed" restriction, confirmed live there
        first) - runs from tree.py's own polling timer instead."""
        socket = self.inputs["Sheet"]
        current_keys = []
        labels_by_key = {}
        for link_position, link in enumerate(socket.links):
            # Same "disappears entirely" treatment as Join Tables' own
            # _sync_table_items (nodes_table_join.py) - see that
            # method's own comment for why.
            if link.is_muted:
                continue
            # Both the KEY and the LABEL come from resolve_origin_node
            # (walks back through any transparent single-input
            # Table/Sheet operator - Move Sheet, Sheet Background, ... -
            # to the real origin), not resolve_through_reroutes - same
            # identity fix, same reasoning, as Join Tables' own
            # _sync_table_items (nodes_table_join.py) - see that
            # method's own comment, and resolve_origin_node's own
            # docstring in tree.py, for the full story/bug this fixes.
            origin_node, origin_socket = resolve_origin_node(link)
            if origin_node is None:
                continue
            try:
                output_index = list(origin_node.outputs).index(origin_socket)
            except ValueError:
                continue
            key = _link_key(origin_node, output_index, link_position)
            current_keys.append(key)
            sheet = get_node_table(self.id_data.name, origin_node.name)
            labels_by_key[key] = _origin_label(origin_node, sheet[output_index] if sheet else None)

        existing_keys = [item.link_key for item in self.table_items]
        for index in reversed(range(len(self.table_items))):
            if existing_keys[index] not in current_keys:
                self.table_items.remove(index)
        tracked_keys = {item.link_key for item in self.table_items}
        for key in current_keys:
            if key not in tracked_keys:
                item = self.table_items.add()
                item.link_key = key
                tracked_keys.add(key)
        for item in self.table_items:
            item.label = labels_by_key.get(item.link_key, "")

    def draw_buttons(self, context, layout):
        # Same layout as Join Tables' own draw_buttons - see that
        # method's own comment for why expand=True has no text= here,
        # and why the move buttons sit in their own column next to the
        # list, not stacked below it.
        layout.row(align=True).prop(self, "direction", expand=True)
        row = layout.row()
        row.template_list(
            "MASTRO_UL_schedule_join_tables", "", self, "table_items", self, "active_table_index", rows=4,
        )
        col = row.column(align=True)
        op = col.operator("mastro_schedule.join_tables_move", icon='TRIA_UP', text="")
        op.node_name = self.name
        op.direction = 'UP'
        op = col.operator("mastro_schedule.join_tables_move", icon='TRIA_DOWN', text="")
        op.node_name = self.name
        op.direction = 'DOWN'

    @staticmethod
    def _cell_count(sheet):
        columns = sheet.get("columns", [])
        if not columns:
            return 0
        return max(len(column.get("cells", [])) for column in columns)

    @staticmethod
    def _blank_cell():
        return {"text": "", "bg": None}

    def _place_horizontal(self, sheets):
        """Side by side: every Sheet's own columns appended in order,
        each column's cell list padded with blank cells up to the
        tallest Sheet in the join - same shape as Join Tables' own
        _join_horizontal, just reading "cells" instead of "rows"."""
        cell_count = max((self._cell_count(s) for s in sheets), default=0)
        columns = []
        for sheet in sheets:
            for column in sheet.get("columns", []):
                cells = list(column.get("cells", []))
                cells.extend(self._blank_cell() for _ in range(cell_count - len(cells)))
                columns.append({"cells": cells})
        return {"columns": columns, "merges": []}

    def _place_vertical(self, sheets):
        """Stacked: every Sheet's own cells appended in order, padding
        with extra blank columns first if a later Sheet has more
        columns than the ones already stacked - so the result always
        has as many columns as the WIDEST Sheet in the join, and every
        column ends up the same total height. Unlike Join Tables'
        never-built vertical case, there is no header to lose here -
        every Sheet's own former header (now just cells[0]) simply
        becomes an ordinary cell in the middle of the stack, exactly
        where it falls - the entire reason Sheet exists."""
        column_count = max((len(s.get("columns", [])) for s in sheets), default=0)
        merged_columns = [{"cells": []} for _ in range(column_count)]
        for sheet in sheets:
            sheet_columns = sheet.get("columns", [])
            this_cell_count = self._cell_count(sheet)
            for index in range(column_count):
                if index < len(sheet_columns):
                    cells = list(sheet_columns[index].get("cells", []))
                else:
                    cells = []
                cells.extend(self._blank_cell() for _ in range(this_cell_count - len(cells)))
                merged_columns[index]["cells"].extend(cells)
        return {"columns": merged_columns, "merges": []}

    def evaluate(self, inputs):
        # inputs[0] is a LIST here, not a single Sheet - see Join
        # Tables' own evaluate() for why (the Sheet input is
        # multi-input, execution.py:eval_node resolves it into a list).
        sheets_by_key = {}
        socket = self.inputs["Sheet"]
        for link_position, (link, value) in enumerate(zip(socket.links, inputs[0] or [])):
            # Same "disappears entirely" treatment as Join Tables' own
            # evaluate() (nodes_table_join.py) - see that method's own
            # comment for why.
            if link.is_muted:
                continue
            # Same identity resolution as _sync_table_items' own key -
            # see that method's own comment, and resolve_origin_node's
            # own docstring, for why.
            origin_node, origin_socket = resolve_origin_node(link)
            if origin_node is None:
                continue
            try:
                output_index = list(origin_node.outputs).index(origin_socket)
            except ValueError:
                continue
            sheets_by_key[_link_key(origin_node, output_index, link_position)] = value or {"columns": [], "merges": []}

        ordered_keys = [item.link_key for item in self.table_items if item.link_key in sheets_by_key]
        for key in sheets_by_key:
            if key not in ordered_keys:
                ordered_keys.append(key)
        sheets = [sheets_by_key[key] for key in ordered_keys]

        if not sheets:
            return [{"columns": [], "merges": []}]
        if self.direction == 'HORIZONTAL':
            return [self._place_horizontal(sheets)]
        return [self._place_vertical(sheets)]
