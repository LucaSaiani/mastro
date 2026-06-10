"""Delete Segment operator.

Removes the portion of an edge between its intersection points with other edges.
Three interaction modes share the same core delete-segment logic:

  CLICK    : hover over an edge (silent snap), LMB deletes the sub-segment under
             the cursor. Stays active for multiple successive clicks. RMB exits.
  POLYLINE : draw a polyline with LMB clicks; every mesh edge crossed by the
             polyline has its intersected sub-segment deleted. RMB/Enter confirms
             and exits. Edges with no mesh intersections are deleted entirely.
  BOX      : LMB to set first corner, LMB again to confirm; edges fully inside
             are deleted, edges crossing the border lose their inside sub-segment.

Core algorithm (all modes):
  1. Identify target edges (via silent snap, polyline crossing, or box).
  2. For each target edge, compute intersection points with all other visible
     edges (compute_edge_cuts). These become the sub-segment boundaries.
  3. Determine which sub-segment contains the selection indicator (click point,
     polyline crossing t, or box interior midpoint).
  4. Delete that sub-segment, preserve the rest with all custom attributes.
  5. Remove orphan endpoints; dissolve collinear cut vertices we created.

Important: _pending_ops is updated only when LMB adds a confirmed polyline point,
NOT on live mouse moves. The live preview (mouse as last point) is purely visual
and does not affect what gets applied on confirmation.

Controls:
  LMB       : delete segment (CLICK) / add polyline point (POLYLINE) / set corner (BOX)
  RMB/Enter : exit (CLICK) / confirm and exit (POLYLINE, BOX)
  Tab       : cycle modes CLICK → POLYLINE → BOX → CLICK
  C         : toggle coplanar-only vs screen projection
  ESC       : cancel without applying
"""

import bpy
import bmesh
import math
from mathutils import Vector
from bpy_extras.view3d_utils import (location_3d_to_region_2d,
                                     region_2d_to_location_3d)
import gpu
from gpu_extras.batch import batch_for_shader

from ...Utils.mastro_cad.cad.cad_utils import (compute_edge_cuts, signed_dist_2d,
                                    copy_bm_edge_attrs, copy_bm_vert_attrs)
from ...Utils.mastro_cad.cad.gpu_utils  import draw_dotted_polyline, draw_strokes_2d, radius_to_pixels
from ...Utils.mastro_cad.cad.constants  import SNAP_RADIUS_EDGE_PX
from .CAD_mixin             import CadMixin

_delete_seg_draw_handle = None

# ── Screen-space edge proximity ───────────────────────────────────────────────

def _pt_to_seg_2d(px, py, ax, ay, bx, by):
    """Signed distance and parameter t of closest point on segment (a,b) to (p)."""
    dx = bx - ax;  dy = by - ay
    l2 = dx*dx + dy*dy
    if l2 < 1e-10:
        return math.hypot(px - ax, py - ay), 0.0
    t  = max(0.0, min(1.0, ((px-ax)*dx + (py-ay)*dy) / l2))
    cx = ax + t*dx;  cy = ay + t*dy
    return math.hypot(px - cx, py - cy), t


def _find_edge_under_mouse(context, mouse_2d, threshold_px=None):
    """Return (edge_obj_ref, t_on_edge, v0_world, v1_world) for the edge nearest
    to mouse_2d within threshold_px, or None.

    Iterates all visible mesh edges and projects them to screen space.
    No SnapContext is used — this is intentionally silent (no UI indicator).
    """
    if threshold_px is None:
        threshold_px = SNAP_RADIUS_EDGE_PX

    region = context.region
    rv3d   = context.space_data.region_3d
    mx, my = mouse_2d

    best_dist = threshold_px
    best      = None

    candidates = [o for o in context.scene.objects
                  if o.visible_get() and o.type == 'MESH']

    for obj in candidates:
        mw = obj.matrix_world
        is_edit = (obj.mode == 'EDIT')
        bm = bmesh.from_edit_mesh(obj.data) if is_edit else bmesh.new()
        if not is_edit:
            bm.from_mesh(obj.data)

        for e in bm.edges:
            if e.hide:
                continue
            v0_w = mw @ e.verts[0].co
            v1_w = mw @ e.verts[1].co
            p0_2d = location_3d_to_region_2d(region, rv3d, v0_w)
            p1_2d = location_3d_to_region_2d(region, rv3d, v1_w)
            if p0_2d is None or p1_2d is None:
                continue
            dist, t = _pt_to_seg_2d(mx, my,
                                     p0_2d[0], p0_2d[1],
                                     p1_2d[0], p1_2d[1])
            if dist < best_dist:
                best_dist = dist
                best = (e.index, obj, t, v0_w.copy(), v1_w.copy())

        if not is_edit:
            bm.free()

    return best   # (edge_index, obj, t, v0_world, v1_world) or None


# ── Polyline / box intersection helpers ──────────────────────────────────────

def _seg2d_param(ax, ay, bx, by, cx, cy, dx, dy):
    """Return (t_ab, t_cd) for intersection of 2D segments, or None."""
    ex = bx-ax;  ey = by-ay
    fx = dx-cx;  fy = dy-cy
    cross = ex*fy - ey*fx
    if abs(cross) < 1e-10:
        return None
    gx = cx-ax;  gy = cy-ay
    t  = (gx*fy - gy*fx) / cross
    u  = (gx*ey - gy*ex) / cross
    return t, u


def _polyline_crosses_edge_2d(poly_pts_2d, e0_2d, e1_2d):
    """Return list of (t_on_edge, seg_idx) where the polyline crosses the edge.
    Only counts crossings where both parameters are in [0,1].
    """
    hits = []
    for i in range(len(poly_pts_2d) - 1):
        p0 = poly_pts_2d[i];   p1 = poly_pts_2d[i+1]
        res = _seg2d_param(e0_2d[0], e0_2d[1], e1_2d[0], e1_2d[1],
                           p0[0], p0[1], p1[0], p1[1])
        if res is None:
            continue
        t_edge, t_poly = res
        if -1e-4 <= t_edge <= 1.0+1e-4 and -1e-4 <= t_poly <= 1.0+1e-4:
            hits.append((max(0.0, min(1.0, t_edge)), i))
    return hits


def _point_in_box_2d(px, py, x0, y0, x1, y1):
    return min(x0,x1) <= px <= max(x0,x1) and min(y0,y1) <= py <= max(y0,y1)


# ── Core delete-segment operation ─────────────────────────────────────────────

def _edge_radius(obj, edge_idx):
    """Return the mastro_drawing_thickness of the edge, or 0.0 if not set."""
    import bmesh as _bmesh
    is_edit = obj.mode == 'EDIT'
    bm = _bmesh.from_edit_mesh(obj.data) if is_edit else _bmesh.new()
    if not is_edit:
        bm.from_mesh(obj.data)
    try:
        bm.edges.ensure_lookup_table()
        layer = bm.edges.layers.float.get('mastro_drawing_thickness')
        if layer is None or edge_idx >= len(bm.edges):
            return 0.0
        return bm.edges[edge_idx][layer]
    finally:
        if not is_edit:
            bm.free()


def _collect_other_edges(context, exclude_edge_idx, exclude_obj):
    """Return list of (v0_world, v1_world) for all visible edges except the target."""
    result = []
    candidates = [o for o in context.scene.objects
                  if o.visible_get() and o.type == 'MESH']
    for obj in candidates:
        mw = obj.matrix_world
        is_edit = (obj.mode == 'EDIT')
        bm = bmesh.from_edit_mesh(obj.data) if is_edit else bmesh.new()
        if not is_edit:
            bm.from_mesh(obj.data)
        for e in bm.edges:
            if e.hide:
                continue
            if obj == exclude_obj and e.index == exclude_edge_idx:
                continue
            result.append((mw @ e.verts[0].co, mw @ e.verts[1].co))
        if not is_edit:
            bm.free()
    return result


def _find_sub_segment(cuts, t_indicator):
    """Given sorted (t, pt) cut list and an indicator t, return (i_lo, i_hi)
    indices into the augmented boundary list [0] + cuts + [1].

    Returns (lo, hi) where lo and hi are indices into the boundaries list such
    that boundaries[lo] <= t_indicator <= boundaries[hi].
    """
    boundaries = [0.0] + [c[0] for c in cuts] + [1.0]
    for i in range(len(boundaries) - 1):
        if boundaries[i] - 1e-6 <= t_indicator <= boundaries[i+1] + 1e-6:
            return i, i+1
    return 0, 1


def _try_dissolve_collinear(bm, v, src_edge_for_attrs):
    """If v has exactly 2 collinear edges, dissolve it by merging them.

    Only call this on vertices WE created (intersection points), not original
    mesh vertices. Merges the two edges into one, preserving attributes.
    """
    if not v.is_valid or len(v.link_edges) != 2:
        return
    e0, e1 = v.link_edges
    va = e0.other_vert(v)
    vb = e1.other_vert(v)
    # Check collinearity: the two edges must point in opposite directions from v.
    d0 = (va.co - v.co)
    d1 = (vb.co - v.co)
    l0, l1 = d0.length, d1.length
    if l0 < 1e-8 or l1 < 1e-8:
        return
    if (d0 / l0).dot(d1 / l1) > -0.9998:   # not collinear (< ~179°)
        return
    # Merge: create one edge from va to vb, copy attrs from the longer sub-edge.
    src = e0 if l0 >= l1 else e1
    ne  = bm.edges.new((va, vb))
    copy_bm_edge_attrs(bm, src, ne)
    ne.select = src.select
    # Delete the vertex — cascades to both edges.
    bmesh.ops.delete(bm, geom=[v], context='VERTS')


def _apply_delete_segment(context, edge_idx, obj, cuts, t_indicators,
                           coplanar_only, edge_map=None):
    """Delete sub-segments of edge (edge_idx on obj) indicated by t_indicators.

    t_indicators: a single float or a list of floats, one per sub-segment
                  to delete (e.g. polyline may cross the same edge multiple times).
    cuts: sorted list of (t, point_world) intersection points with other edges.
    Splits the edge at each cut point, deletes the selected sub-segments, removes
    orphan endpoints, and dissolves collinear cut vertices we created.
    All custom attributes (CAD tags, drawing style) are preserved on kept edges.
    """
    if obj.mode != 'EDIT':
        return

    bm     = bmesh.from_edit_mesh(obj.data)
    mw_inv = obj.matrix_world.inverted()

    if edge_map is not None:
        edge = edge_map.get(edge_idx)
        if edge is None or not edge.is_valid:
            return
    else:
        bm.edges.ensure_lookup_table()
        edge = bm.edges[edge_idx]
        if not edge.is_valid:
            return

    if not cuts:
        # No mesh intersections: delete the whole edge.
        verts = list(edge.verts)
        bmesh.ops.delete(bm, geom=[edge], context='EDGES')
        for v in verts:
            if v.is_valid and not v.link_edges:
                bmesh.ops.delete(bm, geom=[v], context='VERTS')
        bmesh.update_edit_mesh(obj.data)
        return

    # Normalise: accept a single float or a list.
    if isinstance(t_indicators, float):
        t_indicators = [t_indicators]

    # Collect the unique set of sub-segment indices to delete.
    delete_set = set()
    for t in t_indicators:
        lo, _ = _find_sub_segment(cuts, t)
        delete_set.add(lo)

    v0_bm = edge.verts[0]
    v1_bm = edge.verts[1]

    boundaries = [(0.0, None, v0_bm)] \
               + [(t, pt, None) for t, pt in cuts] \
               + [(1.0, None, v1_bm)]
    n = len(boundaries)

    # ── Pre-delete analysis ───────────────────────────────────────────────────
    # Original endpoints become orphan if ALL adjacent sub-segments are deleted
    # AND they have no other edges in the mesh.
    # Sub-segment 0 is adjacent to v0_bm; sub-segment n-2 is adjacent to v1_bm.
    delete_v0 = (0 in delete_set     and len(v0_bm.link_edges) == 1)
    delete_v1 = ((n-2) in delete_set and len(v1_bm.link_edges) == 1)

    # ── Create cut vertices ───────────────────────────────────────────────────
    created_verts = []
    for i in range(1, n - 1):
        t, pt_world, _ = boundaries[i]
        v_new = bm.verts.new(mw_inv @ pt_world)
        src_v = v0_bm if t < 0.5 else v1_bm
        copy_bm_vert_attrs(bm, src_v, v_new)
        boundaries[i] = (t, pt_world, v_new)
        created_verts.append(v_new)

    # ── Rebuild kept sub-segments ─────────────────────────────────────────────
    for i in range(n - 1):
        if i in delete_set:
            continue
        va = boundaries[i][2]
        vb = boundaries[i + 1][2]
        ne = bm.edges.new((va, vb))
        copy_bm_edge_attrs(bm, edge, ne)
        ne.select = edge.select

    # ── Delete original edge + planned orphan endpoints ───────────────────────
    bmesh.ops.delete(bm, geom=[edge], context='EDGES')

    if delete_v0 and v0_bm.is_valid:
        bmesh.ops.delete(bm, geom=[v0_bm], context='VERTS')
    if delete_v1 and v1_bm.is_valid and v1_bm != v0_bm:
        bmesh.ops.delete(bm, geom=[v1_bm], context='VERTS')

    # ── Dissolve created vertices with exactly 2 collinear edges ─────────────
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    for v in created_verts:
        _try_dissolve_collinear(bm, v, edge)

    bmesh.update_edit_mesh(obj.data)


# ── Operator ──────────────────────────────────────────────────────────────────

class MESH_OT_MaStroCad_DeleteSegment(CadMixin, bpy.types.Operator):
    """Delete the portion of an edge between its intersections with other edges."""
    bl_idname  = "mastrocad.delete_segment"
    bl_label   = "Delete Segment"
    bl_options = {'REGISTER', 'UNDO'}

    coplanar_only: bpy.props.BoolProperty(
        name="Coplanar Only",
        description="Only consider edges truly coplanar with the target. "
                    "Off: use screen-space projection",
        default=True,
    )

    # ── Modal state ───────────────────────────────────────────────────────────
    _draw_handle    = None
    _sub_mode       = 'CLICK'    # 'CLICK' | 'POLYLINE' | 'BOX'
    _poly_pts_2d    = None       # screen-space polyline points (POLYLINE mode)
    _poly_pts_3d    = None       # world-space polyline points (for GPU)
    _box_corner_2d  = None       # anchor corner for box (BOX mode)
    _mouse_2d       = (0, 0)     # current mouse screen position
    _hover          = None       # click-mode hover: (edge_idx, obj, t, v0_w, v1_w)
    _hover_cuts     = None       # cuts along hovered edge
    _preview        = None       # GPU preview data
    _pending_ops    = None       # list of (edge_idx, obj, cuts, t_indicators) ready to apply

    # ── Poll ──────────────────────────────────────────────────────────────────

    @classmethod
    def poll(cls, context):
        if not CadMixin.poll(context):
            return False
        return (context.mode == 'EDIT_MESH'
                and context.active_object is not None)

    # ── GPU draw ──────────────────────────────────────────────────────────────

    def _draw_preview(self, context):
        """POST_VIEW: draw the orange polyline cursor only."""
        try:
            sub_mode = self._sub_mode
            poly3d   = self._poly_pts_3d
            mouse_2d = self._mouse_2d
        except ReferenceError:
            global _delete_seg_draw_handle
            if _delete_seg_draw_handle is not None:
                for h in _delete_seg_draw_handle:
                    try:
                        bpy.types.SpaceView3D.draw_handler_remove(h, 'WINDOW')
                    except Exception:
                        pass
                _delete_seg_draw_handle = None
            return

        if sub_mode == 'POLYLINE' and poly3d and len(poly3d) >= 1:
            pts = poly3d[:]
            region = context.region
            rv3d   = context.region_data
            if rv3d and len(poly3d) >= 1:
                depth = poly3d[-1]
                last_w = region_2d_to_location_3d(region, rv3d, mouse_2d, depth)
                if last_w:
                    pts = pts + [last_w]
            if len(pts) >= 2:
                draw_dotted_polyline(pts, closed=False, context=context,
                                     color=(1.0, 0.6, 0.0, 0.9))

    def _draw_preview_2d(self, context):
        """POST_PIXEL: draw the red remove-segments scaled to edge thickness."""
        try:
            preview = self._preview
        except ReferenceError:
            return
        if not preview or not preview.get('remove'):
            return

        region = context.region
        rv3d   = context.space_data.region_3d
        segs_w = preview['remove']   # flat [v0, v1, v0, v1, ...]
        radius = preview.get('radius') or 0.0

        MIN_HW = 2.0
        hw = max(radius_to_pixels(context, radius) if radius > 0.0 else 0.0, MIN_HW)

        segments_px = []
        half_widths = []
        for i in range(0, len(segs_w), 2):
            p0 = location_3d_to_region_2d(region, rv3d, segs_w[i])
            p1 = location_3d_to_region_2d(region, rv3d, segs_w[i + 1])
            if p0 is None or p1 is None:
                continue
            segments_px.append((p0, p1))
            half_widths.append(hw)

        if segments_px:
            draw_strokes_2d(segments_px, half_widths, (1.0, 0.2, 0.2, 0.9))

    def _draw_box_2d(self, context):
        """POST_PIXEL: rubber-band box for BOX mode."""
        try:
            sub_mode = self._sub_mode
            corner   = self._box_corner_2d
            mouse    = self._mouse_2d
        except ReferenceError:
            return

        if sub_mode != 'BOX' or corner is None:
            return

        x0, y0 = corner
        x1, y1 = mouse
        verts = [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
        indices = [(0,1),(1,2),(2,3),(3,0)]

        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        shader.bind()
        gpu.state.blend_set('ALPHA')
        shader.uniform_float("color", (1.0, 0.6, 0.0, 0.6))
        gpu.state.line_width_set(1.0)
        batch_for_shader(shader, 'LINES', {"pos": verts},
                         indices=indices).draw(shader)
        gpu.state.blend_set('NONE')

    # ── Preview computation ───────────────────────────────────────────────────

    def _update_click_preview(self, context):
        """Compute hover edge and preview for CLICK mode."""
        hover = _find_edge_under_mouse(context, self._mouse_2d)
        self._hover = hover
        if hover is None:
            self._hover_cuts = None
            self._preview = None
            return

        edge_idx, obj, t_click, v0_w, v1_w = hover
        others = _collect_other_edges(context, edge_idx, obj)
        cuts   = compute_edge_cuts(v0_w, v1_w, others,
                                    self.coplanar_only, context)
        self._hover_cuts = cuts

        lo, hi = _find_sub_segment(cuts, t_click)
        boundaries_t = [0.0] + [c[0] for c in cuts] + [1.0]
        td = v1_w - v0_w

        keep_segs   = []
        remove_segs = []
        for i in range(len(boundaries_t) - 1):
            pa = v0_w + td * boundaries_t[i]
            pb = v0_w + td * boundaries_t[i+1]
            if i == lo:
                remove_segs.extend([pa, pb])
            else:
                keep_segs.extend([pa, pb])

        self._preview = {'keep': keep_segs, 'remove': remove_segs,
                         'radius': _edge_radius(obj, edge_idx)}

    def _preview_for_indicator(self, context, t_indicators, v0_w, v1_w,
                               edge_idx, obj,
                               keep_segs, remove_segs):
        """Shared helper: compute real sub-segments for one edge, classify
        them as keep/remove, and cache the operation in _pending_ops.

        t_indicators: float or list of floats (one per crossing).
        The cached pending op is consumed by _apply_from_preview.
        """
        others = _collect_other_edges(context, edge_idx, obj)
        cuts   = compute_edge_cuts(v0_w, v1_w, others,
                                    self.coplanar_only, context)
        if not cuts:
            # Edge has no mesh intersections — delete it entirely.
            remove_segs.extend([v0_w, v1_w])
            if self._pending_ops is not None:
                self._pending_ops.append((edge_idx, obj, [], t_indicators))
            return

        if isinstance(t_indicators, float):
            t_indicators = [t_indicators]

        delete_set = set()
        for t in t_indicators:
            lo, _ = _find_sub_segment(cuts, t)
            delete_set.add(lo)

        td = v1_w - v0_w
        boundaries_t = [0.0] + [c[0] for c in cuts] + [1.0]

        for i in range(len(boundaries_t) - 1):
            pa = v0_w + td * boundaries_t[i]
            pb = v0_w + td * boundaries_t[i + 1]
            if i in delete_set:
                remove_segs.extend([pa, pb])
            else:
                keep_segs.extend([pa, pb])

        # Cache for apply only when in confirmed mode (not live preview).
        if self._pending_ops is not None:
            self._pending_ops.append((edge_idx, obj, cuts, list(t_indicators)))

    def _update_polyline_preview(self, context):
        """Compute the actual sub-segments that POLYLINE mode would delete."""
        if not self._poly_pts_2d or len(self._poly_pts_2d) < 2:
            self._preview    = None
            self._pending_ops = []
            return

        region = context.region
        rv3d   = context.space_data.region_3d
        poly2d = self._poly_pts_2d

        keep_segs    = []
        remove_segs  = []
        self._pending_ops = []   # reset; _preview_for_indicator will fill it

        candidates = [o for o in context.scene.objects
                      if o.visible_get() and o.type == 'MESH']

        for obj in candidates:
            mw = obj.matrix_world
            is_edit = (obj.mode == 'EDIT')
            if not is_edit:
                continue   # preview only for editable mesh
            bm = bmesh.from_edit_mesh(obj.data)

            for e in bm.edges:
                if e.hide:
                    continue
                v0_w = mw @ e.verts[0].co
                v1_w = mw @ e.verts[1].co
                p0_2d = location_3d_to_region_2d(region, rv3d, v0_w)
                p1_2d = location_3d_to_region_2d(region, rv3d, v1_w)
                if p0_2d is None or p1_2d is None:
                    continue

                hits = _polyline_crosses_edge_2d(poly2d, p0_2d, p1_2d)
                if not hits:
                    continue

                t_inds = [h[0] for h in hits]
                self._preview_for_indicator(
                    context, t_inds, v0_w, v1_w,
                    e.index, obj, keep_segs, remove_segs)

        self._preview = {'keep': keep_segs, 'remove': remove_segs, 'radius': None}

    def _update_box_preview(self, context):
        """Compute the actual sub-segments that BOX mode would delete."""
        if self._box_corner_2d is None:
            self._preview    = None
            self._pending_ops = []
            return

        region = context.region
        rv3d   = context.space_data.region_3d
        x0, y0 = self._box_corner_2d
        x1, y1 = self._mouse_2d
        box_poly2d = [(x0,y0),(x1,y0),(x1,y1),(x0,y1),(x0,y0)]

        keep_segs    = []
        remove_segs  = []
        self._pending_ops = []   # reset; _preview_for_indicator will fill it

        candidates = [o for o in context.scene.objects
                      if o.visible_get() and o.type == 'MESH']

        for obj in candidates:
            mw = obj.matrix_world
            is_edit = (obj.mode == 'EDIT')
            if not is_edit:
                continue
            bm = bmesh.from_edit_mesh(obj.data)

            for e in bm.edges:
                if e.hide:
                    continue
                v0_w = mw @ e.verts[0].co
                v1_w = mw @ e.verts[1].co
                p0_2d = location_3d_to_region_2d(region, rv3d, v0_w)
                p1_2d = location_3d_to_region_2d(region, rv3d, v1_w)
                if p0_2d is None or p1_2d is None:
                    continue

                # Find which sub-segment has its midpoint inside the box.
                hits = _polyline_crosses_edge_2d(box_poly2d, p0_2d, p1_2d)
                v0_in = _point_in_box_2d(p0_2d[0], p0_2d[1], x0, y0, x1, y1)
                if not hits and not v0_in:
                    continue

                cut_t = sorted(set(h[0] for h in hits))
                td = v1_w - v0_w
                boundaries_t = [0.0] + cut_t + [1.0]
                # Collect all sub-segment midpoints that fall inside the box.
                t_inds = []
                for i in range(len(boundaries_t) - 1):
                    mid_t = (boundaries_t[i] + boundaries_t[i+1]) * 0.5
                    mid_2d = location_3d_to_region_2d(
                        region, rv3d, v0_w + td * mid_t)
                    if mid_2d and _point_in_box_2d(
                            mid_2d[0], mid_2d[1], x0, y0, x1, y1):
                        t_inds.append(mid_t)

                if not t_inds:
                    continue

                self._preview_for_indicator(
                    context, t_inds, v0_w, v1_w,
                    e.index, obj, keep_segs, remove_segs)

        self._preview = {'keep': keep_segs, 'remove': remove_segs, 'radius': None}

    # ── Apply ─────────────────────────────────────────────────────────────────

    def _apply_from_preview(self, context):
        """Apply the pending operations computed during the last preview update.

        Builds index→edge maps per-object BEFORE any modification so that
        index reuse after delete+create cycles doesn't corrupt later lookups.
        """
        if not self._pending_ops:
            return
        # Build edge_map per object so edges from different meshes don't mix.
        edge_maps = {}
        for _, obj, _, _ in self._pending_ops:
            if id(obj) not in edge_maps and obj.mode == 'EDIT':
                bm = bmesh.from_edit_mesh(obj.data)
                bm.edges.ensure_lookup_table()
                bm.verts.ensure_lookup_table()
                edge_maps[id(obj)] = (obj, {e.index: e for e in bm.edges})
        for edge_idx, obj, cuts, t_inds in self._pending_ops:
            edge_map = edge_maps.get(id(obj), (None, {}))[1]
            _apply_delete_segment(context, edge_idx, obj, cuts,
                                   t_inds, self.coplanar_only,
                                   edge_map=edge_map)
        self._pending_ops = []

    def _apply_click(self, context):
        if self._hover is None or self._hover_cuts is None:
            return
        edge_idx, obj, t_click, v0_w, v1_w = self._hover
        _apply_delete_segment(context, edge_idx, obj, self._hover_cuts,
                               t_click, self.coplanar_only)

    def _apply_polyline(self, context):
        if not self._poly_pts_2d or len(self._poly_pts_2d) < 2:
            return  # need at least two points to form a segment

        region = context.region
        rv3d   = context.space_data.region_3d
        poly2d = self._poly_pts_2d

        candidates = [o for o in context.scene.objects
                      if o.visible_get() and o.type == 'MESH']

        to_process = []   # (edge_idx, obj, t_indicator, v0_w, v1_w)

        for obj in candidates:
            mw = obj.matrix_world
            is_edit = (obj.mode == 'EDIT')
            if not is_edit:
                continue   # only modify edit-mode mesh
            bm = bmesh.from_edit_mesh(obj.data)

            for e in bm.edges:
                if e.hide:
                    continue
                v0_w = mw @ e.verts[0].co
                v1_w = mw @ e.verts[1].co
                p0_2d = location_3d_to_region_2d(region, rv3d, v0_w)
                p1_2d = location_3d_to_region_2d(region, rv3d, v1_w)
                if p0_2d is None or p1_2d is None:
                    continue
                hits = _polyline_crosses_edge_2d(poly2d, p0_2d, p1_2d)
                if hits:
                    # Collect ALL crossing t values so multi-crossing cases
                    # (polyline crosses the same edge more than once) are handled.
                    t_inds = [h[0] for h in hits]
                    to_process.append((e.index, obj, t_inds, v0_w.copy(), v1_w.copy()))

        for edge_idx, obj, t_inds, v0_w, v1_w in to_process:
            others = _collect_other_edges(context, edge_idx, obj)
            cuts   = compute_edge_cuts(v0_w, v1_w, others,
                                        self.coplanar_only, context)
            _apply_delete_segment(context, edge_idx, obj, cuts,
                                   t_inds, self.coplanar_only)

    def _apply_box(self, context):
        if self._box_corner_2d is None:
            return

        region = context.region
        rv3d   = context.space_data.region_3d
        x0, y0 = self._box_corner_2d
        x1, y1 = self._mouse_2d
        box_poly2d = [(x0,y0),(x1,y0),(x1,y1),(x0,y1),(x0,y0)]

        candidates = [o for o in context.scene.objects
                      if o.visible_get() and o.type == 'MESH']

        to_process = []

        for obj in candidates:
            mw = obj.matrix_world
            is_edit = (obj.mode == 'EDIT')
            if not is_edit:
                continue
            bm = bmesh.from_edit_mesh(obj.data)

            for e in bm.edges:
                if e.hide:
                    continue
                v0_w = mw @ e.verts[0].co
                v1_w = mw @ e.verts[1].co
                p0_2d = location_3d_to_region_2d(region, rv3d, v0_w)
                p1_2d = location_3d_to_region_2d(region, rv3d, v1_w)
                if p0_2d is None or p1_2d is None:
                    continue

                hits = _polyline_crosses_edge_2d(box_poly2d, p0_2d, p1_2d)
                v0_in = _point_in_box_2d(p0_2d[0], p0_2d[1], x0, y0, x1, y1)

                if not hits and not v0_in:
                    continue  # fully outside

                # Use midpoint of the inside portion as indicator.
                cut_t = sorted(set(h[0] for h in hits))
                boundaries_t = [0.0] + cut_t + [1.0]
                td = v1_w - v0_w

                for i in range(len(boundaries_t) - 1):
                    mid_t = (boundaries_t[i] + boundaries_t[i+1]) * 0.5
                    mid_w = v0_w + td * mid_t
                    mid_2d = location_3d_to_region_2d(region, rv3d, mid_w)
                    if mid_2d and _point_in_box_2d(
                            mid_2d[0], mid_2d[1], x0, y0, x1, y1):
                        to_process.append((e.index, obj, mid_t,
                                           v0_w.copy(), v1_w.copy()))
                        break  # one indicator per edge is enough

        for edge_idx, obj, t_ind, v0_w, v1_w in to_process:
            others = _collect_other_edges(context, edge_idx, obj)
            cuts   = compute_edge_cuts(v0_w, v1_w, others,
                                        self.coplanar_only, context)
            _apply_delete_segment(context, edge_idx, obj, cuts,
                                   t_ind, self.coplanar_only)

    # ── Header / footer ───────────────────────────────────────────────────────

    def _update_header(self, context, modifier=None):
        cop      = "ON" if self.coplanar_only else "OFF"
        mode_info = {
            'CLICK':    ("Click",    "Delete Segment", "Exit",    False),
            'POLYLINE': ("Polyline", "Add Point",      "Confirm", True),
            'BOX':      ("Box",      "Set Corner",     "Confirm", True),
        }
        mode_name, lmb_lbl, rmb_lbl, has_cancel = mode_info[self._sub_mode]
        context.area.header_text_set(
            f"Delete Segment  |  Mode: {mode_name}  |  Coplanar: {cop}")
        extra_keys = [("Cancel", 'EVENT_ESC'), None] if has_cancel else []
        self.set_status(context, modifier,
            mouse=[( lmb_lbl, 'MOUSE_LMB'), None, (rmb_lbl, 'MOUSE_RMB')],
            keys=extra_keys + [
                (f"Mode ({mode_name})", 'EVENT_Q'),
                None,
                ("Coplanar", 'EVENT_C', self.coplanar_only),
            ],
        )

    # ── Modal ─────────────────────────────────────────────────────────────────

    def modal(self, context, event):
        try:
            return self._modal_impl(context, event)
        except ReferenceError:
            self._remove_handlers()
            return {'CANCELLED'}

    def _modal_impl(self, context, event):
        if self.left_edit_mode(context, self._started_in_edit):
            self._remove_handlers()
            context.area.header_text_set(None)
            self.clear_status(context)
            return {'CANCELLED'}

        nav = self.pass_through_navigation(event)
        if nav is not None:
            return nav

        modifier = self.modifier_from_event(event)
        mx, my   = event.mouse_region_x, event.mouse_region_y
        self._mouse_2d = (mx, my)

        if event.type in {'LEFT_CTRL', 'RIGHT_CTRL', 'LEFT_SHIFT', 'RIGHT_SHIFT'}:
            self._update_header(context, modifier)
            return {'RUNNING_MODAL'}

        if event.alt:
            return {'PASS_THROUGH'}

        # ── Mouse move ────────────────────────────────────────────────────────
        if event.type in {'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE'}:
            if self._sub_mode == 'CLICK':
                self._update_click_preview(context)
            elif self._sub_mode == 'POLYLINE':
                self._update_polyline_preview_live(context)
            elif self._sub_mode == 'BOX' and self._box_corner_2d is not None:
                self._update_box_preview(context)
            context.area.tag_redraw()

        # ── Left click ────────────────────────────────────────────────────────
        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            if self._sub_mode == 'CLICK':
                self._apply_click(context)
                self._update_click_preview(context)
                context.area.tag_redraw()

            elif self._sub_mode == 'POLYLINE':
                pt_2d = (mx, my)
                self._poly_pts_2d.append(pt_2d)
                depth = (self._poly_pts_3d[-1] if self._poly_pts_3d
                         else self.depth_reference(context))
                pt_3d = region_2d_to_location_3d(
                    context.region, context.space_data.region_3d, pt_2d, depth)
                if pt_3d:
                    self._poly_pts_3d.append(pt_3d)
                self._update_polyline_preview(context)
                context.area.tag_redraw()

            elif self._sub_mode == 'BOX':
                if self._box_corner_2d is None:
                    self._box_corner_2d = (mx, my)
                else:
                    self._apply_box(context)
                    self._box_corner_2d = None
                    self._preview       = None
                    context.area.tag_redraw()

        # ── RMB / Enter: confirm and exit ────────────────────────────────────
        elif event.type in {'RIGHTMOUSE', 'RET', 'NUMPAD_ENTER'} \
                and event.value == 'PRESS':
            if self._sub_mode == 'POLYLINE' and self._poly_pts_2d:
                self._apply_from_preview(context)
            elif self._sub_mode == 'BOX' and self._box_corner_2d is not None:
                # Apply exactly what the last box preview computed.
                self._apply_from_preview(context)
            # In all cases: exit the modal.
            self._remove_handlers()
            context.area.header_text_set(None)
            self.clear_status(context)
            return {'FINISHED'}

        # ── Tab: cycle CLICK → POLYLINE → BOX → CLICK ────────────────────────
        elif event.type == 'Q' and event.value == 'PRESS':
            modes = ['CLICK', 'POLYLINE', 'BOX']
            self._sub_mode      = modes[(modes.index(self._sub_mode) + 1) % 3]
            self._poly_pts_2d   = []
            self._poly_pts_3d   = []
            self._box_corner_2d = None
            self._preview       = None
            self._pending_ops   = []
            if self._sub_mode == 'CLICK':
                self._update_click_preview(context)
            self._update_header(context, modifier)
            context.area.tag_redraw()

        # ── ESC: cancel without applying ─────────────────────────────────────
        elif event.type == 'ESC' and event.value == 'PRESS':
            self._remove_handlers()
            context.area.header_text_set(None)
            self.clear_status(context)
            return {'CANCELLED'}

        # ── C: toggle coplanar ────────────────────────────────────────────────
        elif event.type == 'C' and event.value == 'PRESS':
            self.coplanar_only = not self.coplanar_only
            self._update_header(context, modifier)
            if self._sub_mode == 'CLICK':
                self._update_click_preview(context)
            context.area.tag_redraw()

        return {'RUNNING_MODAL'}

    def _update_polyline_preview_live(self, context):
        """Visual-only preview with current mouse as last point.

        Does NOT update _pending_ops — those are only updated when LMB confirms
        a new polyline point. This is purely for live visual feedback.
        """
        poly2d_live = self._poly_pts_2d + [self._mouse_2d]
        if len(poly2d_live) < 2:
            return

        region = context.region
        rv3d   = context.space_data.region_3d

        keep_segs   = []
        remove_segs = []

        saved_pending    = self._pending_ops
        self._pending_ops = None   # signal: don't accumulate ops in live mode

        saved_poly       = self._poly_pts_2d
        self._poly_pts_2d = poly2d_live

        # Rebuild preview geometry only (reuse _update_polyline_preview logic).
        candidates = [o for o in context.scene.objects
                      if o.visible_get() and o.type == 'MESH']
        for obj in candidates:
            mw = obj.matrix_world
            is_edit = (obj.mode == 'EDIT')
            if not is_edit:
                continue
            bm = bmesh.from_edit_mesh(obj.data)
            for e in bm.edges:
                if e.hide:
                    continue
                v0_w = mw @ e.verts[0].co
                v1_w = mw @ e.verts[1].co
                p0_2d = location_3d_to_region_2d(region, rv3d, v0_w)
                p1_2d = location_3d_to_region_2d(region, rv3d, v1_w)
                if p0_2d is None or p1_2d is None:
                    continue
                hits = _polyline_crosses_edge_2d(poly2d_live, p0_2d, p1_2d)
                if not hits:
                    continue
                t_inds = [h[0] for h in hits]
                self._preview_for_indicator(
                    context, t_inds, v0_w, v1_w,
                    e.index, obj, keep_segs, remove_segs)

        self._poly_pts_2d = saved_poly
        self._pending_ops = saved_pending   # restore confirmed pending_ops
        self._preview = {'keep': keep_segs, 'remove': remove_segs, 'radius': None}

    # ── Execute (Shift+R repeat) ──────────────────────────────────────────────

    def execute(self, context):
        """Re-launch the modal operator for Shift+R repeat."""
        return self.invoke(context, None)

    # ── Invoke ────────────────────────────────────────────────────────────────

    def invoke(self, context, event):
        self._started_in_edit = context.mode == 'EDIT_MESH'
        self._sub_mode      = 'CLICK'
        self._poly_pts_2d   = []
        self._poly_pts_3d   = []
        self._box_corner_2d = None
        self._mouse_2d      = ((event.mouse_region_x, event.mouse_region_y)
                               if event is not None else (0, 0))
        self._hover         = None
        self._hover_cuts    = None
        self._preview       = None
        self._pending_ops   = []

        global _delete_seg_draw_handle
        h3d  = bpy.types.SpaceView3D.draw_handler_add(
            self._draw_preview,    (context,), 'WINDOW', 'POST_VIEW')
        h2d  = bpy.types.SpaceView3D.draw_handler_add(
            self._draw_preview_2d, (context,), 'WINDOW', 'POST_PIXEL')
        h2db = bpy.types.SpaceView3D.draw_handler_add(
            self._draw_box_2d,     (context,), 'WINDOW', 'POST_PIXEL')
        self._draw_handle        = (h3d, h2d, h2db)
        _delete_seg_draw_handle  = self._draw_handle

        self._update_click_preview(context)
        self._update_header(context)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def _remove_handlers(self):
        global _delete_seg_draw_handle
        if self._draw_handle is not None:
            for h in self._draw_handle:
                bpy.types.SpaceView3D.draw_handler_remove(h, 'WINDOW')
            self._draw_handle = None
        _delete_seg_draw_handle = None
