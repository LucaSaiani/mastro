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
import traceback
import tempfile
import numpy as np
import bpy
from mathutils import Vector, Matrix

from .shadow_helpers import (_set_header, _clear_header, fmt_time,
                              create_shadow_cam_mesh, sun_direction,
                              clear_stash, unhide_empty_children)
from .proj_timer import _proj_state, _tick_projection
from .scene_graph_helpers import apply_depth_offset, convert_objects_to_grease_pencil
from ..get_preferences import get_prefs


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


def _all_view3d_shadings():
    shadings = []
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        shadings.append(space.shading)
    return shadings


def _save_state(scene, camera=None):
    r  = scene.render
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
        'clip_start':      camera.data.clip_start if camera else None,
        'clip_end':        camera.data.clip_end   if camera else None,
        'camera':          camera,
    }

    def _save_shading(ds):
        sh = {}
        for attr in _DISP_SHADING_ATTRS:
            if hasattr(ds, attr):
                val = getattr(ds, attr)
                sh[attr] = tuple(val) if hasattr(val, '__iter__') and \
                            not isinstance(val, str) else val
        return sh

    saved['display_shading'] = _save_shading(scene.display.shading)
    saved['viewport_shadings'] = [_save_shading(ds) for ds in _all_view3d_shadings()]
    return saved


def _apply_workbench_shading(ds):
    ds.type             = 'SOLID'
    ds.light            = 'FLAT'
    ds.color_type       = 'SINGLE'
    if hasattr(ds, 'single_color'):
        ds.single_color = (1.0, 1.0, 1.0)
    ds.show_shadows     = True
    if hasattr(ds, 'shadow_intensity'):
        ds.shadow_intensity = 1.0


def _restore_state(scene, saved):
    r  = scene.render
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
    if saved['clip_start'] is not None:
        s_camera = saved.get('camera')
        if s_camera:
            s_camera.data.clip_start = saved['clip_start']
            s_camera.data.clip_end   = saved['clip_end']

    def _restore_shading(ds, sh_saved):
        for attr, val in sh_saved.items():
            if hasattr(ds, attr):
                try:
                    setattr(ds, attr, val)
                except Exception:
                    pass

    _restore_shading(scene.display.shading, saved['display_shading'])
    for ds, sh_saved in zip(_all_view3d_shadings(), saved['viewport_shadings']):
        _restore_shading(ds, sh_saved)


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point  (called from OBJECT_OT_RunAll)
# ─────────────────────────────────────────────────────────────────────────────

def run_render_shadow(context, light, empty, camera, light_dir=None):
    scene     = context.scene
    cam_cl    = camera.data.mastro_projector_cl
    if light_dir is None:
        light_dir = sun_direction(light)

    render = scene.render
    aspect = ((render.resolution_x * render.pixel_aspect_x) /
              (render.resolution_y * render.pixel_aspect_y))

    n_sub_x   = cam_cl.grid_subdivisions
    n_sub_y   = max(1, round(n_sub_x / aspect))
    tile_px   = 256
    full_w    = n_sub_x * tile_px
    full_h    = max(16, round(full_w / aspect))

    cam_mat   = camera.matrix_world
    cam_loc   = cam_mat.translation.copy()
    cam_fwd   = -Vector(cam_mat.col[2][:3]).normalized()
    cam_right = Vector(cam_mat.col[0][:3]).normalized()
    cam_up    = Vector(cam_mat.col[1][:3]).normalized()
    on_cam    = cam_cl.place_on_camera_plane
    scale     = 1.0

    from_sun = -light_dir
    display_light_dir = Vector((from_sun.x, from_sun.z, -from_sun.y))

    saved = _save_state(scene, camera)

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

    _apply_workbench_shading(scene.display.shading)

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

            if not s.get('running'):
                self._finish(context, s, cancelled=True)
                return {'CANCELLED'}

            i, j = tiles[idx]
            _render_tile(s, i, j, context)
            s['tile_idx'] = idx + 1

            pct = int(100 * (idx + 1) / n_tiles)
            _set_header(f"Shadow [Render] — tile {idx+1}/{n_tiles} ({pct}%)  |  Cancel to stop")
            return {'RUNNING_MODAL'}

        if phase == 'finalize':
            try:
                _finalize(s)
            except Exception as exc:
                import sys
                print(f"[mastro] shadow finalize error: {exc}", file=sys.stderr)
                print(traceback.format_exc(), file=sys.stderr)
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
        _state.clear()


# ─────────────────────────────────────────────────────────────────────────────
# Tile rendering
# ─────────────────────────────────────────────────────────────────────────────

def _render_tile(s, i, j, context=None):
    scene   = s['scene']
    render  = scene.render
    nx, ny  = s['n_sub_x'], s['n_sub_y']

    render.border_min_x = i       / nx
    render.border_max_x = (i + 1) / nx
    render.border_min_y = j       / ny
    render.border_max_y = (j + 1) / ny

    path = os.path.join(s['tmp_dir'], f"projector_tile_{i}_{j}.png")
    render.filepath = path

    _apply_workbench_shading(scene.display.shading)

    override = {}
    if context is not None:
        override['window'] = context.window
        override['screen'] = context.screen
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                override['area'] = area
                for region in area.regions:
                    if region.type == 'WINDOW':
                        override['region'] = region
                        break
                break

    if override:
        with bpy.context.temp_override(**override):
            bpy.ops.render.render(write_still=True)
    else:
        bpy.ops.render.render(write_still=True)

    if not os.path.exists(path):
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

    fb       = max(1, short // bnd_res)
    sb       = shadow_mask[::fb, ::fb]
    sbh, sbw = sb.shape

    he_r, he_c = np.where(sb[:-1, :] != sb[1:, :])
    h_pts = np.column_stack([he_r + 0.5, he_c.astype(np.float64)])

    ve_r, ve_c = np.where(sb[:, :-1] != sb[:, 1:])
    v_pts = np.column_stack([ve_r.astype(np.float64), ve_c + 0.5])

    if len(h_pts) == 0 and len(v_pts) == 0:
        return None
    bnd_rc  = np.vstack([p for p in [h_pts, v_pts] if len(p)])
    bnd_ndc = np.column_stack([
        2.0 * bnd_rc[:, 1] / sbw - 1.0,
        2.0 * (1.0 - bnd_rc[:, 0] / sbh) - 1.0,
    ])

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

    parts = [bnd_ndc] + ([int_ndc] if int_ndc is not None else [])
    all_ndc = np.vstack(parts)
    return all_ndc.astype(np.float64) if len(all_ndc) >= 3 else None


def _finalize_trace(s):
    """Finalise shadow using bpy.ops.grease_pencil.trace_image() (Potrace).

    Pipeline
    --------
    1. Build a black-on-white RGBA image from the assembled render tiles.
    2. Save it to a temp PNG (trace_image poll requires IMA_SRC_FILE).
    3. Create a temporary Image Empty at the projector empty's world transform
       so that Potrace strokes land in the same local space as the Render
       method's mesh vertices.
    4. Call bpy.ops.grease_pencil.trace_image() — the GP object copies the
       Image Empty's loc/rot/scale and places strokes via pixel_to_object_transform.
    5. Parent the GP to the projector empty (MPI = Identity, local = 0) — same
       pattern as create_shadow_cam_mesh — so the shadow follows the empty.
    6. Assign "MaStro Shadow Colour GP" material, replacing any auto-created ones.

    Image Empty setup
    -----------------
    The empty is placed at the projector empty's loc/rot/scale.  This works for
    both on_cam=True (near-plane space) and on_cam=False (flat XY space) because
    in both cases the Render method also expresses vertex positions in the
    projector empty's local coordinate system.

    empty_image_offset = (-0.5, -0.5) centres the image at the empty origin:
    Blender's Image Empty places the bottom-left corner at (ima_ofs.x, ima_ofs.y)
    in local space and the image extends right (+X) and up (+Y).  The offset is
    normalised so ±0.5 always centres regardless of drawsize.
    """
    import tempfile as _tempfile, os as _os
    from mathutils import Matrix as _Matrix
    from .shadow_helpers import (_SHADOW_TAG, link_to_projection_collection)

    scene     = s['scene']
    camera    = s['camera']
    cam_cl    = s['cam_cl']
    on_cam    = s['on_cam']
    aspect    = s['aspect']
    empty     = s['empty']
    full_w    = s['full_w']
    full_h    = s['full_h']

    # Build shadow mask from the raw (un-flipped) render buffer.
    # Image Empty displays row 0 at the top, matching screen convention.
    px_on_trace = s['px_on']
    alpha       = px_on_trace[:, :, 3]
    brightness  = px_on_trace[:, :, :3].mean(axis=2)
    shadow_mask = (alpha > 0.5) & (brightness < 0.95)
    if not shadow_mask.any():
        return

    _set_header("Shadow [Trace] — Saving image…")

    # Black shadow on white background — Potrace traces dark regions.
    pixels = np.ones((full_h, full_w, 4), dtype=np.float32)
    pixels[shadow_mask, 0] = 0.0
    pixels[shadow_mask, 1] = 0.0
    pixels[shadow_mask, 2] = 0.0

    img_name = "_mastro_shadow_trace_tmp"
    if img_name in bpy.data.images:
        bpy.data.images.remove(bpy.data.images[img_name])
    img = bpy.data.images.new(img_name, width=full_w, height=full_h, alpha=True)
    img.use_fake_user = False
    img.pixels.foreach_set(pixels.ravel())
    img.update()

    # trace_image poll requires IMA_SRC_FILE.
    tmp_path = _os.path.join(_tempfile.gettempdir(), "mastro_shadow_trace.png")
    img.filepath_raw = tmp_path
    img.file_format  = 'PNG'
    img.save()
    img.source = 'FILE'

    _set_header("Shadow [Trace] — Tracing…")

    # Remove stale shadow object so the new one can take the name.
    shadow_name = camera.name + "_shadow"
    old = bpy.data.objects.get(shadow_name)
    if old:
        old_data = old.data
        old_type = old.type
        bpy.data.objects.remove(old, do_unlink=True)
        if old_data and old_data.users == 0:
            if old_type == 'MESH':
                bpy.data.meshes.remove(old_data)
            elif old_type == 'GREASEPENCIL':
                bpy.data.grease_pencils.remove(old_data)

    # Image Empty transform — mirrors the projector empty so strokes are in
    # the same local coordinate space used by the Render method's mesh vertices.
    # drawsize = 2*aspect covers the full camera frustum width in local units.
    # ima_ofs = (-0.5, -0.5) centres the image at the empty origin (normalised
    # offset: the Image Empty places its bottom-left at ima_ofs regardless of
    # drawsize or object scale).
    drawsize = 2.0 * aspect
    ima_ofs  = (-0.5, -0.5)

    gp_names_before = {o.name for o in bpy.context.scene.objects
                       if o.type == 'GREASEPENCIL'}

    if empty is not None:
        e_loc   = empty.matrix_world.translation.copy()
        e_rot   = empty.matrix_world.to_euler()
        e_scale = empty.matrix_world.to_scale()
    else:
        e_loc   = (0.0, 0.0, 0.0)
        e_rot   = (0.0, 0.0, 0.0)
        e_scale = (1.0, 1.0, 1.0)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.add(type='EMPTY', location=e_loc, rotation=e_rot)
    img_empty = bpy.context.active_object
    img_empty.name               = "_mastro_shadow_trace_empty"
    img_empty.empty_display_type = 'IMAGE'
    img_empty.data               = img
    img_empty.empty_display_size = drawsize
    img_empty.empty_image_offset = ima_ofs
    img_empty.scale              = e_scale

    bpy.ops.grease_pencil.trace_image(
        target    = 'NEW',
        threshold = cam_cl.trace_threshold,
        mode      = 'SINGLE',
    )

    gp_obj = next(
        (o for o in bpy.context.scene.objects
         if o.type == 'GREASEPENCIL' and o.name not in gp_names_before),
        None,
    )
    if gp_obj is None:
        try:
            if img_empty.name in bpy.data.objects:
                bpy.data.objects.remove(img_empty)
        except ReferenceError:
            pass
        bpy.data.images.remove(img)
        return

    gp_obj.name          = shadow_name
    gp_obj[_SHADOW_TAG]  = True
    gp_obj.hide_viewport = False
    link_to_projection_collection(gp_obj, scene)

    if empty is not None:
        gp_obj.parent                = empty
        gp_obj.matrix_parent_inverse = _Matrix.Identity(4)
        gp_obj.location              = (0.0, 0.0, 0.0)
        gp_obj.rotation_euler        = (0.0, 0.0, 0.0)
        gp_obj.scale                 = (1.0, 1.0, 1.0)

    from .scene_graph_helpers import _get_or_create_gp_material
    gp_mat = _get_or_create_gp_material("MaStro Shadow Colour GP", "MaStro Shadow Colour")
    if gp_mat:
        gp_obj.data.materials.clear()
        gp_obj.data.materials.append(gp_mat)

    prefs = get_prefs()
    apply_depth_offset(gp_obj, camera, -prefs.shadow_offset)

    try:
        if img_empty.name in bpy.data.objects:
            bpy.data.objects.remove(img_empty)
    except ReferenceError:
        pass
    bpy.data.images.remove(img)
    try:
        _os.remove(tmp_path)
    except OSError:
        pass


def _finalize(s):
    if s['cam_cl'].shadow_method == 'TRACE':
        _finalize_trace(s)
        return

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

    px_on = s['px_on'][::-1, :, :]

    alpha       = px_on[:, :, 3]
    brightness  = px_on[:, :, :3].mean(axis=2)

    _THRESHOLD  = 0.95
    shadow_mask = (alpha > 0.5) & (brightness < _THRESHOLD)

    if not shadow_mask.any():
        return

    _set_header("Shadow [Render] — Triangulating…")

    try:
        from scipy.ndimage import gaussian_filter
        from scipy.spatial import Delaunay
    except ImportError as exc:
        raise RuntimeError(f"scipy required: {exc}")

    smooth      = gaussian_filter(shadow_mask.astype(np.float32), sigma=1.0)
    shadow_mask = smooth > 0.5

    w, h    = full_w, full_h
    pts_ndc = _extract_contour_pts(shadow_mask, w, h, s)
    if pts_ndc is None or len(pts_ndc) < 3:
        return

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
        for simplex in tri.simplices:
            cx = pts_ndc[simplex, 0].mean()
            cy = pts_ndc[simplex, 1].mean()
            px_col = max(0, min(w - 1, int((cx + 1.0) / 2.0 * w)))
            px_row = max(0, min(h - 1, int((1.0 - (cy + 1.0) / 2.0) * h)))
            if shadow_mask[px_row, px_col]:
                final_faces.append(list(map(int, simplex)))
    except Exception as exc:
        raise RuntimeError(f"Delaunay error: {exc}")

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

    if obj:
        mat = bpy.data.materials.get("MaStro Shadow Colour")
        if mat:
            obj.data.materials.append(mat)
        prefs = get_prefs()
        if on_cam:
            # The shadow object is created with plane_matrix as matrix_parent_inverse,
            # so its local +Z = cam_fwd (away from camera).  Moving away = positive delta.
            world_offset = prefs.section_offset + prefs.shadow_offset
            obj.location.z += world_offset
            if camera.data.type == 'PERSP':
                d_new = near + world_offset
                if near > 1e-6 and d_new > 1e-6:
                    obj.scale = (d_new / near,) * 3
        else:
            apply_depth_offset(obj, camera, -prefs.shadow_offset)
        obj.hide_viewport = False
        if camera.data.mastro_projector_cl.convert_to_grease_pencil:
            convert_objects_to_grease_pencil([obj])
