from mathutils import Vector

_BOUNDARY_TOL = 1e-4


def _perimeter_t(x, y, xmax, ymax):
    """Arc-length position on the rectangle perimeter.

    Origin at (-xmax, -ymax), traversal: bottom → right → top → left.
    Returns None if the point is not on a boundary edge.
    """
    if abs(y + ymax) < _BOUNDARY_TOL:
        return x + xmax
    if abs(x - xmax) < _BOUNDARY_TOL:
        return 2*xmax + (y + ymax)
    if abs(y - ymax) < _BOUNDARY_TOL:
        return 2*xmax + 2*ymax + (xmax - x)
    if abs(x + xmax) < _BOUNDARY_TOL:
        return 4*xmax + 2*ymax + (ymax - y)
    return None


def _perimeter_pt(t, xmax, ymax):
    """Point at arc-length t on the rectangle perimeter."""
    L1, L2, L3 = 2*xmax, 2*ymax, 2*xmax
    if t <= L1:
        return Vector((-xmax + t, -ymax, 0.0))
    t -= L1
    if t <= L2:
        return Vector((xmax, -ymax + t, 0.0))
    t -= L2
    if t <= L3:
        return Vector((xmax - t, ymax, 0.0))
    t -= L3
    return Vector((-xmax, ymax - t, 0.0))


def _arc_hits_object(mid_2d, aspect, vp_matrix, obj_eval):
    """Return True if a ray from the camera through mid_2d hits obj_eval.

    mid_2d is the arc midpoint in scaled-NDC space (x ∈ [-aspect, aspect],
    y ∈ [-1, 1]). The point is unprojected to a world-space ray using the
    inverse of vp_matrix, then cast against obj_eval in its local space.
    """
    ndc_x = mid_2d.x / aspect
    ndc_y = mid_2d.y

    try:
        inv_vp = vp_matrix.inverted()
    except Exception:
        return False

    # Unproject near and far clip-plane points to get the ray direction.
    def unproject(ndc_x, ndc_y, ndc_z):
        h = inv_vp @ Vector((ndc_x, ndc_y, ndc_z, 1.0))
        if abs(h.w) < 1e-12:
            return None
        return h.xyz / h.w

    world_near = unproject(ndc_x, ndc_y, -1.0)
    world_far  = unproject(ndc_x, ndc_y,  1.0)
    if world_near is None or world_far is None:
        return False

    ray_dir = world_far - world_near
    if ray_dir.length < 1e-12:
        return False
    ray_dir = ray_dir.normalized()

    # Transform ray into object local space.
    try:
        mat_inv = obj_eval.matrix_world.inverted()
    except Exception:
        return False

    origin_local = mat_inv @ world_near
    dir_local    = (mat_inv.to_3x3() @ ray_dir).normalized()

    result = obj_eval.ray_cast(origin_local, dir_local)
    # ray_cast returns (hit, location, normal, face_index)
    return result[0]


def close_boundary_cuts(bm, aspect, vp_matrix=None, obj_eval=None, *_args, **_kwargs):
    """Close gaps at the frame boundary using a 3D ray cast.

    For each arc between consecutive degree-1 boundary vertices, the midpoint
    of the arc is unprojected to a world-space ray and cast against obj_eval.
    If the ray hits the object, the arc is inside the projection and a closure
    segment is drawn along the frame perimeter.

    Falls back silently (draws nothing) if vp_matrix or obj_eval are absent.
    """
    if vp_matrix is None or obj_eval is None:
        return

    xmax, ymax = aspect, 1.0
    perimeter  = 4*xmax + 4*ymax
    corners_t  = [0.0, 2*xmax, 2*xmax + 2*ymax, 4*xmax + 2*ymax]

    boundary_verts = []
    for v in bm.verts:
        if len(v.link_edges) != 1:
            continue
        t = _perimeter_t(v.co.x, v.co.y, xmax, ymax)
        if t is None:
            continue
        boundary_verts.append((t, v))

    if len(boundary_verts) < 2:
        return

    boundary_verts.sort(key=lambda item: item[0])
    n = len(boundary_verts)

    vc = {}
    for _, v in boundary_verts:
        key = (round(v.co.x, 5), round(v.co.y, 5))
        vc[key] = v

    def get_or_add(co):
        key = (round(co.x, 5), round(co.y, 5))
        if key not in vc:
            vc[key] = bm.verts.new(co)
        return vc[key]

    def add_edge_safe(va, vb):
        if va is vb:
            return
        try:
            bm.edges.new((va, vb))
        except ValueError:
            pass

    def draw_arc(t_start, t_end, v_start, v_end):
        # t_end may exceed perimeter for the wrap-around pair; extend corners_t
        # by one full perimeter so the wrapped segment's corners are included.
        extended = corners_t + [ct + perimeter for ct in corners_t]
        mid_corners = [ct for ct in extended
                       if t_start + _BOUNDARY_TOL < ct < t_end - _BOUNDARY_TOL]
        path = [v_start]
        for ct in mid_corners:
            path.append(get_or_add(_perimeter_pt(ct % perimeter, xmax, ymax)))
        path.append(v_end)
        for j in range(len(path) - 1):
            add_edge_safe(path[j], path[j + 1])

    for i in range(n):
        t_a, v_a = boundary_verts[i]
        t_b, v_b = boundary_verts[(i + 1) % n]

        if i < n - 1:
            t_mid = (t_a + t_b) / 2.0
        else:
            t_mid = (t_a + t_b + perimeter) / 2.0

        mid = _perimeter_pt(t_mid % perimeter, xmax, ymax)
        if _arc_hits_object(mid, aspect, vp_matrix, obj_eval):
            if i < n - 1:
                draw_arc(t_a, t_b, v_a, v_b)
            else:
                draw_arc(t_a, t_b + perimeter, v_a, v_b)
