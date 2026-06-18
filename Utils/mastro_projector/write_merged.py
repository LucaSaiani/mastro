import bpy
from .category_map import _CATEGORY_MAP
from .scene_graph_helpers import (link_to_projection_collection,
                                   register_projection_output)
from .tolerance_constants import _COORD_QUANTIZE
from ..mastro_preferences.get_preferences import get_prefs

# =============================================================================
#  Write merged bmesh to scene as a single object with vertex groups
# =============================================================================

def _edge_key(a_xy, b_xy):
    """Order-independent key for an edge from two quantized (x,y) tuples."""
    return frozenset((a_xy, b_xy))


def _write_merged_object(src_name, bm_merged, category_verts, category_edges,
                         scene, props, parent=None):
    """
    Convert bm_merged to a Blender mesh object with vertex groups, and
    return the set of final mesh edge indices belonging to each category.
    bm_merged is freed by this function.

    Returns (obj, category_edge_indices), or (None, {}) if bm_merged has no
    edges. category_edge_indices: dict { bm_key: set of mesh edge index }.

    Edge category membership is resolved from category_edges (exact
    per-edge (BMVert, BMVert) pairs), NOT by checking vertex-group
    membership of both endpoints — vertices are shared across categories at
    coincident positions, so "both endpoints are in group X" can wrongly
    match an edge that does not actually belong to X.
    """
    if not bm_merged.edges:
        bm_merged.free()
        return None, {}

    def xy(co):
        return (int(co.x * _COORD_QUANTIZE), int(co.y * _COORD_QUANTIZE))

    # Snapshot category vert/edge XY positions before to_mesh invalidates BMVert refs.
    category_xy = {}
    for bm_key, _gn in _CATEGORY_MAP:
        vset = category_verts.get(bm_key)
        if vset:
            category_xy[bm_key] = {xy(v.co) for v in vset}

    category_edge_xy = {}
    for bm_key, _gn in _CATEGORY_MAP:
        eset = category_edges.get(bm_key)
        if eset:
            category_edge_xy[bm_key] = {
                _edge_key(xy(va.co), xy(vb.co)) for va, vb in eset
            }

    obj_name = src_name + get_prefs().projection_suffix
    if obj_name in bpy.data.objects:
        old_obj = bpy.data.objects[obj_name]
        if parent is not None and old_obj.parent == parent:
            old_me = old_obj.data
            bpy.data.objects.remove(old_obj, do_unlink=True)
            if old_me and old_me.users == 0:
                bpy.data.meshes.remove(old_me)

    mesh = bpy.data.meshes.new(obj_name)
    bm_merged.to_mesh(mesh)
    bm_merged.free()
    mesh.update()

    obj = bpy.data.objects.new(obj_name, mesh)
    obj.hide_viewport = True
    link_to_projection_collection(obj, scene)
    if parent is not None:
        obj.parent = parent
        register_projection_output(parent, obj.name)
    pos_to_idx = {xy(v.co): v.index for v in mesh.vertices}

    for bm_key, group_name in _CATEGORY_MAP:
        xy_set = category_xy.get(bm_key)
        if not xy_set:
            continue
        indices = [pos_to_idx[p] for p in xy_set if p in pos_to_idx]
        if not indices:
            continue
        vg = obj.vertex_groups.new(name=group_name)
        vg.add(indices, 1.0, 'REPLACE')

    # Resolve each category's edges to final mesh edge indices, by matching
    # the snapshotted endpoint-XY key against the final mesh's own edges.
    # If cross-object dedup already removed an edge from bm_merged before
    # this function ran, its category_edge_xy entry simply won't be found
    # here and is silently dropped — correct, since that edge no longer
    # exists in the final mesh.
    edge_key_to_index = {
        _edge_key(xy(mesh.vertices[e.vertices[0]].co),
                  xy(mesh.vertices[e.vertices[1]].co)): e.index
        for e in mesh.edges
    }
    category_edge_indices = {}
    for bm_key, edge_xy_set in category_edge_xy.items():
        indices = {edge_key_to_index[k] for k in edge_xy_set if k in edge_key_to_index}
        if indices:
            category_edge_indices[bm_key] = indices

    return obj, category_edge_indices