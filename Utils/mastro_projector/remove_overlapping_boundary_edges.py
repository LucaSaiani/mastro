from .tolerance_constants import _TOL_DEGENERATE, _TOL_PARALLEL, _TOL_COLINEAR

# Use the colinearity tolerance for parallelism too — _TOL_PARALLEL alone is
# too tight after Boolean operations / modifier evaluation, which can shift
# normalized directions by ~1e-4 for otherwise truly-parallel edges.
_TOL_PARALLEL_EFFECTIVE = max(_TOL_PARALLEL, _TOL_COLINEAR)

# =============================================================================
#  _remove_overlapping_boundary_edges
# =============================================================================

def _remove_overlapping_boundary_edges(bm_src, props):
    """
    Classify boundary edges (exactly one linked face) within the same object.

    Groups colinear boundary edges and sweeps along their common axis to
    determine, for each sub-segment, whether it is:
      - silhouette  : covered by exactly one boundary edge → always silhouette
      - internal    : covered by 2+ boundary edges → classified by flat-angle
                      and material rules (same as regular edges)
      - gap         : covered by no edge → discarded

    Returns:
        silhouette_segments – list of (Vector a, Vector b) world-space pairs
        internal_segments   – list of (Vector a, Vector b, face_a, face_b)
        boundary_edge_ids   – set of BMEdge indices for ALL boundary edges
    """
    boundary_edges    = [e for e in bm_src.edges if len(e.link_faces) == 1]
    boundary_edge_ids = {e.index for e in boundary_edges}

    if not boundary_edges:
        return [], [], boundary_edge_ids

    silhouette_segments = []
    internal_segments   = []

    def canonical_direction(v0, v1):
        d = v1 - v0
        if d.length < _TOL_DEGENERATE:
            return None
        d = d.normalized()
        for i in range(3):
            if abs(d[i]) > _TOL_DEGENERATE:
                if d[i] < 0:
                    d = -d
                break
        return d

    def are_parallel(d1, d2):
        return d1.cross(d2).length < _TOL_PARALLEL_EFFECTIVE

    def point_to_line_dist(pt, line_origin, line_dir):
        return (pt - line_origin).cross(line_dir).length

    def point_at_t(entry, t):
        t0, t1, v0, v1 = entry[0], entry[1], entry[2], entry[3]
        if abs(t1 - t0) < _TOL_DEGENERATE:
            return v0.copy()
        return v0.lerp(v1, (t - t0) / (t1 - t0))

    # ── Group edges by direction ──────────────────────────────────────────────
    # Quantize the canonical direction to a tuple key for O(1) lookup.
    # Directions within _TOL_PARALLEL_EFFECTIVE of each other share a bucket;
    # we use a coarse quantization (1e3) and fall back to a linear search only
    # within the small list of already-seen direction buckets — in practice
    # this list stays short because boundary edges cluster in a few directions.
    _DIR_Q = 1e3
    dir_bucket_dirs  = []   # list of representative Vector directions
    dir_bucket_edges = []   # parallel list of edge lists

    for e in boundary_edges:
        d = canonical_direction(e.verts[0].co, e.verts[1].co)
        if d is None:
            silhouette_segments.append(
                (e.verts[0].co.copy(), e.verts[1].co.copy())
            )
            continue
        placed = False
        for k, rep in enumerate(dir_bucket_dirs):
            if are_parallel(rep, d):
                dir_bucket_edges[k].append(e)
                placed = True
                break
        if not placed:
            dir_bucket_dirs.append(d)
            dir_bucket_edges.append([e])

    for members, d in zip(dir_bucket_edges, dir_bucket_dirs):

        if len(members) == 1:
            e = members[0]
            silhouette_segments.append(
                (e.verts[0].co.copy(), e.verts[1].co.copy())
            )
            continue

        # ── Group colinear edges within this direction bucket ─────────────
        # Project each vertex onto the direction axis and onto the two
        # perpendicular axes to build a quantized colinearity key.
        # Edges whose perpendicular offset is < _TOL_COLINEAR land in the
        # same bucket without any linear search.
        axis      = max(range(3), key=lambda i: abs(d[i]))
        perp_axes = [i for i in range(3) if i != axis]

        def _perp_key(co):
            # Quantize perpendicular distance from origin along each perp axis.
            return (
                round(co[perp_axes[0]] / max(_TOL_COLINEAR, 1e-9)),
                round(co[perp_axes[1]] / max(_TOL_COLINEAR, 1e-9)),
            )

        sg_map = {}   # perp_key → {'origin', 'dir', 'edges'}
        sg_list = []  # insertion-order list for deterministic output

        for e in members:
            pk = _perp_key(e.verts[0].co)
            if pk in sg_map:
                sg_map[pk]['edges'].append(e)
            else:
                sg = {'origin': e.verts[0].co.copy(), 'dir': d, 'edges': [e]}
                sg_map[pk] = sg
                sg_list.append(sg)

        subgroups = sg_list

        for sg in subgroups:
            sg_edges = sg['edges']

            if len(sg_edges) == 1:
                e = sg_edges[0]
                silhouette_segments.append(
                    (e.verts[0].co.copy(), e.verts[1].co.copy())
                )
                continue

            # axis is already computed above for the whole direction group

            normalised = []
            for e in sg_edges:
                t0   = e.verts[0].co[axis]
                t1   = e.verts[1].co[axis]
                v0   = e.verts[0].co.copy()
                v1   = e.verts[1].co.copy()
                face = e.link_faces[0]
                if t0 > t1:
                    t0, t1 = t1, t0
                    v0, v1 = v1, v0
                normalised.append((t0, t1, v0, v1, face))

            t_values = sorted({t for t0, t1, _, _, _ in normalised
                               for t in (t0, t1)})
            active   = list(normalised)

            for i in range(len(t_values) - 1):
                t_lo = t_values[i]
                t_hi = t_values[i + 1]
                if t_hi - t_lo < _TOL_DEGENERATE:
                    continue

                active   = [e for e in active if e[1] > t_lo + _TOL_DEGENERATE]
                covering = [e for e in active if e[0] <= t_lo + _TOL_DEGENERATE]

                if not covering:
                    continue

                pt_lo = point_at_t(covering[0], t_lo)
                pt_hi = point_at_t(covering[0], t_hi)

                if len(covering) == 1:
                    silhouette_segments.append((pt_lo, pt_hi))
                else:
                    internal_segments.append(
                        (pt_lo, pt_hi, covering[0][4], covering[1][4])
                    )

    return silhouette_segments, internal_segments, boundary_edge_ids