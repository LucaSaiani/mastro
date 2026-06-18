import bmesh
from mathutils import Vector
from .category_map import _CATEGORY_MAP
from .tolerance_constants import _COORD_QUANTIZE

# =============================================================================
#  Merge per-category bmeshes into one merged bmesh
# =============================================================================

def _merge_category_bmeshes(data):
    """
    Merge the four per-category bmeshes into a single BMesh, sharing vertices
    that occupy the same XY position across categories.

    Category vertex registration happens BEFORE the edge-creation attempt so
    that edges shared between categories (e.g. silhouette ⊆ visible) still
    populate their vertex groups correctly even when the edge already exists
    in bm_merged and the new() call raises ValueError.

    category_edges records the (va, vb) BMVert pair for each category,
    independently of vertex sharing — this is the only reliable way to know
    which category a given EDGE belongs to. category_verts alone is not
    enough: vertices are shared across categories at coincident positions,
    so "both endpoints are in group X" can match an edge that does not
    actually belong to X (e.g. a hidden edge whose endpoints happen to also
    be visible-edge endpoints elsewhere).

    Returns:
        bm_merged      – new BMesh (or None if empty)
        category_verts – dict { bm_key: set of BMVert } in bm_merged
        category_edges – dict { bm_key: set of (BMVert, BMVert) } in bm_merged
    """
    bm_merged      = bmesh.new()
    coord_to_vert  = {}
    category_verts = {key: set() for key, _ in _CATEGORY_MAP}
    category_edges = {key: set() for key, _ in _CATEGORY_MAP}

    def get_or_add_merged(co):
        key = (int(co.x * _COORD_QUANTIZE), int(co.y * _COORD_QUANTIZE))
        if key not in coord_to_vert:
            coord_to_vert[key] = bm_merged.verts.new(Vector((co.x, co.y, 0.0)))
        return coord_to_vert[key]

    any_edge = False

    for bm_key, _group_name in _CATEGORY_MAP:
        bm = getattr(data, bm_key)
        if bm is None:
            continue
        for edge in bm.edges:
            va = get_or_add_merged(edge.verts[0].co)
            vb = get_or_add_merged(edge.verts[1].co)
            if va is vb:
                continue

            # Register vertices in this category BEFORE attempting edge
            # creation. If the edge already exists (e.g. a silhouette edge
            # that was also written to bm_visible because visible ⊇ silhouette),
            # the ValueError below would prevent registration, leaving the
            # category vertex group empty.
            category_verts[bm_key].add(va)
            category_verts[bm_key].add(vb)
            category_edges[bm_key].add((va, vb))

            try:
                bm_merged.edges.new((va, vb))
                any_edge = True
            except ValueError:
                # Edge already exists in bm_merged — this is expected when
                # a category is a subset of another (silhouette ⊆ visible).
                pass

        bm.free()
        setattr(data, bm_key, None)

    if not any_edge:
        bm_merged.free()
        return None, {}, {}

    return bm_merged, category_verts, category_edges