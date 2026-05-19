from mathutils import Vector
from mathutils.bvhtree import BVHTree

# =============================================================================
#  _build_global_bvh — build the global BVHTree ONCE
# =============================================================================


def _clip_polygon_to_plane(verts_ws, vert_ds, clip_val, keep_above):
    """
    One Sutherland-Hodgman clip step against the plane d = clip_val.

    keep_above=True  → keep vertices with d >= clip_val  (near-clip filter)
    keep_above=False → keep vertices with d <= clip_val  (far-clip filter)

    Returns (clipped_verts_ws, clipped_ds) or ([], []) when fully clipped.
    """
    out_ws = []
    out_ds = []
    n = len(verts_ws)
    for i in range(n):
        cp, cd  = verts_ws[i], vert_ds[i]
        np_, nd = verts_ws[(i + 1) % n], vert_ds[(i + 1) % n]
        c_in = (cd >= clip_val) if keep_above else (cd <= clip_val)
        n_in = (nd >= clip_val) if keep_above else (nd <= clip_val)
        if c_in:
            out_ws.append(cp)
            out_ds.append(cd)
        if c_in != n_in:
            t = (clip_val - cd) / (nd - cd)
            out_ws.append(cp.lerp(np_, t))
            out_ds.append(clip_val)
    return out_ws, out_ds


def _build_global_bvh(scene, depsgraph, excluded_names,
                      cam_location=None, cam_fwd=None,
                      clip_start=None, clip_end=None):
    """
    Build a global BVHTree from all evaluated meshes in the scene.
    Much faster than scene.ray_cast for repeated queries on static geometry.

    When camera_clipping is active (clip_start provided), faces in front of
    clip_start are excluded.  Objects straddling the clip plane have their
    faces clipped (Sutherland-Hodgman) so the BVH contains only geometry
    that exists within the clip volume — preventing ghost occlusion from
    faces that were cut away.

    Returns:
        bvh          – BVHTree with all geometry in world space (or None)
        poly_to_obj  – list parallel to polygons: poly_to_obj[i] = obj_eval
    """
    clip_active = (clip_start is not None
                   and cam_location is not None
                   and cam_fwd is not None)

    all_verts   = []
    all_polys   = []
    poly_to_obj = []
    vert_offset = 0

    for obj in scene.objects:
        if obj.type != 'MESH':
            continue
        if obj.name in excluded_names:
            continue

        obj_eval  = obj.evaluated_get(depsgraph)
        mesh_data = obj_eval.to_mesh()
        if mesh_data is None:
            continue

        mat      = obj_eval.matrix_world
        ws_verts = [mat @ v.co for v in mesh_data.vertices]

        cut_by_clip = False
        if clip_active:
            bbox_dists = [
                (mat @ Vector(corner) - cam_location).dot(cam_fwd)
                for corner in obj_eval.bound_box
            ]
            bbox_min = min(bbox_dists)
            bbox_max = max(bbox_dists)

            if bbox_max < clip_start:
                # Object entirely in front of near clip — skip.
                obj_eval.to_mesh_clear()
                continue

            if clip_end is not None and bbox_min > clip_end:
                # Object entirely beyond far clip — skip.
                obj_eval.to_mesh_clear()
                continue

            cut_by_clip = (bbox_min < clip_start or
                           (clip_end is not None and bbox_max > clip_end))

        if cut_by_clip:
            # Per-vertex distances along the camera axis.
            vert_dists = [
                (ws_verts[i] - cam_location).dot(cam_fwd)
                for i in range(len(ws_verts))
            ]

            # local_verts starts with the original vertices; clipped-edge
            # intersection points are appended as the loop progresses.
            local_verts = list(ws_verts)
            local_polys = []

            for poly in mesh_data.polygons:
                pv       = list(poly.vertices)
                face_ds  = [vert_dists[vi] for vi in pv]
                face_max = max(face_ds)
                face_min = min(face_ds)

                if face_max < clip_start:
                    continue  # All vertices in front of near clip.
                if clip_end is not None and face_min > clip_end:
                    continue  # All vertices beyond far clip.

                needs_near = face_min < clip_start
                needs_far  = clip_end is not None and face_max > clip_end

                if not needs_near and not needs_far:
                    # Face entirely within clip volume — use original indices.
                    local_polys.append(tuple(pv))
                    continue

                # Clip the polygon so only the portion inside the clip
                # volume enters the BVH.  Without this, the "phantom" part
                # of a straddling face would cause ghost occlusion.
                face_ws = [ws_verts[vi] for vi in pv]
                face_dv = list(face_ds)

                if needs_near:
                    face_ws, face_dv = _clip_polygon_to_plane(
                        face_ws, face_dv, clip_start, keep_above=True
                    )
                    if not face_ws:
                        continue

                if needs_far:
                    face_ws, face_dv = _clip_polygon_to_plane(
                        face_ws, face_dv, clip_end, keep_above=False
                    )
                    if not face_ws:
                        continue

                if len(face_ws) < 3:
                    continue

                base = len(local_verts)
                local_verts.extend(face_ws)
                local_polys.append(tuple(range(base, base + len(face_ws))))

            base_off = vert_offset
            all_verts.extend(local_verts)
            for lp in local_polys:
                all_polys.append(tuple(i + base_off for i in lp))
                poly_to_obj.append(obj_eval)
            vert_offset += len(local_verts)

        else:
            all_verts.extend(ws_verts)
            for poly in mesh_data.polygons:
                all_polys.append(tuple(vi + vert_offset for vi in poly.vertices))
                poly_to_obj.append(obj_eval)
            vert_offset += len(ws_verts)

        obj_eval.to_mesh_clear()

    if not all_polys:
        return None, []

    bvh = BVHTree.FromPolygons(all_verts, all_polys, epsilon=0.0)
    return bvh, poly_to_obj
