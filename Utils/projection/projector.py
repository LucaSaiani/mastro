import bmesh
import math
from mathutils import Vector

from .remove_overlapping_boundary_edges import _remove_overlapping_boundary_edges
from .tolerance_constants import _TOL_DEGENERATE
from .projection_result import ObjectProjection
from .close_boundary_cuts import close_boundary_cuts

# =============================================================================
#  Camera-clipping helper
# =============================================================================

def _clip_segment_to_planes(p0, p1, d0, d1, clip_start, clip_end):
    """
    Clip world-space segment [p0, p1] against the near and far clip planes.
    d0, d1 are the dot products of the endpoints with the camera forward vector.

    Returns (p0, p1, d0, d1, visible) where visible=False means the segment
    is entirely outside one plane and should be discarded.
    """
    if d0 < clip_start and d1 < clip_start:
        return p0, p1, d0, d1, False
    if d0 < clip_start:
        p0 = p0.lerp(p1, (clip_start - d0) / (d1 - d0))
        d0 = clip_start
    elif d1 < clip_start:
        p1 = p0.lerp(p1, (clip_start - d0) / (d1 - d0))
        d1 = clip_start
    if d0 > clip_end and d1 > clip_end:
        return p0, p1, d0, d1, False
    if d0 > clip_end:
        p0 = p0.lerp(p1, (clip_end - d0) / (d1 - d0))
    elif d1 > clip_end:
        p1 = p0.lerp(p1, (clip_end - d0) / (d1 - d0))
    return p0, p1, d0, d1, True


# =============================================================================
#  _Projector — calculation logic, parameterised by a PropertyGroup instance
# =============================================================================

class _Projector:

    def __init__(self, props, global_bvh=None, poly_to_obj=None):
        self.props       = props
        self.global_bvh  = global_bvh
        self.poly_to_obj = poly_to_obj

    # ── Camera matrices ───────────────────────────────────────────────────────

    def get_camera_matrices(self, scene, camera, depsgraph):
        render      = scene.render
        view_matrix = camera.matrix_world.inverted()
        proj_matrix = camera.calc_matrix_camera(
            depsgraph,
            x       = render.resolution_x,
            y       = render.resolution_y,
            scale_x = render.pixel_aspect_x,
            scale_y = render.pixel_aspect_y,
        )
        aspect = (render.resolution_x * render.pixel_aspect_x) / \
                 (render.resolution_y * render.pixel_aspect_y)
        return view_matrix, proj_matrix, aspect

    # ── Projection helpers ────────────────────────────────────────────────────

    @staticmethod
    def world_to_ndc(co_world, view_matrix, proj_matrix):
        co_view = view_matrix @ co_world.to_4d()
        # In Blender's camera space the camera looks down its local -Z axis.
        # After the view transform, points in front of the camera have z < 0;
        # z >= 0 means the point is behind (or on) the camera plane and must
        # be discarded to avoid projecting geometry behind the viewer.
        if co_view.z >= 0:
            return None
        co_ndc  = proj_matrix @ co_view
        if abs(co_ndc.w) < _TOL_DEGENERATE or co_ndc.w < 0:
            return None
        return Vector((co_ndc.x / co_ndc.w,
                       co_ndc.y / co_ndc.w,
                       co_ndc.z / co_ndc.w))

    @staticmethod
    def ndc_to_3d(ndc, scale, aspect):
        return Vector((ndc.x * scale * aspect, ndc.y * scale, 0.0))

    # ── Visibility ────────────────────────────────────────────────────────────

    def sample_visible(self, scene, depsgraph, cam_location, pt_world, exclude_obj,
                       ortho_direction=None):
        """
        Cast a visibility ray from pt_world toward the camera.

        For perspective cameras, the ray direction converges toward cam_location.
        For orthographic cameras, all rays are parallel to the camera forward axis
        (ortho_direction). Using cam_location as the target for ortho would produce
        slightly different directions for off-centre points, causing incorrect
        visibility results — especially noticeable at large ortho scales.
        """
        props = self.props
        if ortho_direction is not None:
            # Orthographic: parallel rays along the camera forward axis.
            direction = ortho_direction
            origin    = pt_world + direction * props.ray_offset
            distance  = 1e6  # large enough to always reach the camera
        else:
            # Perspective: rays converge toward the camera location.
            direction = (cam_location - pt_world).normalized()
            origin    = pt_world + direction * props.ray_offset
            distance  = (cam_location - pt_world).length - props.ray_offset * 2

        if self.global_bvh is not None:
            loc, _normal, poly_idx, _dist = self.global_bvh.ray_cast(
                origin, direction, distance
            )
            if loc is None:
                return True, None
            hit_obj = (self.poly_to_obj[poly_idx]
                       if poly_idx is not None and poly_idx < len(self.poly_to_obj)
                       else None)
            if hit_obj != exclude_obj:
                return False, hit_obj.name if hit_obj else None

        traveled = 0.0
        while traveled < distance:
            hit, loc, _normal, _face_idx, hit_obj, _matrix = scene.ray_cast(
                depsgraph, origin, direction, distance=distance - traveled
            )
            if not hit:
                return True, None
            if hit_obj != exclude_obj:
                return False, hit_obj.name
            step     = (loc - origin).length + props.ray_offset
            origin   = origin + direction * step
            traveled += step

        return True, None

    # ── Adaptive visibility sampling ──────────────────────────────────────────

    def sample_visibility_adaptive(self, scene, depsgraph, cam_location,
                                   p0, p1, obj_eval, ndc0, ndc1,
                                   min_len, depth=0, max_depth=8,
                                   ortho_direction=None):
        """
        Recursively sample visibility along world-space segment [p0, p1].

        Hybrid strategy:
          - Always subdivides until NDC length < min_len to avoid skipping
            small occluders.
          - Skips subdivision early when endpoints AND midpoint agree AND
            the segment is already shorter than 2 * min_len.

        Returns a list of (ndc_start, ndc_end, is_visible) run tuples.
        """
        screen_len = (ndc1.xy - ndc0.xy).length

        if screen_len < min_len or depth >= max_depth:
            vis, _ = self.sample_visible(
                scene, depsgraph, cam_location, p0, obj_eval,
                ortho_direction=ortho_direction,
            )
            return [(ndc0, ndc1, vis)]

        p_mid    = p0.lerp(p1, 0.5)
        ndc_mid  = ndc0.lerp(ndc1, 0.5)

        vis0, _  = self.sample_visible(scene, depsgraph, cam_location, p0,    obj_eval, ortho_direction=ortho_direction)
        vis1, _  = self.sample_visible(scene, depsgraph, cam_location, p1,    obj_eval, ortho_direction=ortho_direction)
        vis_m, _ = self.sample_visible(scene, depsgraph, cam_location, p_mid, obj_eval, ortho_direction=ortho_direction)

        if vis0 == vis1 == vis_m and screen_len < min_len * 2:
            return [(ndc0, ndc1, vis0)]

        left  = self.sample_visibility_adaptive(
            scene, depsgraph, cam_location,
            p0, p_mid, obj_eval, ndc0, ndc_mid,
            min_len, depth + 1, max_depth,
            ortho_direction=ortho_direction,
        )
        right = self.sample_visibility_adaptive(
            scene, depsgraph, cam_location,
            p_mid, p1, obj_eval, ndc_mid, ndc1,
            min_len, depth + 1, max_depth,
            ortho_direction=ortho_direction,
        )

        runs   = left + right
        merged = [runs[0]]
        for run in runs[1:]:
            if run[2] == merged[-1][2]:
                merged[-1] = (merged[-1][0], run[1], run[2])
            else:
                merged.append(run)
        return merged

    # ── Segmentation (uniform mode) ───────────────────────────────────────────

    def compute_segments(self, ndc0, ndc1):
        screen_len = (ndc1.xy - ndc0.xy).length
        if screen_len < _TOL_DEGENERATE:
            return 1
        return max(1, int(screen_len / self.props.segment_length + 0.5))

    # ── Flat-edge filter ─────────────────────────────────────────────────────

    def is_flat_edge(self, edge, mesh_data):
        props     = self.props
        threshold = props.flat_angle_threshold
        if threshold <= 0.0:
            return False

        linked = edge.link_faces
        if len(linked) != 2:
            return False

        fa, fb = linked[0], linked[1]

        if fa.material_index != fb.material_index:
            return False

        mats = mesh_data.materials
        if len(mats) > 1:
            mat_a = mats[fa.material_index] if fa.material_index < len(mats) else None
            mat_b = mats[fb.material_index] if fb.material_index < len(mats) else None
            if mat_a is not mat_b:
                return False

        # Clamp to [-1, 1] before acos: floating-point arithmetic can push the
        # dot product slightly outside this range, which would raise a domain error.
        cos_angle = max(-1.0, min(1.0, fa.normal.dot(fb.normal)))
        return math.acos(cos_angle) < threshold

    # ── Silhouette detection ──────────────────────────────────────────────────

    @staticmethod
    def is_silhouette_edge(edge, view_dir):
        linked = edge.link_faces
        if len(linked) == 1:
            return True
        if len(linked) != 2:
            return False
        fa, fb   = linked[0], linked[1]
        fa_front = fa.normal.dot(view_dir) < 0.0
        fb_front = fb.normal.dot(view_dir) < 0.0
        return fa_front != fb_front

    # ── Bounding-box frustum cull ─────────────────────────────────────────────

    @staticmethod
    def bbox_in_frustum(obj, vp_matrix, view_matrix, camera_clipping=False,
                        clip_start=0.0, clip_end=1e9):
        """Return True if the object's bounding box intersects the view frustum.

        Always tests the 4 lateral clip planes. Near/far depth planes are only
        tested when camera_clipping is True — otherwise large scenes with
        clip_end smaller than the scene extent would incorrectly cull objects.
        """
        mat     = obj.matrix_world
        corners = [mat @ Vector(c) for c in obj.bound_box]

        # Lateral cull: if all corners are outside any one lateral plane, skip.
        clip_corners = [vp_matrix @ co.to_4d() for co in corners]
        for nx, ny, nw in (
            ( 1,  0, 1),   # left
            (-1,  0, 1),   # right
            ( 0,  1, 1),   # bottom
            ( 0, -1, 1),   # top
        ):
            if all(nx*c.x + ny*c.y + nw*c.w < 0 for c in clip_corners):
                return False

        if camera_clipping:
            # Depth cull using view-space z depths.
            depths = [-(view_matrix @ co.to_4d()).z for co in corners]
            if all(d < clip_start for d in depths):
                return False
            if all(d > clip_end for d in depths):
                return False
        else:
            # Without depth clipping, only exclude objects entirely behind camera.
            depths = [-(view_matrix @ co.to_4d()).z for co in corners]
            if all(d <= 0 for d in depths):
                return False

        return True

    # ── Lateral frustum clip (Liang-Barsky in clip space) ─────────────────────

    @staticmethod
    def _clip_segment_lateral(p0, p1, vp_matrix):
        """Clip world-space segment [p0, p1] against the 4 lateral frustum planes
        (x=±1, y=±1 in NDC) using Liang-Barsky in homogeneous clip space.

        A straight 3D line maps linearly to clip space, so the parameter t found
        here can be used directly with p0.lerp(p1, t) to recover world-space
        clip points for correct visibility ray casting.

        Returns (p0_clipped, p1_clipped, visible).
        """
        c0 = vp_matrix @ p0.to_4d()
        c1 = vp_matrix @ p1.to_4d()
        dc = c1 - c0
        t0, t1 = 0.0, 1.0
        for nx, ny, nw in ((1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1)):
            p_val = nx * c0.x + ny * c0.y + nw * c0.w
            d_val = nx * dc.x + ny * dc.y + nw * dc.w
            if abs(d_val) < 1e-12:
                if p_val < 0:
                    return p0, p1, False
                continue
            t = -p_val / d_val
            if d_val < 0:
                t1 = min(t1, t)
            else:
                t0 = max(t0, t)
            if t0 > t1:
                return p0, p1, False
        p0_out = p0.lerp(p1, t0) if t0 > 1e-9       else p0
        p1_out = p0.lerp(p1, t1) if t1 < 1.0 - 1e-9 else p1
        return p0_out, p1_out, True

    # ── Emit a single visibility run into the correct bmeshes ─────────────────

    @staticmethod
    def _emit_run(ndc_s, ndc_e, is_vis, edge_is_sil,
                  bm_visible,   vc_visible,
                  bm_silhouette, vc_silhouette,
                  bm_hidden,    vc_hidden,
                  bm_silhouette_hidden, vc_silhouette_hidden,
                  scale, aspect):
        """
        Add one NDC segment to the appropriate bmesh(es) based on visibility
        and silhouette classification.
        """
        def get_or_add(bm, vc, ndc):
            pt  = Vector((ndc.x * scale * aspect, ndc.y * scale, 0.0))
            key = (int(pt.x * 1e5), int(pt.y * 1e5))
            if key not in vc:
                vc[key] = bm.verts.new(pt)
            return vc[key]

        def add_edge(bm, vc, ndc_a, ndc_b):
            va = get_or_add(bm, vc, ndc_a)
            vb = get_or_add(bm, vc, ndc_b)
            if va is vb:
                return
            try:
                bm.edges.new((va, vb))
            except ValueError:
                pass

        if edge_is_sil:
            if is_vis:
                add_edge(bm_visible, vc_visible, ndc_s, ndc_e)
                if bm_silhouette is not None:
                    add_edge(bm_silhouette, vc_silhouette, ndc_s, ndc_e)
            else:
                if bm_hidden is not None:
                    add_edge(bm_hidden, vc_hidden, ndc_s, ndc_e)
                if bm_silhouette_hidden is not None:
                    add_edge(bm_silhouette_hidden, vc_silhouette_hidden,
                             ndc_s, ndc_e)
        else:
            if is_vis:
                add_edge(bm_visible, vc_visible, ndc_s, ndc_e)
            else:
                if bm_hidden is not None:
                    add_edge(bm_hidden, vc_hidden, ndc_s, ndc_e)

    # ── Main projection loop ──────────────────────────────────────────────────

    def build_projection_per_object(self, scene, depsgraph, camera, excluded_names):
        """
        Returns:
            results – dict { src_obj_name: { "bm_visible":           BMesh | None,
                                              "bm_silhouette":        BMesh | None,
                                              "bm_hidden":            BMesh | None,
                                              "bm_silhouette_hidden": BMesh | None } }
            aspect  – float
        """
        props = self.props
        view_matrix, proj_matrix, aspect = self.get_camera_matrices(
            scene, camera, depsgraph
        )
        vp_matrix    = proj_matrix @ view_matrix
        cam_location = camera.matrix_world.translation.copy()
        # For orthographic cameras, visibility rays must be parallel to the
        # camera forward axis rather than converging toward cam_location.
        # This avoids direction errors for points far from the image centre.
        if camera.data.type == 'ORTHO':
            # Camera forward in world space is the negative Z column of the
            # camera world matrix (pointing INTO the scene from the camera).
            ortho_direction = (camera.matrix_world.col[2].xyz).normalized()
        else:
            ortho_direction = None
        results      = {}

        camera_clipping = props.camera_clipping
        clip_start = camera.data.clip_start
        clip_end   = camera.data.clip_end
        if camera_clipping:
            cam_fwd = (-camera.matrix_world.col[2].xyz).normalized()

        selected_names = (
            {obj.name for obj in scene.objects if obj.select_get()}
            if props.only_selected_objects else None
        )

        for obj in scene.objects:
            if obj.type != 'MESH':
                continue
            if obj.name in excluded_names:
                continue
            if not obj.visible_get():
                continue
            if selected_names is not None and obj.name not in selected_names:
                continue
            if not self.bbox_in_frustum(obj, vp_matrix, view_matrix,
                                        camera_clipping, clip_start, clip_end):
                continue

            obj_eval  = obj.evaluated_get(depsgraph)
            mesh_data = obj_eval.to_mesh()
            if mesh_data is None:
                continue

            materials = mesh_data.materials
            scale     = 1.0

            bm_visible           = bmesh.new()
            bm_silhouette        = bmesh.new() if props.compute_silhouette else None
            bm_hidden            = bmesh.new() if props.include_hidden else None
            bm_silhouette_hidden = (
                bmesh.new()
                if (props.compute_silhouette and props.include_hidden) else None
            )
            bm_section           = bmesh.new() if camera_clipping else None

            vc_visible           = {}
            vc_silhouette        = {}
            vc_hidden            = {}
            vc_silhouette_hidden = {}
            vc_section           = {}

            bm_src = bmesh.new()
            bm_src.from_mesh(mesh_data)
            bm_src.transform(obj_eval.matrix_world)
            bm_src.normal_update()
            bm_src.edges.ensure_lookup_table()
            bm_src.faces.ensure_lookup_table()

            # ── Camera clipping: classify vertices and collect section lines ────
            section_lines = []
            if camera_clipping:
                v_dist = {v.index: (v.co - cam_location).dot(cam_fwd)
                          for v in bm_src.verts}
                for face in bm_src.faces:
                    vd = [v_dist[v.index] for v in face.verts]
                    for plane_val, outside_fn in (
                        (clip_end,   lambda d: d > clip_end),
                        (clip_start, lambda d: d < clip_start),
                    ):
                        n_out = sum(1 for d in vd if outside_fn(d))
                        if n_out == 0 or n_out == len(vd):
                            continue
                        clip_pts = []
                        for fedge in face.edges:
                            d0 = v_dist[fedge.verts[0].index]
                            d1 = v_dist[fedge.verts[1].index]
                            if outside_fn(d0) == outside_fn(d1):
                                continue
                            t = (plane_val - d0) / (d1 - d0)
                            clip_pts.append(
                                fedge.verts[0].co.lerp(fedge.verts[1].co, t).copy()
                            )
                        for k in range(0, len(clip_pts) - 1, 2):
                            section_lines.append((clip_pts[k], clip_pts[k + 1]))

            silhouette_boundary = []
            internal_boundary   = []
            boundary_edge_ids   = set()
            if props.remove_overlapping_boundary and props.flat_angle_threshold > 0.0:
                silhouette_boundary, internal_boundary, boundary_edge_ids = \
                    _remove_overlapping_boundary_edges(bm_src, props)

            emit_kwargs = dict(
                bm_visible           = bm_visible,
                vc_visible           = vc_visible,
                bm_silhouette        = bm_silhouette,
                vc_silhouette        = vc_silhouette,
                bm_hidden            = bm_hidden,
                vc_hidden            = vc_hidden,
                bm_silhouette_hidden = bm_silhouette_hidden,
                vc_silhouette_hidden = vc_silhouette_hidden,
                scale                = scale,
                aspect               = aspect,
            )

            def process_segment(p0, p1, ndc0, ndc1, edge_is_sil):
                N   = self.compute_segments(ndc0, ndc1)
                vis = [
                    self.sample_visible(
                        scene, depsgraph, cam_location,
                        p0.lerp(p1, (k + 0.5) / N), obj_eval,
                        ortho_direction=ortho_direction,
                    )[0]
                    for k in range(N)
                ]
                run_start = 0
                for k in range(1, N + 1):
                    if k == N or vis[k] != vis[run_start]:
                        self._emit_run(
                            ndc0.lerp(ndc1, run_start / N),
                            ndc0.lerp(ndc1, k / N),
                            vis[run_start],
                            edge_is_sil,
                            **emit_kwargs
                        )
                        run_start = k

            # ── Main edge loop ────────────────────────────────────────────────
            for edge in bm_src.edges:
                if boundary_edge_ids and edge.index in boundary_edge_ids:
                    continue

                edge_is_silhouette = False
                if props.compute_silhouette:
                    mid      = (edge.verts[0].co + edge.verts[1].co) * 0.5
                    view_dir = (mid - cam_location).normalized()
                    edge_is_silhouette = self.is_silhouette_edge(edge, view_dir)

                if not edge_is_silhouette and self.is_flat_edge(edge, mesh_data):
                    continue

                p0 = edge.verts[0].co.copy()
                p1 = edge.verts[1].co.copy()

                if camera_clipping:
                    d0 = v_dist[edge.verts[0].index]
                    d1 = v_dist[edge.verts[1].index]
                    p0, p1, d0, d1, visible = _clip_segment_to_planes(
                        p0, p1, d0, d1, clip_start, clip_end)
                    if not visible:
                        continue

                p0, p1, visible = self._clip_segment_lateral(p0, p1, vp_matrix)
                if not visible:
                    continue

                ndc0 = self.world_to_ndc(p0, view_matrix, proj_matrix)
                ndc1 = self.world_to_ndc(p1, view_matrix, proj_matrix)
                if ndc0 is None or ndc1 is None:
                    continue

                process_segment(p0, p1, ndc0, ndc1, edge_is_silhouette)

            # ── Inject silhouette boundary segments ───────────────────────────
            for p0, p1 in silhouette_boundary:
                if camera_clipping:
                    d0 = (p0 - cam_location).dot(cam_fwd)
                    d1 = (p1 - cam_location).dot(cam_fwd)
                    p0, p1, d0, d1, visible = _clip_segment_to_planes(
                        p0, p1, d0, d1, clip_start, clip_end)
                    if not visible:
                        continue
                p0, p1, visible = self._clip_segment_lateral(p0, p1, vp_matrix)
                if not visible:
                    continue
                ndc0 = self.world_to_ndc(p0, view_matrix, proj_matrix)
                ndc1 = self.world_to_ndc(p1, view_matrix, proj_matrix)
                if ndc0 is None or ndc1 is None:
                    continue
                process_segment(p0, p1, ndc0, ndc1, edge_is_sil=True)

            # ── Inject internal boundary segments ─────────────────────────────
            for p0, p1, face_a, face_b in internal_boundary:
                mat_different = face_a.material_index != face_b.material_index
                if not mat_different and len(materials) > 1:
                    ma = materials[face_a.material_index] \
                         if face_a.material_index < len(materials) else None
                    mb = materials[face_b.material_index] \
                         if face_b.material_index < len(materials) else None
                    mat_different = (ma is not mb)

                # Same acos domain guard as in is_flat_edge.
                cos_angle = max(-1.0, min(1.0, face_a.normal.dot(face_b.normal)))
                if mat_different or math.acos(cos_angle) >= props.flat_angle_threshold:
                    if camera_clipping:
                        d0 = (p0 - cam_location).dot(cam_fwd)
                        d1 = (p1 - cam_location).dot(cam_fwd)
                        p0, p1, d0, d1, visible = _clip_segment_to_planes(
                            p0, p1, d0, d1, clip_start, clip_end)
                        if not visible:
                            continue
                    p0, p1, visible = self._clip_segment_lateral(p0, p1, vp_matrix)
                    if not visible:
                        continue
                    ndc0 = self.world_to_ndc(p0, view_matrix, proj_matrix)
                    ndc1 = self.world_to_ndc(p1, view_matrix, proj_matrix)
                    if ndc0 is None or ndc1 is None:
                        continue
                    process_segment(p0, p1, ndc0, ndc1, edge_is_sil=False)

            # ── Inject section lines from clip planes ─────────────────────────
            # Section lines are always visible: the clip plane removes the
            # geometry that would otherwise occlude them, so no ray casting
            # is needed. They go directly into bm_visible and bm_section.
            for p0, p1 in section_lines:
                p0, p1, visible = self._clip_segment_lateral(p0, p1, vp_matrix)
                if not visible:
                    continue
                ndc0 = self.world_to_ndc(p0, view_matrix, proj_matrix)
                ndc1 = self.world_to_ndc(p1, view_matrix, proj_matrix)
                if ndc0 is None or ndc1 is None:
                    continue
                pt0 = self.ndc_to_3d(ndc0, scale, aspect)
                pt1 = self.ndc_to_3d(ndc1, scale, aspect)
                for bm, vc in ((bm_visible, vc_visible),
                               (bm_section, vc_section)):
                    if bm is None:
                        continue
                    k0 = (int(pt0.x * 1e5), int(pt0.y * 1e5))
                    k1 = (int(pt1.x * 1e5), int(pt1.y * 1e5))
                    if k0 not in vc:
                        vc[k0] = bm.verts.new(pt0)
                    if k1 not in vc:
                        vc[k1] = bm.verts.new(pt1)
                    v0, v1 = vc[k0], vc[k1]
                    if v0 is not v1:
                        try:
                            bm.edges.new((v0, v1))
                        except ValueError:
                            pass

            close_boundary_cuts(
                bm_visible, aspect,
                vp_matrix=vp_matrix,
                obj_eval=obj_eval,
            )

            bm_src.free()
            obj_eval.to_mesh_clear()

            has_visible           = bool(bm_visible.edges)
            has_silhouette        = bm_silhouette is not None and bool(bm_silhouette.edges)
            has_hidden            = bm_hidden is not None and bool(bm_hidden.edges)
            has_silhouette_hidden = bm_silhouette_hidden is not None and \
                                    bool(bm_silhouette_hidden.edges)
            has_section           = bm_section is not None and bool(bm_section.edges)

            if has_visible or has_silhouette or has_hidden or has_silhouette_hidden:
                if not has_visible:
                    bm_visible.free()
                    bm_visible = None
                if not has_silhouette:
                    if bm_silhouette: bm_silhouette.free()
                    bm_silhouette = None
                if not has_hidden:
                    if bm_hidden: bm_hidden.free()
                    bm_hidden = None
                if not has_silhouette_hidden:
                    if bm_silhouette_hidden: bm_silhouette_hidden.free()
                    bm_silhouette_hidden = None
                if not has_section:
                    if bm_section: bm_section.free()
                    bm_section = None
                results[obj.name] = ObjectProjection(
                    bm_visible           = bm_visible,
                    bm_silhouette        = bm_silhouette,
                    bm_hidden            = bm_hidden,
                    bm_silhouette_hidden = bm_silhouette_hidden,
                    bm_section           = bm_section,
                )
            else:
                bm_visible.free()
                if bm_silhouette:        bm_silhouette.free()
                if bm_hidden:            bm_hidden.free()
                if bm_silhouette_hidden: bm_silhouette_hidden.free()
                if bm_section:           bm_section.free()

        return results, aspect