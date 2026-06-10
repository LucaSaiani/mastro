"""Persistent draw handler — shows handles when a valid tagged rectangle or
circle is active in edit mode.

The handler is read-only: it uses check_rect() / check_circle() which never
modify the mesh.  Full validation (marking invalid elements) is deferred to
the respective edit operator.
"""

import bpy
import bmesh
from bpy_extras.view3d_utils import location_3d_to_region_2d
import gpu
from gpu_extras.batch import batch_for_shader

from ...Utils.mastro_cad.cad.rect_utils   import check_rect
from ...Utils.mastro_cad.cad.constants    import HANDLE_SIZE_PX as _SZ, HANDLE_THICK_PADDING_PX as _PAD
from ...Utils.mastro_cad.cad.circle_utils import (check_circle, circle_centroid_world,
                                                    circle_plane_axes, circle_points,
                                                    get_circle_layers, CIRCLE_TYPES)
from ...Utils.mastro_cad.cad.gpu_utils    import radius_to_pixels
from ...Operators.mastro_cad.CAD_mixin    import CadMixin


_handle_2d = None   # POST_PIXEL — handle squares
_status_shown = False  # tracks whether the Alt+G hint is currently set




def _get_context_parts(context):
    rv3d   = context.region_data
    region = context.region
    if rv3d is None or region is None:
        return None, None
    return rv3d, region


def _draw_handle_square(shader, region, rv3d, pt_world, s):
    co_2d = location_3d_to_region_2d(region, rv3d, pt_world)
    if co_2d is None:
        return
    x, y    = co_2d
    verts   = [(x-s, y-s), (x+s, y-s), (x+s, y+s), (x-s, y+s)]
    indices = ((0, 1), (1, 2), (2, 3), (3, 0))
    batch_for_shader(shader, 'LINES', {"pos": verts}, indices=indices).draw(shader)


def _draw_handle_circle(shader, region, rv3d, pt_world, s):
    import math as _m
    co_2d = location_3d_to_region_2d(region, rv3d, pt_world)
    if co_2d is None:
        return
    x, y  = co_2d
    segs  = 12
    verts = [(x + s * _m.cos(_m.pi * 2 * i / segs),
              y + s * _m.sin(_m.pi * 2 * i / segs))
             for i in range(segs)]
    lines = []
    for i in range(segs):
        lines.extend([verts[i], verts[(i + 1) % segs]])
    batch_for_shader(shader, 'LINES', {"pos": lines}).draw(shader)


def _set_alt_g_hint(context, show):
    """Set or clear the Alt+G footer hint, only when state changes."""
    global _status_shown
    if show == _status_shown:
        return
    _status_shown = show
    if show:
        def _fn(header, ctx):
            layout = header.layout
            layout.label(text="", icon='EVENT_ALT')
            layout.separator(factor=0.3)
            layout.label(text="Edit", icon='EVENT_G')
        context.workspace.status_text_set(_fn)
    else:
        context.workspace.status_text_set(None)


def _draw_handles():
    """Draw handle squares in 2D (POST_PIXEL) for active rect or circle."""
    from ...Operators.mastro_cad.MESH_OT_EditRectangle import _rect_edit_draw_handle
    from ...Operators.mastro_cad.MESH_OT_EditCircle    import _circle_edit_draw_handle
    if _rect_edit_draw_handle is not None or _circle_edit_draw_handle is not None:
        _set_alt_g_hint(bpy.context, False)
        return   # edit operator already drawing

    context = bpy.context
    if context is None or context.mode != 'EDIT_MESH':
        _set_alt_g_hint(context, False) if context else None
        return
    obj = context.active_object
    if obj is None or obj.type != 'MESH':
        return

    rv3d, region = _get_context_parts(context)
    if rv3d is None:
        return

    bm   = bmesh.from_edit_mesh(obj.data)
    seed = CadMixin.active_seed(bm)
    if seed is None:
        _set_alt_g_hint(context, False)
        return

    mw     = obj.matrix_world
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    shader.bind()
    gpu.state.blend_set('ALPHA')
    shader.uniform_float("color", (1.0, 0.6, 0.0, 0.9))
    gpu.state.line_width_set(2.0)

    thick_layer = bm.edges.layers.float.get("mastro_drawing_thickness")
    if thick_layer is not None:
        if isinstance(seed, bmesh.types.BMEdge):
            max_thick = seed[thick_layer]
        else:
            max_thick = max((e[thick_layer] for e in seed.link_edges), default=0.0)
        thick_px = radius_to_pixels(context, max_thick) if max_thick > 0.0 else 0.0
    else:
        thick_px = 0.0
    s = max(_SZ, thick_px + _PAD)

    # Rectangle: vertex select mode only (edge mode uses native G-G slide)
    if context.tool_settings.mesh_select_mode[0]:
        ok, chain_verts, _ = check_rect(bm, seed)
        if ok:
            for v in chain_verts:
                _draw_handle_square(shader, region, rv3d, mw @ v.co, s)
            gpu.state.blend_set('NONE')
            _set_alt_g_hint(context, True)
            return

    # Circle / arc: works in both vertex and edge select mode
    ok, chain_verts, chain_edges, is_closed = check_circle(bm, seed)
    if ok:
        n_chain = len(chain_verts)
        # Handle at the active selection: vertex → vertex pos, edge → edge
        # midpoint, fallback → chain midpoint vertex.
        active_el = bm.select_history.active
        if isinstance(active_el, bmesh.types.BMVert) and active_el in chain_verts:
            handle_world = mw @ active_el.co
        elif isinstance(active_el, bmesh.types.BMEdge) and active_el in chain_edges:
            v0, v1 = active_el.verts
            handle_world = mw @ ((v0.co + v1.co) / 2)
        else:
            # Fallback: nearest selected vertex or edge midpoint in the chain.
            sel_v = next((v for v in chain_verts if v.select), None)
            sel_e = next((e for e in chain_edges if e.select), None)
            if sel_v is not None:
                handle_world = mw @ sel_v.co
            elif sel_e is not None:
                v0, v1 = sel_e.verts
                handle_world = mw @ ((v0.co + v1.co) / 2)
            else:
                handle_world = mw @ chain_verts[n_chain // 2].co
        # Determine type.
        _layers = get_circle_layers(bm)
        _is_fillet = (_layers is not None and
                      chain_verts[0][_layers[0]] == b"Fillet")
        if _is_fillet:
            _draw_handle_circle(shader, region, rv3d, handle_world, s)
            gpu.state.blend_set('NONE')
            _set_alt_g_hint(context, True)
            return
        # Radius handle (square) + centre handle (circle).
        _draw_handle_square(shader, region, rv3d, handle_world, s)
        from ...Utils.mastro_cad.cad.circle_utils import arc_circumcenter_world
        center_world = arc_circumcenter_world(chain_verts, mw)
        _draw_handle_circle(shader, region, rv3d, center_world, s)
        # Arc handles (> <) — only for open arcs, not full circles
        if not is_closed and len(chain_verts) >= 4:
            arc_start_world = mw @ chain_verts[0].co
            arc_end_world   = mw @ chain_verts[-1].co
            _draw_handle_circle(shader, region, rv3d, arc_start_world, s)
            _draw_handle_circle(shader, region, rv3d, arc_end_world,   s)
        gpu.state.blend_set('NONE')
        _set_alt_g_hint(context, True)
        return

    gpu.state.line_width_set(1.0)
    _set_alt_g_hint(context, False)
    gpu.state.blend_set('NONE')


def register():
    global _handle_2d
    _handle_2d = bpy.types.SpaceView3D.draw_handler_add(
        _draw_handles, (), 'WINDOW', 'POST_PIXEL')


def unregister():
    global _handle_2d
    if _handle_2d is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_handle_2d, 'WINDOW')
        _handle_2d = None
