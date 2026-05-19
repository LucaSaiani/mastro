from .tolerance_constants import _COORD_QUANTIZE

# =============================================================================
#  Cross-object edge deduplication
# =============================================================================

def _deduplicate_merged_edges(merged):
    """
    Remove edges from each object's merged bmesh that are already present in
    a previously processed object's bmesh (cross-object deduplication).

    This prevents visually overlapping edges when multiple source objects share
    a surface or their boundary edges project to the same 2D position.

    Edge identity is determined by the quantized XY positions of both endpoints
    (same resolution used throughout the pipeline: _COORD_QUANTIZE = 1e5).

    Orphan vertices left behind after edge removal are NOT deleted here —
    they are harmless isolated vertices in the final mesh and the BMVert
    references in category_verts remain valid for vertex-group assignment.

    Returns the total number of edges removed.
    """
    global_edge_seen = set()
    removed_total    = 0

    for _src_name, (bm_merged, _cat_v) in merged.items():
        edges_to_remove = []
        for edge in bm_merged.edges:
            ca = (int(edge.verts[0].co.x * _COORD_QUANTIZE),
                  int(edge.verts[0].co.y * _COORD_QUANTIZE))
            cb = (int(edge.verts[1].co.x * _COORD_QUANTIZE),
                  int(edge.verts[1].co.y * _COORD_QUANTIZE))
            key = (min(ca, cb), max(ca, cb))
            if key in global_edge_seen:
                edges_to_remove.append(edge)
            else:
                global_edge_seen.add(key)

        for edge in edges_to_remove:
            bm_merged.edges.remove(edge)

        removed_total += len(edges_to_remove)

    return removed_total
