import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector
from bpy_extras.view3d_utils import location_3d_to_region_2d
from .constants import DOTTED_COLOR, DOTTED_SCALE


def radius_to_pixels(context, radius):
    """Convert a stroke radius (Blender metres) to pixels at the view centre.

    Applies mastro_cad_drawing_scale the same way the GN modifier does.
    Returns the half-width in pixels (i.e. the screen radius).
    """
    from ..cad.constants import DRAWING_SEL_LINE_WIDTH
    region = context.region
    rv3d   = context.space_data.region_3d
    if rv3d is None:
        return DRAWING_SEL_LINE_WIDTH / 2.0
    drawing_scale  = getattr(context.scene, "mastro_cad_drawing_scale", 1)
    scaled_radius  = radius * drawing_scale
    centre = rv3d.view_location
    right  = rv3d.view_rotation @ Vector((scaled_radius, 0.0, 0.0))
    p1 = location_3d_to_region_2d(region, rv3d, centre)
    p2 = location_3d_to_region_2d(region, rv3d, centre + right)
    if p1 is None or p2 is None:
        return DRAWING_SEL_LINE_WIDTH / 2.0
    return max(1.0, (p2 - p1).length)


import math

_CAP_SEGMENTS  = 8
_DISK_SEGMENTS = 12


def _body_tris(ax, ay, bx, by, hw):
    dx = bx - ax;  dy = by - ay
    length = math.sqrt(dx*dx + dy*dy)
    if length < 1e-6:
        return [], 0.0, 0.0
    nx = -dy / length * hw;  ny = dx / length * hw
    return ([(ax+nx, ay+ny), (ax-nx, ay-ny), (bx-nx, by-ny),
             (ax+nx, ay+ny), (bx-nx, by-ny), (bx+nx, by+ny)], nx, ny)


def _cap_tris(cx, cy, hw, ux, uy, forward):
    pts  = []
    base = math.atan2(uy, ux) + (0.0 if forward else math.pi)
    for i in range(_CAP_SEGMENTS):
        a0 = base - math.pi * 0.5 + math.pi * i       / _CAP_SEGMENTS
        a1 = base - math.pi * 0.5 + math.pi * (i + 1) / _CAP_SEGMENTS
        pts += [(cx, cy),
                (cx + math.cos(a0)*hw, cy + math.sin(a0)*hw),
                (cx + math.cos(a1)*hw, cy + math.sin(a1)*hw)]
    return pts


def _disk_tris(cx, cy, hw):
    pts = []
    for i in range(_DISK_SEGMENTS):
        a0 = 2*math.pi * i       / _DISK_SEGMENTS
        a1 = 2*math.pi * (i + 1) / _DISK_SEGMENTS
        pts += [(cx, cy),
                (cx + math.cos(a0)*hw, cy + math.sin(a0)*hw),
                (cx + math.cos(a1)*hw, cy + math.sin(a1)*hw)]
    return pts


def draw_strokes_2d(segments_px, half_widths, color, join_counts=None):
    """Draw 2D screen-space strokes with round caps and disk joins.

    segments_px : list of ((ax,ay),(bx,by)) screen-pixel pairs.
    half_widths : list of half-widths (one per segment).
    color       : RGBA tuple.
    join_counts : optional dict mapping vertex key → number of connected
                  selected segments, used to choose disk vs cap at endpoints.
                  If None, every endpoint gets a semicircle cap.
    """
    tris = []
    for (s0, s1), hw in zip(segments_px, half_widths):
        ax, ay = s0;  bx, by = s1
        body, nx, ny = _body_tris(ax, ay, bx, by, hw)
        tris.extend(body)
        if not body:
            tris.extend(_disk_tris(ax, ay, hw))
            continue
        dx = bx - ax;  dy = by - ay
        length = math.sqrt(dx*dx + dy*dy)
        ux = dx/length;  uy = dy/length
        tris.extend(_cap_tris(ax, ay, hw, ux, uy, forward=False))
        tris.extend(_cap_tris(bx, by, hw, ux, uy, forward=True))

    if not tris:
        return
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    shader.bind()
    shader.uniform_float("color", color)
    gpu.state.blend_set('ALPHA')
    batch_for_shader(shader, 'TRIS', {"pos": tris}).draw(shader)
    gpu.state.blend_set('NONE')


def draw_disks_2d(centres_px, half_widths, color):
    """Draw filled circles at 2D screen-space positions."""
    tris = []
    for (cx, cy), hw in zip(centres_px, half_widths):
        tris.extend(_disk_tris(cx, cy, hw))
    if not tris:
        return
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    shader.bind()
    shader.uniform_float("color", color)
    gpu.state.blend_set('ALPHA')
    batch_for_shader(shader, 'TRIS', {"pos": tris}).draw(shader)
    gpu.state.blend_set('NONE')


def _build_dotted_shader():
    vert_out = gpu.types.GPUStageInterfaceInfo("mastrocad_dot_iface")
    vert_out.smooth('FLOAT', "v_ArcLength")

    info = gpu.types.GPUShaderCreateInfo()
    info.push_constant('MAT4', "u_ViewProjectionMatrix")
    info.push_constant('FLOAT', "u_Scale")
    info.push_constant('VEC4', "u_Color")
    info.vertex_in(0, 'VEC3', "position")
    info.vertex_in(1, 'FLOAT', "arcLength")
    info.vertex_out(vert_out)
    info.fragment_out(0, 'VEC4', "FragColor")

    info.vertex_source(
        "void main() {"
        "  v_ArcLength = arcLength;"
        "  gl_Position = u_ViewProjectionMatrix * vec4(position, 1.0f);"
        "}"
    )
    info.fragment_source(
        "void main() {"
        "  if (step(sin(v_ArcLength * u_Scale), 0.5) == 1) discard;"
        "  FragColor = u_Color;"
        "}"
    )
    return gpu.shader.create_from_info(info)


_dotted_shader = None

def draw_dotted_polyline(pts, closed, context,
                         color=None, scale=None):
    """Draw a dotted polyline (LINE_STRIP) through world-space points.

    pts    : list of mathutils.Vector — world-space vertices.
    closed : bool — if True, closes the loop back to pts[0].
    color  : RGBA tuple.
    scale  : controls dash frequency (higher = more dashes per unit length).
    """
    if color is None:
        color = DOTTED_COLOR
    if scale is None:
        scale = DOTTED_SCALE
    global _dotted_shader
    if _dotted_shader is None:
        _dotted_shader = _build_dotted_shader()
    if len(pts) < 2:
        return

    rv3d = context.space_data.region_3d
    if rv3d is None:
        return

    draw_pts = list(pts)
    if closed:
        draw_pts = draw_pts + [draw_pts[0]]

    arc_lengths = [0.0]
    for a, b in zip(draw_pts[:-1], draw_pts[1:]):
        arc_lengths.append(arc_lengths[-1] + (b - a).length)

    batch = batch_for_shader(_dotted_shader, 'LINE_STRIP',
                             {"position":  draw_pts,
                              "arcLength": arc_lengths})
    _dotted_shader.bind()
    _dotted_shader.uniform_float("u_ViewProjectionMatrix", rv3d.perspective_matrix)
    _dotted_shader.uniform_float("u_Scale", scale)
    _dotted_shader.uniform_float("u_Color", color)
    gpu.state.blend_set('ALPHA')
    gpu.state.depth_test_set('NONE')
    gpu.state.line_width_set(1.0)
    batch.draw(_dotted_shader)
    gpu.state.depth_test_set('LESS_EQUAL')
    gpu.state.blend_set('NONE')


def draw_dotted_line(p0, p1, context, color=None, scale=None):
    """Draw a single dotted segment — convenience wrapper around draw_dotted_polyline."""
    draw_dotted_polyline([p0, p1], closed=False, context=context,
                         color=color, scale=scale)
