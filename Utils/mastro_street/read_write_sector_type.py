"""Per-edge fillet flags for MaStro street intersection sectors.

Four BOOL EDGE-domain attributes, one per (endpoint, side):
  mastro_street_sector_A_left   — fillet on the left  (PREV polar) side at verts[0]
  mastro_street_sector_A_right  — fillet on the right (NEXT polar) side at verts[0]
  mastro_street_sector_B_left   — fillet on the left  (PREV polar) side at verts[1]
  mastro_street_sector_B_right  — fillet on the right (NEXT polar) side at verts[1]

Propagation is a simple mirror: changing left of edge X mirrors to right of its PREV
neighbor at that vertex; changing right mirrors to left of its NEXT neighbor.
"""

SECTOR_ATTRS = {
    'A': {'left': 'mastro_street_sector_A_left', 'right': 'mastro_street_sector_A_right'},
    'B': {'left': 'mastro_street_sector_B_left', 'right': 'mastro_street_sector_B_right'},
}


def endpoint_suffix(edge, vert_index):
    """Return 'A' if vert_index is edge.verts[0], else 'B'."""
    return 'A' if edge.verts[0].index == vert_index else 'B'


def endpoint_suffix_mesh(edge, vert_index):
    """Same as endpoint_suffix but for a mesh.edges item (uses .vertices[])."""
    return 'A' if edge.vertices[0] == vert_index else 'B'


def get_sector_layers(bm):
    """Return a dict {attr_name: layer} for all four sector BOOL layers, or raise KeyError."""
    layers = {}
    for suffix, sides in SECTOR_ATTRS.items():
        for side, attr in sides.items():
            layers[attr] = bm.edges.layers.bool[attr]
    return layers
