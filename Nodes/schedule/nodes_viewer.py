import colorsys

import bpy
import blf
import gpu
from gpu_extras.batch import batch_for_shader
from bpy.types import Node
from bpy.props import CollectionProperty, BoolProperty, IntProperty

from .tree import MaStroScheduleTreeNode
from .properties import MaStro_schedule_key_item, MaStro_schedule_row
from .execution import tag_redraw_node_editors
from ...Utils.mastro_preferences.get_preferences import get_prefs


CELL_WIDTH = 120
NODE_GAP = 4


def _header_text(name):
    """Capitalize a column header's first letter for display - the
    underlying column name/key (e.g. "area", a Get Attribute Names
    value) stays lowercase everywhere else (data, lookups, joins); this
    only affects what's drawn."""
    return name[:1].upper() + name[1:] if name else name


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
        # Column or Attribute alike (see that socket's docstring in
        # sockets.py) - the Viewer has to work for whatever a node
        # happens to output, not be limited to one specific shape.
        # Column rows have a non-id data key that's the upstream node's
        # own node.name, not a readable name - relabeled here using that
        # node's `column_label` (mirrors Evaluate Attribute/Math's
        # `column_label` property - not `label`, which collides with
        # bpy.types.Node's own native `label` attribute), the same way
        # Data's columns are already named by their own dict keys.
        from .tree import resolve_through_reroutes
        socket = self.inputs[0]
        rows = inputs[0] or []
        from_node, from_socket = (None, None)
        if socket.is_linked and socket.links:
            from_node, from_socket = resolve_through_reroutes(socket.links[0])
        if from_node is not None and from_socket.bl_idname == 'MaStroScheduleColumnSocketType':
            label = getattr(from_node, "column_label", "") or from_node.name
            data_key = from_node.name
            relabeled = []
            for row in rows:
                new_row = {}
                for key, value in row.items():
                    new_row[label if key == data_key else key] = value
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
                cell.value = str(row.get(name, ""))

        return []

    def draw_buttons(self, context, layout):
        # Not align=True - that joins the three controls edge-to-edge
        # with no visible gap or individual border, confirmed cramped/
        # hard to read live. A plain row() gives each its own border and
        # Blender's normal widget spacing instead.
        row = layout.row()
        row.prop(self, "show_table", text="", icon='HIDE_OFF' if self.show_table else 'HIDE_ON', emboss=False)
        row.prop(self, "visible_rows", text="")
        # FORWARD/BACK, not +/- or TRIA_LEFT/RIGHT - both of those read as
        # "increment/decrement" right next to the visible_rows number
        # field, confirmed confusing live. FORWARD/BACK reads as
        # advance/retreat through the column layout instead, with no such
        # clash.
        row.prop(self, "show_id_columns", text="", icon='BACK' if self.show_id_columns else 'FORWARD', emboss=False)


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
    # only the actual data column(s) take up space in the overlay.
    id_column_count = node.id_column_count
    if not node.show_id_columns:
        columns = columns[id_column_count:]
        id_column_count = 0
    if not columns:
        return

    prefs = get_prefs()
    cell_height = prefs.schedule_row_height
    font_size = prefs.schedule_font_size

    abs_x, abs_y = _node_abs_location(node)
    ui_scale = bpy.context.preferences.system.ui_scale
    origin_x = (abs_x + node.width + NODE_GAP) * ui_scale
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
        _draw_node_table(node, is_active=(node.name == active_name))

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
