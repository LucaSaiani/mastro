import bpy
import bmesh
import math
from mathutils import Vector
from .scene_graph_helpers import (link_to_projection_collection,
                                   register_projection_output)

# =============================================================================
#  Global section outline — outer boundary of all objects' section edges
# =============================================================================
#
#  Pipeline:
#   A) Collect all 2D section-line segments from per-object bm_section bmeshes.
#   B) Build a planar graph: insert pairwise intersection vertices and split
#      every segment at those points.
#   C) For each connected component (island), trace the outer boundary using
#      the minimum-CCW-angle (rightmost-turn) walk, then write the result as
#      a Blender mesh object.
#
# The rightmost-turn walk is the standard planar-graph outer-face traversal:
# at each vertex choose the outgoing edge whose direction deviates least
# counterclockwise from the reversed incoming direction.  This traces the
# outer boundary of each island.

_Q   = 1e5   # quantisation factor (same as _COORD_QUANTIZE)
_TOL = 1e-7  # strict-interior tolerance for intersection test
_2PI = 2.0 * math.pi


# ── 2D segment–segment intersection ──────────────────────────────────────────

def _seg_intersect_2d(a, b, c, d):
    """
    Return (t, s) if segments [a,b] and [c,d] have a strictly interior
    intersection (both parameters strictly inside (TOL, 1-TOL)), else None.
    """
    dx, dy = b.x - a.x, b.y - a.y
    ex, ey = d.x - c.x, d.y - c.y
    denom  = dx * ey - dy * ex
    if abs(denom) < 1e-12:
        return None
    fx, fy = c.x - a.x, c.y - a.y
    t = (fx * ey - fy * ex) / denom
    s = (fx * dy - fy * dx) / denom
    if _TOL < t < 1.0 - _TOL and _TOL < s < 1.0 - _TOL:
        return t, s
    return None


# ── Planar graph builder ──────────────────────────────────────────────────────

def _build_planar_graph(seg_list):
    """
    Given a list of (Vector_a, Vector_b) 2-D segments, compute all pairwise
    intersection points and return a planar graph.

    Returns
    -------
    verts : list[Vector]  – unique vertex positions (z = 0)
    adj   : dict[int, set[int]]  – adjacency {vertex_index: {neighbour, …}}
    """
    n = len(seg_list)

    # Collect split parameters along every segment (endpoints always included)
    split_ts = [[0.0, 1.0] for _ in range(n)]

    # Build a spatial grid to avoid O(n²) all-pairs intersection testing.
    # Each segment is inserted into every grid cell its bounding box touches;
    # only segments sharing at least one cell are tested against each other.
    if n > 1:
        xs = [min(a.x, b.x) for a, b in seg_list]
        xe = [max(a.x, b.x) for a, b in seg_list]
        ys = [min(a.y, b.y) for a, b in seg_list]
        ye = [max(a.y, b.y) for a, b in seg_list]

        # Cell size: average segment length, clamped to a sensible range.
        avg_len = sum(
            math.hypot(xe[i] - xs[i], ye[i] - ys[i]) for i in range(n)
        ) / n
        cell = max(avg_len, 1e-6)

        grid = {}  # (cx, cy) → list of segment indices
        for i in range(n):
            cx0, cx1 = int(xs[i] / cell), int(xe[i] / cell)
            cy0, cy1 = int(ys[i] / cell), int(ye[i] / cell)
            for cx in range(cx0, cx1 + 1):
                for cy in range(cy0, cy1 + 1):
                    grid.setdefault((cx, cy), []).append(i)

        # Gather candidate pairs (share a grid cell); test each pair once.
        candidates = set()
        for cell_segs in grid.values():
            for ki in range(len(cell_segs)):
                for kj in range(ki + 1, len(cell_segs)):
                    i, j = cell_segs[ki], cell_segs[kj]
                    if i > j:
                        i, j = j, i
                    candidates.add((i, j))

        for i, j in candidates:
            a, b = seg_list[i]
            c, d = seg_list[j]
            result = _seg_intersect_2d(a, b, c, d)
            if result is not None:
                t, s = result
                split_ts[i].append(t)
                split_ts[j].append(s)

    # Build vertex set with quantised deduplication
    vert_key = {}  # (qx, qy) → index
    verts    = []

    def add_vert(co):
        key = (int(round(co.x * _Q)), int(round(co.y * _Q)))
        if key not in vert_key:
            vert_key[key] = len(verts)
            verts.append(Vector((co.x, co.y, 0.0)))
        return vert_key[key]

    adj = {}

    def add_edge(i, j):
        if i == j:
            return
        adj.setdefault(i, set()).add(j)
        adj.setdefault(j, set()).add(i)

    for k, (a, b) in enumerate(seg_list):
        ts = sorted(set(split_ts[k]))
        # Deduplicate very close split parameters
        clean = [ts[0]]
        for t in ts[1:]:
            if t - clean[-1] > 1e-9:
                clean.append(t)

        prev_idx = None
        for t in clean:
            co      = a if t == 0.0 else (b if t == 1.0 else a.lerp(b, t))
            idx     = add_vert(co)
            if prev_idx is not None:
                add_edge(prev_idx, idx)
            prev_idx = idx

    return verts, adj


# ── Connected-component detection ────────────────────────────────────────────

def _find_islands(adj, seed_set):
    """
    Return a list of sets, each containing the vertex indices of one
    connected component (island).  Only vertices in *seed_set* are visited.
    """
    unvisited = set(seed_set)
    islands   = []
    while unvisited:
        start  = next(iter(unvisited))
        island = set()
        stack  = [start]
        while stack:
            v = stack.pop()
            if v in island:
                continue
            island.add(v)
            for u in adj.get(v, ()):
                if u not in island:
                    stack.append(u)
        islands.append(island)
        unvisited -= island
    return islands


# ── Outer-boundary traversal ─────────────────────────────────────────────────

def _trace_outer_boundary(verts, adj, island):
    """
    Trace the outer boundary of a connected island.

    Uses the minimum-CCW-angle rule: at each vertex choose the outgoing edge
    whose direction is closest (in the clockwise sense) to the reversed
    incoming direction.  This selects the "rightmost turn" and walks the
    outer face of the planar graph.

    Starting vertex : leftmost (min x), ties broken by bottommost (min y).
    Starting edge   : neighbour with smallest CCW deviation from downward.

    Returns a list of vertex indices; the implied closing edge reconnects
    the last element back to the first.
    """
    start = min(island, key=lambda i: (verts[i].x, verts[i].y))

    nbrs = list(adj.get(start, ()))
    if not nbrs:
        return [start]

    # Pick the first outgoing edge: smallest CCW angle from the downward dir
    def _ccw_from_down(j):
        ang = math.atan2(verts[j].y - verts[start].y,
                         verts[j].x - verts[start].x)
        return (ang + math.pi * 0.5) % _2PI

    first = min(nbrs, key=_ccw_from_down)

    boundary  = [start]
    prev      = start
    curr      = first
    max_steps = len(island) * 6 + 20

    while curr != start and max_steps > 0:
        boundary.append(curr)
        max_steps -= 1

        non_back = adj.get(curr, set()) - {prev}

        if not non_back:
            # Dead-end spur — U-turn
            prev, curr = curr, prev
            continue

        cx  = verts[curr].x
        cy  = verts[curr].y
        bax = verts[prev].x - cx
        bay = verts[prev].y - cy
        ba  = math.atan2(bay, bax)

        def _rel(j, _ba=ba, _cx=cx, _cy=cy):
            out = math.atan2(verts[j].y - _cy, verts[j].x - _cx)
            r   = (out - _ba + _2PI) % _2PI
            # If exactly 0 (pointing straight back), deprioritise — another
            # vertex coincides with prev in direction; shouldn't normally occur
            return r if r > 1e-12 else _2PI

        next_v     = min(non_back, key=_rel)
        prev, curr = curr, next_v

    return boundary


# ── Helpers to write a Blender mesh object ───────────────────────────────────

def _write_obj(bm, obj_name, scene, parent):
    if obj_name in bpy.data.objects:
        old_obj = bpy.data.objects[obj_name]
        if parent is not None and old_obj.parent == parent:
            old_me = old_obj.data
            bpy.data.objects.remove(old_obj, do_unlink=True)
            if old_me and old_me.users == 0:
                bpy.data.meshes.remove(old_me)
    mesh = bpy.data.meshes.new(obj_name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    obj = bpy.data.objects.new(obj_name, mesh)
    obj.hide_viewport = True
    mat = bpy.data.materials.get("MaStro Section Colour")
    if mat:
        obj.data.materials.append(mat)
    link_to_projection_collection(obj, scene)
    if parent is not None:
        obj.parent = parent
        register_projection_output(parent, obj.name)
    return obj


# ── Main entry point ─────────────────────────────────────────────────────────

def _compute_and_write_section_outline(section_segs, scene, camera_name,
                                       parent=None):
    """
    From a list of (Vector_a, Vector_b) 2-D section segments collected from
    all projected objects, compute the outer boundary of each island and
    write one Blender mesh object:

    ``<camera_name>_section`` – filled N-gon faces, one per island

    Returns a list of the created objects (0–1 elements).
    """
    if not section_segs:
        return []

    verts, adj = _build_planar_graph(section_segs)

    connected = {i for i in range(len(verts)) if adj.get(i)}
    if not connected:
        return []

    islands = _find_islands(adj, connected)

    bm_fill = bmesh.new()
    fi_vmap = {}   # original index → BMVert in bm_fill

    def _fi(i):
        if i not in fi_vmap:
            fi_vmap[i] = bm_fill.verts.new(verts[i])
        return fi_vmap[i]

    for island in islands:
        bnd = _trace_outer_boundary(verts, adj, island)
        if len(bnd) < 3:
            continue

        # Deduplicate vertices — dead-end spurs introduce repeated indices.
        seen       = set()
        face_verts = []
        for i in bnd:
            if i not in seen:
                seen.add(i)
                face_verts.append(_fi(i))
        if len(face_verts) >= 3:
            try:
                bm_fill.faces.new(face_verts)
            except ValueError:
                pass

    if bm_fill.faces:
        return [_write_obj(bm_fill, camera_name + "_section", scene, parent)]

    bm_fill.free()
    return []
