"""
Shadow computation – Render-based method.

Uses bpy.ops.render.render() with the Workbench engine (flat lighting,
single white colour, shadow direction from the selected light).
The scene is rendered in tiles using border rendering for full DPI resolution.
With flat lighting all faces are equally lit, so dark pixels are cast shadows only.

Progress is reported via the header; cancel is supported between tiles.
A modal operator is used so that bpy.ops.render.render() has a valid window context.
"""

import os
import math
import time
import pathlib
import tempfile
import traceback
import numpy as np
import bpy
from mathutils import Vector, Matrix

from .shadow_helpers import (_set_header, _clear_header, fmt_time,
                              create_shadow_cam_mesh, sun_direction,
                              clear_stash, unhide_empty_children)
from .proj_timer import _proj_state, _tick_projection

_DBG = pathlib.Path(__file__).parent.parent / "shadow_render_debug.log"


def _dbg(*args):
    msg = " ".join(str(a) for a in args)
    with _DBG.open("a") as f:
        f.write(msg + "\n")


# ── Global state shared between run_render_shadow and the modal operator ──────
_state: dict = {}


# ─────────────────────────────────────────────────────────────────────────────
# Camera helpers
# ─────────────────────────────────────────────────────────────────────────────

def _camera_world_width(camera, scene):
    cam    = camera.data
    render = scene.render
    aspect = ((render.resolution_x * render.pixel_aspect_x) /
              (render.resolution_y * render.pixel_aspect_y))
    if cam.type == 'ORTHO':
        ow = cam.ortho_scale
        if cam.sensor_fit == 'VERTICAL' or \
           (cam.sensor_fit == 'AUTO' and aspect < 1.0):
            return ow * aspect
        return ow
    return 2.0


def _cam_half_height(camera, near, aspect):
    cam = camera.data
    if cam.type == 'PERSP':
        if cam.sensor_fit == 'VERTICAL' or \
           (cam.sensor_fit == 'AUTO' and aspect < 1.0):
            fov_y = cam.angle
        else:
            fov_y = 2.0 * math.atan(math.tan(cam.angle / 2.0) / aspect)
        return near * math.tan(fov_y / 2.0)
    else:
        ow = cam.ortho_scale
        if cam.sensor_fit == 'VERTICAL' or \
           (cam.sensor_fit == 'AUTO' and aspect < 1.0):
            return ow / 2.0
        return ow / (2.0 * aspect)


# ─────────────────────────────────────────────────────────────────────────────
# State save / restore  (scene.display.shading for real Workbench render)
# ─────────────────────────────────────────────────────────────────────────────

_DISP_SHADING_ATTRS = ('type', 'light', 'color_type', 'single_color',
                       'show_shadows', 'shadow_intensity', 'background_type',
                       'background_color')


def _save_state(scene):
    r  = scene.render
    ds = scene.display.shading
    vs = scene.view_settings
    saved = {
        'engine':          r.engine,
        'film_transparent':r.film_transparent,
        'use_border':      r.use_border,
        'use_crop':        getattr(r, 'use_crop_to_border', False),
        'border':          (r.border_min_x, r.border_max_x,
                            r.border_min_y, r.border_max_y),
        'res_x':           r.resolution_x,
        'res_y':           r.resolution_y,
        'res_pct':         r.resolution_percentage,
        'filepath':        r.filepath,
        'file_format':     r.image_settings.file_format,
        'light_direction': tuple(scene.display.light_direction),
        'shadow_shift':    scene.display.shadow_shift,
        'view_transform':  vs.view_transform,
        'exposure':        vs.exposure,
    }
    sh_saved = {}
    for attr in _DISP_SHADING_ATTRS:
        if hasattr(ds, attr):
            val = getattr(ds, attr)
            sh_saved[attr] = tuple(val) if hasattr(val, '__iter__') and \
                             not isinstance(val, str) else val
    saved['display_shading'] = sh_saved
    return saved


def _restore_state(scene, saved):
    r  = scene.render
    ds = scene.display.shading
    vs = scene.view_settings
    r.engine               = saved['engine']
    r.film_transparent     = saved['film_transparent']
    r.use_border           = saved['use_border']
    if hasattr(r, 'use_crop_to_border'):
        r.use_crop_to_border = saved['use_crop']
    r.border_min_x, r.border_max_x, \
    r.border_min_y, r.border_max_y = saved['border']
    r.resolution_x               = saved['res_x']
    r.resolution_y               = saved['res_y']
    r.resolution_percentage      = saved['res_pct']
    r.filepath                   = saved['filepath']
    r.image_settings.file_format = saved['file_format']
    scene.display.light_direction = saved['light_direction']
    scene.display.shadow_shift    = saved['shadow_shift']
    vs.view_transform             = saved['view_transform']
    vs.exposure                   = saved['exposure']
    for attr, val in saved['display_shading'].items():
        if hasattr(ds, attr):
            try:
                setattr(ds, attr, val)
            except Exception:
                pass


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point  (called from OBJECT_OT_RunAll)
# ─────────────────────────────────────────────────────────────────────────────

def run_render_shadow(context, light, empty, camera):
    _DBG.write_text("")
    _dbg("=== run_render_shadow START ===")

    scene     = context.scene
    cam_cl    = camera.data.mastro_projector_cl
    light_dir = sun_direction(light)
    _dbg(f"camera={camera.name}  light={light.name}")
    _dbg(f"light_dir={tuple(round(x,4) for x in light_dir)}")

    render = scene.render
    aspect = ((render.resolution_x * render.pixel_aspect_x) /
              (render.resolution_y * render.pixel_aspect_y))

    n_sub_x   = cam_cl.grid_subdivisions
    n_sub_y   = max(1, round(n_sub_x / aspect))
    tile_px   = 256
    full_w    = n_sub_x * tile_px
    full_h    = max(16, round(full_w / aspect))

    _dbg(f"n_sub={n_sub_x}x{n_sub_y} tile_px={tile_px} "
         f"full={full_w}x{full_h} aspect={aspect:.3f}")

    cam_mat   = camera.matrix_world
    cam_loc   = cam_mat.translation.copy()
    cam_fwd   = -Vector(cam_mat.col[2][:3]).normalized()
    cam_right = Vector(cam_mat.col[0][:3]).normalized()
    cam_up    = Vector(cam_mat.col[1][:3]).normalized()
    on_cam    = cam_cl.place_on_camera_plane
    scale     = 1.0

    from_sun = -light_dir
    display_light_dir = Vector((from_sun.x, from_sun.z, -from_sun.y))

    saved = _save_state(scene)

    render.engine               = 'BLENDER_WORKBENCH'
    render.film_transparent     = True
    render.resolution_x         = full_w
    render.resolution_y         = full_h
    render.resolution_percentage= 100
    render.image_settings.file_format = 'PNG'
    render.use_border           = True
    if hasattr(render, 'use_crop_to_border'):
        render.use_crop_to_border = True

    scene.display.light_direction = display_light_dir
    scene.display.shadow_shift    = 0.0
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.exposure       = 2.0

    ds = scene.display.shading
    ds.type             = 'SOLID'
    ds.light            = 'FLAT'
    ds.color_type       = 'SINGLE'
    ds.single_color     = (1.0, 1.0, 1.0)
    ds.show_shadows     = True
    ds.shadow_intensity = 1.0

    tiles   = [(i, j) for j in range(n_sub_y) for i in range(n_sub_x)]
    n_tiles = len(tiles)
    px_on   = np.zeros((full_h, full_w, 4), dtype=np.float32)
    tmp_dir = tempfile.gettempdir()

    _state.clear()
    _state.update({
        'running':      True,
        'phase':        'tiles_on',
        'tile_idx':     0,
        'tiles':        tiles,
        'n_tiles':      n_tiles,
        'n_sub_x':      n_sub_x,
        'n_sub_y':      n_sub_y,
        'tile_px':      tile_px,
        'full_w':       full_w,
        'full_h':       full_h,
        'px_on':        px_on,
        'tmp_dir':      tmp_dir,
        'scene':        scene,
        'camera':       camera,
        'cam_cl':       cam_cl,
        'cam_loc':      cam_loc,
        'cam_fwd':      cam_fwd,
        'cam_right':    cam_right,
        'cam_up':       cam_up,
        'on_cam':       on_cam,
        'scale':        scale,
        'aspect':       aspect,
        'empty':        empty,
        'saved':        saved,
        't0':           time.time(),
    })

    context.scene.mastro_projector_props.is_running = True
    bpy.ops.mastro.render_shadow_modal('INVOKE_DEFAULT')


# ─────────────────────────────────────────────────────────────────────────────
# Modal operator — one tile per TIMER event
# ─────────────────────────────────────────────────────────────────────────────

class MASTRO_OT_RenderShadowModal(bpy.types.Operator):
    bl_idname = "mastro.render_shadow_modal"
    bl_label  = "Render Shadow (modal)"

    _timer = None

    def modal(self, context, event):
        if event.type != 'TIMER':
            return {'PASS_THROUGH'}

        s = _state
        if not s.get('running'):
            self._finish(context, s, cancelled=True)
            return {'CANCELLED'}

        phase = s['phase']

        if phase == 'tiles_on':
            idx     = s['tile_idx']
            tiles   = s['tiles']
            n_tiles = s['n_tiles']

            if idx >= len(tiles):
                s['phase'] = 'finalize'
                return {'RUNNING_MODAL'}

            i, j = tiles[idx]
            _render_tile(s, i, j)
            s['tile_idx'] = idx + 1

            pct = int(100 * (idx + 1) / n_tiles)
            _set_header(f"Shadow [Render] — tile {idx+1}/{n_tiles} ({pct}%)  |  Cancel to stop")
            return {'RUNNING_MODAL'}

        if phase == 'finalize':
            try:
                _finalize(s)
            except Exception as exc:
                _dbg(f"FINALIZE ERROR: {exc}")
                _dbg(traceback.format_exc())
            self._finish(context, s, cancelled=False)
            return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self._timer = context.window_manager.event_timer_add(
            0.001, window=context.window)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None

    def _finish(self, context, s, cancelled):
        self.cancel(context)
        scene = s.get('scene')
        if scene and 'saved' in s:
            _restore_state(scene, s['saved'])

        props = bpy.context.scene.mastro_projector_props
        props.is_running = False

        # Start 2D projection timer now that render.resolution is restored.
        if not cancelled and _proj_state.get('running'):
            bpy.app.timers.register(_tick_projection, first_interval=0.0, persistent=False)

        empty = s.get('empty')
        if empty and not props.proj_is_running:
            clear_stash(empty)
            unhide_empty_children(empty)

        _clear_header()
        if cancelled:
            _dbg("run_render_shadow CANCELLED")
        _dbg("=== run_render_shadow END ===")
        _state.clear()


# ─────────────────────────────────────────────────────────────────────────────
# Tile rendering
# ─────────────────────────────────────────────────────────────────────────────

def _render_tile(s, i, j):
    scene   = s['scene']
    render  = scene.render
    nx, ny  = s['n_sub_x'], s['n_sub_y']
    tile_px = s['tile_px']

    render.border_min_x = i       / nx
    render.border_max_x = (i + 1) / nx
    render.border_min_y = j       / ny
    render.border_max_y = (j + 1) / ny

    path = os.path.join(s['tmp_dir'], f"projector_tile_{i}_{j}.png")
    render.filepath = path

    bpy.ops.render.render(write_still=True)

    if not os.path.exists(path):
        _dbg(f"  WARNING: tile render produced no file: {path}")
        return

    img = bpy.data.images.load(path, check_existing=False)
    iw, ih = img.size
    arr = np.array(img.pixels[:], dtype=np.float32).reshape(ih, iw, 4)
    bpy.data.images.remove(img)

    x0 = round(render.border_min_x * s['full_w'])
    y0 = round(render.border_min_y * s['full_h'])
    s['px_on'][y0:y0 + ih, x0:x0 + iw, :] = arr


# ─────────────────────────────────────────────────────────────────────────────
# Finalize — build shadow mesh from rendered pixels
# ─────────────────────────────────────────────────────────────────────────────


def _extract_contour_pts(shadow_mask, w, h, s):
    from scipy.ndimage import binary_erosion

    cam_cl  = s['cam_cl']
    bnd_res = cam_cl.render_boundary_res
    int_res = cam_cl.render_interior_res
    short   = min(h, w)

    # ── Boundary: midpoint degli edge dove il pixel cambia stato ─────────────
    # Questi punti sono subpixel-accurate e non hanno scaletta.
    fb       = max(1, short // bnd_res)
    sb       = shadow_mask[::fb, ::fb]
    sbh, sbw = sb.shape

    # Edge orizzontali: tra riga i e i+1
    he_r, he_c = np.where(sb[:-1, :] != sb[1:, :])
    h_pts = np.column_stack([he_r + 0.5, he_c.astype(np.float64)])

    # Edge verticali: tra colonna j e j+1
    ve_r, ve_c = np.where(sb[:, :-1] != sb[:, 1:])
    v_pts = np.column_stack([ve_r.astype(np.float64), ve_c + 0.5])

    if len(h_pts) == 0 and len(v_pts) == 0:
        return None
    bnd_rc  = np.vstack([p for p in [h_pts, v_pts] if len(p)])
    bnd_ndc = np.column_stack([
        2.0 * bnd_rc[:, 1] / sbw - 1.0,
        2.0 * (1.0 - bnd_rc[:, 0] / sbh) - 1.0,
    ])

    # ── Interior: coarse downsample ───────────────────────────────────────────
    fi       = max(1, short // int_res)
    si       = shadow_mask[::fi, ::fi]
    sih, siw = si.shape
    i_rows, i_cols = np.where(binary_erosion(si, iterations=2))
    _MAX_INT = 3000
    if len(i_rows) > _MAX_INT:
        step   = max(1, len(i_rows) // _MAX_INT)
        i_rows = i_rows[::step]
        i_cols = i_cols[::step]
    int_ndc = np.column_stack([
        2.0 * i_cols / siw - 1.0,
        2.0 * (1.0 - i_rows / sih) - 1.0,
    ]) if len(i_rows) else None

    _dbg(f"boundary pts={len(bnd_ndc)} (factor={fb})  interior pts={len(i_rows)} (factor={fi})")

    parts = [bnd_ndc] + ([int_ndc] if int_ndc is not None else [])
    all_ndc = np.vstack(parts)
    return all_ndc.astype(np.float64) if len(all_ndc) >= 3 else None


def _finalize(s):
    scene     = s['scene']
    camera    = s['camera']
    cam_cl    = s['cam_cl']
    cam_loc   = s['cam_loc']
    cam_fwd   = s['cam_fwd']
    cam_right = s['cam_right']
    cam_up    = s['cam_up']
    on_cam    = s['on_cam']
    scale     = s['scale']
    aspect    = s['aspect']
    empty     = s['empty']
    full_w    = s['full_w']
    full_h    = s['full_h']

    px_on = s['px_on'][::-1, :, :]   # flip to top-down

    alpha       = px_on[:, :, 3]
    brightness  = px_on[:, :, :3].mean(axis=2)

    _THRESHOLD  = 0.95
    shadow_mask = (alpha > 0.5) & (brightness < _THRESHOLD)
    n_shadow    = int(shadow_mask.sum())
    w, h        = full_w, full_h

    _dbg(f"brightness min={float(brightness.min()):.3f} max={float(brightness.max()):.3f}")
    _dbg(f"shadow pixels: {n_shadow}/{w*h} ({100*n_shadow/(w*h):.1f}%)")

    if not shadow_mask.any():
        _dbg("no shadow pixels — no mesh created")
        return

    _set_header("Shadow [Render] — Triangulating…")

    try:
        from scipy.ndimage import gaussian_filter
        from scipy.spatial import Delaunay
    except ImportError as exc:
        raise RuntimeError(f"scipy required: {exc}")

    # Smooth mask slightly to reduce pixel-staircase before contouring
    smooth      = gaussian_filter(shadow_mask.astype(np.float32), sigma=1.0)
    shadow_mask = smooth > 0.5

    pts_ndc     = _extract_contour_pts(shadow_mask, w, h, s)
    if pts_ndc is None or len(pts_ndc) < 3:
        _dbg("too few contour points")
        return
    _dbg(f"contour points after simplification: {len(pts_ndc)}")

    if on_cam:
        near   = camera.data.clip_start * 1.01
        half_h = _cam_half_height(camera, near, aspect)
        pc     = cam_loc + cam_fwd * near
        plane_matrix = Matrix([
            [cam_right.x * half_h * aspect, cam_up.x * half_h, cam_fwd.x, pc.x],
            [cam_right.y * half_h * aspect, cam_up.y * half_h, cam_fwd.y, pc.y],
            [cam_right.z * half_h * aspect, cam_up.z * half_h, cam_fwd.z, pc.z],
            [0,                             0,                  0,          1  ],
        ])
        local_verts = [Vector((float(pts_ndc[k, 0]), float(pts_ndc[k, 1]), 0.0))
                       for k in range(len(pts_ndc))]
    else:
        plane_matrix = None
        local_verts  = [Vector((float(pts_ndc[k, 0]) * scale * aspect,
                                float(pts_ndc[k, 1]) * scale, 0.0))
                        for k in range(len(pts_ndc))]

    final_faces = []
    try:
        tri  = Delaunay(pts_ndc)
        kept = 0
        for simplex in tri.simplices:
            cx = pts_ndc[simplex, 0].mean()
            cy = pts_ndc[simplex, 1].mean()
            px_col = max(0, min(w - 1, int((cx + 1.0) / 2.0 * w)))
            px_row = max(0, min(h - 1, int((1.0 - (cy + 1.0) / 2.0) * h)))
            if not shadow_mask[px_row, px_col]:
                continue
            final_faces.append(list(map(int, simplex)))
            kept += 1
        _dbg(f"triangles: {len(tri.simplices)} → {kept} kept")
    except Exception as exc:
        _dbg(f"Delaunay error: {exc}")
        _dbg(traceback.format_exc())

    _dbg(f"final_verts={len(local_verts)}  final_faces={len(final_faces)}")

    obj = create_shadow_cam_mesh(
        local_verts, camera, scene, empty,
        precomputed_faces=final_faces if final_faces else None,
        plane_matrix=plane_matrix,
    )

    if obj and final_faces:
        import bmesh as _bmesh
        bm = _bmesh.new()
        bm.from_mesh(obj.data)
        _bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(0.1),
                                  verts=bm.verts[:], edges=bm.edges[:])
        bm.to_mesh(obj.data)
        bm.free()
        obj.data.update()
        _dbg(f"dissolve → {len(obj.data.polygons)} polygons")

    elapsed = time.time() - s['t0']
    _dbg(f"mesh created: {obj.name if obj else 'None'}  ({fmt_time(elapsed)})")
