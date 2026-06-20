import bpy
import blf
import gpu
from gpu_extras.batch import batch_for_shader
from bpy.types import Node
from bpy.props import CollectionProperty, BoolProperty

from .tree import MaStroScheduleTreeNode
from .properties import MaStro_schedule_key_item, MaStro_schedule_row


CELL_WIDTH = 120
CELL_HEIGHT = 24
FONT_SIZE = 12
NODE_GAP = 60

_draw_handler = None


def _tag_redraw_node_editors(self, context):
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'NODE_EDITOR':
                area.tag_redraw()


class MaStroScheduleViewerNode(MaStroScheduleTreeNode, Node):
    """Display the incoming table as a grid in the node's side panel, and
    optionally as an overlay table drawn next to the node in the node
    editor"""
    bl_idname = 'MaStroScheduleViewer'
    bl_label = 'Viewer'

    columns: CollectionProperty(type=MaStro_schedule_key_item)
    rows: CollectionProperty(type=MaStro_schedule_row)
    show_table: BoolProperty(name="Show Table", default=False, update=_tag_redraw_node_editors)

    def init(self, context):
        self.inputs.new('MaStroScheduleDataSocketType', "Data")

    def evaluate(self, inputs):
        rows = inputs[0] or []

        column_names = []
        for row in rows:
            for key in row.keys():
                if key.startswith("_"):
                    continue
                if key not in column_names:
                    column_names.append(key)

        self.columns.clear()
        for name in column_names:
            self.columns.add().name = name

        self.rows.clear()
        for row in rows:
            row_item = self.rows.add()
            row_item.is_subtotal = bool(row.get("_subtotal", False))
            row_item.level = int(row.get("_level", 0))
            for name in column_names:
                cell = row_item.cells.add()
                cell.name = name
                cell.value = str(row.get(name, ""))

        return []

    def draw_buttons(self, context, layout):
        layout.prop(self, "show_table")

    def draw_buttons_ext(self, context, layout):
        col = layout.column()

        header = col.row()
        for column in self.columns:
            header.label(text=column.name)

        for row in self.rows:
            row_layout = col.row()
            for cell in row.cells:
                row_layout.label(text=cell.value)


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


def _draw_node_table(node, view2d):
    columns = [c.name for c in node.columns]
    if not columns:
        return

    abs_x, abs_y = _node_abs_location(node)
    origin_x = abs_x + node.width + NODE_GAP
    origin_y = abs_y

    header_color = (0.45, 0.45, 0.45, 0.95)
    subtotal_color = (0.32, 0.32, 0.32, 0.9)
    body_color = (0.18, 0.18, 0.18, 0.85)
    line_color = (1.0, 1.0, 1.0, 0.4)
    text_color = (1.0, 1.0, 1.0, 1.0)

    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    gpu.state.blend_set('ALPHA')

    font_id = 0
    # scale the font size with the current zoom level, based on the on-screen
    # height of one cell, so text stays proportional to the table at any zoom
    _, y0_px = view2d.view_to_region(0.0, 0.0, clip=False)
    _, y1_px = view2d.view_to_region(0.0, CELL_HEIGHT, clip=False)
    cell_height_px = abs(y1_px - y0_px)
    font_size = max(1, round(cell_height_px * (FONT_SIZE / CELL_HEIGHT)))
    blf.size(font_id, font_size)

    def cell_corners(row, col):
        # convert node-tree-space corners to region pixels up front, so the
        # GPU shapes and the blf text below are computed from the exact same
        # screen-space points and stay perfectly in sync when panning/zooming
        x0 = origin_x + col * CELL_WIDTH
        x1 = x0 + CELL_WIDTH
        y1 = origin_y - row * CELL_HEIGHT
        y0 = y1 - CELL_HEIGHT
        return (
            view2d.view_to_region(x0, y0, clip=False),
            view2d.view_to_region(x1, y0, clip=False),
            view2d.view_to_region(x0, y1, clip=False),
            view2d.view_to_region(x1, y1, clip=False),
        )

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

    view2d = context.region.view2d
    for node in tree.nodes:
        if node.bl_idname == 'MaStroScheduleViewer' and node.show_table:
            _draw_node_table(node, view2d)


def register_viewer_draw_handler():
    global _draw_handler
    if _draw_handler is None:
        _draw_handler = bpy.types.SpaceNodeEditor.draw_handler_add(_draw_callback, (), 'WINDOW', 'POST_PIXEL')


def unregister_viewer_draw_handler():
    global _draw_handler
    if _draw_handler is not None:
        bpy.types.SpaceNodeEditor.draw_handler_remove(_draw_handler, 'WINDOW')
        _draw_handler = None
