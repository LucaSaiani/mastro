import bpy
import bmesh
import gpu

from gpu_extras.batch import batch_for_shader

from ....Utils.mastro_preferences.get_preferences import get_prefs


def show_block_overlay(obj):
    """Draw typology-colored edges for a MaStro block object, respecting selection highlight."""
    theme = bpy.context.preferences.themes[0].view_3d
    color_editmesh_active = theme.editmesh_active
    color_edge_mode_select = theme.edge_mode_select

    prefs = get_prefs()

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
        # bm.faces.ensure_lookup_table()

    bm_block_id_layer = bm.edges.layers.int["mastro_typology_id_EDGE"]
    projectTypologies = bpy.context.scene.mastro_typology_name_list

    # matrix = bpy.context.region_data.perspective_matrix
    for edge in bm.edges:
        v1 = obj.matrix_world @ edge.verts[0].co
        v2 = obj.matrix_world @ edge.verts[1].co
        coords = [v1, v2]
        indices = [(0, 1)]

        typology_id = edge[bm_block_id_layer]
        index = next((i for i, elem in enumerate(projectTypologies) if elem.id == typology_id), None)
        if 0 <= typology_id < len(bpy.context.scene.mastro_typology_name_list):
            if mesh.is_editmode:
                if edge is active_edge:
                    r, g, b, a = color_editmesh_active
                elif edge.select:
                    r, g, b, a = (*color_edge_mode_select[:], 1.0)
                else:
                    r, g, b = [c for c in bpy.context.scene.mastro_typology_name_list[index].typologyEdgeColor]
                    a = 1.0
            else:
                r, g, b = [c for c in bpy.context.scene.mastro_typology_name_list[index].typologyEdgeColor]
                a = 1.0

            rgba = (r, g, b, a)
            shader.uniform_float("color", rgba)

            gpu.state.line_width_set(prefs.blockEdgeSize)
            gpu.state.blend_set("ALPHA")
            batch = batch_for_shader(shader, 'LINES', {"pos": coords}, indices=indices)
            batch.draw(shader)

    bm.free()
