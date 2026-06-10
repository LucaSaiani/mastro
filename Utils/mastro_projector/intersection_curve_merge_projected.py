from .intersection_curve_3D_computation import _bbox_overlap_world, _compute_intersection_segments_3d
from .tolerance_constants import _COORD_QUANTIZE

# =============================================================================
#  Intersection curve — merge projected segments into existing result bmeshes
# =============================================================================

def _merge_intersections_into_results(results, scene, depsgraph, projector,
                                      view_matrix, proj_matrix, aspect):
    props      = projector.props
    obj_names  = list(results.keys())
    scene_objs = {o.name: o for o in scene.objects if o.type == 'MESH'}

    # Intersection curves lie exactly on both surfaces simultaneously.
    # The standard ray_offset is too small here: a ray cast from the
    # intersection line would immediately re-hit one of the two surfaces,
    # falsely classifying every segment as occluded. A larger margin (100×)
    # pushes the ray origin safely past both surfaces before the occlusion
    # test begins.
    SURFACE_MARGIN = props.ray_offset * 100
    cam_location   = scene.camera.matrix_world.translation.copy()
    scale          = 1.0

    camera_clipping = props.camera_clipping
    if camera_clipping:
        cam_fwd    = (-scene.camera.matrix_world.col[2].xyz).normalized()
        clip_start = scene.camera.data.clip_start
        clip_end   = scene.camera.data.clip_end

    for i in range(len(obj_names)):
        for j in range(i + 1, len(obj_names)):
            name_a = obj_names[i]
            name_b = obj_names[j]

            if name_a not in scene_objs or name_b not in scene_objs:
                continue

            obj_a = scene_objs[name_a]
            obj_b = scene_objs[name_b]

            if not _bbox_overlap_world(obj_a, obj_b):
                continue

            raw = _compute_intersection_segments_3d(obj_a, obj_b, depsgraph)
            if not raw:
                continue
            segments_3d, _, _ = raw
            if not segments_3d:
                continue

            eval_a    = obj_a.evaluated_get(depsgraph)
            eval_b    = obj_b.evaluated_get(depsgraph)
            skip_pair = {eval_a, eval_b}

            def segment_visible(p0_w, p1_w):
                midpoint  = p0_w.lerp(p1_w, 0.5)
                direction = (cam_location - midpoint).normalized()
                origin    = midpoint + direction * SURFACE_MARGIN
                distance  = (cam_location - midpoint).length - SURFACE_MARGIN
                if distance <= 0.0:
                    return True
                if projector.global_bvh is not None:
                    loc, _n, poly_idx, _d = projector.global_bvh.ray_cast(
                        origin, direction, distance
                    )
                    if loc is None:
                        return True
                    hit_obj = (projector.poly_to_obj[poly_idx]
                               if poly_idx is not None and
                               poly_idx < len(projector.poly_to_obj) else None)
                    # skip_pair contains the two objects whose intersection we
                    # are testing. The ray origin sits on their shared boundary,
                    # so hits on either of these objects are self-hits and must
                    # be ignored; only hits on *other* objects count as occlusion.
                    if hit_obj not in skip_pair:
                        return False
                traveled = 0.0
                while traveled < distance:
                    hit, loc, _, _, hit_obj, _ = scene.ray_cast(
                        depsgraph, origin, direction, distance=distance - traveled
                    )
                    if not hit:
                        return True
                    if hit_obj not in skip_pair:
                        return False
                    step     = (loc - origin).length + props.ray_offset
                    origin   = origin + direction * step
                    traveled += step
                return True

            def project_seg(p0_w, p1_w):
                ndc0 = projector.world_to_ndc(p0_w, view_matrix, proj_matrix)
                ndc1 = projector.world_to_ndc(p1_w, view_matrix, proj_matrix)
                if ndc0 is None or ndc1 is None:
                    return None
                return (projector.ndc_to_3d(ndc0, scale, aspect),
                        projector.ndc_to_3d(ndc1, scale, aspect))

            def add_to_bm(bm, vc, pt0, pt1):
                def get_or_add(pt):
                    k = (int(pt.x * _COORD_QUANTIZE), int(pt.y * _COORD_QUANTIZE))
                    if k not in vc:
                        vc[k] = bm.verts.new(pt)
                    return vc[k]
                va = get_or_add(pt0)
                vb = get_or_add(pt1)
                if va is not vb:
                    try:
                        bm.edges.new((va, vb))
                    except ValueError:
                        pass

            for p0_w, p1_w, _idx_a, _idx_b in segments_3d:
                if camera_clipping:
                    d0 = (p0_w - cam_location).dot(cam_fwd)
                    d1 = (p1_w - cam_location).dot(cam_fwd)
                    if d0 < clip_start and d1 < clip_start:
                        continue
                    if d0 < clip_start:
                        p0_w = p0_w.lerp(p1_w, (clip_start - d0) / (d1 - d0))
                        d0   = clip_start
                    elif d1 < clip_start:
                        p1_w = p0_w.lerp(p1_w, (clip_start - d0) / (d1 - d0))
                        d1   = clip_start
                    if d0 > clip_end and d1 > clip_end:
                        continue
                    if d0 > clip_end:
                        p0_w = p0_w.lerp(p1_w, (clip_end - d0) / (d1 - d0))
                    elif d1 > clip_end:
                        p1_w = p0_w.lerp(p1_w, (clip_end - d0) / (d1 - d0))
                pts = project_seg(p0_w, p1_w)
                if pts is None:
                    continue
                pt0, pt1 = pts
                vis = segment_visible(p0_w, p1_w)
                for name in (name_a, name_b):
                    if name not in results:
                        continue
                    data = results[name]
                    if vis:
                        if data.bm_visible is not None:
                            add_to_bm(data.bm_visible, data.vc_vis, pt0, pt1)
                    elif props.include_hidden and data.bm_hidden is not None:
                        add_to_bm(data.bm_hidden, data.vc_hid, pt0, pt1)