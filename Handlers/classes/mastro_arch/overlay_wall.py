import bpy
import bmesh
import gpu

from gpu_extras.batch import batch_for_shader

from ....Utils.mastro_preferences.get_preferences import get_prefs


def show_wall_overlay(obj):
    """Draw wall-type-colored edges for a MaStro mass object in edge select mode."""
    theme = bpy.context.preferences.themes[0].view_3d
    color_editmesh_active = theme.editmesh_active
    color_edge_mode_select = theme.edge_mode_select

    prefs = get_prefs()

    coords = []
    # edgeIndices = []
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    mesh = obj.data

    if mesh.is_editmode:
        bm = bmesh.from_edit_mesh(mesh)

        # active edge
        active_edge = None
        for e in bm.edges:
            if e.select and e.is_valid and e == bm.select_history.active:
                active_edge = e
                break
    else:
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        active_edge = None

    bm_wall_id_layer = bm.edges.layers.int["mastro_wall_id"]
    projectWalls = bpy.context.scene.mastro_wall_name_list

    # matrix = bpy.context.region_data.perspective_matrix
    for edge in bm.edges:
        v1 = obj.matrix_world @ edge.verts[0].co
        v2 = obj.matrix_world @ edge.verts[1].co
        coords = [v1, v2]
        indices = [(0, 1)]

        wall_id = edge[bm_wall_id_layer]
        index = next((i for i, elem in enumerate(projectWalls) if elem.id == wall_id), None)
        if 0 <= wall_id < len(bpy.context.scene.mastro_wall_name_list):
            if edge is active_edge:
                rgba = color_editmesh_active
            elif edge.select:
                rgba = (*color_edge_mode_select[:], 1.0)
            else:
                r, g, b = [c for c in bpy.context.scene.mastro_wall_name_list[index].wallEdgeColor]
                rgba = (r, g, b, 1.0)
            shader.uniform_float("color", rgba)

            gpu.state.line_width_set(prefs.wallEdgeSize)
            gpu.state.blend_set("ALPHA")
            batch = batch_for_shader(shader, 'LINES', {"pos": coords}, indices=indices)
            batch.draw(shader)

    bm.free()
