"""Timer-based 2D projection.

Phase 'setup': show header, give a cancellation window.
Phase 'run':   run the full projection synchronously and finalize.
"""
import bpy
from mathutils import Vector

from ..get_preferences import get_prefs
from .shadow_helpers import (_set_header, _clear_header, fmt_time,
                             clear_stash, unhide_empty_children,
                             is_shadow_helper)
from .projector import _Projector
from .build_global_bvh import _build_global_bvh
from .intersection_curve_merge_projected import _merge_intersections_into_results
from .merge_per_category import _merge_category_bmeshes
from .merge_by_distance import _merge_bmeshes_by_distance
from .snap_orphans import _snap_orphans_in_bmeshes
from .deduplicate_merged import _deduplicate_merged_edges
from .write_merged import _write_merged_object
from .section_outline import _compute_and_write_section_outline
from .scene_graph_helpers import apply_depth_offset, convert_objects_to_grease_pencil

_proj_state = {}


def _tick_projection():
    s = _proj_state
    if not s or not s.get("running"):
        _clear_header()
        return None

    if s["phase"] == "setup":
        _set_header("2D Projection — ready  |  Cancel to stop")
        s["phase"] = "run"
        return 0.0

    if s["phase"] == "run":
        _run_projection(s)
        return None

    return None


def _run_projection(s):
    import time
    t_start   = time.perf_counter()
    scene     = s["scene"]
    camera    = s["camera"]
    props     = camera.data.mastro_projector_cl
    empty_name = camera.name + get_prefs().projection_suffix
    empty      = bpy.data.objects.get(empty_name) or s.get("empty")
    depsgraph = bpy.context.evaluated_depsgraph_get()
    # Extend excluded set with any shadow helpers that may have been created
    # by a concurrent shadow run (they are not in excluded_names because that
    # set was computed before the shadow timer fired).
    shadow_names = {o.name for o in scene.objects if is_shadow_helper(o)}
    excluded = s["excluded_names"] | shadow_names

    _set_header("2D Projection [Running]…")

    try:
        clip_kw = {}
        if props.camera_clipping:
            clip_kw = {
                "cam_location": camera.matrix_world.translation.copy(),
                "cam_fwd":      (-camera.matrix_world.col[2].xyz).normalized(),
                "clip_start":   camera.data.clip_start,
                "clip_end":     camera.data.clip_end,
            }
        global_bvh, poly_to_obj = _build_global_bvh(scene, depsgraph, excluded, **clip_kw)
        projector = _Projector(props, global_bvh=global_bvh, poly_to_obj=poly_to_obj)

        results, _aspect = projector.build_projection_per_object(
            scene, depsgraph, camera, excluded
        )
        if not results:
            _finalize_proj(s, 0, 0, 0, 0, 0, time.perf_counter() - t_start)
            return

        if props.compute_intersections:
            vm, pm, asp = projector.get_camera_matrices(scene, camera, depsgraph)
            _merge_intersections_into_results(results, scene, depsgraph, projector, vm, pm, asp)

        merged_verts = 0
        if props.merge_by_distance:
            merged_verts = _merge_bmeshes_by_distance(results, props.merge_distance)

        snapped = 0
        if props.snap_orphans:
            snap_bms = [(d.bm_visible, {}) for d in results.values()] + \
                       [(d.bm_hidden,  {}) for d in results.values()]
            sync_bms = [(d.bm_silhouette,        {}) for d in results.values()] + \
                       [(d.bm_silhouette_hidden,  {}) for d in results.values()] + \
                       [(d.bm_section,            {}) for d in results.values()]
            max_d = None  # props.snap_max_distance if props.sampling_method == "ADAPTIVE" else None  — Adaptive disabled
            snapped = _snap_orphans_in_bmeshes(snap_bms, sync_bm_list=sync_bms,
                                               max_snap_distance=max_d)

        section_segs = []
        for data in results.values():
            if data.bm_section is None:
                continue
            for edge in data.bm_section.edges:
                a = Vector((edge.verts[0].co.x, edge.verts[0].co.y, 0.0))
                b = Vector((edge.verts[1].co.x, edge.verts[1].co.y, 0.0))
                if (b - a).length > 1e-7:
                    section_segs.append((a, b))

        merged = {}
        for src_name, data in results.items():
            bm_m, cat_v = _merge_category_bmeshes(data)
            if bm_m is not None:
                merged[src_name] = (bm_m, cat_v)

        dedup = _deduplicate_merged_edges(merged)

        bpy.ops.object.select_all(action="DESELECT")
        created = []
        for src_name, (bm_m, cat_v) in merged.items():
            obj = _write_merged_object(src_name, bm_m, cat_v, scene, props, parent=empty)
            if obj:
                obj.select_set(True)
                created.append(obj)
        for sec_obj in _compute_and_write_section_outline(
                section_segs, scene, camera.name, parent=empty):
            apply_depth_offset(sec_obj, camera, get_prefs().section_offset)
            sec_obj.select_set(True)
            created.append(sec_obj)

        n_edges = sum(len(o.data.edges) for o in created)

        if props.convert_to_grease_pencil and created:
            convert_objects_to_grease_pencil(created)

        _finalize_proj(s, len(created), n_edges, merged_verts, snapped, dedup,
                       time.perf_counter() - t_start)

    except Exception as exc:
        print(f"[Projector] Error during projection: {exc}")
        import traceback; traceback.print_exc()
        bpy.context.scene.mastro_projector_props.proj_is_running = False
        _clear_header()
        _proj_state.clear()


def _finalize_proj(s, n_objs, n_edges, merged_v, snapped, dedup, elapsed):
    camera = s.get("camera")
    empty  = None
    if camera:
        empty = bpy.data.objects.get(camera.name + get_prefs().projection_suffix) or s.get("empty")

    if empty:
        bpy.ops.object.select_all(action="DESELECT")
        empty.select_set(True)
        bpy.context.view_layer.objects.active = empty

    props = bpy.context.scene.mastro_projector_props
    props.proj_is_running = False
    props.last_proj_time  = elapsed
    props.last_proj_edges = n_edges

    if not props.is_running and empty:
        clear_stash(empty)
        unhide_empty_children(empty)

    # print(f"[Projector] {n_objs} obj(s) | {n_edges} edge(s) | "
    #       f"{merged_v} merged | {snapped} snapped | {dedup} dedup | "
    #       f"{fmt_time(elapsed)}")

    _clear_header()
    _proj_state.clear()
