"""
Shadow computation — Silhouette method.

For each sun-visible face (caster), projects it along the sun direction onto
every other sun-visible face (receiver) and clips the projection with
Sutherland-Hodgman to obtain cast-shadow polygons.  Self-shadows (ombre
proprie) are collected as dark faces that are camera-facing.  Both sets are
then projected to camera UV space and occluders (camera-facing geometry in
front of the shadow) are subtracted via the Greiner-Hormann difference.

Phases
------
init      — collect eval objects, build camera parameters, caster faces.
section_a — chunk over receiver faces: compute cast-shadow polygons (ombre portate).
section_b — add self-shadows; build camera-polygon UV cache and spatial grids.
section_c — chunk over shadow polygons: project to UV, subtract occluders, emit.
finalize  — write the final mesh and clean up.
"""

import time
import math
import bpy
from mathutils import Vector

from .shadow_helpers import (
    _set_header, _clear_header,
    create_shadow_cam_mesh, clear_stash, unhide_empty_children,
)
from .scene_graph_helpers import link_to_projection_collection, PROJECTION_COLLECTION
from .proj_timer import _tick_projection
from .projector import _Projector

_sil_state = {}

_EPS          = 1e-3
_CHUNK_A      = 20
_CHUNK_C_MIN  = 1
_CHUNK_C_MAX  = 50
_TICK_BUDGET  = 0.05
_CACHE_PREFIX = "_cast_shadows_"


def _light_key_for(cam_cl):
    """Return the cache key string for the given camera projector properties, or None."""
    if cam_cl.light_source:
        return cam_cl.light_source.name
    if not cam_cl.light_camera_lock:
        az_deg = round(math.degrees(cam_cl.virtual_azimuth))
        el_deg = round(math.degrees(cam_cl.virtual_elevation))
        return f"virtual_world_{az_deg}_{el_deg}"
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Timer entry point
# ─────────────────────────────────────────────────────────────────────────────

def _tick_sil_shadow():
    s = _sil_state
    if not s or not s.get("running"):
        _clear_header()
        return None

    phase = s.get("phase")
    if phase == "setup":
        _set_header("Shadow [Silhouette] — ready  |  Cancel to stop")
        s["phase"] = "init"
        return 0.0

    try:
        if   phase == "init":      _sil_phase_init(s)
        elif phase == "section_a": _sil_phase_section_a(s)
        elif phase == "section_b": _sil_phase_section_b(s)
        elif phase == "section_c": _sil_phase_section_c(s)
        elif phase == "finalize":  _sil_phase_finalize(s); return None
    except Exception as exc:
        import traceback
        print(f"[Shadow Silhouette] Error in phase {phase!r}: {exc}")
        traceback.print_exc()
        bpy.context.scene.mastro_projector_props.is_running = False
        _clear_header()
        _sil_state.clear()
        return None

    return 0.0 if s.get("running") else None


# ─────────────────────────────────────────────────────────────────────────────
# Tick phases
# ─────────────────────────────────────────────────────────────────────────────

def _sil_phase_init(s):
    _set_header("Shadow [Silhouette] — Preparing…")
    s["t0"]   = time.time()
    scene     = s["scene"]
    camera    = s["camera"]
    cam_cl    = camera.data.mastro_projector_cl
    sun_dir   = s["sun_dir"]

    depsgraph = bpy.context.evaluated_depsgraph_get()
    base_objs = [bpy.data.objects[n] for n in s["base_obj_names"]
                 if n in bpy.data.objects
                 and PROJECTION_COLLECTION not in
                     [c.name for c in bpy.data.objects[n].users_collection]]
    eval_objs = [o.evaluated_get(depsgraph) for o in base_objs]
    s["eval_objs"] = eval_objs
    s["ray_len"]   = s["extent"] + 2.0

    on_cam    = cam_cl.place_on_camera_plane
    cam_mat   = camera.matrix_world
    cam_loc   = cam_mat.translation.copy()
    cam_fwd   = -Vector(cam_mat.col[2][:3]).normalized()
    cam_right = Vector(cam_mat.col[0][:3]).normalized()
    cam_up    = Vector(cam_mat.col[1][:3]).normalized()
    s.update({"on_cam": on_cam, "cam_loc": cam_loc, "cam_fwd": cam_fwd,
               "cam_right": cam_right, "cam_up": cam_up})

    proj_params = None
    if not on_cam:
        render = scene.render
        proj_params = (
            camera.matrix_world.inverted(),
            camera.calc_matrix_camera(depsgraph,
                x=render.resolution_x, y=render.resolution_y,
                scale_x=render.pixel_aspect_x, scale_y=render.pixel_aspect_y),
            render.resolution_x * render.pixel_aspect_x /
            render.resolution_y / render.pixel_aspect_y,
        )
    s["proj_params"]           = proj_params
    s["cutter_detection"]      = cam_cl.cutter_detection
    s["intersecting_objects"]  = cam_cl.intersecting_objects

    if on_cam:
        u_max = math.tan(camera.data.angle_x / 2)
        v_max = math.tan(camera.data.angle_y / 2)
    else:
        aspect = proj_params[2]
        u_max  = aspect
        v_max  = 1.0
    s["frame_uv"] = (-u_max, u_max, -v_max, v_max)

    # Camera clipping params.
    cam_clipping = cam_cl.camera_clipping
    clip_start   = camera.data.clip_start if cam_clipping else None
    clip_end     = camera.data.clip_end   if cam_clipping else None
    s["clip_start"] = clip_start
    s["clip_end"]   = clip_end

    # Build VP matrix for frustum culling of receiver objects.
    render      = scene.render
    view_matrix = camera.matrix_world.inverted()
    proj_matrix = camera.calc_matrix_camera(
        depsgraph,
        x=render.resolution_x, y=render.resolution_y,
        scale_x=render.pixel_aspect_x, scale_y=render.pixel_aspect_y,
    )
    vp_matrix = proj_matrix @ view_matrix
    receiver_obj_names = {
        obj.name for obj in eval_objs
        if _Projector.bbox_in_frustum(obj, vp_matrix, view_matrix,
                                      camera_clipping=cam_clipping,
                                      clip_start=clip_start or 0.0,
                                      clip_end=clip_end or 1e9)
    }
    s["receiver_obj_names"] = receiver_obj_names
    light_key = _light_key_for(cam_cl)
    s["light_name"]   = light_key
    s["shadow_polys"] = []

    use_cache  = cam_cl.use_cast_shadow_cache
    cache_name = (_CACHE_PREFIX + light_key) if (light_key and use_cache) else None
    s["cache_name"] = cache_name

    caster_faces    = []
    receiver_mask   = []   # True if this face is from a camera-visible object
    for obj in eval_objs:
        me       = obj.data
        mw       = obj.matrix_world
        mwn      = mw.to_3x3().inverted().transposed()
        is_recv  = obj.name in receiver_obj_names
        for poly in me.polygons:
            if (obj.name, poly.index) not in s["sun_vis"]:
                continue
            verts = [mw @ me.vertices[vi].co for vi in poly.vertices]
            n_ws  = (mwn @ poly.normal).normalized()
            caster_faces.append((verts, n_ws))
            receiver_mask.append(is_recv)

    s["caster_faces"]  = caster_faces
    s["receiver_mask"] = receiver_mask
    s["fp_aabbs"], s["fp_grid"], s["fp_cell"] = \
        _build_shadow_footprint_index(caster_faces, sun_dir)
    s["r_cursor"] = 0
    s["phase"]    = "section_a"
    total = len(caster_faces)
    _set_header(f"Shadow [Silhouette] — Shadows 0/{total} (0%)  |  Cancel to stop")


def _sil_phase_section_a(s):
    caster_faces         = s["caster_faces"]
    receiver_mask        = s["receiver_mask"]
    total                = len(caster_faces)
    cursor               = s["r_cursor"]
    end                  = min(cursor + _CHUNK_A, total)
    sun_dir              = s["sun_dir"]
    fp_aabbs             = s["fp_aabbs"]
    fp_grid              = s["fp_grid"]
    fp_cell              = s["fp_cell"]
    shadow_polys         = s["shadow_polys"]
    intersecting_objects = s["intersecting_objects"]

    for r_idx in range(cursor, end):
        if not receiver_mask[r_idx]:
            continue
        recv_verts, recv_n = caster_faces[r_idx]
        denom = sun_dir.dot(recv_n)
        if abs(denom) < 1e-9:
            continue
        origin     = recv_verts[0]
        u_ax, v_ax = _plane_axes(recv_n)
        recv_2d    = _ensure_ccw(_to_2d(recv_verts, origin, u_ax, v_ax))

        all_segs = []
        for c_idx in _shadow_footprint_candidates(fp_aabbs, fp_grid, fp_cell, r_idx):
            cast_verts, _ = caster_faces[c_idx]
            if intersecting_objects:
                cast_verts = _clip_caster_to_halfspace(cast_verts, origin, recv_n)
                if len(cast_verts) < 3:
                    continue
            proj = []; skip = False
            for v in cast_verts:
                t = (origin - v).dot(recv_n) / denom
                if t < -_EPS:
                    skip = True; break
                proj.append(((v + sun_dir * t - origin).dot(u_ax),
                              (v + sun_dir * t - origin).dot(v_ax)))
            if skip or len(proj) < 3:
                continue
            nv = len(proj)
            for i in range(nv):
                a = proj[i]; b = proj[(i + 1) % nv]
                all_segs.append((Vector((a[0], a[1], 0.0)),
                                 Vector((b[0], b[1], 0.0))))

        if not all_segs:
            continue

        recv_convex = _poly_is_convex(recv_2d)
        recv_fan    = (None if recv_convex else
                       [_ensure_ccw([recv_2d[0], recv_2d[i], recv_2d[i + 1]])
                        for i in range(1, len(recv_2d) - 1)])

        for loop in _shadow_union_loops(all_segs):
            if len(loop) < 3:
                continue
            subj  = _ensure_ccw(loop)
            clips = [recv_2d] if recv_convex else recv_fan
            for clip in clips:
                inter = _sutherland_hodgman(subj, clip)
                if len(inter) >= 3:
                    shadow_polys.append(_to_3d(inter, origin, u_ax, v_ax))

    s["r_cursor"] = end
    pct = int(100 * end / total) if total else 100
    _set_header(f"Shadow [Silhouette] — Shadows {end}/{total} ({pct}%)  |  Cancel to stop")

    if end >= total:
        cache_name = s.get("cache_name")
        if cache_name and shadow_polys:
            old = bpy.data.objects.get(cache_name)
            if old:
                old_me = old.data
                bpy.data.objects.remove(old, do_unlink=True)
                if old_me and old_me.users == 0:
                    bpy.data.meshes.remove(old_me)
            verts_flat = [v for poly in shadow_polys for v in poly]
            faces_flat = []; base = 0
            for poly in shadow_polys:
                faces_flat.append(list(range(base, base + len(poly)))); base += len(poly)
            me_c = bpy.data.meshes.new(cache_name)
            me_c.from_pydata([v.to_tuple() for v in verts_flat], [], faces_flat)
            me_c.update()
            obj_c = bpy.data.objects.new(cache_name, me_c)
            obj_c.hide_render = obj_c.hide_viewport = True
            link_to_projection_collection(obj_c, s["scene"])
        s["phase"] = "section_b"


def _sil_phase_section_b(s):
    _set_header("Shadow [Silhouette] — Building camera data…")
    eval_objs    = s["eval_objs"]
    sun_vis      = s["sun_vis"]
    cam_loc      = s["cam_loc"]
    cam_fwd      = s["cam_fwd"]
    cam_right    = s["cam_right"]
    cam_up       = s["cam_up"]
    on_cam       = s["on_cam"]
    proj_params  = s["proj_params"]
    camera       = s["camera"]
    shadow_polys = s["shadow_polys"]
    clip_start   = s["clip_start"]
    clip_end     = s["clip_end"]

    # Ombre proprie: dark faces that face the camera.
    for obj in eval_objs:
        me  = obj.data
        mw  = obj.matrix_world
        mwn = mw.to_3x3().inverted().transposed()
        for poly in me.polygons:
            if (obj.name, poly.index) in sun_vis:
                continue
            n_ws = (mwn @ poly.normal).normalized()
            if (cam_loc - mw @ poly.center).dot(n_ws) <= 0:
                continue
            shadow_polys.append([mw @ me.vertices[vi].co for vi in poly.vertices])

    if not shadow_polys:
        s["final_verts"] = []
        s["final_faces"] = []
        s["phase"]       = "finalize"
        return

    cam_polys_3d = []
    for obj in eval_objs:
        me  = obj.data
        mw  = obj.matrix_world
        mwn = mw.to_3x3().inverted().transposed()
        for poly in me.polygons:
            n_ws = (mwn @ poly.normal).normalized()
            if (cam_loc - mw @ poly.center).dot(n_ws) <= 0:
                continue
            cam_polys_3d.append([mw @ me.vertices[vi].co for vi in poly.vertices])
    s["cam_polys_3d"] = cam_polys_3d

    def _vkey(v): return (round(v.x, 5), round(v.y, 5), round(v.z, 5))
    s["_vkey"] = _vkey

    vert_cache    = {}
    vert_to_polys = {}
    for p_idx, poly_verts in enumerate(cam_polys_3d):
        for v3 in poly_verts:
            key = _vkey(v3)
            if key not in vert_cache:
                uv, _ = _uv_project(v3, on_cam, cam_loc, cam_fwd, cam_right, cam_up,
                                     proj_params, camera, clip_start, clip_end)
                vert_cache[key] = (uv, (v3 - cam_loc).dot(cam_fwd))
            vert_to_polys.setdefault(key, set()).add(p_idx)
    s["vert_cache"]    = vert_cache
    s["vert_to_polys"] = vert_to_polys

    cam_poly_uvdep = []
    for poly_verts in cam_polys_3d:
        c_uv = []; c_dep = []; ok = True
        for v3 in poly_verts:
            cached = vert_cache.get(_vkey(v3))
            if cached is None or cached[0] is None:
                ok = False; break
            c_uv.append(cached[0]); c_dep.append(cached[1])
        cam_poly_uvdep.append((c_uv, c_dep) if ok and len(c_uv) >= 3 else None)
    s["cam_poly_uvdep"] = cam_poly_uvdep

    cutter_detection = s["cutter_detection"]
    cam_poly_aabb    = []
    if cutter_detection in ('AABB', 'BVH'):
        for uvdep in cam_poly_uvdep:
            if uvdep is None:
                cam_poly_aabb.append(None)
            else:
                us = [uv[0] for uv in uvdep[0]]
                vs = [uv[1] for uv in uvdep[0]]
                cam_poly_aabb.append((min(us), min(vs), max(us), max(vs)))
    s["cam_poly_aabb"] = cam_poly_aabb

    cam_uv_grid  = None; cam_uv_cell  = 1.0
    vert_uv_grid = None; vert_uv_cell = 1.0
    if cutter_detection == 'BVH':
        cam_uv_grid,  cam_uv_cell  = _build_uv_aabb_grid(cam_poly_aabb)
        vert_uv_grid, vert_uv_cell = _build_vert_uv_grid(vert_cache)
    s["cam_uv_grid"]   = cam_uv_grid;  s["cam_uv_cell"]  = cam_uv_cell
    s["vert_uv_grid"]  = vert_uv_grid; s["vert_uv_cell"] = vert_uv_cell

    s["final_verts"] = []
    s["final_faces"] = []
    s["s_cursor"]    = 0
    s["phase"]       = "section_c"
    total = len(shadow_polys)
    _set_header(f"Shadow [Silhouette] — Camera step 0/{total} (0%)  |  Cancel to stop")


def _sil_phase_section_c(s):
    shadow_polys     = s["shadow_polys"]
    total            = len(shadow_polys)
    cursor           = s["s_cursor"]
    chunk            = s.get("chunk_c", _CHUNK_C_MIN)
    end              = min(cursor + chunk, total)
    t0_c             = time.time()

    cam_loc          = s["cam_loc"]
    cam_fwd          = s["cam_fwd"]
    cam_right        = s["cam_right"]
    cam_up           = s["cam_up"]
    on_cam           = s["on_cam"]
    proj_params      = s["proj_params"]
    camera           = s["camera"]
    cam_polys_3d     = s["cam_polys_3d"]
    cam_poly_uvdep   = s["cam_poly_uvdep"]
    cam_poly_aabb    = s["cam_poly_aabb"]
    cam_uv_grid      = s["cam_uv_grid"]
    cam_uv_cell      = s["cam_uv_cell"]
    vert_cache       = s["vert_cache"]
    vert_to_polys    = s["vert_to_polys"]
    vert_uv_grid     = s["vert_uv_grid"]
    vert_uv_cell     = s["vert_uv_cell"]
    cutter_detection = s["cutter_detection"]
    final_verts      = s["final_verts"]
    final_faces      = s["final_faces"]
    frame_uv         = s["frame_uv"]
    clip_start       = s["clip_start"]
    clip_end         = s["clip_end"]

    def _uv_to_pt3d(uv):
        if on_cam:
            pd = camera.data.clip_start * 1.01
            return cam_loc + cam_fwd * pd + cam_right * (uv[0] * pd) + cam_up * (uv[1] * pd)
        return Vector((uv[0], uv[1], 0.0))

    for shadow_poly_3d in shadow_polys[cursor:end]:
        s_uv = []; s_dep = []; skip = False
        for v3 in shadow_poly_3d:
            uv, _ = _uv_project(v3, on_cam, cam_loc, cam_fwd, cam_right, cam_up,
                                 proj_params, camera, clip_start, clip_end)
            if uv is None:
                skip = True; break
            s_uv.append(uv)
            s_dep.append((v3 - cam_loc).dot(cam_fwd))
        if skip or len(s_uv) < 3:
            continue

        s_min_u = min(u for u, v in s_uv); s_max_u = max(u for u, v in s_uv)
        s_min_v = min(v for u, v in s_uv); s_max_v = max(v for u, v in s_uv)
        s_bb    = (s_min_u, s_min_v, s_max_u, s_max_v)

        cutter_indices = set()
        if cutter_detection == 'BVH' and vert_uv_grid is not None:
            check1_iter = ((k, vert_cache[k])
                           for k in _vert_grid_candidates(vert_uv_grid, vert_uv_cell, s_bb))
        else:
            check1_iter = vert_cache.items()
        for key, (uv, depth) in check1_iter:
            if uv is None:
                continue
            if cutter_detection == 'AABB':
                if uv[0] < s_min_u or uv[0] > s_max_u or \
                   uv[1] < s_min_v or uv[1] > s_max_v:
                    continue
            if not _pt_in_poly_winding(uv, s_uv):
                continue
            if depth > _depth_in_poly(s_uv, s_dep, uv) - 0.01:
                continue
            cutter_indices |= vert_to_polys[key] - cutter_indices

        ns = len(s_uv)
        if cutter_detection == 'BVH' and cam_uv_grid is not None:
            p_idx_iter = ((p_idx, cam_poly_uvdep[p_idx])
                          for p_idx in _uv_grid_candidates(cam_poly_aabb, cam_uv_grid,
                                                           cam_uv_cell, s_bb)
                          if p_idx not in cutter_indices
                          and cam_poly_uvdep[p_idx] is not None)
        else:
            p_idx_iter = ((p_idx, uvdep)
                          for p_idx, uvdep in enumerate(cam_poly_uvdep)
                          if p_idx not in cutter_indices and uvdep is not None)
        for p_idx, uvdep in p_idx_iter:
            if cutter_detection == 'AABB':
                bb = cam_poly_aabb[p_idx]
                if bb is None or bb[0] > s_max_u or bb[2] < s_min_u or \
                   bb[1] > s_max_v or bb[3] < s_min_v:
                    continue
            c_uv, c_dep = uvdep
            found = False
            for suv, sdep in zip(s_uv, s_dep):
                if not _pt_in_poly_winding(suv, c_uv):
                    continue
                if _depth_in_poly(c_uv, c_dep, suv) >= sdep - 0.01:
                    continue
                if any(abs(suv[0] - cv[0]) < 1e-4 and abs(suv[1] - cv[1]) < 1e-4
                       for cv in c_uv):
                    continue
                cutter_indices.add(p_idx); found = True; break
            if found:
                continue
            nc = len(c_uv)
            for i in range(ns):
                if found: break
                a = s_uv[i]; b = s_uv[(i + 1) % ns]
                da = s_dep[i]; db = s_dep[(i + 1) % ns]
                for j in range(nc):
                    ts = _seg_isect_ts(a, b, c_uv[j], c_uv[(j + 1) % nc])
                    if ts is None:
                        continue
                    t_par, s_par = ts
                    if c_dep[j] + s_par * (c_dep[(j + 1) % nc] - c_dep[j]) < da + t_par * (db - da):
                        cutter_indices.add(p_idx); found = True; break

        cutter_segs = []
        for p_idx in cutter_indices:
            c_uv2 = []; skip_c = False
            for v3 in cam_polys_3d[p_idx]:
                uv, _ = _uv_project(v3, on_cam, cam_loc, cam_fwd, cam_right, cam_up,
                                     proj_params, camera, clip_start, clip_end)
                if uv is None:
                    skip_c = True; break
                c_uv2.append(uv)
            if skip_c or len(c_uv2) < 3:
                continue
            nc2 = len(c_uv2)
            for i in range(nc2):
                a2, b2 = c_uv2[i], c_uv2[(i + 1) % nc2]
                cutter_segs.append((Vector((a2[0], a2[1], 0.0)),
                                    Vector((b2[0], b2[1], 0.0))))

        result_polys = [s_uv]
        if cutter_segs:
            for union_loop in _shadow_union_loops(cutter_segs):
                if len(union_loop) < 3:
                    continue
                new_result = []
                for poly in result_polys:
                    gh_out = _greiner_hormann_difference(poly, union_loop)
                    if len(gh_out) == 1 and len(gh_out[0]) == len(poly):
                        r0 = gh_out[0]; n = len(poly); is_same = False
                        for off in range(n):
                            if (abs(r0[off][0] - poly[0][0]) < 1e-6 and
                                    abs(r0[off][1] - poly[0][1]) < 1e-6):
                                if all(abs(r0[(off + i) % n][0] - poly[i][0]) < 1e-6 and
                                       abs(r0[(off + i) % n][1] - poly[i][1]) < 1e-6
                                       for i in range(n)):
                                    is_same = True; break
                        if not is_same:
                            for off in range(n):
                                if (abs(r0[off][0] - poly[0][0]) < 1e-6 and
                                        abs(r0[off][1] - poly[0][1]) < 1e-6):
                                    if all(abs(r0[(off - i) % n][0] - poly[i][0]) < 1e-6 and
                                           abs(r0[(off - i) % n][1] - poly[i][1]) < 1e-6
                                           for i in range(n)):
                                        is_same = True; break
                        if is_same:
                            cx = sum(p[0] for p in poly) / len(poly)
                            cy = sum(p[1] for p in poly) / len(poly)
                            inside = _pt_in_poly_winding((cx, cy), union_loop)
                            if not inside:
                                s_depth_c = _depth_in_poly(s_uv, s_dep, (cx, cy))
                                for pi in cutter_indices:
                                    uvdep_i = cam_poly_uvdep[pi]
                                    if uvdep_i is None:
                                        continue
                                    cu_i, cd_i = uvdep_i
                                    if not _pt_in_poly_winding((cx, cy), cu_i):
                                        continue
                                    if _depth_in_poly(cu_i, cd_i, (cx, cy)) < s_depth_c + 0.01:
                                        inside = True; break
                            if inside:
                                gh_out = []
                    new_result.extend(gh_out)
                result_polys = new_result

        fu_min, fu_max, fv_min, fv_max = frame_uv
        frame_clip = [(fu_min, fv_min), (fu_max, fv_min),
                      (fu_max, fv_max), (fu_min, fv_max)]

        for poly_uv in result_polys:
            if len(poly_uv) < 3:
                continue
            # Clip to camera frame before dedup/area check
            poly_uv = _sutherland_hodgman(poly_uv, frame_clip)
            if len(poly_uv) < 3:
                continue
            _DUP  = 1e-3
            clean = [poly_uv[0]]
            for p in poly_uv[1:]:
                if abs(p[0] - clean[-1][0]) > _DUP or abs(p[1] - clean[-1][1]) > _DUP:
                    clean.append(p)
            if abs(clean[0][0] - clean[-1][0]) < _DUP and abs(clean[0][1] - clean[-1][1]) < _DUP:
                clean = clean[:-1]
            if len(clean) < 3:
                continue
            area2 = 0.0
            for i in range(len(clean)):
                ax, ay = clean[i]; bx, by = clean[(i + 1) % len(clean)]
                area2 += ax * by - bx * ay
            if abs(area2) < 1e-6:
                continue
            pts3d = [_uv_to_pt3d(uv) for uv in clean]
            base  = len(final_verts)
            final_verts.extend(pts3d)
            final_faces.append(list(range(base, base + len(pts3d))))

    elapsed = time.time() - t0_c
    done    = end - cursor
    if done > 0:
        s["chunk_c"] = max(_CHUNK_C_MIN,
                           min(_CHUNK_C_MAX, int(done * _TICK_BUDGET / max(elapsed, 1e-9))))
    s["s_cursor"] = end
    pct = int(100 * end / total) if total else 100
    _set_header(f"Shadow [Silhouette] — Camera step {end}/{total} ({pct}%)  |  Cancel to stop")
    if end >= total:
        s["phase"] = "finalize"


def _sil_phase_finalize(s):
    _set_header("Shadow [Silhouette] — Finalizing…")
    _finalize_sil(s, s.get("final_verts", []), s.get("final_faces", []), s.get("t0", 0))


# ─────────────────────────────────────────────────────────────────────────────
# Finalise
# ─────────────────────────────────────────────────────────────────────────────




def _finalize_sil(s, pts_3d, faces, t0):
    cam_obj = s.get("camera")
    props   = bpy.context.scene.mastro_projector_props

    if pts_3d and cam_obj:
        empty_name = s.get("empty_name")
        empty      = bpy.data.objects.get(empty_name) if empty_name else None
        create_shadow_cam_mesh(pts_3d, cam_obj, bpy.context.scene, empty,
                               precomputed_faces=faces)

    props.is_running = False

    if not props.proj_is_running:
        empty = bpy.data.objects.get(s.get("empty_name", ""))
        if empty:
            clear_stash(empty)
            unhide_empty_children(empty)
    else:
        bpy.app.timers.register(_tick_projection, first_interval=0.0, persistent=False)

    _clear_header()
    _sil_state["running"] = False
    _sil_state.clear()


# ─────────────────────────────────────────────────────────────────────────────
# UV projection helper
# ─────────────────────────────────────────────────────────────────────────────

def _uv_project(hit_pos, on_cam, cam_loc, cam_fwd, cam_right, cam_up,
                proj_params, camera, clip_start=None, clip_end=None):
    depth = (hit_pos - cam_loc).dot(cam_fwd)
    if depth <= 0:
        return None, None
    if clip_start is not None and depth < clip_start:
        return None, None
    if clip_end is not None and depth > clip_end:
        return None, None

    if on_cam:
        u    = (hit_pos - cam_loc).dot(cam_right) / depth
        v    = (hit_pos - cam_loc).dot(cam_up)    / depth
        near = camera.data.clip_start
        pd   = near * 1.01
        pt3d = cam_loc + cam_fwd * pd + cam_right * (u * pd) + cam_up * (v * pd)
        return (u, v), pt3d
    else:
        view_m, proj_m, aspect = proj_params
        ndc = _Projector.world_to_ndc(hit_pos, view_m, proj_m)
        if ndc is None:
            return None, None
        xu = ndc.x * aspect
        yv = ndc.y
        return (xu, yv), Vector((xu, yv, 0.0))


# ─────────────────────────────────────────────────────────────────────────────
# Geometry helpers
# ─────────────────────────────────────────────────────────────────────────────

def _plane_axes(normal):
    arb = Vector((0, 0, 1)) if abs(normal.dot(Vector((0, 0, 1)))) < 0.99 \
          else Vector((1, 0, 0))
    u = normal.cross(arb).normalized()
    v = normal.cross(u).normalized()
    return u, v


def _to_2d(pts, origin, u_ax, v_ax):
    return [((p - origin).dot(u_ax), (p - origin).dot(v_ax)) for p in pts]


def _to_3d(pts_2d, origin, u_ax, v_ax):
    return [origin + u_ax * p[0] + v_ax * p[1] for p in pts_2d]


def _ensure_ccw(poly):
    area = sum(poly[i][0] * poly[(i + 1) % len(poly)][1] -
               poly[(i + 1) % len(poly)][0] * poly[i][1]
               for i in range(len(poly)))
    return list(reversed(poly)) if area < 0 else poly


def _poly_is_convex(poly):
    n = len(poly); sign = None
    for i in range(n):
        ax, ay = poly[i]; bx, by = poly[(i + 1) % n]; cx, cy = poly[(i + 2) % n]
        cross = (bx - ax) * (cy - by) - (by - ay) * (cx - bx)
        if abs(cross) < 1e-12:
            continue
        s = cross > 0
        if sign is None:
            sign = s
        elif sign != s:
            return False
    return True


def _pt_in_poly_winding(p, poly):
    px, py  = p; winding = 0; n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        if y1 <= py:
            if y2 > py and (x2 - x1) * (py - y1) - (px - x1) * (y2 - y1) > 0:
                winding += 1
        else:
            if y2 <= py and (x2 - x1) * (py - y1) - (px - x1) * (y2 - y1) < 0:
                winding -= 1
    return winding != 0


def _bary_interp(a, b, c, da, db, dc, p):
    ax, ay = a; bx, by = b; cx, cy = c; px, py = p
    v0x, v0y = bx - ax, by - ay; v1x, v1y = cx - ax, cy - ay; v2x, v2y = px - ax, py - ay
    d00 = v0x * v0x + v0y * v0y; d01 = v0x * v1x + v0y * v1y
    d11 = v1x * v1x + v1y * v1y; d20 = v2x * v0x + v2y * v0y; d21 = v2x * v1x + v2y * v1y
    denom = d00 * d11 - d01 * d01
    if abs(denom) < 1e-14:
        return (da + db + dc) / 3.0
    bv = (d11 * d20 - d01 * d21) / denom
    bw = (d00 * d21 - d01 * d20) / denom
    return (1.0 - bv - bw) * da + bv * db + bw * dc


def _depth_in_poly(poly_uv, poly_dep, p):
    for i in range(1, len(poly_uv) - 1):
        a, b, c = poly_uv[0], poly_uv[i], poly_uv[i + 1]
        def _c2(o, u, v):
            return (u[0] - o[0]) * (v[1] - o[1]) - (u[1] - o[1]) * (v[0] - o[0])
        d1 = _c2(a, b, p); d2 = _c2(b, c, p); d3 = _c2(c, a, p)
        if not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0)):
            return _bary_interp(a, b, c, poly_dep[0], poly_dep[i], poly_dep[i + 1], p)
    return sum(poly_dep) / len(poly_dep)


def _seg_isect_ts(a, b, c, d):
    ax, ay = a; bx, by = b; cx, cy = c; dx, dy = d
    denom = (ax - bx) * (cy - dy) - (ay - by) * (cx - dx)
    if abs(denom) < 1e-12:
        return None
    t = ((ax - cx) * (cy - dy) - (ay - cy) * (cx - dx)) / denom
    s = -((ax - bx) * (ay - cy) - (ay - by) * (ax - cx)) / denom
    if -1e-9 < t < 1 + 1e-9 and -1e-9 < s < 1 + 1e-9:
        return t, s
    return None


def _sutherland_hodgman(subject, clip):
    def _inside(p, a, b):
        return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) >= 0

    def _intersect(p1, p2, p3, p4):
        x1, y1 = p1; x2, y2 = p2; x3, y3 = p3; x4, y4 = p4
        d = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(d) < 1e-12:
            return p2
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / d
        return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))

    output = list(subject)
    n      = len(clip)
    for i in range(n):
        if not output:
            return []
        inp = output; output = []
        a = clip[i]; b = clip[(i + 1) % n]
        for j in range(len(inp)):
            cur = inp[j]; prv = inp[j - 1]
            if _inside(cur, a, b):
                if not _inside(prv, a, b):
                    output.append(_intersect(prv, cur, a, b))
                output.append(cur)
            elif _inside(prv, a, b):
                output.append(_intersect(prv, cur, a, b))
    return output


def _greiner_hormann_difference(subject, clip):
    if len(subject) < 3 or len(clip) < 3:
        return [list(subject)] if len(subject) >= 3 else []

    def _area2(p):
        n = len(p)
        return sum(p[i][0] * p[(i + 1) % n][1] - p[(i + 1) % n][0] * p[i][1]
                   for i in range(n))

    sp = list(subject) if _area2(subject) >= 0 else list(reversed(subject))
    cp = list(clip)    if _area2(clip) >= 0    else list(reversed(clip))

    class _V:
        __slots__ = ('x', 'y', 'a', 'isX', 'entry', 'seen', 'nbr', 'nx', 'pv')
        def __init__(s, x, y, a=0., isX=False):
            s.x = x; s.y = y; s.a = a; s.isX = isX
            s.entry = False; s.seen = False; s.nbr = None; s.nx = s.pv = None

    def _build(pts):
        vs = [_V(x, y) for x, y in pts]
        n  = len(vs)
        for i, v in enumerate(vs):
            v.nx = vs[(i + 1) % n]; v.pv = vs[(i - 1) % n]
        return vs[0]

    def _ins(start, nv):
        cur = start
        while cur.nx.isX and cur.nx.a < nv.a:
            cur = cur.nx
        nv.nx = cur.nx; nv.pv = cur
        cur.nx.pv = nv; cur.nx = nv

    def _sx(ax, ay, bx, by, cx, cy, dx, dy):
        d1x = bx - ax; d1y = by - ay; d2x = dx - cx; d2y = dy - cy
        den = d1x * d2y - d1y * d2x
        if abs(den) < 1e-12:
            return None
        t = ((cx - ax) * d2y - (cy - ay) * d2x) / den
        s = ((cx - ax) * d1y - (cy - ay) * d1x) / den
        if 1e-8 < t < 1 - 1e-8 and 1e-8 < s < 1 - 1e-8:
            return t, s, ax + t * d1x, ay + t * d1y
        return None

    def _inside(px, py, head):
        r = False; v = head
        while True:
            if (v.y > py) != (v.nx.y > py):
                xi = (v.nx.x - v.x) * (py - v.y) / (v.nx.y - v.y + 1e-12) + v.x
                if px < xi:
                    r = not r
            v = v.nx
            if v is head: break
        return r

    S = _build(sp); C = _build(cp)

    def _edges(head):
        e = []; v = head
        while True:
            e.append((v, v.nx)); v = v.nx
            if v is head: break
        return e

    s_edges = _edges(S); c_edges = _edges(C)
    has = False
    for sv, sv_nx in s_edges:
        for cv, cv_nx in c_edges:
            r = _sx(sv.x, sv.y, sv_nx.x, sv_nx.y, cv.x, cv.y, cv_nx.x, cv_nx.y)
            if r:
                t, u, ix, iy = r
                vs_ = _V(ix, iy, a=t, isX=True)
                vc_ = _V(ix, iy, a=u, isX=True)
                vs_.nbr = vc_; vc_.nbr = vs_
                _ins(sv, vs_); _ins(cv, vc_)
                has = True

    if not has:
        v = S
        while True:
            if _inside(v.x, v.y, C):
                return []
            v = v.nx
            if v is S: break
        return [sp]

    v = S
    while True:
        if v.isX:
            mx = (v.pv.x + v.x) * 0.5; my = (v.pv.y + v.y) * 0.5
            v.entry = not _inside(mx, my, C)
        v = v.nx
        if v is S: break

    results = []; sv = S
    while True:
        if sv.isX and not sv.entry and not sv.seen:
            res = []; start = sv; v = sv; on_s = True
            lim = 4 * (len(sp) + len(cp) + 10)
            while lim > 0:
                lim -= 1; v.seen = True; res.append((v.x, v.y))
                if on_s:
                    v = v.nx
                    if v is start: break
                    if v.isX and v.entry:
                        v = v.nbr; on_s = False
                else:
                    v = v.pv
                    if v is start: break
                    if v.isX and not v.nbr.entry:
                        v = v.nbr; on_s = True
                        if v is start: break
            if 3 <= len(res) <= len(sp) + len(cp) + 4:
                results.append(res)
        sv = sv.nx
        if sv is S: break

    return results if results else [sp]


def _shadow_union_loops(segs_2d):
    from .section_outline import (_build_planar_graph, _find_islands,
                                   _trace_outer_boundary)
    if not segs_2d:
        return []
    verts, adj = _build_planar_graph(segs_2d)
    connected  = {i for i in range(len(verts)) if adj.get(i)}
    if not connected:
        return []
    loops = []
    for island in _find_islands(adj, connected):
        bnd = _trace_outer_boundary(verts, adj, island)
        if len(bnd) >= 3:
            loops.append([(verts[i].x, verts[i].y) for i in bnd])
    return loops


# ─────────────────────────────────────────────────────────────────────────────
# Caster half-space clip
# ─────────────────────────────────────────────────────────────────────────────

def _clip_caster_to_halfspace(cast_verts, origin, recv_n):
    """Clip cast_verts to the half-space origin·recv_n >= 0 (above receiver plane).

    Returns the clipped polygon as a list of Vector, or [] if nothing remains.
    Uses Sutherland-Hodgman with a single half-space plane.
    """
    def signed_dist(v):
        return (v - origin).dot(recv_n)

    out = []
    n = len(cast_verts)
    for i in range(n):
        a = cast_verts[i]
        b = cast_verts[(i + 1) % n]
        da = signed_dist(a)
        db = signed_dist(b)
        if da >= 0:
            out.append(a)
        if (da >= 0) != (db >= 0):
            t = da / (da - db)
            out.append(a.lerp(b, t))
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Spatial index helpers
# ─────────────────────────────────────────────────────────────────────────────

def _build_shadow_footprint_index(caster_faces, sun_dir):
    arb  = Vector((0, 0, 1)) if abs(sun_dir.dot(Vector((0, 0, 1)))) < 0.99 \
           else Vector((1, 0, 0))
    u_ax = sun_dir.cross(arb).normalized()
    v_ax = sun_dir.cross(u_ax).normalized()

    aabbs = []
    for verts, _ in caster_faces:
        us = [v.dot(u_ax) for v in verts]
        vs = [v.dot(v_ax) for v in verts]
        aabbs.append((min(us), min(vs), max(us), max(vs)))

    sizes     = [(bb[2] - bb[0]) + (bb[3] - bb[1]) for bb in aabbs]
    cell_size = max(sum(sizes) / len(sizes) * 2.0, 1e-6) if sizes else 1.0
    grid      = {}
    for i, (mn_u, mn_v, mx_u, mx_v) in enumerate(aabbs):
        for cu in range(math.floor(mn_u / cell_size), math.floor(mx_u / cell_size) + 1):
            for cv in range(math.floor(mn_v / cell_size), math.floor(mx_v / cell_size) + 1):
                grid.setdefault((cu, cv), []).append(i)
    return aabbs, grid, cell_size


def _shadow_footprint_candidates(aabbs, grid, cell_size, r_idx):
    mn_u, mn_v, mx_u, mx_v = aabbs[r_idx]
    seen = set(); result = []
    for cu in range(math.floor(mn_u / cell_size), math.floor(mx_u / cell_size) + 1):
        for cv in range(math.floor(mn_v / cell_size), math.floor(mx_v / cell_size) + 1):
            for c_idx in grid.get((cu, cv), []):
                if c_idx == r_idx or c_idx in seen:
                    continue
                seen.add(c_idx)
                c = aabbs[c_idx]
                if c[0] <= mx_u and c[2] >= mn_u and c[1] <= mx_v and c[3] >= mn_v:
                    result.append(c_idx)
    return result


def _build_uv_aabb_grid(aabbs):
    sizes = [(bb[2] - bb[0]) + (bb[3] - bb[1]) for bb in aabbs if bb is not None]
    cell_size = max(sum(sizes) / len(sizes) * 2.0, 1e-6) if sizes else 1.0
    grid = {}
    for i, bb in enumerate(aabbs):
        if bb is None:
            continue
        mn_u, mn_v, mx_u, mx_v = bb
        for cu in range(math.floor(mn_u / cell_size), math.floor(mx_u / cell_size) + 1):
            for cv in range(math.floor(mn_v / cell_size), math.floor(mx_v / cell_size) + 1):
                grid.setdefault((cu, cv), []).append(i)
    return grid, cell_size


def _uv_grid_candidates(aabbs, grid, cell_size, query_bb):
    mn_u, mn_v, mx_u, mx_v = query_bb
    seen = set(); result = []
    for cu in range(math.floor(mn_u / cell_size), math.floor(mx_u / cell_size) + 1):
        for cv in range(math.floor(mn_v / cell_size), math.floor(mx_v / cell_size) + 1):
            for idx in grid.get((cu, cv), []):
                if idx in seen: continue
                seen.add(idx)
                bb = aabbs[idx]
                if bb and bb[0] <= mx_u and bb[2] >= mn_u and bb[1] <= mx_v and bb[3] >= mn_v:
                    result.append(idx)
    return result


def _build_vert_uv_grid(vert_cache):
    items = [(key, uv, dep) for key, (uv, dep) in vert_cache.items() if uv is not None]
    if not items:
        return {}, 1.0
    us = [uv[0] for _, uv, _ in items]; vs = [uv[1] for _, uv, _ in items]
    spread    = max(max(us) - min(us), max(vs) - min(vs), 1e-6)
    cell_size = max(spread / max(len(items) ** 0.5, 1.0), 1e-6)
    grid      = {}
    for key, uv, _ in items:
        cu = math.floor(uv[0] / cell_size); cv = math.floor(uv[1] / cell_size)
        grid.setdefault((cu, cv), []).append(key)
    return grid, cell_size


def _vert_grid_candidates(grid, cell_size, query_bb):
    mn_u, mn_v, mx_u, mx_v = query_bb
    seen = set(); result = []
    for cu in range(math.floor(mn_u / cell_size), math.floor(mx_u / cell_size) + 1):
        for cv in range(math.floor(mn_v / cell_size), math.floor(mx_v / cell_size) + 1):
            for key in grid.get((cu, cv), []):
                if key not in seen:
                    seen.add(key); result.append(key)
    return result
