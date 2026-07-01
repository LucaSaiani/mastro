import bpy
import bmesh

from ....Utils.mastro_street.read_write_sector_type import endpoint_suffix, SECTOR_ATTRS, get_sector_layers

# Guards the sector flag update= callbacks from firing (and writing back to the
# mesh) when the handler is resyncing the UI to reflect the newly active edge —
# not an actual user choice. Same pattern as MESH_OT_EditCircle._arc_prop_updating.
_resyncing_sector_type = False


def _polar_neighbors(obj, edge, vert):
    """Return (prev, next) edges around `vert` in polar order (atan2 on world XY),
    excluding `edge` itself. Returns (None, None) if vert has no other edges."""
    import math
    mw = obj.matrix_world
    origin = mw @ vert.co

    others = [e for e in vert.link_edges if e != edge]
    if not others:
        return None, None

    def angle_for(e):
        p = mw @ e.other_vert(vert).co
        return math.atan2(p.y - origin.y, p.x - origin.x)

    ref_angle = angle_for(edge)
    # Sort by CCW delta from edge's own angle; largest delta = prev, smallest = next.
    deltas = sorted(others, key=lambda e: (angle_for(e) - ref_angle) % (2 * math.pi))
    return deltas[-1], deltas[0]  # prev, next


def _get_flag(edge, vert, side, layers):
    """Read the 'left' or 'right' fillet flag for `edge` at `vert`."""
    suffix = endpoint_suffix(edge, vert.index)
    return edge[layers[SECTOR_ATTRS[suffix][side]]]


def _set_flag(edge, vert, side, value, layers):
    """Write the 'left' or 'right' fillet flag for `edge` at `vert`."""
    suffix = endpoint_suffix(edge, vert.index)
    edge[layers[SECTOR_ATTRS[suffix][side]]] = value


def _propagate(obj, bm, edge, vert, side, value, layers):
    """Mirror a single fillet flag change to the neighbor that shares that sector.

    Each sector (gap between two consecutive edges in polar order around a vertex)
    has exactly two 'faces': the right side of the CCW-previous edge and the left
    side of the CCW-next edge. They must always agree, so changing one mirrors to
    the other:
      - changing 'left'  of edge X  →  mirror to 'right' of PREV neighbor
      - changing 'right' of edge X  →  mirror to 'left'  of NEXT neighbor
    """
    prev_edge, next_edge = _polar_neighbors(obj, edge, vert)

    if side == 'left' and prev_edge is not None:
        _set_flag(prev_edge, vert, 'right', value, layers)
    elif side == 'right' and next_edge is not None:
        _set_flag(next_edge, vert, 'left', value, layers)


def _handle_street_sectors(scene, obj, bm):
    """Resync the sector UI props to the active edge's stored flag values.

    Called from update_view3D_panels on every selection change while editing a
    MaStro street with edge-select active. Reads the four BOOL attributes from the
    active edge and pushes them into the scene properties (both the raw bool props
    and the derived 3-button enum) without triggering their update= callbacks.
    """
    global _resyncing_sector_type

    if not bpy.context.scene.tool_settings.mesh_select_mode[1]:
        return
    if not isinstance(bm.select_history.active, bmesh.types.BMEdge):
        return

    active_edge = bm.select_history.active
    if not active_edge.is_valid:
        return

    try:
        layers = get_sector_layers(bm)
    except KeyError:
        return

    scene.mastro_street_active_edge = active_edge.index

    al = _get_flag(active_edge, active_edge.verts[0], 'left',  layers)
    ar = _get_flag(active_edge, active_edge.verts[0], 'right', layers)
    bl = _get_flag(active_edge, active_edge.verts[1], 'left',  layers)
    br = _get_flag(active_edge, active_edge.verts[1], 'right', layers)

    def to_enum(left, right):
        # Translate two bool flags to the 3-button enum shown in the panel.
        if left and right: return 'BOTH'
        if left:           return 'LEFT'
        if right:          return 'RIGHT'
        return 'BOTH'  # both False: degenerate state, default to Both in the UI

    _resyncing_sector_type = True
    try:
        scene.mastro_street_sector_A_left  = al
        scene.mastro_street_sector_A_right = ar
        scene.mastro_street_sector_B_left  = bl
        scene.mastro_street_sector_B_right = br
        scene.mastro_street_sector_enum_A  = to_enum(al, ar)
        scene.mastro_street_sector_enum_B  = to_enum(bl, br)
    finally:
        _resyncing_sector_type = False
