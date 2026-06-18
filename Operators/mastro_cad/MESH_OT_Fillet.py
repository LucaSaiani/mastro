import bpy
import bmesh
import math
from mathutils import Vector
from bpy_extras.view3d_utils import region_2d_to_location_3d
import gpu
from gpu_extras.batch import batch_for_shader

from ...Utils.mastro_cad.cad.cad_utils import (compute_plane, are_coplanar, to_2d,
                                    get_attr_layers, copy_drawing_attrs,
                                    copy_bm_vert_attrs, copy_bm_edge_attrs)
from ...Utils.mastro_cad.cad.snap_utils import SnapContext
from .CAD_mixin import CadMixin, CAD_CHAR_MAP

# Module-level draw handle so it can be removed even if the operator is gc'd.
_fillet_draw_handle = None


# ── Intersection helpers ──────────────────────────────────────────────────────

def _line_intersect_2d(p1, d1, p2, d2):
    """Intersect two 2D lines p1+t*d1 and p2+s*d2.

    Returns (t, s) or None if lines are parallel.
    t is the parameter along the first line, s along the second.
    """
    # Normalise directions before cross-product so the threshold is scale-independent.
    len1 = (d1[0]**2 + d1[1]**2) ** 0.5
    len2 = (d2[0]**2 + d2[1]**2) ** 0.5
    if len1 < 1e-12 or len2 < 1e-12:
        return None
    n1 = (d1[0]/len1, d1[1]/len1)
    n2 = (d2[0]/len2, d2[1]/len2)
    cross_norm = n1[0] * n2[1] - n1[1] * n2[0]
    if abs(cross_norm) < 1e-4:
        return None  # parallel or nearly parallel

    cross = d1[0] * d2[1] - d1[1] * d2[0]
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    t = (dx * d2[1] - dy * d2[0]) / cross
    s = (dx * d1[1] - dy * d1[0]) / cross
    return t, s


def _classify_intersection(t, s):
    """Classify the intersection relative to two segments [0,1].

    Returns (on_e0, on_e1) where each is True when the intersection lies
    on the segment (including endpoints).

    Case 3: both strictly interior  → on_e0_int AND on_e1_int
    Case 2: one contains it, the other at most at a vertex
            → NOT (on_e0_int AND on_e1_int)
    Case 1: outside both
    """
    eps = 1e-6
    on_e0 = -eps <= t <= 1 + eps
    on_e1 = -eps <= s <= 1 + eps
    on_e0_int = eps < t < 1 - eps   # strictly interior
    on_e1_int = eps < s < 1 - eps
    return on_e0, on_e1, on_e0_int, on_e1_int


def _move_or_dup_vert(bm, edge, v_move, new_co):
    """Move v_move to new_co on edge, preserving all custom attributes.

    If v_move is only used by this edge, moves it in place (no new topology).
    If v_move is shared with other edges, creates a new vertex at new_co,
    re-links the edge to it (new edge + remove old), and copies all custom
    data layers so drawing attributes are fully preserved.
    Returns (vertex_at_new_co, edge_after).
    """
    others = [e for e in v_move.link_edges if e != edge]
    if not others:
        v_move.co = new_co
        return v_move, edge
    # Shared vertex — disconnect this edge by creating a new vertex + edge.
    v_keep  = edge.verts[0] if edge.verts[1] is v_move else edge.verts[1]
    v_new   = bm.verts.new(new_co)
    copy_bm_vert_attrs(bm, v_move, v_new)
    new_edge = bm.edges.new((v_keep, v_new))
    copy_bm_edge_attrs(bm, edge, new_edge)
    bm.edges.remove(edge)
    return v_new, new_edge


def _angle_ccw(origin, pt):
    """Counter-clockwise angle from origin to pt in 2D."""
    return math.atan2(pt[1] - origin[1], pt[0] - origin[0])


def _sector_from_mouse(ix, iy, arm_pts_2d, mouse_2d):
    """Return the two arm indices that bracket the mouse position (CCW order).

    arm_pts_2d : list of 2D points (the free endpoints of the two arms).
    mouse_2d   : 2D mouse position projected onto the plane.
    Returns (idx_before, idx_after) — indices into arm_pts_2d.
    """
    angles  = [_angle_ccw((ix, iy), p) for p in arm_pts_2d]
    mouse_a = _angle_ccw((ix, iy), mouse_2d)

    n = len(arm_pts_2d)
    # Sort arm indices by angle.
    order = sorted(range(n), key=lambda i: angles[i])

    # Find where mouse_a falls between consecutive (wrapped) arm angles.
    for k in range(n):
        a0 = angles[order[k]]
        a1 = angles[order[(k + 1) % n]]
        # Normalize sector to [a0, a0+2π).
        diff = (a1 - a0) % (2 * math.pi)
        mdiff = (mouse_a - a0) % (2 * math.pi)
        if mdiff < diff:
            return order[k], order[(k + 1) % n]

    # Fallback — return first two.
    return order[0], order[1]


# ── Fillet geometry ───────────────────────────────────────────────────────────

def _fillet_result(e0_pts, e1_pts, plane_axes, mouse_world):
    """Compute the fillet result for radius=0 (sharp corner).

    e0_pts, e1_pts : (world_start, world_end) for each edge.
    plane_axes     : (x_axis, y_axis, normal).
    mouse_world    : 3D mouse position.

    Returns a dict:
      'intersection' : Vector (world) — the meeting point
      'v0_keep'      : Vector (world) — endpoint of e0 to keep
      'v1_keep'      : Vector (world) — endpoint of e1 to keep
      'v0_move'      : Vector (world) — endpoint of e0 to move to intersection
      'v1_move'      : Vector (world) — endpoint of e1 to move to intersection
      'valid'        : bool
    """
    x_axis, y_axis, normal = plane_axes

    # Project to 2D.
    def w2(v):
        return (v.dot(x_axis), v.dot(y_axis))
    p0, p1 = w2(e0_pts[0]), w2(e0_pts[1])
    p2, p3 = w2(e1_pts[0]), w2(e1_pts[1])
    d0 = (p1[0]-p0[0], p1[1]-p0[1])
    d1 = (p3[0]-p2[0], p3[1]-p2[1])

    result = _line_intersect_2d(p0, d0, p2, d1)
    if result is None:
        return {'valid': False, 'reason': 'parallel'}   # Parallel lines.

    t, s = result
    on_e0, on_e1, on_e0_int, on_e1_int = _classify_intersection(t, s)

    ix = p0[0] + t * d0[0]
    iy = p0[1] + t * d0[1]

    # World-space intersection (project back, depth = average of all pts).
    depth = sum(v.dot(normal) for v in [*e0_pts, *e1_pts]) / 4
    i_world = x_axis * ix + y_axis * iy + normal * depth

    # Determine the "arm" endpoints (the free ends to keep).
    mouse_2d = w2(mouse_world)

    # Case 3 = both strictly interior.
    if on_e0_int and on_e1_int:
        # Case 3: 4 sectors — all four endpoints are arms.
        arm_pts_2d = [p0, p1, p2, p3]
        arm_world  = [e0_pts[0], e0_pts[1], e1_pts[0], e1_pts[1]]
        ia, ib = _sector_from_mouse(ix, iy, arm_pts_2d, mouse_2d)
        # All 4 sectors are valid — each gives one arm from each edge.
        e0_arm = arm_world[ia] if ia < 2 else arm_world[ib]
        e1_arm = arm_world[ib] if ia < 2 else arm_world[ia]

    elif on_e0 or on_e1:
        # Case 2: one edge contains the intersection (interior or vertex),
        # the other has it at most at a vertex (not strictly interior).
        # The "free" edge (the one not strictly containing it) determines
        # left/right via mouse.
        def _side(px, py, lx, ly, dx, dy):
            """Signed side of (px,py) relative to line through (lx,ly) dir (dx,dy)."""
            return (px - lx) * (-dy) + (py - ly) * dx

        if on_e0_int:
            # e0 strictly contains the intersection — e1 is the free edge.
            t0 = abs(0 - s); t1 = abs(1 - s)
            e1_arm = e1_pts[0] if t0 > t1 else e1_pts[1]
            sm = _side(mouse_2d[0], mouse_2d[1], p2[0], p2[1], d1[0], d1[1])
            s0 = _side(p0[0], p0[1],            p2[0], p2[1], d1[0], d1[1])
            e0_arm = e0_pts[0] if sm * s0 > 0 else e0_pts[1]
        else:
            # e1 strictly contains the intersection — e0 is the free edge.
            t0 = abs(0 - t); t1 = abs(1 - t)
            e0_arm = e0_pts[0] if t0 > t1 else e0_pts[1]
            sm = _side(mouse_2d[0], mouse_2d[1], p0[0], p0[1], d0[0], d0[1])
            s2 = _side(p2[0], p2[1],            p0[0], p0[1], d0[0], d0[1])
            e1_arm = e1_pts[0] if sm * s2 > 0 else e1_pts[1]

    else:
        # Case 1: intersection outside both edges — extend both, then Case 3.
        # The free endpoints are those farther from the intersection.
        e0_arm = e0_pts[0] if abs(0-t) > abs(1-t) else e0_pts[1]
        e1_arm = e1_pts[0] if abs(0-s) > abs(1-s) else e1_pts[1]

    # The endpoints to MOVE are those not kept.
    v0_move = e0_pts[1] if e0_arm is e0_pts[0] else e0_pts[0]
    v1_move = e1_pts[1] if e1_arm is e1_pts[0] else e1_pts[0]

    return {
        'valid':        True,
        'intersection': i_world,
        'v0_keep':      e0_arm,
        'v1_keep':      e1_arm,
        'v0_move':      v0_move,
        'v1_move':      v1_move,
        'on_e0':        on_e0,
        'on_e1':        on_e1,
    }


def _split_shared_vertex(bm0, shared, e1, t2_world, mw0_inv):
    """When e0 and e1 already share a vertex, keep it as e0's endpoint
    (caller has already moved it to t1_world) and create a new vertex for
    e1 at t2_world, rewiring e1 onto it. Returns the new vertex."""
    v1_keep = e1.verts[0] if e1.verts[1] == shared else e1.verts[1]
    new_v = bm0.verts.new(mw0_inv @ t2_world)
    copy_bm_vert_attrs(bm0, shared, new_v)
    new_e1 = bm0.edges.new((new_v, v1_keep))
    copy_bm_edge_attrs(bm0, e1, new_e1)
    bm0.edges.remove(e1)
    return new_v


def _clamp_fillet_to_segments(arc_data, ix_2d, d0, d1, arm0_2d, arm1_2d, n0, n1):
    """If either tangent point is beyond its segment endpoint, recompute the
    circle constrained to the shorter arm length."""
    from ...Utils.mastro_cad.cad.circle_utils import circle_ttp
    center_2d, radius, tang_2d, t2_2d = arc_data

    # Distance from intersection to each arm endpoint (maximum allowed reach).
    def arm_len(arm_2d):
        dx = arm_2d[0] - ix_2d[0]; dy = arm_2d[1] - ix_2d[1]
        return (dx*dx + dy*dy) ** 0.5

    # Distance from intersection to each tangent point along the arm.
    # d0/d1 point FROM arm TOWARD intersection, so tangent points are in the
    # -d direction → negate the dot product to get positive distance.
    def proj_on_arm(pt_2d, d):
        return -((pt_2d[0]-ix_2d[0])*d[0] + (pt_2d[1]-ix_2d[1])*d[1])

    l0 = arm_len(arm0_2d)
    l1 = arm_len(arm1_2d)
    p0 = proj_on_arm(tang_2d, d0)
    p1 = proj_on_arm(t2_2d,   d1)

    if p0 > l0 + 1e-6 or p1 > l1 + 1e-6:
        # One or both tangent points exceed the segment — use the arm endpoint
        # of the shorter arm as the new constraint.
        # Clamp to the arm with the smallest ratio.
        r0 = l0 / p0 if p0 > 1e-8 else 1.0
        r1 = l1 / p1 if p1 > 1e-8 else 1.0
        scale = min(r0, r1)
        # New radius proportional to the scale.
        new_radius = radius * scale
        # Recompute tangent points from new radius.
        # Tang pt on arm = intersection + (new_radius / tan(half_angle)) * arm_dir
        # Easier: scale existing tang points toward intersection.
        new_t1 = (ix_2d[0] + (tang_2d[0]-ix_2d[0])*scale,
                  ix_2d[1] + (tang_2d[1]-ix_2d[1])*scale)
        new_t2 = (ix_2d[0] + (t2_2d[0]-ix_2d[0])*scale,
                  ix_2d[1] + (t2_2d[1]-ix_2d[1])*scale)
        cx, cy = center_2d
        new_cx = ix_2d[0] + (cx - ix_2d[0]) * scale
        new_cy = ix_2d[1] + (cy - ix_2d[1]) * scale
        return (new_cx, new_cy), new_radius, new_t1, new_t2

    return arc_data


# ── Operator ──────────────────────────────────────────────────────────────────

class MESH_OT_MaStroCad_Fillet(bpy.types.Operator):
    """Fillet (or sharp-corner) two coplanar edges.

    Finds the intersection of the two edge lines and moves the relevant
    endpoints to meet at that point.  Mouse position selects the sector.
    Radius = 0 (sharp corner); arc support will be added later.
    """
    bl_idname  = "mastrocad.fillet"
    bl_label   = "Fillet"
    bl_options = {'REGISTER', 'UNDO'}

    segments: bpy.props.IntProperty(
        name="Segments",
        description="0=sharp corner  1=chamfer  2+=arc",
        default=0,
        min=0,
        max=64,
    )
    size: bpy.props.FloatProperty(
        name="Size",
        description="Radius (arc) or Length (chamfer). 0 = mouse controlled",
        default=0.0,
        min=0.0,
        subtype='DISTANCE',
    )
    limit: bpy.props.BoolProperty(
        name="Limit",
        description="Clamp when tangent point reaches the segment endpoint",
        default=True,
    )

    def draw(self, context):
        """Custom F9 redo panel."""
        layout = self.layout
        layout.use_property_split = True
        layout.prop(self, "segments")
        row = layout.row()
        row.enabled = self.segments > 0
        if self.segments == 1:
            row.prop(self, "size", text="Length")
        else:
            row.prop(self, "size", text="Radius")
        layout.prop(self, "limit")

    # ── Modal state ────────────────────────────────────────────────────────────
    _draw_handle   = None
    _preview_verts = []
    _mouse_world   = None
    _mouse_world_edge_key = None  # (obj0, e0_idx, obj1, e1_idx) _mouse_world was computed for
    _edge_key      = None  # edge_key of the pair currently being filleted (set in invoke)
    _size_input    = ""   # numeric input buffer for radius/length
    _e0_pts        = None
    _e1_pts        = None
    _plane_axes    = None
    _result        = None
    _snap          = None
    _snap_hit      = None

    # ── GPU preview ───────────────────────────────────────────────────────────

    def _draw_snap(self, context):
        try:
            snap_hit = self._snap_hit
        except ReferenceError:
            return
        if snap_hit is not None and self._snap is not None:
            self._snap.draw_indicator(snap_hit, context)

    def _draw_preview(self, context):
        try:
            verts = self._preview_verts
        except ReferenceError:
            global _fillet_draw_handle
            if _fillet_draw_handle is not None:
                if isinstance(_fillet_draw_handle, tuple):
                    for h in _fillet_draw_handle:
                        bpy.types.SpaceView3D.draw_handler_remove(h, 'WINDOW')
                else:
                    bpy.types.SpaceView3D.draw_handler_remove(_fillet_draw_handle, 'WINDOW')
                _fillet_draw_handle = None
            return
        if not verts:
            return
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        coords = [co for pair in self._preview_verts for co in pair]
        batch  = batch_for_shader(shader, 'LINES', {"pos": coords})
        shader.bind()
        shader.uniform_float("color", (1.0, 0.6, 0.0, 0.8))
        gpu.state.line_width_set(1.5)
        gpu.state.blend_set('ALPHA')
        gpu.state.depth_test_set('NONE')
        batch.draw(shader)
        gpu.state.depth_test_set('LESS_EQUAL')
        gpu.state.blend_set('NONE')


    def _update_preview(self, context, mouse_world):
        self._mouse_world = mouse_world
        self._mouse_world_edge_key = self._edge_key
        from ...Utils.mastro_cad.cad.circle_utils import circle_ttp, circle_ttr, arc_points_3d
        if self._e0_pts is None:
            return
        r = _fillet_result(self._e0_pts, self._e1_pts,
                           self._plane_axes, mouse_world)
        self._result = r
        if not r['valid']:
            self._preview_verts = []
            if r.get('reason') == 'parallel':
                context.area.header_text_set("Fillet: edges are parallel")
            return

        x_axis, y_axis, normal = self._plane_axes
        ix_world = r['intersection']

        def w2(v): return (v.dot(x_axis), v.dot(y_axis))

        # Compute the circle tangent to both arms and passing through mouse.
        ix_2d    = w2(ix_world)
        mouse_2d = w2(mouse_world)
        arm0_2d  = w2(r['v0_keep'])
        arm1_2d  = w2(r['v1_keep'])

        def unit(ax, ay, bx, by):
            dx, dy = bx-ax, by-ay
            l = (dx*dx + dy*dy)**0.5
            return (dx/l, dy/l) if l > 1e-8 else (1.0, 0.0)

        # Arm directions: from keep-point toward intersection.
        d0 = unit(arm0_2d[0], arm0_2d[1], ix_2d[0], ix_2d[1])
        d1 = unit(arm1_2d[0], arm1_2d[1], ix_2d[0], ix_2d[1])

        # Inward normals: rotate arm directions 90° toward the interior.
        # The interior is where the other arm is — determined by sign of cross.
        def perp_toward(dx, dy, ref_x, ref_y):
            """Perpendicular to (dx,dy) pointing toward (ref_x,ref_y)."""
            n0x, n0y = -dy,  dx
            n1x, n1y =  dy, -dx
            # ref relative to intersection
            return (n0x, n0y) if n0x*(ref_x-ix_2d[0])+n0y*(ref_y-ix_2d[1]) >= 0 \
                               else (n1x, n1y)

        n0 = perp_toward(d0[0], d0[1], arm1_2d[0], arm1_2d[1])
        n1 = perp_toward(d1[0], d1[1], arm0_2d[0], arm0_2d[1])

        # ── Chamfer (1 segment) ───────────────────────────────────────────────
        if self.segments == 1:
            # Bisector direction (inward).
            bx = n0[0] + n1[0]; by = n0[1] + n1[1]
            bl = (bx*bx + by*by)**0.5
            if bl > 1e-8:
                bx /= bl; by /= bl
            # Point P on bisector: from explicit length or mouse projection.
            if self._size_input and self.size > 1e-8:
                from ...Utils.mastro_cad.cad.circle_utils import chamfer_ttl
                arm0_dir = (-d0[0], -d0[1])
                arm1_dir = (-d1[0], -d1[1])
                ch = chamfer_ttl(ix_2d[0], ix_2d[1],
                                 d0[0], d0[1], d1[0], d1[1], self.size)
                if ch:
                    ct1, ct2 = ch
                    depth = ix_world.dot(normal)
                    def to_3d_2d(x2, y2):
                        return x_axis*x2 + y_axis*y2 + normal*depth
                    w_t1 = to_3d_2d(*ct1); w_t2 = to_3d_2d(*ct2)
                    r['arc'] = {'chamfer': True,
                                't1_world': w_t1, 't2_world': w_t2,
                                'v0_move_world': r['v0_move'],
                                'v1_move_world': r['v1_move']}
                    self._preview_verts = [(r['v0_keep'], w_t1),
                                           (r['v1_keep'], w_t2),
                                           (w_t1, w_t2)]
                else:
                    r['arc'] = None
                    self._preview_verts = [(r['v0_keep'], ix_world),
                                           (r['v1_keep'], ix_world)]
                return
            mp = (mouse_2d[0]-ix_2d[0])*bx + (mouse_2d[1]-ix_2d[1])*by
            if mp < 0:
                mp = 0.0
            self.size = mp   # store for header display
            px = ix_2d[0] + mp * bx
            py = ix_2d[1] + mp * by
            # Chamfer line: perpendicular to bisector through P.
            cx_dir, cy_dir = -by, bx   # perpendicular direction
            # Intersect chamfer line with arm0 (through ix in direction -d0).
            def line_intersect_2d(p0, d0_, p1, d1_):
                cross = d0_[0]*d1_[1] - d0_[1]*d1_[0]
                if abs(cross) < 1e-10: return None
                dx = p1[0]-p0[0]; dy = p1[1]-p0[1]
                t = (dx*d1_[1] - dy*d1_[0]) / cross
                return p0[0]+t*d0_[0], p0[1]+t*d0_[1]
            arm0_dir = (-d0[0], -d0[1])
            arm1_dir = (-d1[0], -d1[1])
            ct1 = line_intersect_2d((px, py), (cx_dir, cy_dir), ix_2d, arm0_dir)
            ct2 = line_intersect_2d((px, py), (cx_dir, cy_dir), ix_2d, arm1_dir)
            if ct1 and ct2:
                def to_3d_2d(x2, y2):
                    return x_axis*x2 + y_axis*y2 + normal*depth
                depth = ix_world.dot(normal)
                # Limit to segment if needed.
                def clamp_to_arm(pt, arm_2d):
                    vx = pt[0]-ix_2d[0]; vy = pt[1]-ix_2d[1]
                    arm_dx = arm_2d[0]-ix_2d[0]; arm_dy = arm_2d[1]-ix_2d[1]
                    l = (arm_dx**2+arm_dy**2)**0.5
                    if l < 1e-8: return pt
                    t_ = (vx*arm_dx+vy*arm_dy)/l**2
                    if self.limit: t_ = max(0.0, min(1.0, t_))
                    return ix_2d[0]+t_*arm_dx, ix_2d[1]+t_*arm_dy
                if self.limit:
                    ct1 = clamp_to_arm(ct1, arm0_2d)
                    ct2 = clamp_to_arm(ct2, arm1_2d)
                w_t1 = to_3d_2d(*ct1); w_t2 = to_3d_2d(*ct2)
                r['arc'] = {'chamfer': True,
                            't1_world': w_t1, 't2_world': w_t2,
                            'v0_move_world': r['v0_move'],
                            'v1_move_world': r['v1_move']}
                self._preview_verts = [
                    (r['v0_keep'], w_t1),
                    (r['v1_keep'], w_t2),
                    (w_t1, w_t2),
                ]
            else:
                r['arc'] = None
                self._preview_verts = [(r['v0_keep'], ix_world),
                                       (r['v1_keep'], ix_world)]
            return

        # ── Sharp corner (0 segments) ─────────────────────────────────────────
        if self.segments == 0:
            r['arc'] = None
            self._preview_verts = [(r['v0_keep'], ix_world),
                                   (r['v1_keep'], ix_world)]
            return

        # ── Arc (2+ segments) ─────────────────────────────────────────────────
        if self._size_input and self.size > 1e-8:
            # Explicit radius typed by user: use TTR.
            arc_data = circle_ttr(ix_2d[0], ix_2d[1],
                                  d0[0], d0[1], d1[0], d1[1],
                                  n0[0], n0[1], n1[0], n1[1],
                                  self.size)
        else:
            # Mouse-controlled: use TTP, then store computed radius.
            arc_data = circle_ttp(ix_2d[0], ix_2d[1],
                                  d0[0], d0[1], d1[0], d1[1],
                                  mouse_2d[0], mouse_2d[1],
                                  n0[0], n0[1], n1[0], n1[1])

        # Store computed radius for header display (only in mouse/TTP mode).
        if arc_data and not self._size_input:
            self.size = arc_data[1]  # update from mouse-computed radius

        # Limit: clamp tangent points to segment endpoints.
        if arc_data and self.limit:
            arc_data = _clamp_fillet_to_segments(
                arc_data, ix_2d, d0, d1, arm0_2d, arm1_2d,
                n0, n1)
            if arc_data:
                self.size = arc_data[1]  # update after clamp

        depth = ix_world.dot(normal)

        if arc_data:
            center_2d, radius, tang_2d, t2_2d = arc_data
            # Arc direction: use the inner midpoint (point on circle between
            # intersection and center) — always on the concave/fillet side.
            cx, cy = center_2d
            dx, dy = ix_2d[0] - cx, ix_2d[1] - cy
            dist_ic = (dx*dx + dy*dy) ** 0.5
            if dist_ic > 1e-8:
                inner_mid = (cx + radius * dx / dist_ic,
                             cy + radius * dy / dist_ic)
            else:
                inner_mid = tang_2d
            arc_pts = arc_points_3d(center_2d, radius, tang_2d, t2_2d,
                                    x_axis, y_axis, normal, depth,
                                    self.segments,
                                    pass_through_2d=inner_mid)
            # Store arc data for apply (inner_mid needed for correct arc direction).
            r['arc'] = {
                'center_2d': center_2d, 'radius': radius,
                'tang_2d': tang_2d, 't2_2d': t2_2d, 'depth': depth,
                'inner_mid': inner_mid,
            }
            # Preview: two trimmed arms + arc.
            def to_3d(x, y):
                return x_axis * x + y_axis * y + normal * depth
            t1_world = to_3d(*tang_2d)
            t2_world = to_3d(*t2_2d)
            pairs  = [(r['v0_keep'], t1_world), (r['v1_keep'], t2_world)]
            pairs += [(arc_pts[i], arc_pts[i+1])
                      for i in range(len(arc_pts)-1)]
        else:
            r['arc'] = None
            pairs = [(r['v0_keep'], ix_world), (r['v1_keep'], ix_world)]

        self._preview_verts = pairs

    # ── Geometry ──────────────────────────────────────────────────────────────

    @classmethod
    def poll(cls, context):
        return (context.mode == 'EDIT_MESH' and
                context.active_object is not None)

    def _get_two_edges(self, context):
        """Return [(obj,bm,edge),(obj,bm,edge)] active-edge-first, or None."""
        result = []
        for obj in context.objects_in_mode:
            if obj.type != 'MESH':
                continue
            bm = bmesh.from_edit_mesh(obj.data)
            bm.edges.ensure_lookup_table()
            for e in bm.edges:
                if e.select:
                    result.append((obj, bm, e))
            if len(result) > 2:
                return None
        if len(result) != 2:
            return None
        # Put active edge first so it becomes src_edge in _apply_fillet.
        active_obj = context.active_object
        if active_obj and active_obj.type == 'MESH':
            bm_act = bmesh.from_edit_mesh(active_obj.data)
            ae = bm_act.select_history.active
            if isinstance(ae, bmesh.types.BMEdge) and result[1][2] is ae:
                result = [result[1], result[0]]
        return result

    def _apply_fillet(self, context):
        if not self._result or not self._result['valid']:
            return

        from ...Utils.mastro_cad.cad.circle_utils import (arc_points_3d,
                                               ensure_circle_layers,
                                               set_circle_attrs)
        import math as _math

        edge_infos = self._get_two_edges(context)
        if edge_infos is None:
            return
        (obj0, bm0, e0), (obj1, bm1, e1) = edge_infos
        mw0      = obj0.matrix_world
        mw1      = obj1.matrix_world
        mw0_inv  = mw0.inverted()
        same_obj = (obj0 is obj1)

        # Ensure circle layers BEFORE saving element references (may invalidate refs).
        # Save indices now so we can restore the correct order after re-fetch.
        arc = self._result.get('arc')
        if arc and not arc.get('chamfer'):
            e0_idx = e0.index
            e1_idx = e1.index
            circle_layers = ensure_circle_layers(bm0)
            bm0.edges.ensure_lookup_table()
            e0 = bm0.edges[e0_idx]
            if same_obj:
                e1 = bm0.edges[e1_idx]
            else:
                bm1.edges.ensure_lookup_table()
                e1 = bm1.edges[e1_idx]
        else:
            circle_layers = None

        def _find_vert(edge, mw, world_pos):
            d0 = (mw @ edge.verts[0].co - world_pos).length
            d1 = (mw @ edge.verts[1].co - world_pos).length
            return edge.verts[0] if d0 < d1 else edge.verts[1]

        # Capture drawing attributes from e0 before any topology changes.
        attr_layers = get_attr_layers(bm0)
        saved_attrs = {name: e0[layer] for name, layer in attr_layers.items()} if attr_layers else {}

        if arc and arc.get('chamfer'):
            t1_world = arc['t1_world']
            t2_world = arc['t2_world']
            v0_move  = _find_vert(e0, mw0, self._result['v0_move'])
            v1_move  = _find_vert(e1, mw1, self._result['v1_move'])
            if same_obj and v0_move == v1_move:
                shared = v0_move
                shared.co = mw0_inv @ t1_world
                v1_move = _split_shared_vertex(bm0, shared, e1, t2_world, mw0_inv)
            else:
                v0_move, e0 = _move_or_dup_vert(bm0, e0, v0_move, mw0_inv @ t1_world)
                mw1_inv = mw1.inverted()
                v1_move, e1 = _move_or_dup_vert(bm1, e1, v1_move, mw1_inv @ t2_world)
            bm0.verts.ensure_lookup_table()
            if same_obj:
                ne = bm0.edges.new((v0_move, v1_move))
            else:
                end_v = bm0.verts.new(mw0_inv @ t2_world)
                ne = bm0.edges.new((v0_move, end_v))
            ne.select = True
            if saved_attrs:
                for name, layer in attr_layers.items():
                    ne[layer] = saved_attrs[name]
            bmesh.ops.remove_doubles(bm0, verts=bm0.verts, dist=1e-6)
            bmesh.update_edit_mesh(obj0.data)
            if not same_obj:
                bmesh.ops.remove_doubles(bm1, verts=bm1.verts, dist=1e-6)
                bmesh.update_edit_mesh(obj1.data)
            return

        if arc:
            x_axis, y_axis, normal = self._plane_axes
            arc_pts = arc_points_3d(
                arc['center_2d'], arc['radius'],
                arc['tang_2d'],   arc['t2_2d'],
                x_axis, y_axis, normal, arc['depth'],
                self.segments,
                pass_through_2d=arc.get('inner_mid'))

            t1_world = arc_pts[0]
            t2_world = arc_pts[-1]

            cx, cy   = arc['center_2d']
            t1x, t1y = arc['tang_2d']
            t2x, t2y = arc['t2_2d']
            a1 = _math.atan2(t1y - cy, t1x - cx)
            a2 = _math.atan2(t2y - cy, t2x - cx)
            inner_mid = arc.get('inner_mid')
            if inner_mid:
                aM       = _math.atan2(inner_mid[1] - cy, inner_mid[0] - cx)
                span_ccw = (a2 - a1) % (2 * _math.pi)
                aM_ccw   = (aM - a1) % (2 * _math.pi)
                arc_span = span_ccw if aM_ccw <= span_ccw else (2 * _math.pi - span_ccw)
            else:
                diff     = (a2 - a1) % (2 * _math.pi)
                arc_span = diff if diff <= _math.pi else 2 * _math.pi - diff
            arc_span = max(arc_span, 1e-8)
            n_total  = max(3, round(self.segments * 2 * _math.pi / arc_span))

            v0_move = _find_vert(e0, mw0, self._result['v0_move'])
            v1_move = _find_vert(e1, mw1, self._result['v1_move'])

            if same_obj and v0_move == v1_move:
                shared = v0_move
                shared.co = mw0_inv @ t1_world
                arc_end_v = _split_shared_vertex(bm0, shared, e1, t2_world, mw0_inv)
            else:
                v0_move, e0 = _move_or_dup_vert(bm0, e0, v0_move, mw0_inv @ t1_world)
                if circle_layers:
                    e0[circle_layers[4]] = 0  # trimmed edge is no longer part of an arc
                mw1_inv = mw1.inverted()
                v1_move, e1 = _move_or_dup_vert(bm1, e1, v1_move, mw1_inv @ t2_world)
                if circle_layers and same_obj:
                    e1[circle_layers[4]] = 0
                if same_obj:
                    arc_end_v = v1_move
                else:
                    # Arc lives in bm0 — create an endpoint at t2_world in bm0.
                    arc_end_v = bm0.verts.new(mw0_inv @ t2_world)

            arc_verts = [bm0.verts.new(mw0_inv @ p) for p in arc_pts[1:-1]]
            all_verts = [v0_move] + arc_verts + [arc_end_v]
            all_edges = []
            for i in range(len(all_verts) - 1):
                ne = bm0.edges.new((all_verts[i], all_verts[i + 1]))
                ne.select = True
                all_edges.append(ne)
                if saved_attrs:
                    for name, layer in attr_layers.items():
                        ne[layer] = saved_attrs[name]

            set_circle_attrs(bm0, all_verts, all_edges, n_total,
                             layers=circle_layers, type_tag=b"Fillet")
            mid_v = all_verts[len(all_verts) // 2]
            mid_e = all_edges[len(all_edges) // 2]
            mid_v.select = True
            mid_e.select  = True
            bm0.select_history.clear()
            bm0.select_history.add(mid_e)
        else:
            # Radius 0: move both endpoints to intersection.
            ix = self._result['intersection']
            v0_move = _find_vert(e0, mw0, self._result['v0_move'])
            v1_move = _find_vert(e1, mw1, self._result['v1_move'])
            v0_move.co = mw0_inv @ ix
            if not (same_obj and v0_move == v1_move):
                mw1_inv = mw1.inverted()
                v1_move.co = mw1_inv @ ix

        bmesh.ops.remove_doubles(bm0, verts=bm0.verts, dist=1e-6)
        bmesh.update_edit_mesh(obj0.data)
        if not same_obj:
            bmesh.ops.remove_doubles(bm1, verts=bm1.verts, dist=1e-6)
            bmesh.update_edit_mesh(obj1.data)

    # ── UI ────────────────────────────────────────────────────────────────────

    def _update_header(self, context):
        segs  = self.segments
        mode  = "Sharp" if segs == 0 else ("Chamfer" if segs == 1 else f"Arc ({segs})")
        if segs == 0:
            context.area.header_text_set(f"Fillet  |  {mode}")
        else:
            label = "Length" if segs == 1 else "Radius"
            val   = self._size_input if self._size_input else f"{self.size:.4f}"
            context.area.header_text_set(f"Fillet  |  {mode}  |  {label}: {val}")

        CadMixin.set_status(context,
            mouse=[("Confirm", 'MOUSE_LMB'), None, ("Cancel", 'MOUSE_RMB')],
            ctrl_mouse=[("Resolution", 'MOUSE_MMB_SCROLL')],
            keys=[("Limit", 'EVENT_L', self.limit)],
            alt_keys=[("Edit Circle/Arc", 'EVENT_G')],
        )

    # ── Modal ─────────────────────────────────────────────────────────────────

    def modal(self, context, event):
        if CadMixin.left_edit_mode(context, self._started_in_edit):
            self._remove_draw_handler()
            context.area.header_text_set(None)
            return {'CANCELLED'}
        nav = CadMixin.pass_through_navigation(self, event)
        if nav is not None:
            return nav
        if event.type in {'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE'}:
            CadMixin.maybe_rebuild_snap(self, context)
            mouse  = (event.mouse_region_x, event.mouse_region_y)
            if self._e0_pts and self._plane_axes:
                from ...Utils.mastro_cad.cad.cad_utils import ray_plane_intersect
                raw_3d   = ray_plane_intersect(
                    context, mouse, self._plane_axes, self._e0_pts[0])
                snapped  = (self._snap.snap(mouse, context, raw_world=raw_3d)
                            if self._snap and not self._size_input
                            and not event.ctrl else None)
                self._snap_hit = snapped
                mouse_3d = snapped if snapped is not None else raw_3d
            else:
                mouse_3d       = Vector((0, 0, 0))
                self._snap_hit = None
            self._update_preview(context, mouse_3d)
            self._update_header(context)
            context.area.tag_redraw()

        elif event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            if not event.ctrl:
                return {'PASS_THROUGH'}
            self.segments = (min(self.segments + 1, 64)
                             if event.type == 'WHEELUPMOUSE'
                             else max(self.segments - 1, 0))
            if self._mouse_world:
                self._update_preview(context, self._mouse_world)
            self._update_header(context)
            context.area.tag_redraw()

        elif (event.type in CAD_CHAR_MAP and event.value == 'PRESS'
              and self.segments > 0):
            self._size_input += CAD_CHAR_MAP[event.type]
            from ...Utils.mastro_cad.cad.cad_utils import safe_eval
            val = safe_eval(self._size_input)
            if val is not None:
                self.size = val
            if self._mouse_world:
                self._update_preview(context, self._mouse_world)
            self._update_header(context)
            context.area.tag_redraw()

        elif event.type == 'BACK_SPACE' and event.value == 'PRESS' and self._size_input:
            self._size_input = self._size_input[:-1]
            if self._size_input:
                from ...Utils.mastro_cad.cad.cad_utils import safe_eval
                val = safe_eval(self._size_input)
                if val is not None:
                    self.size = val
            else:
                self.size = 0.0
            if self._mouse_world:
                self._update_preview(context, self._mouse_world)
            self._update_header(context)
            context.area.tag_redraw()

        elif event.type == 'L' and event.value == 'PRESS':
            self.limit = not self.limit
            if self._mouse_world:
                self._update_preview(context, self._mouse_world)
            self._update_header(context)
            context.area.tag_redraw()

        elif event.type in {'RET', 'NUMPAD_ENTER', 'LEFTMOUSE'} and event.value == 'PRESS':
            self._remove_draw_handler()
            self._apply_fillet(context)
            context.area.header_text_set(None)
            context.workspace.status_text_set(None)
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'} and event.value == 'PRESS':
            self._remove_draw_handler()
            context.area.header_text_set(None)
            context.workspace.status_text_set(None)
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self._started_in_edit = context.mode == 'EDIT_MESH'
        edge_infos = self._get_two_edges(context)
        if edge_infos is None:
            self.report({'WARNING'}, "Select exactly two edges")
            return {'CANCELLED'}

        self._size_input = ""
        self.size        = 0.0

        (obj0, bm0, e0), (obj1, bm1, e1) = edge_infos
        mw0, mw1 = obj0.matrix_world, obj1.matrix_world
        self._edge_key = (obj0.name, e0.index, obj1.name, e1.index)

        # If the two edges share a vertex they already meet —
        # default to arc mode (8 segments).
        if obj0 is obj1:
            shared = set(v.index for v in e0.verts) & set(v.index for v in e1.verts)
            if shared:
                self.segments = 8

        all_pts = [mw0 @ v.co for v in e0.verts] + [mw1 @ v.co for v in e1.verts]

        if not are_coplanar(all_pts, tol=1e-4):
            self.report({'WARNING'}, "Selected edges are not coplanar")
            return {'CANCELLED'}

        self._plane_axes = compute_plane(all_pts, context, obj0)
        self._e0_pts = (mw0 @ e0.verts[0].co, mw0 @ e0.verts[1].co)
        self._e1_pts = (mw1 @ e1.verts[0].co, mw1 @ e1.verts[1].co)

        # Reject parallel edges before entering modal.
        test = _fillet_result(self._e0_pts, self._e1_pts, self._plane_axes,
                              self._e0_pts[0])
        if not test['valid'] and test.get('reason') == 'parallel':
            self.report({'WARNING'}, "Fillet: edges are parallel")
            return {'CANCELLED'}

        self._snap_hit = None
        self._snap     = SnapContext(context, select_modes=('VERT', 'EDGE'))

        global _fillet_draw_handle
        h3d = bpy.types.SpaceView3D.draw_handler_add(
            self._draw_preview, (context,), 'WINDOW', 'POST_VIEW')
        h2d = bpy.types.SpaceView3D.draw_handler_add(
            self._draw_snap, (context,), 'WINDOW', 'POST_PIXEL')
        self._draw_handle = (h3d, h2d)
        _fillet_draw_handle = self._draw_handle

        self._update_header(context)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def _remove_draw_handler(self):
        global _fillet_draw_handle
        if self._draw_handle is not None:
            for h in self._draw_handle:
                bpy.types.SpaceView3D.draw_handler_remove(h, 'WINDOW')
            self._draw_handle = None
            _fillet_draw_handle = None

    def execute(self, context):
        """Called by Shift+R or from the F9 redo panel with stored properties."""
        edge_infos = self._get_two_edges(context)
        if edge_infos is None:
            self.report({'WARNING'}, "Select exactly two edges")
            return {'CANCELLED'}
        (obj0, bm0, e0), (obj1, bm1, e1) = edge_infos
        mw0, mw1 = obj0.matrix_world, obj1.matrix_world
        all_pts = [mw0 @ v.co for v in e0.verts] + [mw1 @ v.co for v in e1.verts]
        if not are_coplanar(all_pts, tol=1e-4):
            self.report({'WARNING'}, "Selected edges are not coplanar")
            return {'CANCELLED'}
        self._plane_axes = compute_plane(all_pts, context, obj0)
        self._e0_pts = (mw0 @ e0.verts[0].co, mw0 @ e0.verts[1].co)
        self._e1_pts = (mw1 @ e1.verts[0].co, mw1 @ e1.verts[1].co)

        # Use centre of selection as mouse proxy so _fillet_result finds
        # the correct sector when called from the redo panel. Recompute it
        # if the selected edges changed since it was last set (e.g. the user
        # picked a different pair of edges before re-running from the redo
        # panel) — otherwise the stale sector can pick the wrong arms.
        edge_key = (obj0.name, e0.index, obj1.name, e1.index)
        self._edge_key = edge_key
        if self._mouse_world is None or self._mouse_world_edge_key != edge_key:
            self._mouse_world = sum(all_pts, all_pts[0] * 0) / len(all_pts)
            self._mouse_world_edge_key = edge_key

        # When called from redo panel, treat size > 0 as explicitly set.
        if self.size > 1e-8:
            self._size_input = f"{self.size:.6g}"
        self._update_preview(context, self._mouse_world)
        self._apply_fillet(context)
        return {'FINISHED'}
