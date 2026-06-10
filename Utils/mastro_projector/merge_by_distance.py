from .projection_result import ObjectProjection
import bmesh
from mathutils import Vector

# =============================================================================
#  Merge by distance — operates on per-category bmeshes before snap
# =============================================================================

def _merge_bmeshes_by_distance(results, threshold):
    """
    Apply merge-by-distance to all category bmeshes in results.
    Operates before snap so that near-coincident vertices are collapsed
    before orphan detection — avoids snapping false orphans.

    All category bmeshes for the same source object share a single merged
    vertex pool, so every category ends up using identical representative
    coordinates.  This is essential: snap_orphans looks up split-target
    edges in sync bmeshes (bm_silhouette, bm_section …) by the quantised
    coordinates of the active bmesh (bm_visible / bm_hidden).  If the two
    bmeshes used different per-category pools their coordinates could
    diverge, causing the lookup to miss and leaving the new split vertex
    unregistered in the subset's vertex group.

    Returns the total number of vertices merged across all bmeshes.
    """
    BM_KEYS = ("bm_visible", "bm_silhouette", "bm_hidden",
               "bm_silhouette_hidden", "bm_section")

    merged_total = 0

    inv_th = 1.0 / threshold if threshold > 0 else 1e9

    for data in results.values():
        # ── Build one shared vertex pool from ALL categories ──────────────
        unique_verts = []
        cell_map = {}  # quantized cell key → index in unique_verts

        def find_or_add(co, _uv=unique_verts, _cm=cell_map, _inv=inv_th, _th=threshold):
            # Map the coordinate to a grid cell of size `threshold`.
            # A vertex near a cell boundary can be within threshold of a vertex
            # in any of the 26 adjacent cells, so all 27 cells (3³) must be
            # checked to guarantee no merge is missed.
            cx = int(co.x * _inv)
            cy = int(co.y * _inv)
            cz = int(co.z * _inv)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        idx = _cm.get((cx + dx, cy + dy, cz + dz))
                        if idx is not None and (co - _uv[idx]).length <= _th:
                            return idx
            idx = len(_uv)
            _uv.append(Vector(co))
            _cm[(cx, cy, cz)] = idx
            return idx

        for bm_key in BM_KEYS:
            bm = getattr(data, bm_key)
            if bm is None:
                continue
            for edge in bm.edges:
                find_or_add(edge.verts[0].co)
                find_or_add(edge.verts[1].co)

        if not unique_verts:
            continue

        # ── Rebuild each category bmesh using the shared pool ─────────────
        for bm_key in BM_KEYS:
            bm = getattr(data, bm_key)
            if bm is None:
                continue

            coord_edges = [
                (Vector(e.verts[0].co), Vector(e.verts[1].co))
                for e in bm.edges
            ]
            if not coord_edges:
                bm.free()
                setattr(data, bm_key, None)
                continue

            used_indices = set()
            unique_edges = set()
            for a, b in coord_edges:
                ia = find_or_add(a)
                ib = find_or_add(b)
                used_indices.add(ia)
                if ia == ib:
                    continue
                used_indices.add(ib)
                unique_edges.add((min(ia, ib), max(ia, ib)))

            # Each edge references 2 vertices; len(coord_edges)*2 is the total
            # vertex references before merging. Subtracting the unique vertex
            # count gives the number of references that were collapsed.
            merged_total += max(0, len(coord_edges) * 2 - len(used_indices))

            if not unique_edges:
                bm.free()
                setattr(data, bm_key, None)
                continue

            bm.free()
            bm_new = bmesh.new()
            for co in unique_verts:
                bm_new.verts.new(co)
            bm_new.verts.ensure_lookup_table()
            for ia, ib in unique_edges:
                try:
                    bm_new.edges.new((bm_new.verts[ia], bm_new.verts[ib]))
                except ValueError:
                    pass
            bm_new.edges.ensure_lookup_table()

            setattr(data, bm_key, bm_new)

    return merged_total