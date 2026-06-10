"""Edit-mode selection overlay for MaStro Drawing Mesh objects.

Draws selected edges as filled rounded strokes in screen space (POST_PIXEL),
matching the visual width of the Grease Pencil output of the GN modifier.
"""

import bpy
import bmesh
from collections import defaultdict
from bpy_extras.view3d_utils import location_3d_to_region_2d

from ...Utils.mastro_cad.cad.gpu_utils import radius_to_pixels, draw_strokes_2d, draw_disks_2d
from ...Utils.mastro_cad.cad.constants import DRAWING_SEL_COLOR, DRAWING_ACTIVE_COLOR

_handle = None


def _draw():
    context = bpy.context
    if context.mode != 'EDIT_MESH':
        return
    obj = context.active_object
    if obj is None or obj.type != 'MESH':
        return
    if not obj.data.get("MaStro drawing mesh"):
        return

    region = context.region
    rv3d   = context.space_data.region_3d
    if rv3d is None:
        return

    bm          = bmesh.from_edit_mesh(obj.data)
    mw          = obj.matrix_world
    thick_layer = bm.edges.layers.float.get("mastro_drawing_thickness")
    active_elt  = bm.select_history.active
    active_edge = active_elt if isinstance(active_elt, bmesh.types.BMEdge) else None

    def to_screen(co_world):
        return location_3d_to_region_2d(region, rv3d, mw @ co_world)

    # Collect edges grouped by (is_active) for two colour passes.
    sel_segs    = [];  sel_hws    = []
    active_segs = [];  active_hws = []

    for e in bm.edges:
        if not e.select:
            continue
        radius = e[thick_layer] if thick_layer is not None else 0.0
        if radius <= 0.0:
            continue
        s0 = to_screen(e.verts[0].co)
        s1 = to_screen(e.verts[1].co)
        if s0 is None or s1 is None:
            continue
        hw = radius_to_pixels(context, radius)
        if e is active_edge:
            active_segs.append((s0, s1));  active_hws.append(hw)
        else:
            sel_segs.append((s0, s1));     sel_hws.append(hw)

    if sel_segs:
        draw_strokes_2d(sel_segs,    sel_hws,    DRAWING_SEL_COLOR)
    if active_segs:
        draw_strokes_2d(active_segs, active_hws, DRAWING_ACTIVE_COLOR)

    # Vertex dots — sized to the first connected edge's radius.
    active_vert = active_elt if isinstance(active_elt, bmesh.types.BMVert) else None

    vert_radii = {}
    if thick_layer is not None:
        for e in bm.edges:
            r = e[thick_layer]
            if r <= 0.0:
                continue
            for v in e.verts:
                if v.index not in vert_radii:
                    vert_radii[v.index] = r

    sel_verts    = [];  sel_vhws    = []
    active_verts = [];  active_vhws = []

    for v in bm.verts:
        if not v.select:
            continue
        radius = vert_radii.get(v.index, 0.0)
        if radius <= 0.0:
            continue
        co = to_screen(v.co)
        if co is None:
            continue
        hw = radius_to_pixels(context, radius)
        if v is active_vert:
            active_verts.append(co);  active_vhws.append(hw)
        else:
            sel_verts.append(co);     sel_vhws.append(hw)

    if sel_verts:
        draw_disks_2d(sel_verts,    sel_vhws,    DRAWING_SEL_COLOR)
    if active_verts:
        draw_disks_2d(active_verts, active_vhws, DRAWING_ACTIVE_COLOR)


def register():
    global _handle
    if _handle is None:
        _handle = bpy.types.SpaceView3D.draw_handler_add(
            _draw, (), 'WINDOW', 'POST_PIXEL')


def unregister():
    global _handle
    if _handle is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_handle, 'WINDOW')
        _handle = None
