import bpy
import bmesh

from ....Utils.mastro_street.angle_ordered_branches import angle_ordered_branches
from ....Utils.mastro_street.read_write_sector_type import sector_suffix_for_bmesh_edge

# Guards mastro_street_active_branch_type's update= callback from firing (and
# writing back to the mesh) when we're only resyncing the enum to reflect the
# branch the user just cycled to, not an actual user choice - same pattern as
# MESH_OT_EditCircle.py's _arc_prop_updating.
_resyncing_branch_type = False



def _handle_street_sectors(scene, obj, bm):
    """Resync the active-branch cycling state to the active vertex's branches.

    Called from update_view3D_panels on every selection change while editing a
    MaStro street with vertex-select active. Clamps mastro_street_active_branch to
    the valid range for however many branches the active vertex has, resolves
    that branch to an (edge, vertex) pair, and resyncs the type enum to the
    branch's current stored value - without triggering its update= (the user
    hasn't chosen anything yet, this is just reflecting mesh state in the UI).
    """
    global _resyncing_branch_type

    if not bpy.context.scene.tool_settings.mesh_select_mode[0]:
        scene.mastro_street_active_branch_count = 0
        return
    if not isinstance(bm.select_history.active, bmesh.types.BMVert):
        scene.mastro_street_active_branch_count = 0
        return

    active_vert = bm.select_history.active
    if not active_vert.is_valid:
        scene.mastro_street_active_branch_count = 0
        return

    branches = angle_ordered_branches(obj, active_vert)
    scene.mastro_street_active_branch_count = len(branches)
    if not branches:
        return

    index = scene.mastro_street_active_branch % len(branches)
    if scene.mastro_street_active_branch != index:
        scene.mastro_street_active_branch = index

    edge = branches[index]
    scene.mastro_street_active_branch_vertex = active_vert.index
    scene.mastro_street_active_branch_edge = edge.index

    try:
        bm_sector_a = bm.edges.layers.int["mastro_street_sector_type_A"]
        bm_sector_b = bm.edges.layers.int["mastro_street_sector_type_B"]
    except KeyError:
        return

    suffix = sector_suffix_for_bmesh_edge(edge, active_vert.index)
    layer = bm_sector_a if suffix == "A" else bm_sector_b

    _resyncing_branch_type = True
    try:
        scene.mastro_street_active_branch_type = str(edge[layer])
    finally:
        _resyncing_branch_type = False
