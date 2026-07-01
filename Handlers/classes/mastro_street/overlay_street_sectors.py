import bpy
import bmesh
import gpu
import blf
import math

from gpu_extras.batch import batch_for_shader
from mathutils import Vector

from ....Utils.mastro_street.angle_ordered_branches import angle_ordered_branches
from ....Utils.mastro_cad.cad.circle_utils import circle_ttr, arc_points_3d

ARC_SEGMENTS = 24


def _unit(ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    length = math.hypot(dx, dy)
    return (dx / length, dy / length) if length > 1e-8 else (1.0, 0.0)


def _perp_toward(dx, dy, ix, iy, ref_x, ref_y):
    n0x, n0y = -dy, dx
    n1x, n1y = dy, -dx
    if n0x * (ref_x - ix) + n0y * (ref_y - iy) >= 0:
        return (n0x, n0y)
    return (n1x, n1y)


def _local_plane(active_world, other_a_world, other_b_world):
    """Compute (x_axis, y_axis, normal) for the plane defined by the three world
    points: intersection vertex + two branch endpoints. Each fillet gets its own plane."""
    v1 = (other_a_world - active_world).normalized()
    v2 = (other_b_world - active_world).normalized()
    normal = v1.cross(v2)
    if normal.length < 1e-6:
        normal = Vector((0, 0, 1))
    normal = normal.normalized()
    x_axis = v1
    y_axis = normal.cross(x_axis).normalized()
    return x_axis, y_axis, normal


def _arc_segments(active_world, other_a_world, other_b_world, radius):
    """Build line segments for the fillet arc between two branches meeting at
    `active_world`. Returns [] if no valid tangent solution exists."""
    x_axis, y_axis, normal = _local_plane(active_world, other_a_world, other_b_world)

    def w2(v):
        return (v.dot(x_axis), v.dot(y_axis))

    ix, iy = w2(active_world)
    a2d = w2(other_a_world)
    b2d = w2(other_b_world)

    d0 = _unit(a2d[0], a2d[1], ix, iy)
    d1 = _unit(b2d[0], b2d[1], ix, iy)
    n0 = _perp_toward(d0[0], d0[1], ix, iy, b2d[0], b2d[1])
    n1 = _perp_toward(d1[0], d1[1], ix, iy, a2d[0], a2d[1])

    arc_data = circle_ttr(ix, iy, d0[0], d0[1], d1[0], d1[1], n0[0], n0[1], n1[0], n1[1], radius)
    if arc_data is None:
        return []

    center_2d, r, t1_2d, t2_2d = arc_data
    depth = active_world.dot(normal)
    arc_pts = arc_points_3d(center_2d, r, t1_2d, t2_2d, x_axis, y_axis, normal, depth, ARC_SEGMENTS)
    return [(arc_pts[i], arc_pts[i + 1]) for i in range(len(arc_pts) - 1)]


def _draw_lines(segments, color):
    if not segments:
        return
    pos = [p for pair in segments for p in pair]
    indices = [(i, i + 1) for i in range(0, len(pos), 2)]
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'LINES', {"pos": pos}, indices=indices)
    gpu.state.line_width_set(3.0)
    gpu.state.blend_set("ALPHA")
    shader.uniform_float("color", color)
    batch.draw(shader)


def _active_object_color():
    r, g, b, a = bpy.context.preferences.themes[0].view_3d.editmesh_active
    return (r, g, b, 1.0)


def _draw_label(text, world_co, color):
    """Draw a BLF label at a 3D world position projected to 2D screen space."""
    region = bpy.context.region
    rv3d = bpy.context.region_data
    if region is None or rv3d is None:
        return
    from bpy_extras.view3d_utils import location_3d_to_region_2d
    co2d = location_3d_to_region_2d(region, rv3d, world_co)
    if co2d is None:
        return
    font_id = 0
    blf.size(font_id, 16)
    blf.color(font_id, *color)
    blf.position(font_id, co2d.x + 8, co2d.y + 8, 0)
    blf.draw(font_id, text)


def _draw_fillets_at_vert(obj, bm, vert, edge, left_fillet, right_fillet, bm_radius, color):
    """Draw fillet arcs for one vertex end of `edge`.

    left_fillet: True if the sector toward the PREV polar neighbor should be drawn.
    right_fillet: True if the sector toward the NEXT polar neighbor should be drawn.
    Each arc is drawn in its own local plane (vert + the two branch endpoints).
    """
    branches = angle_ordered_branches(obj, vert)
    n = len(branches)
    if n < 2:
        return

    try:
        idx = next(i for i, e in enumerate(branches) if e.index == edge.index)
    except StopIteration:
        return

    active_world = obj.matrix_world @ vert.co
    this_other = obj.matrix_world @ edge.other_vert(vert).co

    if left_fillet:
        prev_edge = branches[(idx - 1) % n]
        prev_other = obj.matrix_world @ prev_edge.other_vert(vert).co
        radius = (edge[bm_radius] + prev_edge[bm_radius]) / 2
        if radius > 0:
            _draw_lines(_arc_segments(active_world, this_other, prev_other, radius), color)

    if right_fillet:
        next_edge = branches[(idx + 1) % n]
        next_other = obj.matrix_world @ next_edge.other_vert(vert).co
        radius = (edge[bm_radius] + next_edge[bm_radius]) / 2
        if radius > 0:
            _draw_lines(_arc_segments(active_world, this_other, next_other, radius), color)


def show_street_sector_labels(obj):
    """Draw A/B vertex labels for the active edge in pixel-space (POST_PIXEL callback)."""
    if not (obj.type == "MESH" and "MaStro street" in obj.data):
        return
    if not obj.data.is_editmode:
        return
    if not bpy.context.scene.tool_settings.mesh_select_mode[1]:
        return

    bm = bmesh.from_edit_mesh(obj.data)
    active = bm.select_history.active
    if not isinstance(active, bmesh.types.BMEdge) or not active.is_valid:
        return

    color = _active_object_color()
    active_a = obj.matrix_world @ active.verts[0].co
    active_b = obj.matrix_world @ active.verts[1].co
    _draw_label("A", active_a, color)
    _draw_label("B", active_b, color)


def show_street_sector_overlay(obj):
    """Draw fillet arcs and A/B labels for both ends of the active edge."""
    if not (obj.type == "MESH" and "MaStro street" in obj.data):
        return
    if not obj.data.is_editmode:
        return
    if not bpy.context.scene.tool_settings.mesh_select_mode[1]:
        return

    bm = bmesh.from_edit_mesh(obj.data)
    active = bm.select_history.active
    if not isinstance(active, bmesh.types.BMEdge) or not active.is_valid:
        return

    try:
        bm_radius = bm.edges.layers.float["mastro_street_radius"]
        bm_al = bm.edges.layers.bool["mastro_street_sector_A_left"]
        bm_ar = bm.edges.layers.bool["mastro_street_sector_A_right"]
        bm_bl = bm.edges.layers.bool["mastro_street_sector_B_left"]
        bm_br = bm.edges.layers.bool["mastro_street_sector_B_right"]
    except KeyError:
        return

    color = _active_object_color()

    vert_a = active.verts[0]
    vert_b = active.verts[1]
    active_a = obj.matrix_world @ vert_a.co
    active_b = obj.matrix_world @ vert_b.co

    # Highlight active edge.
    _draw_lines([(active_a, active_b)], color)

    # Fillet arcs at each vertex end — pass left/right flags directly.
    _draw_fillets_at_vert(obj, bm, vert_a, active, active[bm_al], active[bm_ar], bm_radius, color)
    _draw_fillets_at_vert(obj, bm, vert_b, active, active[bm_bl], active[bm_br], bm_radius, color)

