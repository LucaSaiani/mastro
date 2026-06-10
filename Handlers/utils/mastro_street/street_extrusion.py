import bpy
import bmesh


def _handle_street_extrusion(scene, obj, bm):
    """Detect vertex extrusion on a MaStro street and copy street attributes."""
    if not bpy.context.scene.tool_settings.mesh_select_mode[0]:
        return
    if not isinstance(bm.select_history.active, bmesh.types.BMVert):
        return

    active_vert = bm.select_history.active
    if scene.mastro_previous_selection_vert_id == active_vert.index:
        return

    scene.mastro_previous_selection_vert_id = active_vert.index
    selected_verts = [v for v in bm.verts if v.select]
    if len(selected_verts) != 1 or len(active_vert.link_edges) != 1:
        return

    new_edge = active_vert.link_edges[0]
    try:
        bm_id     = bm.edges.layers.int["mastro_street_id"]
        bm_width  = bm.edges.layers.float["mastro_street_width"]
        bm_radius = bm.edges.layers.float["mastro_street_radius"]
    except KeyError:
        return

    if new_edge[bm_id] != 0:
        return

    other_vert = new_edge.other_vert(active_vert)
    source_edge = next((e for e in other_vert.link_edges if e != new_edge), None)
    if source_edge is None:
        return

    new_edge[bm_id]     = source_edge[bm_id]
    new_edge[bm_width]  = source_edge[bm_width]
    new_edge[bm_radius] = source_edge[bm_radius]
    bmesh.update_edit_mesh(obj.data)
