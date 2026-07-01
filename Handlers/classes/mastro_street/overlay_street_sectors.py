import bpy
import bmesh
import gpu
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
    """Perpendicular to (dx,dy), the one pointing from (ix,iy) toward (ref_x,ref_y)."""
    n0x, n0y = -dy, dx
    n1x, n1y = dy, -dx
    if n0x * (ref_x - ix) + n0y * (ref_y - iy) >= 0:
        return (n0x, n0y)
    return (n1x, n1y)


def _arc_segments_for_pair(active_world, other_a_world, other_b_world, radius, x_axis, y_axis, normal):
    """Build the line segments approximating the fillet arc between two branches
    meeting at `active_world`, in the (x_axis, y_axis, normal) local plane. Returns
    [] if no valid tangent solution exists (e.g. branches nearly collinear)."""
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


def _active_object_color():
    """Return the theme color used for the active mesh element (same as overlay_street.py)."""
    r, g, b, a = bpy.context.preferences.themes[0].view_3d.editmesh_active
    return (r, g, b, 1.0)


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


def show_street_sector_overlay(obj):
    """Draw the real-radius fillet arc(s) for the currently selected branch of the
    active intersection vertex, in the local 3D plane of that vertex and its two
    neighboring branches (streets aren't necessarily flat in XY). Toggled the same
    way as show_street_overlay (optional - GN already shows the real result when
    its modifier is on; this exists for when it's off or for a quick preview)."""
    if not (obj.type == "MESH" and "MaStro street" in obj.data):
        return
    if not obj.data.is_editmode:
        return
    if not bpy.context.scene.tool_settings.mesh_select_mode[0]:
        return

    scene = bpy.context.scene
    bm = bmesh.from_edit_mesh(obj.data)
    active = bm.select_history.active
    if not isinstance(active, bmesh.types.BMVert) or not active.is_valid:
        return

    branches = angle_ordered_branches(obj, active)
    n = len(branches)
    if n < 2:
        return

    index = scene.mastro_street_active_branch % n
    edge = branches[index]
    prev_edge = branches[(index - 1) % n]
    next_edge = branches[(index + 1) % n]

    try:
        bm_radius = bm.edges.layers.float["mastro_street_radius"]
    except KeyError:
        return

    color = _active_object_color()

    active_world = obj.matrix_world @ active.co
    this_other = obj.matrix_world @ edge.other_vert(active).co
    prev_other = obj.matrix_world @ prev_edge.other_vert(active).co
    next_other = obj.matrix_world @ next_edge.other_vert(active).co

    # Highlight the active branch edge itself.
    _draw_lines([(active_world, this_other)], color)

    # Build the local plane from the actual 3D positions of the three points
    # involved (active vertex + the two neighboring branch endpoints), so the
    # fillet arc is correct even for streets that are not flat in world XY.
    v1 = (this_other - active_world).normalized()
    v2 = (prev_other - active_world).normalized()
    normal = v1.cross(v2)
    if normal.length < 1e-6:
        v2 = (next_other - active_world).normalized()
        normal = v1.cross(v2)
    if normal.length < 1e-6:
        normal = active_world.normalized() if active_world.length > 1e-6 else Vector((0, 0, 1))
    normal = normal.normalized()
    x_axis = v1
    y_axis = normal.cross(x_axis).normalized()

    sector_type = scene.mastro_street_active_branch_type
    prev_is_fillet = sector_type in ('0', '1')
    next_is_fillet = sector_type in ('0', '2')

    if prev_is_fillet:
        radius = (edge[bm_radius] + prev_edge[bm_radius]) / 2
        if radius > 0:
            segs = _arc_segments_for_pair(active_world, this_other, prev_other, radius, x_axis, y_axis, normal)
            _draw_lines(segs, color)

    if next_is_fillet:
        radius = (edge[bm_radius] + next_edge[bm_radius]) / 2
        if radius > 0:
            segs = _arc_segments_for_pair(active_world, this_other, next_other, radius, x_axis, y_axis, normal)
            _draw_lines(segs, color)
