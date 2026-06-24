import bpy
import blf
import gpu
from gpu_extras.batch import batch_for_shader
from bpy.types import Node
from bpy.props import CollectionProperty, BoolProperty

from .tree import MaStroScheduleTreeNode
from .properties import MaStro_schedule_key_item, MaStro_schedule_row
from .execution import tag_redraw_node_editors
from ...Utils.mastro_preferences.get_preferences import get_prefs


CELL_WIDTH = 120
NODE_GAP = 4

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

    def init(self, context):
        self.inputs.new('MaStroScheduleAnySocketType', "Data")

    def evaluate(self, inputs):
        # A single MaStroScheduleAnySocketType input, accepting Data,
        # Column or Attribute alike (see that socket's docstring in
        # sockets.py) - the Viewer has to work for whatever a node
        # happens to output, not be limited to one specific shape.
        # Column rows have a non-id data key that's the upstream node's
        # own node.name, not a readable name - relabeled here using that
        # node's `label` (mirrors Evaluate Attribute/Math's `label`
        # property), the same way Data's columns are already named by
        # their own dict keys.
        socket = self.inputs[0]
        rows = inputs[0] or []
        if (socket.is_linked and socket.links
                and socket.links[0].from_socket.bl_idname == 'MaStroScheduleColumnSocketType'):
            from_node = socket.links[0].from_node
            label = getattr(from_node, "label", "") or from_node.name
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
        debug_present = [key for key in debug_keys if any(key in row for row in rows)]

        column_names = list(debug_present)
        for row in rows:
            for key in row.keys():
                if key.startswith("_") or key in column_names:
                    continue
                column_names.append(key)

        self.columns.clear()
        for name in column_names:
            label = name[1:] if name in debug_present else name
            self.columns.add().name = label

        self.rows.clear()
        for row in rows:
            row_item = self.rows.add()
            row_item.is_subtotal = bool(row.get("_subtotal", False))
            row_item.level = int(row.get("_level", 0))
            for name in column_names:
                cell = row_item.cells.add()
                cell.name = name[1:] if name in debug_present else name
                cell.value = str(row.get(name, ""))

        return []

    def draw_buttons(self, context, layout):
        layout.prop(self, "show_table", text="Show Table", icon='HIDE_OFF' if self.show_table else 'HIDE_ON')


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


def _draw_node_table(node):
    # Drawn in POST_VIEW: both the GPU batches and blf respect the node
    # editor's current view2d transform automatically here, so coordinates
    # are node-tree space (same units as node.location), scaled by ui_scale
    # like the old prototype's dataForGraphic/draw_callback_schedule_overlay
    # did - no manual view_to_region conversion (that caused a parallax-like
    # drift when panning/zooming, confirmed by A/B testing against the old
    # technique).
    columns = [c.name for c in node.columns]
    if not columns:
        return

    prefs = get_prefs()
    cell_height = prefs.schedule_row_height
    font_size = prefs.schedule_font_size

    abs_x, abs_y = _node_abs_location(node)
    ui_scale = bpy.context.preferences.system.ui_scale
    origin_x = (abs_x + node.width + NODE_GAP) * ui_scale
    origin_y = abs_y * ui_scale

    header_color = (0.45, 0.45, 0.45, 0.95)
    subtotal_color = (0.32, 0.32, 0.32, 0.9)
    body_color = (0.18, 0.18, 0.18, 0.85)
    line_color = (1.0, 1.0, 1.0, 0.4)
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

    def cell_corners(row, col):
        x0 = origin_x + col * CELL_WIDTH * ui_scale
        x1 = x0 + CELL_WIDTH * ui_scale
        y1 = origin_y - row * cell_height * ui_scale
        y0 = y1 - cell_height * ui_scale
        return ((x0, y0), (x1, y0), (x0, y1), (x1, y1))

    def draw_cell(corners, color, text):
        p00, p10, p01, p11 = corners

        batch = batch_for_shader(shader, 'TRIS', {"pos": (p00, p10, p01, p11)}, indices=((0, 1, 2), (2, 1, 3)))
        shader.uniform_float("color", color)
        batch.draw(shader)

        batch = batch_for_shader(shader, 'LINES', {"pos": (p00, p10, p10, p11, p11, p01, p01, p00)})
        shader.uniform_float("color", line_color)
        gpu.state.line_width_set(1.0)
        batch.draw(shader)

        blf.position(font_id, p00[0] + 4, p00[1] + (p01[1] - p00[1]) / 2 - font_size / 2, 0)
        blf.color(font_id, *text_color)
        blf.draw(font_id, text)

    for col_idx, name in enumerate(columns):
        draw_cell(cell_corners(0, col_idx), header_color, name)

    for row_idx, row_item in enumerate(node.rows, start=1):
        color = subtotal_color if row_item.is_subtotal else body_color
        for col_idx, name in enumerate(columns):
            value = ""
            for cell in row_item.cells:
                if cell.name == name:
                    value = cell.value
                    break
            if col_idx == 0:
                value = "  " * row_item.level + value
            draw_cell(cell_corners(row_idx, col_idx), color, value)


def _draw_callback():
    context = bpy.context
    space = context.space_data
    if space is None or space.type != 'NODE_EDITOR':
        return
    tree = space.edit_tree
    if tree is None or tree.bl_idname != 'MaStroScheduleTreeType':
        return

    for node in tree.nodes:
        if node.bl_idname == 'MaStroScheduleViewer' and node.show_table:
            _draw_node_table(node)


def register_viewer_draw_handler():
    global _draw_handler
    if _draw_handler is None:
        _draw_handler = bpy.types.SpaceNodeEditor.draw_handler_add(_draw_callback, (), 'WINDOW', 'POST_VIEW')


def unregister_viewer_draw_handler():
    global _draw_handler
    if _draw_handler is not None:
        bpy.types.SpaceNodeEditor.draw_handler_remove(_draw_handler, 'WINDOW')
        _draw_handler = None
