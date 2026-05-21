from mathutils import Vector
from collections import defaultdict

from .tolerance_constants import (
    _TOL_DEGENERATE,   # min edge length — filters degenerate orphan edges
    _TOL_RAY_DENOM,    # min |denominator| for 2D ray/segment intersection
    _EPSILON,          # t_seg boundary tolerance and min cell_size
    _TOL_SNAP_SELF,    # min |t_ray| to skip self-intersection hits
    _COORD_QUANTIZE,   # quantization factor for 2D vertex position hashing
)

# =============================================================================
#  Snap orphan vertices
# =============================================================================

def _ray_seg_intersect_2d(origin: Vector, direction: Vector,
                           a: Vector, b: Vector):
    """
    Intersect 2D ray P(t) = origin + t * direction with segment [a, b].
    t can be any real number (negative = behind the origin).
    Returns (hit_point, t_ray, t_seg) or None if parallel or outside segment.
    Only X and Y components are used.
    """
    dx, dy = direction.x, direction.y
    ex, ey = b.x - a.x, b.y - a.y
    denom  = dx * ey - dy * ex
    if abs(denom) < _TOL_RAY_DENOM:
        return None
    fx, fy = a.x - origin.x, a.y - origin.y
    t_ray  = (fx * ey - fy * ex) / denom
    t_seg  = (fx * dy - fy * dx) / denom
    if not (-_EPSILON <= t_seg <= 1.0 + _EPSILON):
        return None
    t_seg = max(0.0, min(1.0, t_seg))
    hit   = a.lerp(b, t_seg)
    return hit, t_ray, t_seg


def _collect_bm_edges(bm_list):
    """
    Build a flat segment list from a list of (bmesh, any) pairs.
    Each entry: (Vector_a, Vector_b, bm, BMEdge).
    """
    segments = []
    for bm, _vc in bm_list:
        if bm is None:
            continue
        for edge in bm.edges:
            a = Vector((edge.verts[0].co.x, edge.verts[0].co.y, 0.0))
            b = Vector((edge.verts[1].co.x, edge.verts[1].co.y, 0.0))
            segments.append((a, b, bm, edge))
    return segments


def _build_spatial_grid(segments, cell_size):
    """
    Build a 2D spatial hash grid from a flat segment list.

    Each segment is registered in every grid cell it overlaps, computed
    from its axis-aligned bounding box. This allows fast candidate lookup
    for a query point: only cells within a neighbourhood of the point are
    checked, instead of the full segment list.

    Returns a defaultdict(set): grid_cell → set of segment indices.
    """
    grid = defaultdict(set)

    def cell_range(v_min, v_max):
        """Return integer cell indices covering [v_min, v_max]."""
        return range(int(v_min / cell_size) - 1,
                     int(v_max / cell_size) + 2)

    for idx, (a, b, _bm, _edge) in enumerate(segments):
        min_x = min(a.x, b.x)
        max_x = max(a.x, b.x)
        min_y = min(a.y, b.y)
        max_y = max(a.y, b.y)

        for cx in cell_range(min_x, max_x):
            for cy in cell_range(min_y, max_y):
                grid[(cx, cy)].add(idx)

    return grid


def _query_grid(grid, origin, direction, cell_size, search_radius):
    """
    Return the set of segment indices that fall in cells within search_radius
    of origin, extended along direction.

    We query a bounding box around the orphan vertex extended by search_radius
    in all directions — conservative but correct.
    """
    min_x = origin.x - search_radius
    max_x = origin.x + search_radius
    min_y = origin.y - search_radius
    max_y = origin.y + search_radius

    candidate_indices = set()
    for cx in range(int(min_x / cell_size) - 1, int(max_x / cell_size) + 2):
        for cy in range(int(min_y / cell_size) - 1, int(max_y / cell_size) + 2):
            candidate_indices |= grid.get((cx, cy), set())

    return candidate_indices


def _snap_orphans_in_bmeshes(snap_bm_list, sync_bm_list=None,
                              max_snap_distance=None, frame_bounds=None):
    """
    Snap orphan (degree-1) vertices across a list of (bmesh, _) pairs,
    operating in 2D (XY only, Z=0).

    A vertex is considered a true orphan only if its XY position has
    global degree 1 across ALL bmeshes in snap_bm_list combined — not just
    within its own bmesh. This prevents snapping vertices that appear
    orphaned locally but are connected via other category bmeshes.

    Uses a 2D spatial hash grid to limit segment intersection tests to
    candidates near each orphan vertex — reduces complexity from O(N×M)
    to approximately O(N × k) where k is the average number of segments
    per grid cell (typically small even in dense scenes).

    sync_bm_list: optional list of (bmesh, _) pairs whose vertices are
        NOT sources of orphans and are NOT modified structurally, but whose
        vertex positions are updated to match any moves applied to
        snap_bm_list. Use this to keep subset bmeshes (e.g. bm_silhouette
        ⊆ bm_visible) in sync after snap — otherwise the subset retains
        pre-snap vertex positions and produces overlapping edges in the
        final merged mesh.

    max_snap_distance: optional float. If set, orphan vertices whose nearest
        hit is farther than (max_snap_distance * orphan_edge_length) are left
        untouched. Useful with adaptive sampling where short run-boundary edges
        can produce spurious long-range snaps.

    Returns the number of vertices snapped.
    """
    active = [(bm, vc) for bm, vc in snap_bm_list if bm is not None]
    if not active:
        return 0

    sync_active = []
    if sync_bm_list:
        sync_active = [(bm, vc) for bm, vc in sync_bm_list if bm is not None]

    all_segments = _collect_bm_edges(active)

    if not all_segments:
        return 0

    # ------------------------------------------------------------------
    # Build the spatial grid.
    # Cell size is chosen as a fraction of the average segment length —
    # small enough to give good spatial filtering, large enough to avoid
    # excessive cell registrations for long segments.
    # ------------------------------------------------------------------
    avg_len = sum((b - a).length for a, b, _, _ in all_segments) / len(all_segments)
    cell_size = max(avg_len * 2.0, _EPSILON)

    grid = _build_spatial_grid(all_segments, cell_size)

    # Build per-bmesh adjacency and global position → degree map.
    adjacencies = {}   # id(bm) → {BMVert: [(BMVert, BMEdge)]}
    pos_degree  = {}   # (int x, int y) → total degree across all active bmeshes

    for bm, _vc in active:
        adj = {vert: [] for vert in bm.verts}
        for edge in bm.edges:
            va, vb = edge.verts[0], edge.verts[1]
            adj[va].append((vb, edge))
            adj[vb].append((va, edge))
            # Accumulate global degree while building adjacency (single pass).
            for vert in (va, vb):
                key = (int(vert.co.x * _COORD_QUANTIZE), int(vert.co.y * _COORD_QUANTIZE))
                pos_degree[key] = pos_degree.get(key, 0) + 1
        adjacencies[id(bm)] = adj

    moves_per_bm  = {id(bm): [] for bm, _ in active}
    splits_per_bm = {id(bm): [] for bm, _ in active}
    snapped       = 0

    # Pre-compute boundary check if frame limits are provided.
    # Clipped vertices land exactly on a frustum boundary plane; snapping them
    # would move them off the boundary, producing incorrect geometry.
    _fb_tol = 1e-4
    if frame_bounds is not None:
        fb_xmin, fb_xmax, fb_ymin, fb_ymax = frame_bounds
        def _on_boundary(v):
            x, y = v.co.x, v.co.y
            return (abs(x - fb_xmin) < _fb_tol or abs(x - fb_xmax) < _fb_tol or
                    abs(y - fb_ymin) < _fb_tol or abs(y - fb_ymax) < _fb_tol)
    else:
        def _on_boundary(v):
            return False

    for bm, _vc in active:
        adjacency = adjacencies[id(bm)]

        for vert, neighbors in adjacency.items():
            # Local degree must be 1.
            if len(neighbors) != 1:
                continue

            # Global degree must also be 1 — not connected in other bmeshes.
            key = (int(vert.co.x * _COORD_QUANTIZE), int(vert.co.y * _COORD_QUANTIZE))
            if pos_degree.get(key, 0) != 1:
                continue

            # Skip vertices produced by lateral frustum clipping.
            if _on_boundary(vert):
                continue

            v_co             = Vector((vert.co.x, vert.co.y, 0.0))
            u_vert, own_edge = neighbors[0]
            u_co             = Vector((u_vert.co.x, u_vert.co.y, 0.0))

            edge_vec = v_co - u_co
            if edge_vec.length < _TOL_DEGENERATE:
                continue

            direction = edge_vec.normalized()
            own_edges = {own_edge} | {e for (_, e) in adjacency[u_vert]}

            # Determine search radius: use max_snap_distance if set,
            # otherwise fall back to a generous multiple of cell_size so
            # that the grid query covers all plausible snap targets.
            if max_snap_distance is not None:
                search_radius = edge_vec.length * max_snap_distance
            else:
                search_radius = cell_size * 8.0

            # Query the spatial grid for candidate segment indices.
            candidate_indices = _query_grid(
                grid, v_co, direction, cell_size, search_radius
            )

            best_t   = None
            best_hit = None
            best_seg = None

            for idx in candidate_indices:
                seg_a, seg_b, seg_bm, seg_edge = all_segments[idx]
                if seg_bm is bm and seg_edge in own_edges:
                    continue
                result = _ray_seg_intersect_2d(v_co, direction, seg_a, seg_b)
                if result is None:
                    continue
                hit, t_ray, t_seg = result
                if abs(t_ray) < _TOL_SNAP_SELF:
                    continue
                if max_snap_distance is not None:
                    if abs(t_ray) > edge_vec.length * max_snap_distance:
                        continue
                if best_t is None or abs(t_ray) < abs(best_t):
                    best_t   = t_ray
                    best_hit = hit
                    best_seg = (seg_bm, seg_edge, t_seg)

            if best_hit is None:
                continue

            moves_per_bm[id(bm)].append((vert, best_hit))
            seg_bm, seg_edge, t_seg = best_seg
            if id(seg_bm) in splits_per_bm and _TOL_SNAP_SELF < t_seg < 1.0 - _TOL_SNAP_SELF:
                splits_per_bm[id(seg_bm)].append((seg_edge, t_seg, best_hit))
            snapped += 1

    # ------------------------------------------------------------------
    # Apply vertex moves to active bmeshes.
    # Record coordinate remapping for synchronisation with sync bmeshes.
    # ------------------------------------------------------------------
    coord_remap = {}   # (int x, int y) old_key → Vector new_co

    for bm, _vc in active:
        for vert, new_co in moves_per_bm.get(id(bm), []):
            old_key = (int(vert.co.x * _COORD_QUANTIZE), int(vert.co.y * _COORD_QUANTIZE))
            coord_remap[old_key] = new_co
            vert.co = new_co

    # ------------------------------------------------------------------
    # Apply edge splits to active bmeshes.
    # Collect applied splits as (snap_co, va_key, vb_key) for later
    # propagation to sync bmeshes — bm_silhouette ⊆ bm_visible: if
    # bm_visible's edge A-B is split into A-V and V-B but bm_silhouette
    # still holds the original A-B edge, _merge_category_bmeshes would
    # add A-B to bm_merged as a new edge alongside A-V and V-B, creating
    # a visible duplicate that overlaps the split path.
    # ------------------------------------------------------------------
    applied_splits = []  # list of (snap_co, va_key, vb_key)

    for bm, _vc in active:
        splits = splits_per_bm.get(id(bm), [])
        if not splits:
            continue
        dedup = {}
        for seg_edge, t_seg, snap_co in splits:
            key = id(seg_edge)
            if key not in dedup or abs(t_seg - 0.5) < abs(dedup[key][1] - 0.5):
                dedup[key] = (seg_edge, t_seg, snap_co)
        for _key, (seg_edge, _t, snap_co) in dedup.items():
            try:
                va = seg_edge.verts[0]
                vb = seg_edge.verts[1]
            except ReferenceError:
                continue
            va_key = (int(va.co.x * _COORD_QUANTIZE), int(va.co.y * _COORD_QUANTIZE))
            vb_key = (int(vb.co.x * _COORD_QUANTIZE), int(vb.co.y * _COORD_QUANTIZE))
            bm.edges.remove(seg_edge)
            new_v = bm.verts.new(snap_co)
            try:
                bm.edges.new((va, new_v))
                bm.edges.new((new_v, vb))
            except ValueError:
                pass
            applied_splits.append((snap_co, va_key, vb_key))

    # ------------------------------------------------------------------
    # Propagate edge splits to sync bmeshes (e.g. bm_silhouette).
    # For each split applied above, find the matching edge in every sync
    # bmesh (by quantized endpoint positions) and apply the same split.
    # Non-orphan vertices are never moved, so the position lookup against
    # the pre-move coord_remap is safe here.
    # ------------------------------------------------------------------
    if applied_splits and sync_active:
        for bm_sync, _vc in sync_active:
            if bm_sync is None:
                continue
            bm_sync.verts.ensure_lookup_table()
            bm_sync.edges.ensure_lookup_table()

            # Build a lookup: canonical (min_key, max_key) → BMEdge
            edge_by_keys = {}
            for edge in bm_sync.edges:
                ka = (int(edge.verts[0].co.x * _COORD_QUANTIZE),
                      int(edge.verts[0].co.y * _COORD_QUANTIZE))
                kb = (int(edge.verts[1].co.x * _COORD_QUANTIZE),
                      int(edge.verts[1].co.y * _COORD_QUANTIZE))
                edge_by_keys[(min(ka, kb), max(ka, kb))] = edge

            for snap_co, va_key, vb_key in applied_splits:
                canon = (min(va_key, vb_key), max(va_key, vb_key))
                sync_edge = edge_by_keys.get(canon)
                if sync_edge is None:
                    continue
                try:
                    sva = sync_edge.verts[0]
                    svb = sync_edge.verts[1]
                except ReferenceError:
                    continue
                bm_sync.edges.remove(sync_edge)
                new_sv = bm_sync.verts.new(snap_co)
                try:
                    bm_sync.edges.new((sva, new_sv))
                except ValueError:
                    pass
                try:
                    bm_sync.edges.new((new_sv, svb))
                except ValueError:
                    pass
                del edge_by_keys[canon]

    # ------------------------------------------------------------------
    # Propagate vertex moves to sync bmeshes (e.g. bm_silhouette).
    # bm_silhouette ⊆ bm_visible: every vertex in bm_silhouette that was
    # moved in bm_visible must be updated to the same new position so that
    # merge_per_category finds consistent coordinates and does not produce
    # overlapping edges in the final merged mesh.
    # Edge splits have already been propagated above.
    # ------------------------------------------------------------------
    if coord_remap and sync_active:
        for bm, _vc in sync_active:
            for vert in bm.verts:
                old_key = (int(vert.co.x * _COORD_QUANTIZE), int(vert.co.y * _COORD_QUANTIZE))
                if old_key in coord_remap:
                    vert.co = coord_remap[old_key]

    return snapped