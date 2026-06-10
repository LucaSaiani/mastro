import bpy
import bmesh
import gpu

from gpu_extras.batch import batch_for_shader

from ....Utils.mastro_preferences.get_preferences import get_prefs


def show_street_overlay(obj):
    """Draw street-type-colored edges for a MaStro street object."""
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

    bm_street_id_layer = bm.edges.layers.int["mastro_street_id"]
    projectStreets = bpy.context.scene.mastro_street_name_list

    for edge in bm.edges:
        v1 = obj.matrix_world @ edge.verts[0].co
        v2 = obj.matrix_world @ edge.verts[1].co
        coords = [v1, v2]
        indices = [(0, 1)]

        street_id = edge[bm_street_id_layer]
        index = next((i for i, elem in enumerate(projectStreets) if elem.id == street_id), None)
        if 0 <= street_id < len(bpy.context.scene.mastro_street_name_list):
            if mesh.is_editmode:
                if edge is active_edge:
                    r, g, b, a = color_editmesh_active
                elif edge.select:
                    r, g, b, a = (*color_edge_mode_select[:], 1.0)
                else:
                    r, g, b = [c for c in bpy.context.scene.mastro_street_name_list[index].streetEdgeColor]
                    a = 1.0
            else:
                r, g, b = [c for c in bpy.context.scene.mastro_street_name_list[index].streetEdgeColor]
                a = 1.0
            rgba = (r, g, b, a)
            shader.uniform_float("color", rgba)

            batch = batch_for_shader(
                shader, 'LINES',
                {"pos": coords},
                indices = indices
            )

            gpu.state.line_width_set(prefs.streetEdgeSize)
            gpu.state.blend_set("ALPHA")

            batch.draw(shader)

    bm.free()
