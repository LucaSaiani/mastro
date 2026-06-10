"""Circle and arc construction methods for MaStroCad.

All functions work in 2D plane coordinates (projected via plane axes).
Intersection I = (ix, iy) is the meeting point of the two tangent lines.
d1, d2 = unit directions of the two lines (pointing FROM arm TOWARD I).

# ── Circle / arc definition methods ──────────────────────────────────────────
#
# A circle has 3 degrees of freedom (cx, cy, r).  Each method below
# constrains all three; the number of solutions depends on the geometry.
#
# ── 1 solution ────────────────────────────────────────────────────────────────
#
#   Centro + Raggio       C+R   click centre, type/drag radius
#   Centro + Punto        C+P   centre click + point on circle (r = distance)
#   Diametro              DIA   two diametrically opposite points
#   3 Punti               3P    three points on the circle (unique if not collinear)
#
# ── 2 solutions ───────────────────────────────────────────────────────────────
#
#   2 Punti + Raggio      2P+R  two points + explicit radius; centre on either
#                               side of the chord                    [TODO]
#   TTR  Tangente Tangente Raggio   tangent to 2 edges + radius
#                               (already in circle_utils: circle_ttr)
#   TTP  Tangente Tangente Punto    tangent to 2 edges + pass-through point
#                               (already in circle_utils: circle_ttp)
#   Tangente + 2 Punti    T+2P  tangent to 1 edge, passes through 2 points
#                               (quadratic — 2 solutions)            [TODO]
#
# ── 4 solutions ───────────────────────────────────────────────────────────────
#
#   TTR con 4 quadranti         all four angle-bisector combinations for TTR
#                               (fillet exposes only the 2 useful ones)
#
# ── NOT implemented (require arc/circle edges as input) ───────────────────────
#
#   Tangente a cerchio + ...    any method needing tangency to a circular edge;
#                               mastroCad edges are straight segments only, so
#                               there is no way to detect that an edge is an arc.
#   Apollonio generalizzato     circle tangent to 3 arbitrary objects
#                               (point / line / circle): up to 8 solutions.
#
# ── Arcs ──────────────────────────────────────────────────────────────────────
#
#   All circle methods above can produce an arc by adding start/end constraints:
#   start point, end point, subtended angle, or chord length.
#   arc_points_3d() converts a solved circle into a polyline arc.
#
# ─────────────────────────────────────────────────────────────────────────────
n1, n2 = inward unit normals (pointing toward the arc center / concave side).
"""

import math
import bmesh
from mathutils import Vector


# ── Attribute constants ───────────────────────────────────────────────────────

ATTR_TYPE        = "mastro_cad_type"
CIRCLE_TYPES     = {b"Circle", b"Fillet"}   # types recognised by check_circle
ATTR_STATUS      = "mastro_cad_status"
ATTR_RESOLUTION  = "mastro_cad_resolution"
ATTR_TYPE_EDGE   = "mastro_cad_type_EDGE"
ATTR_STATUS_EDGE = "mastro_cad_status_EDGE"
ATTR_RES_EDGE    = "mastro_cad_resolution_EDGE"


# ── Attribute helpers ─────────────────────────────────────────────────────────

def ensure_circle_layers(bm):
    """Get or create the six mastro_cad attribute layers for circles.

    Must be called BEFORE creating any bmesh geometry — new layers invalidate
    all existing bmesh element references.
    """
    vt = bm.verts.layers.string.get(ATTR_TYPE)       or bm.verts.layers.string.new(ATTR_TYPE)
    vs = bm.verts.layers.int.get(ATTR_STATUS)        or bm.verts.layers.int.new(ATTR_STATUS)
    vr = bm.verts.layers.int.get(ATTR_RESOLUTION)    or bm.verts.layers.int.new(ATTR_RESOLUTION)
    et = bm.edges.layers.string.get(ATTR_TYPE_EDGE)  or bm.edges.layers.string.new(ATTR_TYPE_EDGE)
    es = bm.edges.layers.int.get(ATTR_STATUS_EDGE)   or bm.edges.layers.int.new(ATTR_STATUS_EDGE)
    er = bm.edges.layers.int.get(ATTR_RES_EDGE)      or bm.edges.layers.int.new(ATTR_RES_EDGE)
    return vt, vs, vr, et, es, er


def set_circle_attrs(bm, verts, edges, resolution, layers=None,
                     type_tag=b"Circle"):
    """Tag verts and edges as belonging to a circle/arc with given segment count.

    type_tag: b"Circle" (default) or b"Fillet" for fillet arcs.
    layers:   pre-obtained tuple — pass to avoid calling ensure_circle_layers()
              after geometry has been created.
    """
    if layers is None:
        layers = ensure_circle_layers(bm)
    vt, vs, vr, et, es, er = layers
    for v in verts:
        v[vt] = type_tag
        v[vs] = 1
        v[vr] = resolution
    for e in edges:
        e[et] = type_tag
        e[es] = 1
        e[er] = resolution


# ── Read-only layer access ────────────────────────────────────────────────────

def get_circle_layers(bm):
    """Return (vt, vs, vr, et, es, er) or None if any layer is missing."""
    vt = bm.verts.layers.string.get(ATTR_TYPE)
    vs = bm.verts.layers.int.get(ATTR_STATUS)
    vr = bm.verts.layers.int.get(ATTR_RESOLUTION)
    et = bm.edges.layers.string.get(ATTR_TYPE_EDGE)
    es = bm.edges.layers.int.get(ATTR_STATUS_EDGE)
    er = bm.edges.layers.int.get(ATTR_RES_EDGE)
    if None in (vt, vs, vr, et, es, er):
        return None
    return vt, vs, vr, et, es, er


# ── Chain invalidation ───────────────────────────────────────────────────────

def invalidate_circle_chain(bm, seed, layers=None):
    """Walk all circle-tagged edges reachable from seed and mark them es=0.

    Called when check_circle fails on a seed that still has es=1, so the
    handler stops showing handles and future walks skip the stale chain.
    Only walks in both directions from the seed vertex; stops at dead ends
    or branching (same logic as _walk_circle_chain without length trimming).
    """
    if layers is None:
        layers = get_circle_layers(bm)
    if layers is None:
        return
    vt, vs, vr, et, es, er = layers

    start_v = seed.verts[0] if isinstance(seed, bmesh.types.BMEdge) else seed
    if start_v[vt] not in CIRCLE_TYPES or start_v[vs] != 1:
        return

    def circle_nbrs(v, exclude=None):
        return [e for e in v.link_edges
                if e[es] == 1 and e[et] in CIRCLE_TYPES and e != exclude]

    visited = set()

    def walk(v, prev_e):
        while True:
            nexts = circle_nbrs(v, exclude=prev_e)
            if not nexts or len(nexts) > 1:
                break
            e = nexts[0]
            if e in visited:
                break
            visited.add(e)
            e[es] = 0
            prev_e = e
            v = e.other_vert(v)

    init = circle_nbrs(start_v)
    for first_e in init:
        if first_e not in visited:
            visited.add(first_e)
            first_e[es] = 0
            walk(first_e.other_vert(start_v), first_e)


# ── Chain walker ──────────────────────────────────────────────────────────────

def _walk_circle_chain(bm, start_v, layers, mark_boundaries=False):
    """Walk tagged circle edges from start_v.

    Returns (chain_verts, chain_edges, is_closed) or (None, None, None).
    chain_verts[i] and chain_verts[i+1] are connected by chain_edges[i].
    For a closed circle len(chain_edges) == len(chain_verts).

    mark_boundaries=True: after walking, trim the chain from its midpoint
    outward by edge length consistency.  Edges that break the length uniformity
    are marked es=0 so future walks treat them as non-arc boundaries.  This is
    needed after fillet-on-fillet where old arc edges (longer) are still tagged
    es=1 and would otherwise be included in the chain.
    """
    vt, vs, vr, et, es, er = layers

    def circle_nbrs(v, exclude=None):
        return [e for e in v.link_edges
                if e[es] == 1 and e[et] in CIRCLE_TYPES and e != exclude]

    init_nexts = circle_nbrs(start_v)
    if not init_nexts:
        return None, None, None

    first_e = init_nexts[0]
    first_v = first_e.other_vert(start_v)
    if first_v is start_v:
        return None, None, None

    # Reference length from the first edge — boundaries are edges that differ.
    ref_len = first_e.calc_length()
    if ref_len < 1e-8:
        return None, None, None
    tol = ref_len * 0.01

    def _len_ok(e):
        return abs(e.calc_length() - ref_len) <= tol

    fwd_verts = [start_v, first_v]
    fwd_edges = [first_e]
    prev_e    = first_e
    cur       = first_v

    while True:
        nexts = circle_nbrs(cur, exclude=prev_e)
        if not nexts:
            break
        if len(nexts) > 1:
            return None, None, None
        e  = nexts[0]
        if not _len_ok(e):
            e[es] = 0                          # exclude boundary edge from future checks
            break
        nv = e.other_vert(cur)
        if nv is start_v:
            fwd_edges.append(e)
            return fwd_verts, fwd_edges, True  # closed circle
        if nv in fwd_verts:
            return None, None, None
        fwd_edges.append(e)
        fwd_verts.append(nv)
        prev_e = e
        cur    = nv

    # Open chain — walk backward from start_v
    bwd_verts = [start_v]
    bwd_edges = []
    prev_e    = first_e
    cur       = start_v

    while True:
        nexts = circle_nbrs(cur, exclude=prev_e)
        if not nexts:
            break
        if len(nexts) > 1:
            return None, None, None
        e  = nexts[0]
        if not _len_ok(e):
            e[es] = 0                          # exclude boundary edge from future checks
            break
        nv = e.other_vert(cur)
        if nv in fwd_verts[1:] or nv in bwd_verts[1:]:
            return None, None, None
        bwd_edges.append(e)
        bwd_verts.append(nv)
        prev_e = e
        cur    = nv

    chain_verts = list(reversed(bwd_verts)) + fwd_verts[1:]
    chain_edges = list(reversed(bwd_edges)) + fwd_edges

    # Length-based boundary trimming: walk outward from the midpoint.
    # Clips the chain to the longest consistent-length inner segment.
    # When mark_boundaries=True, also marks boundary edges es=0 so future
    # read-only walks no longer traverse them.
    if chain_edges and len(chain_edges) >= 2:
        mid = len(chain_edges) // 2
        ref_len = chain_edges[mid].calc_length()
        tol = ref_len * 0.01

        lo = mid
        while lo > 0:
            if abs(chain_edges[lo - 1].calc_length() - ref_len) > tol:
                if mark_boundaries:
                    chain_edges[lo - 1][es] = 0
                break
            lo -= 1

        hi = mid
        while hi < len(chain_edges) - 1:
            if abs(chain_edges[hi + 1].calc_length() - ref_len) > tol:
                if mark_boundaries:
                    chain_edges[hi + 1][es] = 0
                break
            hi += 1

        chain_edges = chain_edges[lo:hi + 1]
        chain_verts = chain_verts[lo:hi + 2]

    return chain_verts, chain_edges, False


# ── Geometry helpers ──────────────────────────────────────────────────────────

def circle_centroid_world(chain_verts, mw):
    """World-space centroid of a chain of bmesh verts."""
    pts = [mw @ v.co for v in chain_verts]
    return sum(pts, Vector((0.0, 0.0, 0.0))) / len(pts)


def arc_circumcenter_world(chain_verts, mw):
    """True geometric centre of the circle/arc in world space.

    Computed as the circumcenter of three well-separated points on the arc
    (first, middle, last).  Works for both closed circles and open arcs;
    unlike the centroid, it returns the correct circle centre even when the
    arc covers less than half the circle.

    Falls back to the centroid on degenerate input (collinear points).
    """
    n   = len(chain_verts)
    pts = [mw @ v.co for v in chain_verts]

    p0 = pts[0]
    p1 = pts[n // 2]
    p2 = pts[-1] if n > 2 else pts[1]

    d1 = p1 - p0
    d2 = p2 - p0

    d11 = d1.dot(d1)
    d12 = d1.dot(d2)
    d22 = d2.dot(d2)
    det = d11 * d22 - d12 * d12

    if abs(det) < 1e-12:
        # Degenerate (collinear) — fall back to centroid
        return sum(pts, Vector((0.0, 0.0, 0.0))) / n

    # C = p0 + a*d1 + b*d2  such that |C-p0|²=|C-p1|²=|C-p2|²
    a = d22 * (d11 - d12) / (2.0 * det)
    b = d11 * (d22 - d12) / (2.0 * det)
    return p0 + d1 * a + d2 * b


def circle_plane_axes(chain_verts, mw, handle_world, centroid=None):
    """Compute (right, up, normal, centroid) for a circle in world space.

    right : direction from centroid to handle_world (= "angle 0" axis)
    up    : normal × right
    normal: Newell's polygon normal
    """
    pts = [mw @ v.co for v in chain_verts]
    n   = len(pts)

    # Newell's method for polygon normal
    normal = Vector((0.0, 0.0, 0.0))
    for i in range(n):
        a = pts[i];  b = pts[(i + 1) % n]
        normal.x += (a.y - b.y) * (a.z + b.z)
        normal.y += (a.z - b.z) * (a.x + b.x)
        normal.z += (a.x - b.x) * (a.y + b.y)
    if normal.length < 1e-8:
        normal = Vector((0.0, 0.0, 1.0))
    else:
        normal = normal.normalized()

    if centroid is None:
        centroid = sum(pts, Vector((0.0, 0.0, 0.0))) / n

    r = handle_world - centroid
    if r.length > 1e-8:
        right = r.normalized()
    else:
        fallback = Vector((0.0, 1.0, 0.0)) if abs(normal.dot(Vector((0.0, 1.0, 0.0)))) < 0.9 \
                   else Vector((1.0, 0.0, 0.0))
        right = normal.cross(fallback).normalized()

    up = normal.cross(right).normalized()
    return right, up, normal, centroid


# ── Validity check ────────────────────────────────────────────────────────────

def check_circle(bm, seed, mark_boundaries=False):
    """Circle/arc validity check starting from seed (BMVert or BMEdge).

    Returns (True, chain_verts, chain_edges, is_closed) if all conditions pass,
    or (False, None, None, None).

    mark_boundaries=True: delegates to _walk_circle_chain to trim length-
    inconsistent boundary edges (marking them es=0).  Use only from write
    contexts (e.g. EditCircle.invoke).

    Checks (in order):
      1. Layers present and seed tagged b"Circle" with status=1
      2. Chain walkable (closed → circle, open → arc)
      3. Connectivity (2 circle edges per interior vert, 1 at endpoints)
      4. Edge lengths equal within 1 % tolerance  ← early exit
      5. Coplanar within 1e-4
      6. Equal turning angles between consecutive edges within 1 % tolerance
         (works for both open arcs and closed circles; direction-consistent
         via a fixed plane normal derived from the first two edge vectors)
    """
    from .cad_utils import are_coplanar

    layers = get_circle_layers(bm)
    if layers is None:
        return False, None, None, None

    vt, vs, vr, et, es, er = layers
    start_v = seed.verts[0] if isinstance(seed, bmesh.types.BMEdge) else seed

    if start_v[vt] not in CIRCLE_TYPES or start_v[vs] != 1:
        return False, None, None, None

    chain_verts, chain_edges, is_closed = _walk_circle_chain(
        bm, start_v, layers, mark_boundaries=mark_boundaries)
    if chain_verts is None or len(chain_verts) < 3:
        return False, None, None, None

    n = len(chain_verts)

    # Connectivity — count only edges that belong to this chain
    chain_edge_set = set(chain_edges)
    for i, v in enumerate(chain_verts):
        deg = len([e for e in v.link_edges if e in chain_edge_set])
        expected = 2 if (is_closed or 0 < i < n - 1) else 1
        if deg != expected:
            return False, None, None, None

    # Edge lengths (early exit)
    lengths = [e.calc_length() for e in chain_edges]
    avg_len = sum(lengths) / len(lengths)
    if avg_len < 1e-8:
        return False, None, None, None
    tol_len = avg_len * 0.01
    if any(abs(l - avg_len) > tol_len for l in lengths):
        return False, None, None, None

    # Coplanarity
    pts = [v.co.copy() for v in chain_verts]
    if not are_coplanar(pts, tol=1e-4):
        return False, None, None, None

    # Equal turning angles — vertices lie on a common circle iff every
    # consecutive edge pair turns by the same signed angle.
    # Works for both open (arc) and closed chains.
    #
    # Edge vectors are built going forward along the chain; for closed chains
    # the wrap-around edge is appended.  The plane normal is derived from the
    # first two edges so the signed angle is measured consistently.
    e_vecs = [(pts[i + 1] - pts[i]).normalized() for i in range(n - 1)]
    if is_closed:
        e_vecs.append((pts[0] - pts[-1]).normalized())

    normal_raw = e_vecs[0].cross(e_vecs[1])
    if normal_raw.length < 1e-8:
        return False, None, None, None   # degenerate / collinear
    plane_n = normal_raw.normalized()

    def _signed_angle(a, b):
        return math.atan2(plane_n.dot(a.cross(b)), a.dot(b))

    n_turns = len(e_vecs) - 1 if not is_closed else len(e_vecs)
    if n_turns < 1:
        return False, None, None, None
    if is_closed:
        angles = [_signed_angle(e_vecs[i], e_vecs[(i + 1) % len(e_vecs)])
                  for i in range(len(e_vecs))]
    else:
        angles = [_signed_angle(e_vecs[i], e_vecs[i + 1])
                  for i in range(len(e_vecs) - 1)]

    avg_a = sum(angles) / len(angles)
    if abs(avg_a) < 1e-8:
        return False, None, None, None   # straight line, not a circle
    tol_a = abs(avg_a) * 0.01
    if any(abs(a - avg_a) > tol_a for a in angles):
        return False, None, None, None

    return True, chain_verts, chain_edges, is_closed


# ── Geometry helper ───────────────────────────────────────────────────────────

def circle_points(center, radius, segments, right, up, phase=0.0):
    """Return `segments` equally-spaced points on a circle in world space.

    center:   world-space Vector — the circle's centre
    radius:   float — circle radius in world units
    segments: int   — number of vertices (= number of edges)
    right, up: unit Vectors spanning the circle's plane
    phase:    float — starting angle in radians (rotates the whole polygon)
    """
    pts = []
    for i in range(segments):
        a = 2.0 * math.pi * i / segments + phase
        pts.append(center + right * (math.cos(a) * radius)
                           + up    * (math.sin(a) * radius))
    return pts


# ── Tangent-Tangent-Radius ────────────────────────────────────────────────────

def circle_ttr(ix, iy, d1x, d1y, d2x, d2y, n1x, n1y, n2x, n2y, radius):
    """Circle tangent to two lines through I with a given radius (fillet variant).

    Returns a single solution with tangent points, for use by the Fillet operator.
    For all solutions without tangent points use circle_ttr_all instead.

    Center lies on the angle bisector at t = radius / k1 from I,
    where k1 = bisector · inward_normal_1.

    Returns (center_2d, radius, t1_2d, t2_2d) or None.
    """
    bx = n1x + n2x;  by = n1y + n2y
    b_len = math.sqrt(bx*bx + by*by)
    if b_len < 1e-8:
        return None
    bx /= b_len;  by /= b_len

    k1 = bx * n1x + by * n1y
    if abs(k1) < 1e-8:
        return None

    t  = radius / k1
    cx = ix + t * bx;  cy = iy + t * by

    cix = cx - ix;  ciy = cy - iy
    proj1 = cix * d1x + ciy * d1y
    t1x   = ix + proj1 * d1x;  t1y = iy + proj1 * d1y

    proj2 = cix * d2x + ciy * d2y
    t2x   = ix + proj2 * d2x;  t2y = iy + proj2 * d2y

    return (cx, cy), radius, (t1x, t1y), (t2x, t2y)


# ── Tangent-Tangent-Point ─────────────────────────────────────────────────────

def circle_ttp(ix, iy, d1x, d1y, d2x, d2y, mx, my, n1x, n1y, n2x, n2y):
    """Circle tangent to two lines through I and passing through point M.

    Center on angle bisector: C = I + t * b̂
    r = t * k1.  Condition |C − M|² = r² → quadratic in t.
    Picks the solution whose center lies on the concave side (same side as M).

    Returns (center_2d, radius, t1_2d, t2_2d) or None.
    """
    bx = n1x + n2x;  by = n1y + n2y
    b_len = math.sqrt(bx*bx + by*by)
    if b_len < 1e-8:
        return None
    bx /= b_len;  by /= b_len

    k1 = bx * n1x + by * n1y
    if abs(k1) < 1e-8:
        return None

    Dx = ix - mx;  Dy = iy - my
    Db = Dx * bx + Dy * by
    D2 = Dx * Dx + Dy * Dy

    A = 1.0 - k1 * k1
    B = 2.0 * Db
    C = D2

    candidates = []
    if abs(A) < 1e-10:
        if abs(B) > 1e-10:
            t = -C / B
            if t > 1e-8:
                candidates.append(t)
    else:
        disc = B * B - 4.0 * A * C
        if disc < 0:
            return None
        sq = math.sqrt(disc)
        for t_sol in ((-B + sq) / (2*A), (-B - sq) / (2*A)):
            if t_sol > 1e-8:
                candidates.append(t_sol)

    if not candidates:
        return None

    def sd1(cx, cy):
        return (cx - ix) * (-d1y) + (cy - iy) * d1x
    def sd2(cx, cy):
        return (cx - ix) * (-d2y) + (cy - iy) * d2x

    sign_ref1 = 1.0 if sd1(mx, my) >= 0 else -1.0
    sign_ref2 = 1.0 if sd2(mx, my) >= 0 else -1.0

    best_t = None
    for t_sol in sorted(candidates, reverse=True):
        cx_sol = ix + t_sol * bx;  cy_sol = iy + t_sol * by
        if (sd1(cx_sol, cy_sol) * sign_ref1 > 0 and
                sd2(cx_sol, cy_sol) * sign_ref2 > 0):
            best_t = t_sol
            break
    if best_t is None:
        best_t = max(candidates)

    r  = best_t * k1
    cx = ix + best_t * bx;  cy = iy + best_t * by

    cix = cx - ix;  ciy = cy - iy
    proj1 = cix * d1x + ciy * d1y
    t1x   = ix + proj1 * d1x;  t1y = iy + proj1 * d1y

    proj2 = cix * d2x + ciy * d2y
    t2x   = ix + proj2 * d2x;  t2y = iy + proj2 * d2y

    return (cx, cy), r, (t1x, t1y), (t2x, t2y)


# ── Circle-from-3-inputs math ─────────────────────────────────────────────────
#
# All functions work in 2D plane coordinates (the working plane of the operator).
# edge arguments are always ((x0,y0), (x1,y1)) — two endpoint tuples.
# pt  arguments are         (x, y)             — a single point tuple.
# Return values are (cx, cy, r) triples, or lists thereof.
# ─────────────────────────────────────────────────────────────────────────────

def _line_from_edge_2d(p0_2d, p1_2d):
    """(px, py, dx, dy, nx, ny): unit direction and unit normal for the 2D line.

    Returns None if the two points are coincident.
    nx = -dy (90° CCW rotation of direction).
    """
    dx = p1_2d[0] - p0_2d[0]
    dy = p1_2d[1] - p0_2d[1]
    length = math.sqrt(dx * dx + dy * dy)
    if length < 1e-10:
        return None
    dx /= length;  dy /= length
    return p0_2d[0], p0_2d[1], dx, dy, -dy, dx


def _lines_intersection_2d(px0, py0, dx0, dy0, px1, py1, dx1, dy1):
    """Intersection point of two infinite 2D lines.  Returns (ix, iy) or None."""
    cross = dx0 * dy1 - dy0 * dx1
    if abs(cross) < 1e-8:
        return None
    dpx = px1 - px0;  dpy = py1 - py0
    t   = (dpx * dy1 - dpy * dx1) / cross
    return px0 + t * dx0, py0 + t * dy0


# ── 3 Points ──────────────────────────────────────────────────────────────────

def circle_3p_2d(p0x, p0y, p1x, p1y, p2x, p2y):
    """Circumscribed circle of 3 points in 2D.

    Returns (cx, cy, r) or None if the points are collinear.
    """
    ax = p1x - p0x;  ay = p1y - p0y
    bx = p2x - p0x;  by = p2y - p0y
    D  = 2.0 * (ax * by - ay * bx)
    if abs(D) < 1e-12:
        return None
    ux = (by * (ax*ax + ay*ay) - ay * (bx*bx + by*by)) / D
    uy = (ax * (bx*bx + by*by) - bx * (ax*ax + ay*ay)) / D
    return p0x + ux, p0y + uy, math.sqrt(ux*ux + uy*uy)


# ── 2 Points + Radius ─────────────────────────────────────────────────────────

def circle_2pr_2d(p0x, p0y, p1x, p1y, r):
    """Circles of radius r passing through two points.

    Returns a list of (cx, cy) — 0, 1, or 2 entries.
    """
    mx = (p0x + p1x) * 0.5;  my = (p0y + p1y) * 0.5
    dx = p1x - p0x;           dy = p1y - p0y
    d_sq  = dx*dx + dy*dy
    if d_sq < 1e-14:
        return []
    d_len     = math.sqrt(d_sq)
    half_chord = d_len * 0.5
    if half_chord > r + 1e-8:
        return []            # chord longer than diameter
    h = math.sqrt(max(0.0, r*r - half_chord*half_chord))
    px = -dy / d_len;  py = dx / d_len     # unit perpendicular
    c1 = (mx + h * px, my + h * py)
    if h < 1e-8:
        return [c1]
    return [c1, (mx - h * px, my - h * py)]


# ── Tangent-to-1-line + 2 Points ──────────────────────────────────────────────

def circle_t2p_2d(edge0, p1_2d, p2_2d):
    """Circles tangent to a line and passing through two points.

    edge0 : ((x0,y0), (x1,y1)) — line defined by two endpoints (treated as infinite).
    Returns a list of (cx, cy, r) — up to 4 entries (2 per side of the line).
    """
    l0 = _line_from_edge_2d(*edge0)
    if l0 is None:
        return []
    lpx, lpy, ldx, ldy, lnx, lny = l0
    lc  = lnx * lpx + lny * lpy        # line eq: lnx·x + lny·y = lc
    p1x, p1y = p1_2d
    p2x, p2y = p2_2d

    # Perpendicular bisector of P1P2: bx·cx + by·cy = k
    bx = p2x - p1x;  by = p2y - p1y
    k  = (bx * (p1x + p2x) + by * (p1y + p2y)) * 0.5

    results = []
    for s in (1, -1):
        # Tangency: lnx·cx + lny·cy = s·r + lc
        # Combined with bisector → linear in (cx, cy) as functions of r
        det = bx * lny - by * lnx
        if abs(det) < 1e-10:
            continue
        cx0 = (k * lny - by * lc)     / det
        cx1 = (-by * s)               / det
        cy0 = (bx * lc - k * lnx)    / det
        cy1 = ( bx * s)               / det
        # Substitute into |C - P1|² = r²
        Ax  = cx0 - p1x;  Ay = cy0 - p1y
        A   = cx1*cx1 + cy1*cy1 - 1.0
        B   = 2.0 * (Ax * cx1 + Ay * cy1)
        C   = Ax*Ax + Ay*Ay
        if abs(A) < 1e-10:
            if abs(B) < 1e-10:
                continue
            r_sol = -C / B
            if r_sol > 1e-6:
                results.append((cx0 + cx1*r_sol, cy0 + cy1*r_sol, r_sol))
        else:
            disc = B*B - 4.0*A*C
            if disc < 0:
                continue
            sq = math.sqrt(disc)
            for r_sol in ((-B + sq) / (2*A), (-B - sq) / (2*A)):
                if r_sol > 1e-6:
                    results.append((cx0 + cx1*r_sol, cy0 + cy1*r_sol, r_sol))

    return _dedup_circles(results)


# ── Tangent-to-1-line + 1 Point + Radius ──────────────────────────────────────

def circle_lpr_2d(edge0, pt_2d, r):
    """Circles of radius r tangent to a line and passing through a point.

    Returns a list of (cx, cy, r) — up to 4 entries (2 per side of the line).
    """
    l0 = _line_from_edge_2d(*edge0)
    if l0 is None:
        return []
    lpx, lpy, ldx, ldy, lnx, lny = l0
    p1x, p1y = pt_2d
    results = []
    for s in (1, -1):
        # Center on offset line: base = (lpx + s·r·lnx, lpy + s·r·lny), dir = (ldx, ldy)
        ox = lpx + s * r * lnx - p1x
        oy = lpy + s * r * lny - p1y
        # (ox + t·ldx)² + (oy + t·ldy)² = r²
        B    = 2.0 * (ox * ldx + oy * ldy)
        C    = ox*ox + oy*oy - r*r
        disc = B*B - 4.0*C          # A = ldx²+ldy² = 1
        if disc < 0:
            continue
        sq = math.sqrt(disc)
        for t_sol in ((-B + sq) * 0.5, (-B - sq) * 0.5):
            cx = lpx + s * r * lnx + t_sol * ldx
            cy = lpy + s * r * lny + t_sol * ldy
            results.append((cx, cy, r))
    return _dedup_circles(results)


# ── Tangent-Tangent-Radius (all 4 bisectors) ──────────────────────────────────

def circle_ttr_all(edge0, edge1, radius):
    """All circles of given radius tangent to two lines (up to 4).

    Uses the offset-line approach: intersect the 4 pairs of parallel offset
    lines (±r from each line).  Works even without computing the intersection
    of the original lines.

    Returns a list of (cx, cy, radius).
    """
    l0 = _line_from_edge_2d(*edge0)
    l1 = _line_from_edge_2d(*edge1)
    if l0 is None or l1 is None:
        return []
    px0, py0, dx0, dy0, nx0, ny0 = l0
    px1, py1, dx1, dy1, nx1, ny1 = l1
    results = []
    for s0 in (1, -1):
        op0x = px0 + s0 * radius * nx0
        op0y = py0 + s0 * radius * ny0
        for s1 in (1, -1):
            op1x = px1 + s1 * radius * nx1
            op1y = py1 + s1 * radius * ny1
            hit  = _lines_intersection_2d(op0x, op0y, dx0, dy0,
                                          op1x, op1y, dx1, dy1)
            if hit is None:
                continue
            results.append((hit[0], hit[1], radius))
    return _dedup_circles(results)


# ── Tangent-Tangent-Point (all 4 bisectors) ───────────────────────────────────

def _circle_ttp_roots(ix, iy, dx0, dy0, dx1, dy1, mx, my, n1x, n1y, n2x, n2y):
    """Like circle_ttp but returns ALL valid (cx, cy, r) roots from the quadratic."""
    bx = n1x + n2x;  by = n1y + n2y
    b_len = math.sqrt(bx*bx + by*by)
    if b_len < 1e-8:
        return []
    bx /= b_len;  by /= b_len

    k1 = bx * n1x + by * n1y
    if abs(k1) < 1e-8:
        return []

    Dx = ix - mx;  Dy = iy - my
    Db = Dx * bx + Dy * by
    D2 = Dx * Dx + Dy * Dy

    A = 1.0 - k1 * k1
    B = 2.0 * Db
    C = D2

    candidates = []
    if abs(A) < 1e-10:
        if abs(B) > 1e-10:
            t = -C / B
            if t > 1e-8:
                candidates.append(t)
    else:
        disc = B * B - 4.0 * A * C
        if disc < 0:
            return []
        sq = math.sqrt(disc)
        for t_sol in ((-B + sq) / (2*A), (-B - sq) / (2*A)):
            if t_sol > 1e-8:
                candidates.append(t_sol)

    results = []
    for t_sol in candidates:
        r = t_sol * k1
        if abs(r) > 1e-6:
            results.append((ix + t_sol * bx, iy + t_sol * by, abs(r)))
    return results


def circle_ttp_all(edge0, edge1, pt_2d):
    """All circles tangent to two lines and passing through a point (up to 8).

    Tries all four sign combinations of inward normals, collecting both roots
    of the quadratic for each combination.
    Returns a list of (cx, cy, r).
    """
    l0 = _line_from_edge_2d(*edge0)
    l1 = _line_from_edge_2d(*edge1)
    if l0 is None or l1 is None:
        return []
    px0, py0, dx0, dy0, nx0, ny0 = l0
    px1, py1, dx1, dy1, nx1, ny1 = l1
    ix_iy = _lines_intersection_2d(px0, py0, dx0, dy0, px1, py1, dx1, dy1)
    if ix_iy is None:
        return []    # parallel lines — TTP has no solution
    ix, iy = ix_iy
    mx, my = pt_2d
    results = []
    for s0 in (1, -1):
        for s1 in (1, -1):
            for cx, cy, rr in _circle_ttp_roots(ix, iy, dx0, dy0, dx1, dy1, mx, my,
                                                 s0*nx0, s0*ny0, s1*nx1, s1*ny1):
                results.append((cx, cy, rr))
    return _dedup_circles(results)


# ── Tangent-Tangent-Tangent (incircle + excircles) ────────────────────────────

def circle_ttt_2d(edge0, edge1, edge2):
    """Circles tangent to three lines (up to 4: incircle + 3 excircles).

    Solves the 3×3 linear system  s_i·(nx_i·cx + ny_i·cy − lc_i) = r  for
    each of the 4 sign triples that produce unique solutions.

    Returns a list of (cx, cy, r).
    """
    lines = []
    for e in (edge0, edge1, edge2):
        l = _line_from_edge_2d(*e)
        if l is None:
            return []
        lines.append(l)

    def det3(r0, r1, r2):
        return (r0[0] * (r1[1]*r2[2] - r1[2]*r2[1])
              - r0[1] * (r1[0]*r2[2] - r1[2]*r2[0])
              + r0[2] * (r1[0]*r2[1] - r1[1]*r2[0]))

    results = []
    for s0, s1, s2 in ((1, 1, 1), (1, 1, -1), (1, -1, 1), (-1, 1, 1)):
        rows, rhs = [], []
        for si, li in zip((s0, s1, s2), lines):
            px, py, _, _, nx, ny = li
            lc = nx * px + ny * py
            rows.append((si * nx, si * ny, -1.0))
            rhs.append(si * lc)

        D = det3(rows[0], rows[1], rows[2])
        if abs(D) < 1e-10:
            continue

        Dcx = det3((rhs[0], rows[0][1], rows[0][2]),
                   (rhs[1], rows[1][1], rows[1][2]),
                   (rhs[2], rows[2][1], rows[2][2]))
        Dcy = det3((rows[0][0], rhs[0], rows[0][2]),
                   (rows[1][0], rhs[1], rows[1][2]),
                   (rows[2][0], rhs[2], rows[2][2]))
        Dr  = det3((rows[0][0], rows[0][1], rhs[0]),
                   (rows[1][0], rows[1][1], rhs[1]),
                   (rows[2][0], rows[2][1], rhs[2]))

        r_val = Dr / D
        if r_val < 1e-6:
            continue
        results.append((Dcx / D, Dcy / D, r_val))

    return _dedup_circles(results)


def _dedup_circles(circles, tol=1e-4):
    """Remove duplicate (cx, cy, r) entries within position tolerance."""
    unique = []
    for c in circles:
        if not any(abs(c[0] - u[0]) < tol and abs(c[1] - u[1]) < tol
                   for u in unique):
            unique.append(c)
    return unique


# ── Chamfer ───────────────────────────────────────────────────────────────────

def chamfer_ttl(ix, iy, d1x, d1y, d2x, d2y, length):
    """Chamfer endpoints at a given length from the intersection along each arm.

    Arms extend in direction -d (since d points toward I).

    Returns (t1_2d, t2_2d) or None.
    """
    if length < 1e-8:
        return None
    t1x = ix + length * (-d1x);  t1y = iy + length * (-d1y)
    t2x = ix + length * (-d2x);  t2y = iy + length * (-d2y)
    return (t1x, t1y), (t2x, t2y)


# ── Arc points ────────────────────────────────────────────────────────────────

def arc_points_3d(center_2d, radius, t1_2d, t2_2d,
                  x_axis, y_axis, normal, depth, segments,
                  pass_through_2d=None):
    """Generate 3D world-space points along the arc from t1 to t2 (inclusive).

    pass_through_2d : optional (x,y) used to choose the correct arc direction
                      (the arc going from t1 to t2 that includes this point).
                      If None, the shorter arc is used.

    Returns a list of Vector.
    """
    cx, cy = center_2d

    def angle_of(px, py):
        return math.atan2(py - cy, px - cx)

    a1 = angle_of(t1_2d[0], t1_2d[1])
    a2 = angle_of(t2_2d[0], t2_2d[1])

    if pass_through_2d is not None:
        aM       = angle_of(pass_through_2d[0], pass_through_2d[1])
        diff_ccw = (a2 - a1) % (2 * math.pi)
        aM_ccw   = (aM - a1) % (2 * math.pi)
        diff = diff_ccw if aM_ccw <= diff_ccw else diff_ccw - 2 * math.pi
    else:
        diff = (a2 - a1) % (2 * math.pi)
        if diff > math.pi:
            diff -= 2 * math.pi

    def to_3d(x, y):
        return x_axis * x + y_axis * y + normal * depth

    pts = []
    for i in range(segments + 1):
        frac  = i / segments
        angle = a1 + frac * diff
        pts.append(to_3d(cx + radius * math.cos(angle),
                         cy + radius * math.sin(angle)))
    return pts
