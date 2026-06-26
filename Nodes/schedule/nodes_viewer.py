import colorsys

import bpy
import blf
import gpu
from gpu_extras.batch import batch_for_shader
from bpy.types import Node
from bpy.props import CollectionProperty, BoolProperty, IntProperty

from .tree import MaStroScheduleTreeNode
from .properties import (
    MaStro_schedule_key_item, MaStro_schedule_row, MaStro_schedule_table_column, MaStro_schedule_table_merge,
)
from .execution import tag_redraw_node_editors
from ...Utils.mastro_preferences.get_preferences import get_prefs
from ... import Icons as icons


CELL_WIDTH = 120
# Used by _draw_table_overlay (Table) only - _draw_node_table
# (Column/List) uses COLUMN_NODE_GAP below instead, the user's own call:
# the visible empty strip this left between the node and its own
# overlay read as wrong specifically for Column/List, not for Table.
NODE_GAP = 4
COLUMN_NODE_GAP = 0
# Row numbers in a Table overlay (_draw_table_overlay) never go past two
# digits in practice (see that function's reasoning) - "0" sets a flat,
# content-independent width for that left-hand band, shared with
# _draw_node_table's identical margin so a Viewer's grid doesn't shift
# sideways when replugged between a Column/Data input and a Table one.
# Single digit rather than two - the user's call: a two-row-number-wide
# margin read as too wide, even though an actual two-digit row number
# will end up slightly overflowing this band's left edge as a result
# (an accepted trade-off, same shape as row_label_width itself already
# being a flat allowance rather than sized to the real row count).
ROW_LABEL_TEXT = "0"


def _row_label_width(font_id):
    """blf.dimensions reads whatever size was last set on font_id via
    blf.size() - callers must call that first, same as before any other
    blf.dimensions call in this file."""
    return blf.dimensions(font_id, ROW_LABEL_TEXT)[0] + 8


def _header_text(name):
    """Capitalize a column header's first letter for display, and -
    for an id key (e.g. "_Object", "_Face") - strip the leading "_" and
    append "_id" (so "_Object" reads "Object_id") - the user's own call:
    leading-underscore "_Object" reads as an internal implementation
    detail, "Object_id" reads as what it actually is, a stable row
    identity rather than a regular data value. The underlying column
    name/key stays exactly as-is everywhere else (data, lookups, joins)
    - this only affects what's drawn here and in nodes_id_keys.py's own
    Get Id Keys picker, which calls this same function for the same
    reason."""
    if not name:
        return name
    if name.startswith("_"):
        return name[1:] + "_id"
    return name[:1].upper() + name[1:]


def _cell_text(value):
    """Same str() every cell value already went through, except a float
    is formatted to 2 decimal places first - plain str(float) shows
    IEEE754's own binary-representation noise (e.g. 0.3 typed into a
    Value node coming back as "0.299999999999999989..."), not a problem
    with the user's own data, just how Python's float repr works. The
    underlying value itself is untouched (no rounding happens to
    anything actually used in a calculation) - this only formats what's
    drawn here."""
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def _srgb_color(*channels):
    """No-op: kept as the single place every color in this file passes
    through before reaching the shader. An earlier version of this
    function pre-applied an sRGB->linear conversion, reasoning that
    gpu.shader.from_builtin('UNIFORM_COLOR') doesn't correctly convert
    colors back for display - but checking Blender's actual shader
    source (gpu_shader_uniform_color_frag.glsl ->
    blender_srgb_to_framebuffer_space(), gpu_shader_colorspace_lib.glsl)
    shows the GPU already performs exactly that sRGB->linear conversion
    itself when the framebuffer needs it (`srgbTarget`), and is a no-op
    otherwise - applying the same conversion again in Python double-
    counts it, which is what was making rgb(130, 53, 76) actually
    render as something like rgb(113, 17, 36), confirmed by the user
    reading the on-screen color back. The right answer is to hand the
    shader the plain requested RGB values, unmodified."""
    return channels


def _hsv_variant(rgb, saturation_delta=0.0, value_delta=0.0):
    """Derive a paler/brighter variant of an RGB color by nudging its
    HSV saturation/value - the same technique the old prototype used
    (mastro_schedule.py's hand-rolled rgb_to_hsv/hsv_to_rgb, here via
    Python's standard colorsys instead of reimplementing the math) to
    get a header color from the theme's input_node color. A flat linear
    blend toward white (the first version of this code did
    `c + (1-c)*factor` per channel) shifts both saturation AND value at
    once in a way that doesn't match how Blender's own color variants
    (or the human eye) read as "paler" - HSV lets each be controlled
    on its own axis."""
    h, s, v = colorsys.rgb_to_hsv(*rgb)
    s = min(1.0, max(0.0, s + saturation_delta))
    v = min(1.0, max(0.0, v + value_delta))
    return colorsys.hsv_to_rgb(h, s, v)

_draw_handler = None


def _on_show_table_changed(self, context):
    tag_redraw_node_editors()


class MaStroScheduleViewerNode(MaStroScheduleTreeNode, Node):
    """Display the incoming table as a grid in the node's side panel, and
    optionally as an overlay table drawn next to the node in the node
    editor"""
    bl_idname = 'MaStroScheduleViewer'
    bl_label = 'Viewer'

    columns: CollectionProperty(type=MaStro_schedule_key_item)
    rows: CollectionProperty(type=MaStro_schedule_row)
    # Populated instead of columns/rows when the linked input is a Table
    # (MaStroScheduleTableSocketType) - a Table's shape (a list of
    # independent columns, each with its own header/row cells and no
    # shared row identity, see sockets.py) doesn't fit columns/rows'
    # flat-dict-row model, so it gets its own storage and its own draw
    # path (_draw_table_overlay) entirely, rather than forcing one shape
    # into the other's schema.
    table_columns: CollectionProperty(type=MaStro_schedule_table_column)
    # Merged-cell regions of the same Table (see sockets.py:
    # MaStroScheduleTableSocket's module-level comment) - drawn after
    # every normal cell, on top, by _draw_table_overlay.
    table_merges: CollectionProperty(type=MaStro_schedule_table_merge)
    # Which of the two storages above is actually populated by the last
    # evaluate() - read by the draw callback to pick which overlay
    # function to call, since a Viewer can be replugged from a Column to
    # a Table input (or vice versa) without re-running init().
    showing_table: BoolProperty(default=False)
    # Set when the linked input is a List (Group Into List's own output,
    # see nodes_groupby_column.py) - both this and showing_table False
    # means "showing a plain Column", the only case the Show Id Columns
    # toggle below actually does anything for (see that property's own
    # comment for why Table's collapsed/expanded id columns has no
    # equivalent concept for a List either - "Key"/"Rows" are two fixed
    # columns, not a variable-length run of id columns to collapse).
    showing_list: BoolProperty(default=False)
    show_table: BoolProperty(name="Show Table", default=True, update=_on_show_table_changed)
    # Number of leading id columns (Object, and one of Face/Edge/Vertex/
    # Level) among `columns`, computed in evaluate() - used by
    # _draw_node_table to color those differently from the actual data
    # column(s) that follow.
    id_column_count: IntProperty()
    # Collapses the leading id columns (Object/Face/Edge/Vertex/Level) to
    # a single thin placeholder column in the overlay - useful once the
    # data column is the only thing of interest and the id columns are
    # just taking up space. Toggled by the FORWARD/BACK button in
    # draw_buttons. Defaults to collapsed (False) - the data column is
    # what the user is after most of the time, id columns are extra
    # context shown on demand.
    show_id_columns: BoolProperty(name="Show Id Columns", default=False, update=_on_show_table_changed)
    # Caps how many rows the overlay draws (0 = no cap, show every row) -
    # set from the "Visible Rows" preference when this node is created
    # (init(), below), not as this property's own `default`: a property
    # default is evaluated once at class-registration time, before
    # preferences are even loadable, so it can't reflect the user's
    # current preference value the way init() reading it per-instance can.
    visible_rows: IntProperty(
        name="Visible Rows",
        min=0,
        default=0,
        description="Maximum number of rows to show in the table overlay. 0 shows every row",
        update=_on_show_table_changed,
    )

    def init(self, context):
        self.inputs.new('MaStroScheduleAnySocketType', "Data")
        self.visible_rows = get_prefs().schedule_visible_rows

    def evaluate(self, inputs):
        # A single MaStroScheduleAnySocketType input, accepting Data,
        # Column, Attribute or Table alike (see that socket's docstring in
        # sockets.py) - the Viewer has to work for whatever a node
        # happens to output, not be limited to one specific shape.
        from .tree import resolve_through_reroutes
        socket = self.inputs[0]
        from_node, from_socket = (None, None)
        if socket.is_linked and socket.links:
            from_node, from_socket = resolve_through_reroutes(socket.links[0])
        if from_node is not None and from_socket.bl_idname == 'MaStroScheduleTableSocketType':
            self._evaluate_table(inputs[0] or {"columns": [], "merges": []})
            self.showing_table = True
            self.showing_list = False
            return []
        self.showing_table = False

        # A List (Group Into List's own output, see nodes_groupby_column.py)
        # has no flat-dict-row shape at all - each element is {"key": ...,
        # "rows": [...]}, the rows themselves still full Column rows, not
        # meant to be flattened/dumped raw into the grid below (confirmed
        # live: doing nothing here showed Python repr() text for "Rows",
        # unreadable). Reused as an ordinary 2-column table instead of a
        # dedicated storage/draw path the way Table got (_evaluate_table/
        # _draw_table_overlay) - the user's own call: just Key + a row
        # COUNT is enough here, drilling into a group's actual rows is
        # already Item from List's job, not the Viewer's.
        if from_node is not None and from_socket.bl_idname == 'MaStroScheduleListSocketType':
            groups = inputs[0] or []
            self.showing_list = True
            # "Key" colored the SAME as "Rows" (the data color), not the
            # id color a Column's own id columns get - the user's own
            # reversal of an earlier call: the id color visually implies
            # "this is part of a collapsible run of id columns", but a
            # List's expand/collapse toggle is deliberately hidden (see
            # draw_buttons' has_extra_id_columns check) - showing the id
            # color anyway would be a false promise of an interaction
            # that doesn't exist here.
            self.id_column_count = 0
            self.columns.clear()
            self.columns.add().name = "Key"
            self.columns.add().name = "Rows"
            self.rows.clear()
            for group in groups:
                row_item = self.rows.add()
                key_cell = row_item.cells.add()
                key_cell.name = "Key"
                key_cell.value = str(group.get("key", ""))
                count_cell = row_item.cells.add()
                count_cell.name = "Rows"
                count_cell.value = str(len(group.get("rows", [])))
            return []
        self.showing_list = False

        # Column rows have a non-id data key that's the upstream node's
        # own node.name, not a readable name - relabeled here using that
        # node's `column_label` (mirrors Evaluate Attribute/Math's
        # `column_label` property - not `label`, which collides with
        # bpy.types.Node's own native `label` attribute), the same way
        # Data's columns are already named by their own dict keys.
        rows = inputs[0] or []
        if from_node is not None and from_socket.bl_idname == 'MaStroScheduleColumnSocketType':
            # No "or from_node.name" fallback - the user's explicit
            # call: an intentionally empty label (e.g. Rename Header
            # with nothing typed into String) should show as empty,
            # never fall back to showing the node's own internal name
            # ("Rename Header", "Rename Header.001", ...) instead.
            label = getattr(from_node, "column_label", "")
            relabeled = []
            for row in rows:
                new_row = {}
                for key, value in row.items():
                    # The data key is whichever key doesn't start with
                    # "_" (same elimination rule as Math/Header's
                    # _data_key) - NOT from_node.name: a pass-through
                    # node like Header (which renames a Column's label
                    # without touching its rows/data key at all) means
                    # from_node is Header, but the actual key in the row
                    # is still whatever upstream node originally
                    # produced the Column (e.g. Evaluate Attribute) -
                    # confirmed live: the Viewer kept showing that
                    # original node's name as the header even when a
                    # Header node further downstream had renamed the
                    # Column, because this used to compare against
                    # from_node.name instead.
                    new_row[label if not key.startswith("_") else key] = value
                relabeled.append(new_row)
            rows = relabeled

        # _Object and the element-index column (_Face/_Edge/_Vertex - a
        # row only ever has one of these, never more than one, since
        # they correspond to mutually exclusive Fields) are shown as
        # "Object"/"Face"/"Edge"/"Vertex" debug columns - useful to see
        # which object/element a row came from, especially once Input
        # Mesh can mix heterogeneous categories (Mass/Plan/Drawing/
        # Street/Mesh) in one table. _Level (the per-floor expansion row
        # index, Face only) is shown the same way as "Level". Still
        # excluded: _subtotal/_RNA_UI-style purely-internal bookkeeping
        # keys that aren't meant to be read by the user at all.
        debug_keys = ("_Object", "_Face", "_Edge", "_Vertex", "_Level")
        underscore_id_keys = [key for key in debug_keys if any(key in row for row in rows)]
        if underscore_id_keys:
            id_keys = underscore_id_keys
        elif any("Field" in row and "Name" in row for row in rows):
            # An Attribute Ref (Get Attribute Names) plugged straight
            # into the Viewer, with no Evaluate Attribute in between -
            # {"Field": ..., "Name": ...}, neither key underscore-
            # prefixed, so none of the usual id keys apply. The node's
            # actual output is the chosen attribute Name (Field is just
            # metadata describing where that Name lives - Object/Face/
            # Edge/Vertex) - so Field is the "id" column here and Name
            # is the "data" one, the same id/data split as everywhere
            # else, just using different key names for this one input
            # shape. Field has no leading underscore to strip, unlike
            # underscore_id_keys - kept in a separate variable so the
            # stripping below only ever applies to the real _-prefixed
            # keys.
            id_keys = ["Field"]
        else:
            id_keys = []
        self.id_column_count = len(id_keys)

        column_names = list(id_keys)
        for row in rows:
            for key in row.keys():
                if key.startswith("_") or key in column_names:
                    continue
                column_names.append(key)

        self.columns.clear()
        for name in column_names:
            label = name[1:] if name in underscore_id_keys else name
            self.columns.add().name = label

        self.rows.clear()
        for row in rows:
            row_item = self.rows.add()
            row_item.is_subtotal = bool(row.get("_subtotal", False))
            row_item.level = int(row.get("_level", 0))
            for name in column_names:
                cell = row_item.cells.add()
                cell.name = name[1:] if name in underscore_id_keys else name
                cell.value = _cell_text(row.get(name, ""))

        return []

    def _evaluate_table(self, table):
        """Populate table_columns/table_merges from a Table value (see
        sockets.py:MaStroScheduleTableSocket for its shape) - the
        separate storage/draw path for Table, kept apart from
        columns/rows above which assume Column/Data's flat-dict-row
        shape instead."""
        self.table_columns.clear()
        for column in table.get("columns", []):
            col_item = self.table_columns.add()
            header = column.get("header") or {}
            col_item.header.text = str(header.get("text", ""))
            header_bg = header.get("bg")
            col_item.header.has_bg = header_bg is not None
            if header_bg is not None:
                col_item.header.bg = header_bg
            header_text_color = header.get("text_color")
            col_item.header.has_text_color = header_text_color is not None
            if header_text_color is not None:
                col_item.header.text_color = header_text_color
            col_item.header.text_align = header.get("text_align", "LEFT")
            for row in column.get("rows", []):
                row_item = col_item.rows.add()
                row_item.text = str(row.get("text", ""))
                row_bg = row.get("bg")
                row_item.has_bg = row_bg is not None
                if row_bg is not None:
                    row_item.bg = row_bg

        self.table_merges.clear()
        for merge in table.get("merges", []):
            merge_item = self.table_merges.add()
            merge_item.start_row = int(merge.get("start_row", 0))
            merge_item.start_col = int(merge.get("start_col", 0))
            merge_item.end_row = int(merge.get("end_row", 0))
            merge_item.end_col = int(merge.get("end_col", 0))
            merge_item.cell.text = str(merge.get("text", ""))
            merge_bg = merge.get("bg")
            merge_item.cell.has_bg = merge_bg is not None
            if merge_bg is not None:
                merge_item.cell.bg = merge_bg
            merge_text_color = merge.get("text_color")
            merge_item.cell.has_text_color = merge_text_color is not None
            if merge_text_color is not None:
                merge_item.cell.text_color = merge_text_color
            merge_item.cell.text_align = merge.get("text_align", "LEFT")

    def draw_buttons(self, context, layout):
        # Not align=True - that joins the three controls edge-to-edge
        # with no visible gap or individual border, confirmed cramped/
        # hard to read live. A plain row() gives each its own border and
        # Blender's normal widget spacing instead.
        row = layout.row()
        row.prop(self, "show_table", text="", icon='HIDE_OFF' if self.show_table else 'HIDE_ON', emboss=False)
        row.prop(self, "visible_rows", text="")
        # General rule: only worth showing when there's at least one id
        # column AND at least one data column beyond those - otherwise
        # collapsing/expanding has nothing meaningful left to change
        # (covers Value/Integer/List Length/... automatically: a single
        # one-row Column with no id keys at all has id_column_count==0,
        # no per-node special-casing needed for any of them).
        #
        # showing_table/showing_list stay as their own explicit
        # exceptions on top of that rule, not folded into it - Table has
        # already discarded the id-key concept entirely (see sockets.py:
        # MaStroScheduleTableSocket), and List's "Key"/"Rows" are two
        # fixed columns, not a variable-length run of id columns, so
        # collapsing "Key" alone would leave a Viewer showing only a
        # column of row counts with no idea which group each one
        # belongs to - both would otherwise satisfy the general rule
        # above on a technicality. The user's own explicit call, to keep
        # future new shapes from silently growing this exception list:
        # a new socket type needs an actual reason like these two before
        # earning a third one, not just "it happens to have id_column_count
        # > 0 the same way Column does".
        #
        # Hidden rather than just disabled in every case - greyed out
        # but still present would invite clicking it to see what it
        # does, only to find out it does nothing for this input.
        has_extra_id_columns = self.id_column_count > 0 and len(self.columns) > self.id_column_count
        if has_extra_id_columns and not self.showing_table and not self.showing_list:
            # Custom icons (Icons/node_viewer_expand.svg, Icons/
            # node_viewer_collapse.svg - placeholders copied from xy_on/
            # xy_off.svg, meant to be redrawn) - not +/- or
            # TRIA_LEFT/RIGHT, both of which read as "increment/
            # decrement" right next to the visible_rows number field,
            # confirmed confusing live.
            expand_icon = icons.icon_id("node_viewer_expand" if self.show_id_columns else "node_viewer_collapse")
            row.prop(self, "show_id_columns", text="", icon_value=expand_icon, emboss=False)


def _node_abs_location(node):
    """Node.location is relative to the node's parent frame (if any), so
    walk up the parent chain to get the position in node-tree space"""
    x, y = node.location
    parent = node.parent
    while parent is not None:
        x += parent.location.x
        y += parent.location.y
        parent = parent.parent
    return x, y


def _draw_node_table(node, is_active=True):
    # Drawn in POST_VIEW: both the GPU batches and blf respect the node
    # editor's current view2d transform automatically here, so coordinates
    # are node-tree space (same units as node.location), scaled by ui_scale
    # like the old prototype's dataForGraphic/draw_callback_schedule_overlay
    # did - no manual view_to_region conversion (that caused a parallax-like
    # drift when panning/zooming, confirmed by A/B testing against the old
    # technique).
    columns = [c.name for c in node.columns]
    # "Show Id Columns" off hides the id columns (Object/Face/Edge/
    # Vertex/Level) entirely - not just shrunk, not drawn at all - so
    # only the actual data column(s) take up space in the overlay. Does
    # NOT apply to a List's own "Key" column even while show_id_columns
    # is at its normal default of False - the toggle controlling it is
    # hidden for a List (draw_buttons' own has_extra_id_columns check),
    # so there's no way for the user to ever turn it back on; confirmed
    # live as a real bug otherwise, "Key" silently missing from every
    # List Viewer with show_id_columns left at its default.
    id_column_count = node.id_column_count
    if not node.show_id_columns and not node.showing_list:
        columns = columns[id_column_count:]
        id_column_count = 0
    if not columns:
        return

    prefs = get_prefs()
    cell_height = prefs.schedule_row_height
    font_size = prefs.schedule_font_size

    abs_x, abs_y = _node_abs_location(node)
    ui_scale = bpy.context.preferences.system.ui_scale
    origin_x = (abs_x + node.width + COLUMN_NODE_GAP) * ui_scale
    origin_y = abs_y * ui_scale

    # Headers and rows are two independent color groups, each split
    # id-columns (Object/Face/Edge/Vertex/Level) vs the data column (the
    # actual attribute value - what the user actually cares about):
    # - Headers: id columns get rgb(130, 53, 76) exactly, just brighter
    #   (this node tree's own accent color); the data column header is
    #   that same color at its base (darker) value - inverted from the
    #   first version of this, per the user's explicit call.
    # - Rows: id columns get this overlay's original neutral dark gray,
    #   just brighter; the data column rows are that same gray at its
    #   base (darker) value.
    # Plain variables for now, not preferences - the user expects to ask
    # for these to move into Preferences in a follow-up once the look is
    # settled, so this intentionally doesn't wire them up yet.
    ACCENT_COLOR = (130 / 255, 53 / 255, 76 / 255)
    ROW_BASE_COLOR = (0.18, 0.18, 0.18)
    id_header_color = _srgb_color(*_hsv_variant(ACCENT_COLOR, value_delta=0.2), 0.95)
    data_header_color = _srgb_color(*ACCENT_COLOR, 0.95)
    id_body_color = _srgb_color(*_hsv_variant(ROW_BASE_COLOR, value_delta=0.2), 0.85)
    data_body_color = _srgb_color(*ROW_BASE_COLOR, 0.85)
    subtotal_color = _srgb_color(0.32, 0.32, 0.32, 0.9)
    # Non-active Viewers' grid lines (the thin borders between cells)
    # are dark gray instead of white - a quick visual cue for which
    # table is the active one, since multiple Viewer overlays in the
    # same tree otherwise all look identical at a glance.
    line_color = (1.0, 1.0, 1.0, 0.4) if is_active else (0.3, 0.3, 0.3, 0.6)
    text_color = (1.0, 1.0, 1.0, 1.0)

    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    gpu.state.blend_set('ALPHA')

    font_id = 0
    # blf.size() is always literal screen pixels (BLF_size(fontid, size,
    # dpi) - confirmed against Blender's source, no view-matrix scaling
    # applied to it). Only blf.position() is transformed by the POST_VIEW
    # matrix, same as the GPU batches below. So the glyph is rasterized at
    # a fixed pixel size regardless of zoom; what changes with zoom is only
    # where that fixed-size glyph ends up on screen relative to the
    # (zoomable) cell grid - this is also exactly what the old prototype did
    # with its always-12 fontSize.
    blf.size(font_id, font_size)

    # A flat single-digit-wide margin on the left, matching the band
    # _draw_table_overlay reserves there for its row numbers (see that
    # function's comment) - so the grid's horizontal position stays the
    # same whether the same Viewer is showing a Column/Data input or a
    # Table one, instead of jumping sideways. This margin is otherwise
    # unused here (no row numbers are drawn in this function).
    origin_x += _row_label_width(font_id) * ui_scale

    # Column width: a fixed CELL_WIDTH for everyone, or - when the
    # "Dynamic Column Width" preference is on - each column sized to fit
    # its own longest text (checking the header AND every row's cell,
    # since a long object name or value can be wider than the header
    # itself). text padding (8px: 4px each side, matching draw_cell's
    # existing 4px left inset) is added on top of the raw text width.
    TEXT_PADDING = 8
    if prefs.schedule_dynamic_column_width:
        col_widths = []
        for col_idx, name in enumerate(columns):
            widest = blf.dimensions(font_id, name)[0]
            for row_item in node.rows:
                for cell in row_item.cells:
                    if cell.name != name:
                        continue
                    text = cell.value
                    if col_idx == 0 and id_column_count > 0:
                        text = "  " * row_item.level + text
                    widest = max(widest, blf.dimensions(font_id, text)[0])
                    break
            col_widths.append(widest + TEXT_PADDING)
    else:
        col_widths = [CELL_WIDTH] * len(columns)

    col_x_offsets = [0]
    for width in col_widths:
        col_x_offsets.append(col_x_offsets[-1] + width)

    def cell_corners(row, col):
        x0 = origin_x + col_x_offsets[col] * ui_scale
        x1 = origin_x + col_x_offsets[col + 1] * ui_scale
        y1 = origin_y - row * cell_height * ui_scale
        y0 = y1 - cell_height * ui_scale
        return ((x0, y0), (x1, y0), (x0, y1), (x1, y1))

    # Fill + text for every cell first, borders for every cell after, in
    # two separate passes - a later cell's TRIS fill was drawing on top
    # of an earlier cell's already-drawn LINES border wherever the two
    # touched (most visibly the very first column's left edge, the one
    # border with no neighboring cell drawn before it to share/reinforce
    # that edge). Confirmed live: this was an ordering bug, not a GPU
    # antialiasing limitation.
    def fill_cell(corners, color, text):
        p00, p10, p01, p11 = corners

        batch = batch_for_shader(shader, 'TRIS', {"pos": (p00, p10, p01, p11)}, indices=((0, 1, 2), (2, 1, 3)))
        shader.uniform_float("color", color)
        batch.draw(shader)

        blf.position(font_id, p00[0] + 4, p00[1] + (p01[1] - p00[1]) / 2 - font_size / 2, 0)
        blf.color(font_id, *text_color)
        blf.draw(font_id, text)

    def border_cell(corners):
        p00, p10, p01, p11 = corners
        batch = batch_for_shader(shader, 'LINES', {"pos": (p00, p10, p10, p11, p11, p01, p01, p00)})
        shader.uniform_float("color", line_color)
        gpu.state.line_width_set(1.0)
        batch.draw(shader)

    is_id_column = [col_idx < id_column_count for col_idx in range(len(columns))]
    all_corners = []

    for col_idx, name in enumerate(columns):
        header_color = id_header_color if is_id_column[col_idx] else data_header_color
        corners = cell_corners(0, col_idx)
        fill_cell(corners, header_color, _header_text(name))
        all_corners.append(corners)

    # visible_rows == 0 means "no cap, show every row" - slicing with
    # `[:0]` would instead mean "show nothing", so that case skips the
    # slice entirely. Slicing past the end of node.rows (more visible_rows
    # than there are rows) is safe in Python - it just returns every row,
    # no IndexError - so no extra bounds check is needed for that case.
    visible_rows = node.rows if node.visible_rows == 0 else node.rows[:node.visible_rows]
    for row_idx, row_item in enumerate(visible_rows, start=1):
        for col_idx, name in enumerate(columns):
            value = ""
            for cell in row_item.cells:
                if cell.name == name:
                    value = cell.value
                    break
            if col_idx == 0 and id_column_count > 0:
                value = "  " * row_item.level + value
            if row_item.is_subtotal:
                color = subtotal_color
            else:
                color = id_body_color if is_id_column[col_idx] else data_body_color
            corners = cell_corners(row_idx, col_idx)
            fill_cell(corners, color, value)
            all_corners.append(corners)

    for corners in all_corners:
        border_cell(corners)


def _column_letter(index):
    """0, 1, 2, ... -> "A", "B", ..., "Z", "AA", "AB", ... - the same
    base-26 letter-only numbering spreadsheets use for column headers,
    spelled out here since Python has no builtin for it."""
    letters = ""
    index += 1
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        letters = chr(ord('A') + remainder) + letters
    return letters


def _draw_table_overlay(node, is_active=True):
    """Table's own draw path, separate from _draw_node_table above -
    Table columns are independent (no shared row count/identity, see
    sockets.py:MaStroScheduleTableSocket), so this lays each column out
    by its own row count rather than one shared grid. A column letter
    above each column and a row number to the left of each row are drawn
    OUTSIDE the cell grid itself (the user's explicit requirement) -
    spreadsheet-style reference labels, not part of the Table's own
    data/header text."""
    columns = list(node.table_columns)
    merges = list(node.table_merges)
    if not columns and not merges:
        return

    prefs = get_prefs()
    cell_height = prefs.schedule_row_height
    font_size = prefs.schedule_font_size

    abs_x, abs_y = _node_abs_location(node)
    ui_scale = bpy.context.preferences.system.ui_scale
    origin_x = (abs_x + node.width + NODE_GAP) * ui_scale
    # The header itself is flush with the node's own top edge (abs_y) -
    # the column letters get their own band ABOVE that (added to it, not
    # subtracted from it), so the header still lines up with the node
    # like every other Viewer overlay, and the letters end up outside/
    # above the node as required.
    origin_y = abs_y * ui_scale

    HEADER_COLOR = (0.18, 0.18, 0.18, 0.95)
    ROW_COLOR = (0.12, 0.12, 0.12, 0.85)
    line_color = (1.0, 1.0, 1.0, 0.4) if is_active else (0.3, 0.3, 0.3, 0.6)
    text_color = (1.0, 1.0, 1.0, 1.0)
    # Reference labels (column letters/row numbers) read as UI chrome, not
    # data - dimmer than the actual cell text so the two are never
    # confused for one another.
    ref_label_color = (0.6, 0.6, 0.6, 1.0)

    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    gpu.state.blend_set('ALPHA')

    font_id = 0
    blf.size(font_id, font_size)

    TEXT_PADDING = 8
    col_widths = []
    for column in columns:
        # A column with 0 rows (the user's call: Rows can be 0 on the
        # Table primitive, e.g. a title-only Table - a purely graphical
        # section header in the final schedule's layout, with no
        # per-column data of its own) still sizes against its own header
        # text - column.rows is just empty, the max() below already
        # handles that with no special-casing needed.
        widest = blf.dimensions(font_id, _header_text(column.header.text))[0]
        for row in column.rows:
            widest = max(widest, blf.dimensions(font_id, row.text)[0])
        col_widths.append(widest + TEXT_PADDING)

    col_x_offsets = [0]
    for width in col_widths:
        col_x_offsets.append(col_x_offsets[-1] + width)

    # Reference labels need their own room outside the grid - a fixed
    # band above the header row for column letters, and a fixed band to
    # the left of the grid for row numbers. Row number width is a flat
    # single-digit allowance (the user's call - a two-digit-wide margin
    # read as too wide), not sized to the actual row count - a Table
    # running past 9 rows overflowing this band's left edge slightly is
    # an accepted trade-off, not worth the grid's own width changing
    # depending on how many rows happen to be in it.
    row_label_width = _row_label_width(font_id)
    col_label_height = cell_height

    def cell_corners(row, col):
        # row 0 (the header) is flush with the node's own top edge
        # (origin_y) - the column letter goes in a band ABOVE that, not
        # squeezed between origin_y and the header, so the header stays
        # aligned with the node like every other Viewer overlay.
        x0 = origin_x + row_label_width * ui_scale + col_x_offsets[col] * ui_scale
        x1 = origin_x + row_label_width * ui_scale + col_x_offsets[col + 1] * ui_scale
        y1 = origin_y - row * cell_height * ui_scale
        y0 = y1 - cell_height * ui_scale
        return ((x0, y0), (x1, y0), (x0, y1), (x1, y1))

    # Same two-pass fill-then-border split as _draw_node_table - see that
    # function's comment for why (a later cell's fill would otherwise
    # paint over an earlier cell's already-drawn border).
    def fill_cell(corners, color, text, this_text_color=None, align='LEFT'):
        p00, p10, p01, p11 = corners
        batch = batch_for_shader(shader, 'TRIS', {"pos": (p00, p10, p01, p11)}, indices=((0, 1, 2), (2, 1, 3)))
        shader.uniform_float("color", color)
        batch.draw(shader)
        # align (Edit Header's/Table primitive's Alignment, see those
        # files) picks where the text sits within the cell's own width -
        # LEFT keeps the existing fixed 4px inset from the cell's left
        # edge, CENTER/RIGHT measure the text and offset from the
        # opposite edges instead, the same general approach
        # draw_ref_label already uses for its own CENTER/RIGHT cases.
        cell_width = p10[0] - p00[0]
        if align == 'CENTER':
            text_width = blf.dimensions(font_id, text)[0]
            text_x = p00[0] + (cell_width - text_width) / 2
        elif align == 'RIGHT':
            text_width = blf.dimensions(font_id, text)[0]
            text_x = p10[0] - text_width - 4
        else:
            text_x = p00[0] + 4
        blf.position(font_id, text_x, p00[1] + (p01[1] - p00[1]) / 2 - font_size / 2, 0)
        # blf.color() is stateful but freely settable per call (confirmed
        # - this file already draws ref_label_color and text_color as
        # two different colors within the same frame) - this_text_color
        # (Edit Header's Text Color, see nodes_table_edit_header.py)
        # overrides the flat default the same way a cell's own bg
        # overrides HEADER_COLOR/ROW_COLOR above.
        blf.color(font_id, *(this_text_color or text_color))
        blf.draw(font_id, text)

    def border_cell(corners):
        p00, p10, p01, p11 = corners
        batch = batch_for_shader(shader, 'LINES', {"pos": (p00, p10, p10, p11, p11, p01, p01, p00)})
        shader.uniform_float("color", line_color)
        gpu.state.line_width_set(1.0)
        batch.draw(shader)

    def draw_ref_label(x, y, width, height, text, align='CENTER'):
        """A reference label in its own band - no fill/border, purely
        text, since these aren't cells of the Table itself. Row numbers
        are right-aligned (align='RIGHT') so the digits stay flush
        against the grid regardless of how many digits a given number
        has - row_label_width is already fixed to fit the widest number
        needed (see above), so this never shifts the grid itself, only
        where the text sits within that already-fixed band."""
        text_width = blf.dimensions(font_id, text)[0]
        if align == 'RIGHT':
            text_x = x + width - text_width - TEXT_PADDING / 2
        else:
            text_x = x + (width - text_width) / 2
        blf.position(font_id, text_x, y + (height - font_size) / 2, 0)
        blf.color(font_id, *ref_label_color)
        blf.draw(font_id, text)

    all_corners = []
    for col_idx, column in enumerate(columns):
        corners = cell_corners(0, col_idx)
        # has_bg/bg (Edit Header's/Table primitive's Background, see
        # nodes_table_edit_header.py/nodes_table_primitive.py) overrides the flat HEADER_COLOR for
        # this one column's header cell when set - alpha kept at
        # HEADER_COLOR's own 0.95 rather than 1.0, so an overridden
        # header still blends consistently with the rest of the overlay.
        header_color = (*column.header.bg, HEADER_COLOR[3]) if column.header.has_bg else HEADER_COLOR
        header_text_color = (*column.header.text_color, 1.0) if column.header.has_text_color else None
        fill_cell(corners, header_color, _header_text(column.header.text), header_text_color, column.header.text_align)
        all_corners.append(corners)
        # Column letter, in its own band directly above the header cell -
        # above origin_y, never below it, so the header itself stays
        # flush with the node's top edge.
        (x0, _y0), (x1, _y1b), _p01, (_x1b, y1) = corners
        draw_ref_label(x0, y1, x1 - x0, col_label_height * ui_scale, _column_letter(col_idx))

    visible_rows = node.visible_rows
    for col_idx, column in enumerate(columns):
        rows = column.rows if visible_rows == 0 else column.rows[:visible_rows]
        for row_idx, row in enumerate(rows, start=1):
            corners = cell_corners(row_idx, col_idx)
            # has_bg/bg overrides the flat ROW_COLOR for this one cell
            # when set - same reasoning as the header's own override
            # above. No node sets this on a row yet (Edit Header only
            # edits a column's header cell today), but the storage and
            # this read are already in place for whenever one does.
            row_color = (*row.bg, ROW_COLOR[3]) if row.has_bg else ROW_COLOR
            fill_cell(corners, row_color, row.text)
            all_corners.append(corners)
            if col_idx == 0:
                # Row number, in the band to the left of this row's
                # first-column cell only - drawn once per row, not once
                # per column, since it labels the row as a whole.
                (x0, y0), _p10, _p01, (_x1, y1) = corners
                draw_ref_label(origin_x, y0, row_label_width * ui_scale, y1 - y0, str(row_idx), align='RIGHT')

    for corners in all_corners:
        border_cell(corners)

    # Merge regions drawn LAST, on top of every normal cell already
    # drawn above (the user's explicit call - same fill/border pass
    # shape as everything else, just deferred to the very end so a
    # merge's one big rectangle paints over whatever grid lines/cell
    # fills would otherwise show through underneath it).
    merge_corners = []
    for merge in merges:
        start = cell_corners(merge.start_row, merge.start_col)
        end = cell_corners(merge.end_row, merge.end_col)
        # cell_corners returns (p00, p10, p01, p11) - bottom-left,
        # bottom-right, top-left, top-right, in that order (see its own
        # definition above) - the merged region spans from the start
        # cell's top-left corner to the end cell's bottom-right one.
        corners = (start[0], end[1], start[2], end[3])
        merge_bg = (*merge.cell.bg, HEADER_COLOR[3]) if merge.cell.has_bg else HEADER_COLOR
        merge_text_color = (*merge.cell.text_color, 1.0) if merge.cell.has_text_color else None
        fill_cell(corners, merge_bg, _header_text(merge.cell.text), merge_text_color, merge.cell.text_align)
        merge_corners.append(corners)
    for corners in merge_corners:
        border_cell(corners)


def _draw_callback():
    context = bpy.context
    space = context.space_data
    if space is None or space.type != 'NODE_EDITOR':
        return
    tree = space.edit_tree
    if tree is None or tree.bl_idname != 'MaStroScheduleTreeType':
        return

    # Draw order otherwise follows tree.nodes' own internal order (not
    # spatial position), so two overlapping overlays would always have
    # the same one "on top" no matter which one was moved over the
    # other. Drawing the active node last (so its overlay paints over
    # any other one it overlaps) at least makes "click a Viewer to bring
    # its table to the front" work, without needing real Z-ordering.
    # Confirmed live (debug print, since removed) that tree.nodes.active
    # does update correctly on click between two Viewers - the earlier
    # "ordering doesn't work" report turned out to be the id_column_count
    # mis-detection bug (see evaluate() above), not this.
    active = tree.nodes.active
    # Compare by name, not identity (`is`) - bpy wraps each access to
    # tree.nodes in a fresh Python RNA proxy object, so two references
    # to "the same" underlying node from separate lookups (here,
    # iterating tree.nodes vs tree.nodes.active) are not `is`-identical
    # even though they're the same node - confirmed live: `is active`
    # never matched either Viewer, even right after clicking one.
    active_name = active.name if active is not None else None
    viewers = [n for n in tree.nodes if n.bl_idname == 'MaStroScheduleViewer' and n.show_table]
    viewers.sort(key=lambda n: n.name == active_name)
    for node in viewers:
        is_active = node.name == active_name
        if node.showing_table:
            _draw_table_overlay(node, is_active=is_active)
        else:
            _draw_node_table(node, is_active=is_active)

    _draw_evaluation_errors(tree)


def _draw_evaluation_errors(tree):
    """Draw each erroring node's exception message just above it - the
    node is already colored red by tree.py:_mark_evaluation_errors, but
    that alone doesn't say *why*. Read directly from
    execution.py:_evaluation_errors (the same dict the poller reads to
    decide which nodes to color) rather than caching anything here - this
    runs on every redraw, always wants the latest state."""
    from .execution import _evaluation_errors
    errors = _evaluation_errors.get(tree.name, {})
    if not errors:
        return

    prefs = get_prefs()
    font_id = 0
    blf.size(font_id, prefs.schedule_font_size)
    ui_scale = bpy.context.preferences.system.ui_scale

    for node in tree.nodes:
        message = errors.get(node.name)
        if message is None:
            continue
        abs_x, abs_y = _node_abs_location(node)
        # node.location is the node's top-left corner in node-tree space
        # (Y growing upward) - a small gap above that top edge is where
        # the node's own header already is, so this sits just above the
        # header, not overlapping it.
        text_x = abs_x * ui_scale
        text_y = (abs_y + 4) * ui_scale
        blf.color(font_id, 1.0, 0.6, 0.6, 1.0)
        blf.position(font_id, text_x, text_y, 0)
        # blf draws actual text glyphs, not Blender's native icon set - U+26A0
        # (WARNING SIGN) is just a Unicode character, drawn like any other,
        # not the same thing as Blender's own warning icon. Relies on
        # whatever font Blender's UI is using having that glyph - if it
        # doesn't, this falls back to whatever blf's own missing-glyph
        # placeholder is (a box, typically), not a crash.
        blf.draw(font_id, "⚠ " + message)


def register_viewer_draw_handler():
    global _draw_handler
    if _draw_handler is None:
        _draw_handler = bpy.types.SpaceNodeEditor.draw_handler_add(_draw_callback, (), 'WINDOW', 'POST_VIEW')


def unregister_viewer_draw_handler():
    global _draw_handler
    if _draw_handler is not None:
        bpy.types.SpaceNodeEditor.draw_handler_remove(_draw_handler, 'WINDOW')
        _draw_handler = None
