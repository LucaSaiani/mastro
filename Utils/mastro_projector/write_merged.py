import bpy
from .category_map import _CATEGORY_MAP
from .scene_graph_helpers import (link_to_projection_collection,
                                   register_projection_output)
from .tolerance_constants import _COORD_QUANTIZE
from ..mastro_preferences.get_preferences import get_prefs

# =============================================================================
#  Write merged bmesh to scene as a single object with vertex groups
# =============================================================================

def _write_merged_object(src_name, bm_merged, category_verts, scene, props,
                         parent=None):
    """
    Convert bm_merged to a Blender mesh object with vertex groups.
    bm_merged is freed by this function.
    Returns the created bpy.types.Object, or None if bm_merged has no edges.
    """
    if not bm_merged.edges:
        bm_merged.free()
        return None

    # Snapshot category vert XY positions before to_mesh invalidates BMVert refs.
    category_xy = {}
    for bm_key, _gn in _CATEGORY_MAP:
        vset = category_verts.get(bm_key)
        if vset:
            category_xy[bm_key] = {
                (int(v.co.x * _COORD_QUANTIZE), int(v.co.y * _COORD_QUANTIZE)) for v in vset
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
    pos_to_idx = {
        (int(v.co.x * _COORD_QUANTIZE), int(v.co.y * _COORD_QUANTIZE)): v.index
        for v in mesh.vertices
    }

    for bm_key, group_name in _CATEGORY_MAP:
        xy_set = category_xy.get(bm_key)
        if not xy_set:
            continue
        indices = [pos_to_idx[xy] for xy in xy_set if xy in pos_to_idx]
        if not indices:
            continue
        vg = obj.vertex_groups.new(name=group_name)
        vg.add(indices, 1.0, 'REPLACE')

    return obj