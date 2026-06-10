import bpy
import bmesh

from ....Utils.mastro_arch.read_write_bmesh_storey_attribute import read_bmesh_storey_attribute
from ....Utils.mastro_arch.read_write_bmesh_use_attribute import read_bmesh_use_attribute


def _fill_new_block_edge(bm, new_edge, parent_edge, typology_id):
    """Copy attributes from parent_edge to a newly extruded block edge.
    No bmesh.update_edit_mesh call — from_edit_mesh is a live reference,
    writes persist without forcing an update (which would crash during depsgraph)."""
    field = bm.edges
    storeys_layer = field.layers.int["mastro_number_of_storeys_EDGE"]
    depth_layer   = field.layers.float["mastro_block_depth"]

    new_edge[field.layers.int["mastro_typology_id_EDGE"]] = typology_id

    n_storeys = parent_edge[storeys_layer] if parent_edge[storeys_layer] > 0 else bpy.context.scene.mastro_attribute_mass_storeys
    data = read_bmesh_storey_attribute(n_storeys, typology_id)
    if data:
        new_edge[storeys_layer]                                  = data["numberOfStoreys"]
        new_edge[field.layers.int["mastro_list_storey_A_EDGE"]] = data["storey_list_A"]
        new_edge[field.layers.int["mastro_list_storey_B_EDGE"]] = data["storey_list_B"]

    depth = parent_edge[depth_layer] if parent_edge[depth_layer] > 0 else bpy.context.scene.mastro_attribute_block_depth
    if depth == 0:
        depth = 18
    new_edge[depth_layer] = depth

    use_data = read_bmesh_use_attribute(typology_id)
    if use_data:
        new_edge[field.layers.int["mastro_list_use_id_A_EDGE"]] = use_data["use_id_list_A"]
        new_edge[field.layers.int["mastro_list_use_id_B_EDGE"]] = use_data["use_id_list_B"]
        new_edge[field.layers.int["mastro_list_height_A_EDGE"]] = use_data["height_A"]
        new_edge[field.layers.int["mastro_list_height_B_EDGE"]] = use_data["height_B"]
        new_edge[field.layers.int["mastro_list_height_C_EDGE"]] = use_data["height_C"]
        new_edge[field.layers.int["mastro_list_height_D_EDGE"]] = use_data["height_D"]
        new_edge[field.layers.int["mastro_list_height_E_EDGE"]] = use_data["height_E"]


def _handle_block_extrusion(scene, obj, bm):
    """Detect vertex extrusion / new-edge on a MaStro block and fill attributes."""
    if not bpy.context.scene.tool_settings.mesh_select_mode[0]:
        return
    if not isinstance(bm.select_history.active, bmesh.types.BMVert):
        return

    active_vert = bm.select_history.active
    number_of_edges = len(bm.edges)

    typology_enum = bpy.context.scene.mastro_typology_names or "id_0"
    typology_id = int(typology_enum.replace("id_", ""))

    try:
        storeys_layer = bm.edges.layers.int["mastro_number_of_storeys_EDGE"]
        angle_layer   = bm.verts.layers.float["mastro_side_angle"]
    except KeyError:
        return

    if scene.mastro_previous_selection_vert_id != active_vert.index:
        scene.mastro_previous_selection_vert_id = active_vert.index
        selected_verts = [v for v in bm.verts if v.select]
        if len(selected_verts) == 1 and len(active_vert.link_edges) == 1:
            new_edge = active_vert.link_edges[0]
            if new_edge[storeys_layer] == 0:
                other_vert = new_edge.other_vert(active_vert)
                parent_edge = next((e for e in other_vert.link_edges if e != new_edge), None)
                if parent_edge is not None:
                    _fill_new_block_edge(bm, new_edge, parent_edge, typology_id)
                    active_vert[angle_layer] = 0
    else:
        selected_verts = [v for v in bm.verts if v.select]
        if len(selected_verts) == 2 and scene.mastro_previous_edge_number == number_of_edges - 1:
            last_edge = bm.edges[-1]
            if last_edge[storeys_layer] == 0:
                src_vert = next((v for v in last_edge.verts if len(v.link_edges) > 1), None)
                parent_edge = next((e for e in src_vert.link_edges if e != last_edge), None) if src_vert else None
                if parent_edge is not None:
                    _fill_new_block_edge(bm, last_edge, parent_edge, typology_id)

    scene.mastro_previous_edge_number = number_of_edges
