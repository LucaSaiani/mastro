"""Order the edges (branches) meeting at a street intersection vertex by polar angle.

Used purely for the UI's circular selection (cycling through branches around the
active vertex in a stable, predictable visual order) - the sector type itself is
stored per-edge (mastro_street_sector_A/B_left/right, see read_write_sector_type.py), not
indexed by this ordering, so there's no need for it to match anything GN computes.
"""

import math


def angle_ordered_branches(obj, vert):
    """Return `vert.link_edges` ordered by polar angle (atan2 on world-space XY,
    increasing angle) of each edge's other endpoint around `vert`.

    `obj` supplies matrix_world for the world-space projection. `vert` is a BMVert.
    """
    origin = obj.matrix_world @ vert.co

    def angle_for(edge):
        other = edge.other_vert(vert)
        p = obj.matrix_world @ other.co
        return math.atan2(p.y - origin.y, p.x - origin.x)

    return sorted(vert.link_edges, key=angle_for)
