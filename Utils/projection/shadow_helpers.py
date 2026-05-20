import bpy
import math
from mathutils import Vector
from .scene_graph_helpers import link_to_projection_collection

_SHADOW_TAG    = "sun_shadow_points"
_STASH_SUFFIX  = "__stash__"


def get_light_source(context):
    """Return the selected SUN/AREA light from the active camera's properties, or None."""
    cam = context.scene.camera
    if cam is None:
        return None
    light = cam.data.mastro_projector_cl.light_source
    if light and light.type == 'LIGHT' and light.data.type in ('SUN', 'AREA'):
        return light
    return None


def sun_direction(light_obj):
    return (light_obj.matrix_world.to_3x3() @ Vector((0, 0, -1))).normalized()


def sun_direction_from_props(props, camera=None):
    """Return a sun direction vector (points toward the ground, i.e. where light travels).

    Uses a real light when assigned; otherwise computes from virtual azimuth/elevation.

    Convention: azimuth = shadow direction, counterclockwise from North (+Y).
      0° = shadow North, 90° = shadow West, 180° = shadow South, 270° = shadow East.
      315° = shadow NE (upper-right in top view) — same as 45° clockwise from North.

    In CAMERA mode the same convention applies relative to camera-up, then the
    direction is rotated into world space via the camera matrix.
    """
    light = props.light_source
    if light and light.type == 'LIGHT' and light.data.type in ('SUN', 'AREA'):
        return sun_direction(light)

    az = props.virtual_azimuth
    el = props.virtual_elevation
    # Counterclockwise from +Y (North): x = -sin(az), y = cos(az).
    x_base = -math.sin(az) * math.cos(el)
    y_base =  math.cos(az) * math.cos(el)
    z_base = -math.sin(el)

    if props.light_space == 'CAMERA' and camera is not None:
        # Same formula in camera local space (up=+Y_cam, right=+X_cam, into-scene=-Z_cam),
        # then rotated to world via the camera's rotation matrix.
        dir_cam = Vector((x_base, y_base, z_base))
        return (camera.matrix_world.to_3x3() @ dir_cam).normalized()

    return Vector((x_base, y_base, z_base)).normalized()


def is_shadow_helper(obj):
    return bool(obj.get(_SHADOW_TAG))


def scene_mesh_objects(context, light_obj):
    return [
        o for o in context.scene.objects
        if o != light_obj and o.type == "MESH"
        and not is_shadow_helper(o) and o.visible_get()
    ]


def collect_world_vertices(eval_objs):
    verts = []
    for obj in eval_objs:
        for v in obj.data.vertices:
            verts.append(obj.matrix_world @ v.co)
    return verts


def build_sun_visible_faces(mesh_objs, sun_dir):
    visible = set()
    for obj in mesh_objs:
        mat3 = obj.matrix_world.to_3x3()
        for poly in obj.data.polygons:
            if (mat3 @ poly.normal).normalized().dot(sun_dir) <= 0:
                visible.add((obj.name, poly.index))
    return visible


def get_scene_extent(world_verts, sun_dir):
    projs = [v.dot(sun_dir) for v in world_verts]
    return max(projs) - min(projs)


def collect_projector_empty_children(scene):
    """Return the set of names of all objects that are children of any projector empty."""
    from .scene_graph_helpers import _PROJECTOR_EMPTY_TAG
    children = set()
    def _walk(obj):
        for ch in obj.children:
            children.add(ch.name)
            _walk(ch)
    for obj in scene.objects:
        if obj.get(_PROJECTOR_EMPTY_TAG) and obj.type == 'EMPTY':
            _walk(obj)
    return children


def purge_shadow_helpers(empty=None):
    """Remove shadow helper objects.

    If empty is given, only remove objects that are direct or indirect children
    of that empty (plus any orphaned shadow helpers with no parent).
    This avoids deleting shadow meshes belonging to other cameras.
    """
    if empty is not None:
        owned = set()
        def _walk(obj):
            for ch in obj.children:
                owned.add(ch.name)
                _walk(ch)
        _walk(empty)

    for obj in list(bpy.data.objects):
        if not obj.get(_SHADOW_TAG):
            continue
        if obj.name.endswith(_STASH_SUFFIX):
            continue
        if empty is not None and obj.name not in owned and obj.parent is not None:
            continue
        me = obj.data if obj.type == "MESH" else None
        bpy.data.objects.remove(obj, do_unlink=True)
        if me and me.users == 0:
            bpy.data.meshes.remove(me)


def stash_children(empty):
    """Rename + hide projector-generated children so they can be restored on cancel.
    User-added children (no _SHADOW_TAG) are left untouched."""
    for child in list(empty.children):
        if not child.get(_SHADOW_TAG):
            continue
        child.name += _STASH_SUFFIX
        if child.type == "MESH" and child.data:
            child.data.name += _STASH_SUFFIX
        child.hide_viewport = True


def restore_stash(empty):
    """Delete partial new projector children; restore stashed projector children.
    User-added children (no _SHADOW_TAG) are left untouched."""
    for child in list(empty.children):
        if child.name.endswith(_STASH_SUFFIX):
            continue
        if not child.get(_SHADOW_TAG):
            continue
        me = child.data if child.type == "MESH" else None
        bpy.data.objects.remove(child, do_unlink=True)
        if me and me.users == 0:
            bpy.data.meshes.remove(me)
    for child in list(empty.children):
        if child.name.endswith(_STASH_SUFFIX):
            child.name = child.name[:-len(_STASH_SUFFIX)]
            if child.type == "MESH" and child.data and \
               child.data.name.endswith(_STASH_SUFFIX):
                child.data.name = child.data.name[:-len(_STASH_SUFFIX)]
            child.hide_viewport = False


def clear_stash(empty):
    """Delete stashed projector children (called on successful completion).
    User-added children are left untouched."""
    for child in list(empty.children):
        if child.name.endswith(_STASH_SUFFIX) and child.get(_SHADOW_TAG):
            me = child.data if child.type == "MESH" else None
            bpy.data.objects.remove(child, do_unlink=True)
            if me and me.users == 0:
                bpy.data.meshes.remove(me)


def collect_shadow_hit_points(face_data, mesh_objs):
    obj_map   = {o.name: o for o in mesh_objs}
    positions = []
    for (obj_name, poly_idx), data in face_data.items():
        if data["status"] != "shadow":
            continue
        obj = obj_map.get(obj_name)
        if not obj or poly_idx >= len(obj.data.polygons):
            continue
        if data["hit_points"]:
            positions.extend(data["hit_points"])
        else:
            positions.append(obj.matrix_world @ obj.data.polygons[poly_idx].center)
    return positions


def build_dark_face_tasks(mesh_objs, sun_vis, camera_obj):
    cam_pos = camera_obj.matrix_world.translation.copy() if camera_obj else None
    tasks = []
    for obj in mesh_objs:
        mw   = obj.matrix_world
        mw_n = mw.to_3x3().inverted().transposed()
        for poly in obj.data.polygons:
            if (obj.name, poly.index) in sun_vis:
                continue
            normal_ws = (mw_n @ poly.normal).normalized()
            if cam_pos is not None:
                if (cam_pos - mw @ poly.center).dot(normal_ws) <= 0:
                    continue
            tasks.append((obj, poly.index))
    return tasks


def build_dark_silhouette_edges(dark_tasks):
    """Boundary edges of the dark-face set (non-manifold within that set)."""
    edge_count = {}
    edge_data  = {}
    for obj, poly_idx in dark_tasks:
        poly = obj.data.polygons[poly_idx]
        n = len(poly.vertices)
        for i in range(n):
            vi_a = poly.vertices[i]
            vi_b = poly.vertices[(i + 1) % n]
            key  = (obj.name, min(vi_a, vi_b), max(vi_a, vi_b))
            edge_count[key] = edge_count.get(key, 0) + 1
            edge_data[key]  = (vi_a, vi_b, obj)
    result = []
    for key, cnt in edge_count.items():
        if cnt == 1:
            vi_a, vi_b, obj = edge_data[key]
            mw = obj.matrix_world
            result.append((mw @ obj.data.vertices[vi_a].co.copy(),
                           mw @ obj.data.vertices[vi_b].co.copy()))
    return result


def sample_edge_persp(A, B, cam_params, cell_size):
    """Samples along edge A-B including both endpoints, perspective-correct density."""
    if not cam_params or not cam_params.get("is_persp"):
        n = max(0, int(math.floor((B - A).length / cell_size)) - 1)
        return [A.lerp(B, k / (n + 1)) for k in range(0, n + 2)]

    cam_inv = cam_params["cam_inv"]
    A_cam   = cam_inv @ A
    B_cam   = cam_inv @ B
    d_a = -A_cam.z
    d_b = -B_cam.z
    if d_a <= 0 or d_b <= 0:
        return [A, B]
    d_avg   = (d_a + d_b) / 2
    cs      = cell_size / max(1.0, d_avg)
    A_ndc   = (A_cam.x / d_a, A_cam.y / d_a)
    B_ndc   = (B_cam.x / d_b, B_cam.y / d_b)
    ndc_len = math.sqrt((B_ndc[0] - A_ndc[0]) ** 2 + (B_ndc[1] - A_ndc[1]) ** 2)
    n = max(0, int(math.floor(ndc_len / cs)) - 1)
    return [A.lerp(B, k / (n + 1)) for k in range(0, n + 2)]


def process_dark_face(obj, poly_idx, cell_size, cam_params):
    me   = obj.data
    mw   = obj.matrix_world
    mw_n = mw.to_3x3().inverted().transposed()
    poly = me.polygons[poly_idx]

    normal_ws = (mw_n @ poly.normal).normalized()
    verts_ws  = [mw @ me.vertices[vi].co for vi in poly.vertices]

    arb    = Vector((0, 0, 1)) if abs(normal_ws.dot(Vector((0, 0, 1)))) < 0.99 \
             else Vector((1, 0, 0))
    fu     = normal_ws.cross(arb).normalized()
    fv     = normal_ws.cross(fu).normalized()
    origin = verts_ws[0]
    plane_d = normal_ws.dot(origin)

    verts2d = [((p - origin).dot(fu), (p - origin).dot(fv)) for p in verts_ws]

    def _in_poly(px, py, verts2d=verts2d):
        inside = False
        x1, y1 = verts2d[-1]
        for x2, y2 in verts2d:
            if (y1 > py) != (y2 > py):
                if px < (x2 - x1) * (py - y1) / (y2 - y1 + 1e-12) + x1:
                    inside = not inside
            x1, y1 = x2, y2
        return inside

    positions  = []
    use_persp  = bool(cam_params and cam_params.get("is_persp"))

    if use_persp:
        cam_pos    = cam_params["cam_pos"]
        cam_inv    = cam_params["cam_inv"]
        cam_mat3   = cam_params["cam_mat3"]
        clip_start = cam_params.get("clip_start", 0.01)

        verts_cam = [cam_inv @ p for p in verts_ws]
        depths    = [-v.z for v in verts_cam]

        if min(depths) <= clip_start:
            use_persp = False
        else:
            d_avg = sum(depths) / len(depths)
            cs    = cell_size / max(1.0, d_avg)
            verts_proj = [(v.x / (-v.z), v.y / (-v.z)) for v in verts_cam]
            us = [p[0] for p in verts_proj]; vs = [p[1] for p in verts_proj]
            min_u, max_u = min(us), max(us)
            min_v, max_v = min(vs), max(vs)
            nx = max(1, math.ceil((max_u - min_u) / cs))
            ny = max(1, math.ceil((max_v - min_v) / cs))
            if nx * ny > 10_000:
                scale = math.sqrt(10_000 / (nx * ny))
                nx = max(1, round(nx * scale))
                ny = max(1, round(ny * scale))

            for iy in range(ny):
                for ix in range(nx):
                    pu = min_u + (ix + 0.5) * cs
                    pv = min_v + (iy + 0.5) * cs
                    ray_dir_ws = (cam_mat3 @ Vector((pu, pv, -1))).normalized()
                    denom = normal_ws.dot(ray_dir_ws)
                    if abs(denom) < 1e-9:
                        continue
                    t = (plane_d - normal_ws.dot(cam_pos)) / denom
                    if t <= 0:
                        continue
                    pos = cam_pos + t * ray_dir_ws
                    if not _in_poly((pos - origin).dot(fu), (pos - origin).dot(fv)):
                        continue
                    positions.append(pos.copy())

    if not use_persp:
        xs = [p[0] for p in verts2d]; ys = [p[1] for p in verts2d]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        nx = max(1, math.ceil((max_x - min_x) / cell_size))
        ny = max(1, math.ceil((max_y - min_y) / cell_size))
        if nx * ny > 10_000:
            scale = math.sqrt(10_000 / (nx * ny))
            nx = max(1, round(nx * scale))
            ny = max(1, round(ny * scale))

        for iy in range(ny):
            for ix in range(nx):
                px = min_x + (ix + 0.5) * cell_size
                py = min_y + (iy + 0.5) * cell_size
                if not _in_poly(px, py):
                    continue
                positions.append((origin + fu * px + fv * py).copy())

    if not positions:
        positions.append((mw @ poly.center).copy())

    return positions


def create_shadow_cam_mesh(positions, camera, scene, empty,
                           uv_pairs=None, alpha=0.0, reconstruct=False,
                           precomputed_faces=None, plane_matrix=None):
    """
    Create the {cam_name}_shadow mesh and parent it to *empty*.

    Face priority:
      precomputed_faces – use as-is (silhouette method passes triangles here)
      reconstruct=True  – run alpha-shape on uv_pairs
      else              – vertex-only point cloud

    plane_matrix (optional):
      When provided, *positions* are 2D local-space coords (x, y, 0) and this
      4×4 matrix transforms them to world space (camera near-plane placement).
      This guarantees perfect coplanarity — no floating-point drift across verts.

      When None and place_on_camera_plane=True, the legacy path is used: positions
      are world-space 3D coords and are first projected onto the exact near plane
      to eliminate any accumulated floating-point error.
    """
    if not positions:
        return None

    mesh_name = camera.name + "_shadow"
    old = bpy.data.objects.get(mesh_name)
    if old:
        old_data = old.data
        old_type = old.type
        bpy.data.objects.remove(old, do_unlink=True)
        if old_data and old_data.users == 0:
            if old_type == 'MESH':
                bpy.data.meshes.remove(old_data)
            elif old_type == 'GPENCIL' and hasattr(bpy.data, 'grease_pencils'):
                bpy.data.grease_pencils.remove(old_data)
            elif old_type == 'GREASEPENCIL' and hasattr(bpy.data, 'grease_pencils_v3'):
                bpy.data.grease_pencils_v3.remove(old_data)

    # ── For on-cam world-space verts: project onto exact near plane ───────────
    # (silhouette / adaptive-grid paths — eliminates floating-point drift)
    if plane_matrix is None and camera.data.mastro_projector_cl.place_on_camera_plane:
        from mathutils import Vector as _V
        cam_mat  = camera.matrix_world
        cam_fwd  = -_V(cam_mat.col[2][:3]).normalized()
        near     = camera.data.clip_start * 1.01
        plane_pt = cam_mat.translation + cam_fwd * near
        positions = [v - cam_fwd * (v - plane_pt).dot(cam_fwd) for v in positions]

    if precomputed_faces is not None:
        faces = precomputed_faces
    elif reconstruct and uv_pairs and len(uv_pairs) >= 3:
        faces = []
        try:
            from .alpha_shape import alpha_shape_triangles
            _, tris = alpha_shape_triangles(uv_pairs, alpha)
            faces = tris
        except Exception as exc:
            print(f"[Shadow] Alpha shape failed, falling back to point cloud: {exc}")
    else:
        faces = []

    me = bpy.data.meshes.new(mesh_name)
    me.from_pydata([v.to_tuple() for v in positions], [], faces)
    me.update()

    # When a plane_matrix is provided the vertices are in 2D local space (z=0)
    # and the mesh normal points in local +Z. The plane_matrix Z column is cam_fwd
    # (away from camera), so we flip all face normals so they point toward camera.
    if plane_matrix is not None and faces:
        import bmesh as _bm
        bm = _bm.new()
        bm.from_mesh(me)
        _bm.ops.reverse_faces(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
        me.update()

    obj = bpy.data.objects.new(mesh_name, me)
    obj[_SHADOW_TAG]    = True
    obj.hide_viewport   = True
    link_to_projection_collection(obj, scene)

    if empty is not None:
        obj.parent = empty
        if plane_matrix is not None:
            # vertices are in 2D local space; encode the full world transform via
            # matrix_parent_inverse so obj.matrix_world == plane_matrix
            obj.matrix_parent_inverse = empty.matrix_world.inverted() @ plane_matrix
        elif camera.data.mastro_projector_cl.place_on_camera_plane:
            obj.matrix_parent_inverse = empty.matrix_world.inverted()

    return obj


def unhide_empty_children(empty):
    """Recursively unhide all children of *empty* in the viewport."""
    for child in empty.children:
        child.hide_viewport = False
        unhide_empty_children(child)


def fmt_time(seconds):
    return f"{seconds:.2f}s" if seconds < 60 else f"{int(seconds//60)}m {seconds%60:.1f}s"


def _set_header(text):
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == "VIEW_3D":
                area.header_text_set(text)
                area.tag_redraw()
                return


def _clear_header():
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == "VIEW_3D":
                area.header_text_set(None)
                area.tag_redraw()
                return
