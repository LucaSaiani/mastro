"""
Alpha shape reconstruction from a 2D point cloud.

Uses scipy.spatial.Delaunay (Qhull/C backend) to compute the Delaunay
triangulation, then filters triangles whose circumradius exceeds a threshold.

The circumradius is computed on coordinates normalised by the bounding-box
diagonal, making the alpha parameter dimensionless and scene-scale independent:

  alpha = 0   → convex hull (keep all triangles)
  alpha = 1   → keep triangles whose circumradius ≤ 100 % of bbox diagonal
  alpha = 5   → keep triangles whose circumradius ≤  20 % of bbox diagonal
  alpha = 20  → keep triangles whose circumradius ≤   5 % of bbox diagonal

Larger alpha → tighter/more concave boundary, better island separation;
too large removes interior triangles and fragments the mesh.
"""

import numpy as np


def alpha_shape_triangles(uv_points, alpha):
    """
    Parameters
    ----------
    uv_points : sequence of (u, v) floats  (len >= 3)
    alpha     : float >= 0.  0 = convex hull.

    Returns
    -------
    pts  : np.ndarray shape (N, 2)   original (un-normalised) points
    tris : list of (i0, i1, i2)      indices into pts, alpha-valid triangles only
    """
    from scipy.spatial import Delaunay  # noqa: PLC0415

    pts = np.array(uv_points, dtype=np.float64)
    if len(pts) < 3:
        return pts, []

    # Normalise to make alpha scale-independent
    bbox_min = pts.min(axis=0)
    bbox_max = pts.max(axis=0)
    diagonal = float(np.linalg.norm(bbox_max - bbox_min))
    if diagonal < 1e-12:
        return pts, []
    pts_n = (pts - bbox_min) / diagonal   # coords in [0, 1/√2] range

    try:
        tri = Delaunay(pts_n)
    except Exception:
        return pts, []

    simplices = tri.simplices   # (M, 3) int array

    if alpha == 0.0:
        return pts, simplices.tolist()

    # Vectorised circumradius on normalised coords
    A = pts_n[simplices[:, 0]]
    B = pts_n[simplices[:, 1]]
    C = pts_n[simplices[:, 2]]

    ab = B - A
    ac = C - A
    bc = C - B

    la = np.linalg.norm(bc, axis=1)
    lb = np.linalg.norm(ac, axis=1)
    lc = np.linalg.norm(ab, axis=1)

    cross = ab[:, 0] * ac[:, 1] - ab[:, 1] * ac[:, 0]
    area2 = np.abs(cross)

    with np.errstate(divide='ignore', invalid='ignore'):
        r = (la * lb * lc) / (2.0 * area2)

    threshold = 1.0 / alpha
    mask = r <= threshold

    return pts, simplices[mask].tolist()
