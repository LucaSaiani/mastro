"""Per-edge intersection-sector type for MaStro street, at each of the edge's two ends.

mastro_street_sector_type_A/B are plain EDGE-domain INT attributes (0/1/2): A is the
type at the edge's first vertex (index 0), B at its second (index 1) - the edge's own
native, stable vertex order. No digit-packing needed since an edge always has exactly
two ends.
"""


def sector_suffix_for_bmesh_edge(edge, vert_index):
    """Return "A" or "B" for a BMEdge `edge`, given the index of one of its two verts."""
    return "A" if edge.verts[0].index == vert_index else "B"


def sector_suffix_for_mesh_edge(edge, vert_index):
    """Return "A" or "B" for a mesh.edges item `edge`, given one of its `vertices[]`."""
    return "A" if edge.vertices[0] == vert_index else "B"
