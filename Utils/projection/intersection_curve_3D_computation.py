import bmesh
from mathutils.geometry import intersect_line_plane
from mathutils import Vector
from mathutils.bvhtree import BVHTree

from .tolerance_constants import _EPSILON, _MIN_SEG_LEN

# =============================================================================
#  Intersection curve — 3D computation
# =============================================================================

# _EPSILON     = 1e-6
# _MIN_SEG_LEN = 1e-4


def _get_face_plane(face_verts):
    # Uses only the first three vertices to define the plane normal via cross
    # product. This is valid because both meshes are triangulated before this
    # function is called (bmesh.ops.triangulate), so every face is a triangle.
    v0, v1, v2 = face_verts[0], face_verts[1], face_verts[2]
    n = (v1 - v0).cross(v2 - v0)
    if n.length < _EPSILON:
        return None, None
    return v0, n.normalized()


def _point_in_triangle(p, tri, normal):
    # For each edge (a→b), the cross product (b-a)×(p-a) points in the same
    # direction as `normal` when p is on the CCW (inside) side of that edge.
    # A negative dot product means p is outside that edge, so the point is
    # outside the triangle. Winding order must match the face normal direction.
    for i in range(3):
        a, b = tri[i], tri[(i + 1) % 3]
        if (b - a).cross(p - a).dot(normal) < -_EPSILON:
            return False
    return True


def _get_intersection_segment(fA_verts, fB_verts):
    pA, nA = _get_face_plane(fA_verts)
    pB, nB = _get_face_plane(fB_verts)

    if pA is None or pB is None:
        return None
    if abs(nA.dot(nB)) > 1.0 - _EPSILON:
        return None

    pts = []
    for i in range(3):
        a, b = fA_verts[i], fA_verts[(i + 1) % 3]
        pt = intersect_line_plane(a, b, pB, nB)
        if pt:
            seg = b - a
            u = seg.dot(pt - a) / seg.length_squared
            if -_EPSILON <= u <= 1.0 + _EPSILON:
                if _point_in_triangle(pt, fB_verts, nB):
                    pts.append(pt)

    for i in range(3):
        a, b = fB_verts[i], fB_verts[(i + 1) % 3]
        pt = intersect_line_plane(a, b, pA, nA)
        if pt:
            seg = b - a
            u = seg.dot(pt - a) / seg.length_squared
            if -_EPSILON <= u <= 1.0 + _EPSILON:
                if _point_in_triangle(pt, fA_verts, nA):
                    pts.append(pt)

    if len(pts) < 2:
        return None

    # The true intersection of two triangles is a line segment whose endpoints
    # are the two furthest candidate points. Near-degenerate intersections or
    # numerical noise can produce more than two candidate points; selecting the
    # maximum-distance pair gives the longest (most accurate) segment.
    p1, p2   = pts[0], pts[1]
    dist_max = (p1 - p2).length_squared
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            d = (pts[i] - pts[j]).length_squared
            if d > dist_max:
                dist_max = d
                p1, p2 = pts[i], pts[j]

    return (p1, p2) if dist_max > _MIN_SEG_LEN ** 2 else None


def _bbox_overlap_world(obj_a, obj_b):
    def world_aabb(obj):
        mat     = obj.matrix_world
        corners = [mat @ Vector(c) for c in obj.bound_box]
        xs = [c.x for c in corners]
        ys = [c.y for c in corners]
        zs = [c.z for c in corners]
        return min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)

    ax0, ax1, ay0, ay1, az0, az1 = world_aabb(obj_a)
    bx0, bx1, by0, by1, bz0, bz1 = world_aabb(obj_b)

    if ax1 < bx0 or bx1 < ax0: return False
    if ay1 < by0 or by1 < ay0: return False
    if az1 < bz0 or bz1 < az0: return False
    return True


def _compute_intersection_segments_3d(obj_a, obj_b, depsgraph):
    eval_a = obj_a.evaluated_get(depsgraph)
    eval_b = obj_b.evaluated_get(depsgraph)
    mesh_a = eval_a.to_mesh()
    mesh_b = eval_b.to_mesh()

    if mesh_a is None or mesh_b is None:
        if mesh_a: eval_a.to_mesh_clear()
        if mesh_b: eval_b.to_mesh_clear()
        return []

    mat_a = eval_a.matrix_world
    mat_b = eval_b.matrix_world

    bm_a = bmesh.new(); bm_a.from_mesh(mesh_a); bm_a.transform(mat_a)
    bm_b = bmesh.new(); bm_b.from_mesh(mesh_b); bm_b.transform(mat_b)
    bmesh.ops.triangulate(bm_a, faces=bm_a.faces)
    bmesh.ops.triangulate(bm_b, faces=bm_b.faces)
    bm_a.faces.ensure_lookup_table()
    bm_b.faces.ensure_lookup_table()

    faces_a = [[v.co.copy() for v in f.verts] for f in bm_a.faces]
    faces_b = [[v.co.copy() for v in f.verts] for f in bm_b.faces]

    bvh_a = BVHTree.FromBMesh(bm_a)
    bvh_b = BVHTree.FromBMesh(bm_b)
    overlapping_pairs = bvh_a.overlap(bvh_b)

    segments = []
    for idx_a, idx_b in overlapping_pairs:
        if idx_a >= len(faces_a) or idx_b >= len(faces_b):
            continue
        seg = _get_intersection_segment(faces_a[idx_a], faces_b[idx_b])
        if seg is not None:
            segments.append((seg[0], seg[1], idx_a, idx_b))

    bm_a.free(); bm_b.free()
    eval_a.to_mesh_clear(); eval_b.to_mesh_clear()
    return segments, [], []