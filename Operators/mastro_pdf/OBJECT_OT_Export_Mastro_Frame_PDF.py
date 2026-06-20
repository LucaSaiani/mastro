import bpy
import os
import re as _re
import subprocess
import tempfile
import mathutils
from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty
from bpy_extras.io_utils import ExportHelper


# ── Geometry helpers ──────────────────────────────────────────────────────────

def _frame_bounds(obj):
    """Return (min_x, min_y, max_x, max_y) in world space from a frame empty.

    The frame is a Cube Empty centred on its origin, sized by empty_display_size
    and scaled per-axis (Z scale is 0), so its local-space corners are at
    (+/-half, +/-half, 0) where half = empty_display_size."""
    world = obj.matrix_world
    half = obj.empty_display_size
    local_corners = [
        mathutils.Vector((-half, -half, 0.0)),
        mathutils.Vector((+half, -half, 0.0)),
        mathutils.Vector((+half, +half, 0.0)),
        mathutils.Vector((-half, +half, 0.0)),
    ]
    coords = [world @ c for c in local_corners]
    xs = [c.x for c in coords]
    ys = [c.y for c in coords]
    return min(xs), min(ys), max(xs), max(ys)


def _gp_world_bounds(obj, scene):
    """Return (min_x, min_y, max_x, max_y) from GP stroke points in world space.

    Uses the evaluated object so modifiers and transforms are applied.
    Iterates all layers and finds the active frame at or before frame_current.
    Falls back to obj.bound_box if no stroke points are found."""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj  = obj.evaluated_get(depsgraph)
    world     = eval_obj.matrix_world
    frame_num = scene.frame_current
    xs, ys = [], []
    for layer in eval_obj.data.layers:
        # Walk layer frames to find the last one at or before the current frame.
        best = None
        for f in layer.frames:
            if f.frame_number == frame_num:
                best = f
                break
            if f.frame_number < frame_num:
                best = f
        if best is None:
            continue
        try:
            for stroke in best.drawing.strokes:
                for pt in stroke.points:
                    co = world @ pt.position
                    xs.append(co.x)
                    ys.append(co.y)
        except Exception:
            pass
    if xs:
        return min(xs), min(ys), max(xs), max(ys)
    # Fallback: use the evaluated bounding box.
    wc = [world @ mathutils.Vector(c) for c in eval_obj.bound_box]
    return min(c.x for c in wc), min(c.y for c in wc), max(c.x for c in wc), max(c.y for c in wc)


def _bake_drawing_to_gp(obj, depsgraph):
    """Materialise a MaStro drawing's evaluated Grease Pencil geometry (produced
    by its GN modifier's "Curves to Grease Pencil" output) into a real, standalone
    GP object placed at the same world transform.

    bpy.ops.object.convert(target='GREASEPENCIL') does not pick up GN-generated GP
    geometry on a mesh object (it converts the base mesh topology instead and
    yields an empty result), so we read the evaluated geometry set directly via
    evaluated_geometry().grease_pencil and copy that datablock to a real one.

    The original mesh object is left untouched. Returns the temporary GP object,
    which the caller is responsible for removing after export, or None if the
    modifier produced no Grease Pencil geometry."""
    eval_obj = obj.evaluated_get(depsgraph)
    # `geo` must stay a live local: if evaluated_geometry() is chained directly
    # into `.grease_pencil` with no variable holding the GeometrySet, Python
    # garbage-collects it immediately and gp_eval becomes a dangling RNA pointer.
    geo = eval_obj.evaluated_geometry()
    gp_eval = geo.grease_pencil
    if gp_eval is None or len(gp_eval.layers) == 0:
        return None

    gp_data = gp_eval.copy()
    gp_obj = bpy.data.objects.new(obj.name + "__gp_tmp", gp_data)
    bpy.context.collection.objects.link(gp_obj)
    gp_obj.matrix_world = obj.matrix_world.copy()

    return gp_obj


def _objects_in_frame(min_x, min_y, max_x, max_y, scene):
    """Return GP objects whose stroke bounds overlap the given XY frame bounds.

    MaStro drawing objects (mesh + GN modifier outputting Grease Pencil geometry)
    are baked into temporary GP objects first; the originals stay untouched. The
    second return value lists those temporaries so the caller can remove them."""
    drawing_objs = [o for o in scene.objects
                    if o.type == 'MESH' and o.data.get("MaStro drawing")]
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    temp_objs = []
    for d in drawing_objs:
        baked = _bake_drawing_to_gp(d, depsgraph)
        if baked is not None:
            temp_objs.append(baked)

    result = []
    for obj in list(bpy.data.objects):
        if obj.type != 'GREASEPENCIL':
            continue
        ox1, oy1, ox2, oy2 = _gp_world_bounds(obj, scene)
        if ox2 >= min_x and ox1 <= max_x and oy2 >= min_y and oy1 <= max_y:
            result.append(obj)
    return result, temp_objs


# ── Invisible GP anchor for coordinate calibration ────────────────────────────

def _make_anchor(scene, corners):
    """Create and link an invisible GP object with one stroke through corners.

    The stroke has opacity=0 and radius=0 so it is exported but invisible.
    It is used as a known-coordinate landmark to measure the Haru→PDF point mapping."""
    anchor_data = bpy.data.grease_pencils.new("_mastro_pdf_anchor")
    layer   = anchor_data.layers.new("anchor")
    frame_d = layer.frames.new(scene.frame_current)
    drawing = frame_d.drawing
    drawing.add_strokes([len(corners)])
    stroke = drawing.strokes[0]
    stroke.cyclic = True
    for i, co in enumerate(corners):
        stroke.points[i].position = mathutils.Vector(co)
        stroke.points[i].opacity  = 0.0
        stroke.points[i].radius   = 0.0
    anchor_obj = bpy.data.objects.new("_mastro_pdf_anchor", anchor_data)
    scene.collection.objects.link(anchor_obj)
    return anchor_obj, anchor_data


# ── GP export helpers ─────────────────────────────────────────────────────────

def _find_view3d_context():
    """Return (area, region, space) for the first VIEW_3D area, or (None, None, None)."""
    for area in bpy.context.screen.areas:
        if area.type != 'VIEW_3D':
            continue
        space  = next((s for s in area.spaces  if s.type == 'VIEW_3D'), None)
        region = next((r for r in area.regions if r.type == 'WINDOW'),  None)
        if space and region:
            return area, region, space
    return None, None, None


def _gp_export_pdf(filepath, selected_object_type='SELECTED'):
    """Call grease_pencil_export_pdf, forcing camera view in the active VIEW_3D.

    The built-in exporter reads the camera projection; switching to CAMERA view
    first ensures the ortho camera we set up in `_setup_scene` is actually used."""
    area, region, space = _find_view3d_context()
    if area is None:
        bpy.ops.wm.grease_pencil_export_pdf(filepath=filepath,
                                             selected_object_type=selected_object_type)
        return
    prev_persp = space.region_3d.view_perspective
    space.region_3d.view_perspective = 'CAMERA'
    with bpy.context.temp_override(area=area, region=region, space_data=space):
        bpy.ops.wm.grease_pencil_export_pdf(filepath=filepath,
                                             selected_object_type=selected_object_type)
    space.region_3d.view_perspective = prev_persp


def _setup_scene(scene, cam_obj, frame_w_mm, frame_h_mm):
    """Override scene camera and render resolution; return previous values for restore."""
    prev = (scene.camera,
            scene.render.resolution_x, scene.render.resolution_y,
            scene.render.resolution_percentage,
            scene.render.pixel_aspect_x, scene.render.pixel_aspect_y)
    scene.camera = cam_obj
    scene.render.resolution_percentage = 100
    scene.render.pixel_aspect_x = 1.0
    scene.render.pixel_aspect_y = 1.0
    # Resolution in mm equals pixels when percentage=100 and aspect=1:1.
    scene.render.resolution_x = max(1, int(round(frame_w_mm)))
    scene.render.resolution_y = max(1, int(round(frame_h_mm)))
    return prev


def _restore_scene(scene, prev):
    (scene.camera,
     scene.render.resolution_x, scene.render.resolution_y,
     scene.render.resolution_percentage,
     scene.render.pixel_aspect_x, scene.render.pixel_aspect_y) = prev


# ── PDF stream parsing ────────────────────────────────────────────────────────

def _read_anchor_haru_bounds(filepath):
    """Parse the first content stream and return (min_x, min_y, max_x, max_y)
    of m/l path commands.

    In pass 1 only the anchor is exported, so these coordinates come entirely
    from the anchor stroke — giving us the Haru point values that correspond to
    the known world-space frame corners."""
    with open(filepath, 'rb') as f:
        data = f.read()
    parts = _re.split(rb'(stream\r?\n)(.*?)(\r?\nendstream)', data, flags=_re.DOTALL)
    if len(parts) < 5:
        return None
    body = parts[2]
    coord_re = _re.compile(rb'([-+]?[0-9]*\.?[0-9]+)\s+([-+]?[0-9]*\.?[0-9]+)\s+([mlML])')
    coords = [(float(x), float(y)) for x, y, _ in coord_re.findall(body)]
    if not coords:
        return None
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    return min(xs), min(ys), max(xs), max(ys)


def _read_max_haru_coords(filepath):
    """Return (max_x, max_y) of all m/l commands in the first content stream.

    In pass 2 the extended anchor covers the union bbox of frame + all GP objects,
    so its top-right corner is the stream maximum.  GP strokes are strictly inside,
    so the maximum always comes from the anchor."""
    with open(filepath, 'rb') as f:
        data = f.read()
    parts = _re.split(rb'(stream\r?\n)(.*?)(\r?\nendstream)', data, flags=_re.DOTALL)
    if len(parts) < 5:
        return None, None
    body = parts[2]
    coord_re = _re.compile(rb'([-+]?[0-9]*\.?[0-9]+)\s+([-+]?[0-9]*\.?[0-9]+)\s+([mlML])')
    coords = [(float(x), float(y)) for x, y, _ in coord_re.findall(body)]
    if not coords:
        return None, None
    return max(c[0] for c in coords), max(c[1] for c in coords)


# ── PDF xref / MediaBox rewriting ─────────────────────────────────────────────

def _rebuild_xref(data):
    """Rebuild the xref table and startxref pointer after binary patching.

    When we insert or modify PDF objects the byte offsets change, making the
    original xref invalid.  We scan for all `N 0 obj` markers, record their
    new offsets, then write a fresh xref + trailer at the end of the file."""
    obj_offsets = {}
    for m in _re.finditer(rb'\n(\d+)\s+0\s+obj\b', data):
        obj_offsets[int(m.group(1))] = m.start() + 1
    if not obj_offsets:
        return data
    trailer_m = _re.search(rb'trailer\s*(<<.*?>>)', data, _re.DOTALL)
    if not trailer_m:
        return data
    trailer_dict = trailer_m.group(1)
    xref_m = _re.search(rb'\nxref\b', data)
    body = data[:xref_m.start() + 1] if xref_m else data
    max_id = max(obj_offsets)
    out = bytearray(body)
    xref_offset = len(out)
    out += b'xref\n'
    out += f'0 {max_id + 1}\n'.encode()
    out += b'0000000000 65535 f \n'
    for i in range(1, max_id + 1):
        if i in obj_offsets:
            out += f'{obj_offsets[i]:010d} 00000 n \n'.encode()
        else:
            out += b'0000000000 65535 f \n'
    out += b'trailer\n'
    out += trailer_dict + b'\n'
    out += b'startxref\n'
    out += f'{xref_offset}\n'.encode()
    out += b'%%EOF\n'
    return bytes(out)


def _fix_mediabox(filepath, width_pt, height_pt, frame_x_haru, frame_y_haru, scale_x, scale_y):
    """Rewrite MediaBox to the frame size and wrap content streams with clip + scale.

    Haru writes GP strokes in its own internal coordinate system, which may be
    offset and scaled relative to the final PDF point grid.  This function:
      1. Replaces MediaBox and CropBox with the exact frame dimensions.
      2. Wraps every content stream in a `q … Q` save/restore block that:
         - Clips to the page rectangle (prevents GP strokes from bleeding outside).
         - Applies a cm transform to map Haru coordinates to PDF points."""
    tx = -frame_x_haru * scale_x
    ty = -frame_y_haru * scale_y

    with open(filepath, 'rb') as f:
        data = f.read()

    new_box = f'[0 0 {width_pt:.3f} {height_pt:.3f}]'.encode()
    data = _re.sub(rb'/MediaBox\s*\[[^\]]+\]', b'/MediaBox ' + new_box, data)
    data = _re.sub(rb'/CropBox\s*\[[^\]]+\]',  b'/CropBox '  + new_box, data)

    prefix = (
        f'q\n'
        f'0 0 {width_pt:.3f} {height_pt:.3f} re W n\n'  # clip rect
        f'{scale_x:.6f} 0 0 {scale_y:.6f} {tx:.3f} {ty:.3f} cm\n'  # scale + translate
    ).encode()
    suffix = b'\nQ'

    parts = _re.split(rb'(stream\r?\n)(.*?)(\r?\nendstream)', data, flags=_re.DOTALL)
    n_streams = (len(parts) - 1) // 4
    if n_streams > 0:
        out = bytearray()
        for i in range(n_streams):
            segment  = parts[i * 4]
            old_body = parts[i * 4 + 2]
            new_body = prefix + old_body + suffix
            segment  = _re.sub(rb'/Length\s+\d+', f'/Length {len(new_body)}'.encode(), segment)
            out += segment + parts[i * 4 + 1] + new_body + parts[i * 4 + 3]
        out += parts[n_streams * 4]
        data = bytes(out)

    data = _rebuild_xref(data)

    with open(filepath, 'wb') as f:
        f.write(data)


# ── Image processing ──────────────────────────────────────────────────────────

def _rotate_image_blender(img_path, rot_z, world_w, world_h, px_w, px_h, obj_name):
    """Return a JPEG + alpha mask for an image rotated by rot_z (radians, CCW in world space).

    Strategy:
      1. Compute the axis-aligned bounding box of the rotated image.
      2. Create a destination canvas of that bounding-box size, filled with white (alpha 0).
      3. Use inverse pixel mapping (numpy) to rotate the source pixels into the canvas.
         Pixels that fall outside the source image stay white and transparent.
      4. Save the RGB channels as JPEG via Blender (which Y-flips on save).
      5. Extract the alpha channel (top-down, matching Blender's JPEG flip) and
         compress it with zlib to produce a PDF /SMask grayscale stream.

    Notes on coordinate systems:
      - Blender pixels:   Y=0 at bottom (bottom-up, "bu").
      - Standard images:  Y=0 at top    (top-down,  "td").
      - Blender rot_z is CCW in world space (Y-up), which is CW in image space (Y-down).
        The inverse-mapping rotation therefore uses angle = -rot_z.
      - Blender saves JPEG with a Y-flip (reads bottom-up, writes top-down on disk).
        The alpha mask must therefore also be top-down so it stays aligned with the JPEG.

    Returns (jpeg_bytes, mask_bytes, bb_px_w, bb_px_h, bb_world_w, bb_world_h),
    or (None, None, 0, 0, 0, 0) on error."""
    import math, tempfile
    try:
        import numpy as np
    except ImportError:
        return None, None, 0, 0, 0, 0

    loaded  = False
    tmp_img = None
    try:
        # Reuse image if already loaded in Blender.
        src_img = next((i for i in bpy.data.images
                        if bpy.path.abspath(i.filepath) == img_path), None)
        if src_img is None:
            src_img = bpy.data.images.load(img_path)
            loaded = True
        src_img.update()

        # Read pixels and flip to top-down for rotation math.
        src_bu = np.array(src_img.pixels[:], dtype=np.float32).reshape(px_h, px_w, 4)
        src_td = src_bu[::-1]

        # Axis-aligned bounding box of the rotated image.
        c = abs(math.cos(rot_z));  s = abs(math.sin(rot_z))
        bb_world_w = world_w * c + world_h * s
        bb_world_h = world_w * s + world_h * c

        # Maintain the same pixel density as the original (pixels per BU, based on height).
        density = px_h / world_h
        bb_px_w = max(1, int(round(bb_world_w * density)))
        bb_px_h = max(1, int(round(bb_world_h * density)))

        # Canvas: white RGB, alpha=0 (transparent outside the source image).
        dst_td = np.zeros((bb_px_h, bb_px_w, 4), dtype=np.float32)
        dst_td[:, :, :3] = 1.0

        # Inverse mapping: for every destination pixel, find where it came from in the source.
        cos_a = math.cos(-rot_z);  sin_a = math.sin(-rot_z)
        cx_dst = bb_px_w / 2;  cy_dst = bb_px_h / 2
        cx_src = px_w    / 2;  cy_src = px_h    / 2

        y_d, x_d = np.mgrid[0:bb_px_h, 0:bb_px_w]
        dx = x_d - cx_dst;  dy = y_d - cy_dst

        # Rotate displacement back to source-image coordinates.
        x_s = cx_src + dx * cos_a + dy * sin_a
        y_s = cy_src - dx * sin_a + dy * cos_a

        valid = (x_s >= 0) & (x_s < px_w) & (y_s >= 0) & (y_s < px_h)
        xi = x_s.astype(int);  yi = y_s.astype(int)

        dst_td[valid] = src_td[yi[valid], xi[valid]]
        dst_td[valid, 3] = 1.0   # mark source pixels as fully opaque

        # Flip back to bottom-up for Blender's pixel buffer.
        dst_bu = dst_td[::-1]

        # Save RGB channels as JPEG via Blender.
        tmp_img = bpy.data.images.new("_mastro_rot_tmp", bb_px_w, bb_px_h, alpha=False)
        tmp_img.pixels = dst_bu.flatten().tolist()
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            tmp_path = f.name
        tmp_img.file_format  = 'JPEG'
        tmp_img.filepath_raw = tmp_path
        tmp_img.save()
        bpy.data.images.remove(tmp_img);  tmp_img = None
        with open(tmp_path, 'rb') as f:
            jpeg_bytes = f.read()
        os.unlink(tmp_path)

        # Build PDF /SMask: grayscale uint8 (DeviceGray), zlib compressed.
        # We use dst_td (top-down) because Blender Y-flips the JPEG on save,
        # so both image and mask are in top-down order as stored on disk.
        import zlib
        alpha_f32 = dst_td[:, :, 3]
        alpha_u8  = (alpha_f32 * 255).clip(0, 255).astype(np.uint8)
        mask_bytes = zlib.compress(alpha_u8.tobytes(), level=6)

        return jpeg_bytes, mask_bytes, bb_px_w, bb_px_h, bb_world_w, bb_world_h

    except Exception:
        return None, None, 0, 0, 0, 0
    finally:
        if tmp_img is not None:
            bpy.data.images.remove(tmp_img)
        if loaded and src_img is not None:
            bpy.data.images.remove(src_img)


def _crop_with_blender(img_path, crop_l, crop_u, crop_r, crop_b, obj_name):
    """Load an image via bpy.data.images, crop to the given pixel box, save as JPEG.

    Crop coordinates are top-down (crop_u = top row, crop_b = bottom row exclusive),
    matching standard image conventions.  Blender's pixel buffer is bottom-up
    (Y=0 at bottom), so we convert before reading rows.

    Returns (jpeg_bytes, cropped_width, cropped_height) or (None, 0, 0) on error."""
    import tempfile
    crop_img = None
    loaded   = False
    src_img  = None
    try:
        src_img = next((i for i in bpy.data.images
                        if bpy.path.abspath(i.filepath) == img_path), None)
        if src_img is None:
            src_img = bpy.data.images.load(img_path)
            loaded = True

        src_img.update()
        px_w, px_h = src_img.size

        # Convert top-down crop bounds to Blender's bottom-up row indices.
        bl_y0 = px_h - crop_b   # first Blender row (= bottom of visible strip)
        bl_y1 = px_h - crop_u   # last  Blender row (exclusive, = top of visible strip)
        new_w = crop_r - crop_l
        new_h = crop_b - crop_u

        src = src_img.pixels[:]   # flat RGBA float tuple, bottom-up
        dst = []
        for bl_y in range(bl_y0, bl_y1):
            row_start = (bl_y * px_w + crop_l) * 4
            dst.extend(src[row_start: row_start + new_w * 4])

        crop_img = bpy.data.images.new("_mastro_crop_tmp", new_w, new_h, alpha=False)
        crop_img.pixels = dst

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            tmp_path = f.name
        crop_img.file_format  = 'JPEG'
        crop_img.filepath_raw = tmp_path
        crop_img.save()

        with open(tmp_path, 'rb') as f:
            data = f.read()
        os.unlink(tmp_path)
        return data, new_w, new_h

    except Exception:
        return None, 0, 0
    finally:
        if crop_img is not None:
            bpy.data.images.remove(crop_img)
        if loaded and src_img is not None:
            bpy.data.images.remove(src_img)


# ── Image entry builder ───────────────────────────────────────────────────────

def _build_image_entries(empties, min_x, min_y, frame_w, frame_h, width_pt, height_pt):
    """Convert a list of Image Empty objects into PDF image placement records.

    Each record is a dict with:
      img_bytes  – JPEG bytes for the image XObject
      mask_bytes – zlib-compressed grayscale alpha for /SMask (None if not needed)
      px_w/px_h  – pixel dimensions of the image (after crop/rotation)
      cx/cy      – bottom-left corner of the image in PDF points (origin = page bottom-left)
      pw/ph      – width/height of the image rectangle in PDF points
      rot_z      – rotation (always 0.0 here; rotation is baked into the image)

    Coordinate notes:
      - empty_display_size in Blender controls the HEIGHT of the image (not width).
        Width = height / pixel_aspect_ratio.
      - empty_image_offset (ox, oy): ox is in units of world_w, oy in units of world_h.
        Default (-0.5, -0.5) centres the image on the object origin.
      - For non-rotated images the visible portion is clipped to the frame rectangle
        and cropped in pixel space (no PDF clip path needed).
      - For rotated images we bake rotation + alpha mask in `_rotate_image_blender`
        and place the bounding-box image directly (no crop; it is assumed to be
        fully inside the frame)."""
    import math
    max_x = min_x + frame_w
    max_y = min_y + frame_h
    result = []
    for obj in empties:
        w_mat      = obj.matrix_world
        rot_z      = w_mat.to_euler().z
        px_w, px_h = obj.data.size
        if px_w == 0 or px_h == 0:
            continue

        pos    = w_mat.translation
        sx     = w_mat.to_scale().x
        sy     = w_mat.to_scale().y
        aspect = px_h / px_w   # height / width

        # empty_display_size = HEIGHT of the displayed image.
        world_h = obj.empty_display_size * abs(sy)
        world_w = world_h / aspect

        # empty_image_offset: moves the image so that offset=(−0.5,−0.5) centres it.
        ox, oy   = tuple(getattr(obj, 'empty_image_offset', (0.0, 0.0)))
        img_bl_x = pos.x + ox * world_w   # world X of the image bottom-left corner
        img_bl_y = pos.y + oy * world_h   # world Y of the image bottom-left corner

        img_path = bpy.path.abspath(obj.data.filepath)
        if not os.path.isfile(img_path):
            continue
        ext = os.path.splitext(img_path)[1].lower()

        # ── Rotated image ──────────────────────────────────────────────────
        if rot_z != 0.0:
            # Bake rotation into a bounding-box JPEG + alpha mask.
            img_bytes, mask_bytes, px_w, px_h, bb_world_w, bb_world_h = \
                _rotate_image_blender(img_path, rot_z, world_w, world_h, px_w, px_h, obj.name)
            if img_bytes is None:
                continue
            # Centre of the original image in world space.
            img_cx = img_bl_x + world_w / 2
            img_cy = img_bl_y + world_h / 2
            # Bottom-left of the bounding-box image (centred on the same point).
            cx = (img_cx - bb_world_w / 2 - min_x) / frame_w * width_pt
            cy = (img_cy - bb_world_h / 2 - min_y) / frame_h * height_pt
            pw = bb_world_w / frame_w * width_pt
            ph = bb_world_h / frame_h * height_pt
            result.append({'img_bytes': img_bytes, 'mask_bytes': mask_bytes,
                           'px_w': px_w, 'px_h': px_h,
                           'cx': cx, 'cy': cy, 'pw': pw, 'ph': ph, 'rot_z': 0.0})
            continue

        # ── Non-rotated image: clip to frame, then crop pixels ─────────────
        vis_x1 = max(img_bl_x, min_x);  vis_x2 = min(img_bl_x + world_w, max_x)
        vis_y1 = max(img_bl_y, min_y);  vis_y2 = min(img_bl_y + world_h, max_y)
        if vis_x2 <= vis_x1 or vis_y2 <= vis_y1:
            continue   # completely outside the frame

        # Fractional positions within the image that are visible.
        fx1 = (vis_x1 - img_bl_x) / world_w;  fx2 = (vis_x2 - img_bl_x) / world_w
        fy1 = (vis_y1 - img_bl_y) / world_h;  fy2 = (vis_y2 - img_bl_y) / world_h

        # Convert to top-down pixel crop coordinates (Blender Y=0 is bottom).
        crop_l = int(fx1 * px_w);  crop_r = int(fx2 * px_w)
        crop_u = int((1.0 - fy2) * px_h);  crop_b = int((1.0 - fy1) * px_h)
        crop_l = max(0, crop_l);  crop_r = min(px_w, crop_r)
        crop_u = max(0, crop_u);  crop_b = min(px_h, crop_b)
        if crop_r <= crop_l or crop_b <= crop_u:
            continue

        # PDF coordinates of the visible rectangle (bottom-left corner).
        cx = (vis_x1 - min_x) / frame_w * width_pt
        cy = (vis_y1 - min_y) / frame_h * height_pt
        pw = (vis_x2 - vis_x1) / frame_w * width_pt
        ph = (vis_y2 - vis_y1) / frame_h * height_pt

        needs_crop = (crop_l > 0 or crop_u > 0 or crop_r < px_w or crop_b < px_h)

        if needs_crop or ext not in ('.jpg', '.jpeg'):
            img_bytes, px_w, px_h = _crop_with_blender(
                img_path, crop_l, crop_u, crop_r, crop_b, obj.name)
            if img_bytes is None:
                continue
        else:
            with open(img_path, 'rb') as fi:
                img_bytes = fi.read()

        result.append({'img_bytes': img_bytes, 'mask_bytes': None,
                       'px_w': px_w, 'px_h': px_h,
                       'cx': cx, 'cy': cy, 'pw': pw, 'ph': ph, 'rot_z': 0.0})
    return result


# ── PDF image embedding ───────────────────────────────────────────────────────

def _make_image_draw(entries, start_num, width_pt, height_pt):
    """Build PDF object bytes and a draw stream for a list of image entries.

    For each entry:
      - If mask_bytes is present, prepend a /SMask XObject (DeviceGray, FlateDecode).
      - Emit an Image XObject (DeviceRGB, DCTDecode) with optional /SMask reference.
      - Append a `cm … Do` command to the draw stream that places the image at
        the correct position and size in PDF points.

    The PDF `cm` matrix maps the unit square [0,1]×[0,1] to the image rectangle.
    For a non-rotated image of size (pw, ph) with bottom-left at (cx, cy):
        [pw  0  0  ph  cx  cy]
    (rot_z is always 0 here; rotation is already baked into the image pixels.)

    Returns (new_obj_bytes, xobj_refs, draw_stream_bytes, next_num)
    where next_num is the next available PDF object number after all objects created here."""
    import math
    new_obj_bytes = b''
    xobj_refs     = []
    # Open with a clip rect so the images respect the page boundary.
    draw = (f'q\n0 0 {width_pt:.3f} {height_pt:.3f} re W n\n').encode()
    next_num = start_num
    for e in entries:
        num  = next_num
        name = f'Im{num}'
        next_num += 1
        xobj_refs.append(f'/{name} {num} 0 R'.encode())

        # Optional alpha mask (needed when the image has transparent corners, e.g. rotated).
        mask_bytes = e.get('mask_bytes')
        smask_ref  = ''
        if mask_bytes:
            mnum = next_num;  next_num += 1
            smask_ref = f' /SMask {mnum} 0 R'
            mask_hdr = (
                f'{mnum} 0 obj\n'
                f'<< /Type /XObject /Subtype /Image'
                f' /Width {e["px_w"]} /Height {e["px_h"]}'
                f' /ColorSpace /DeviceGray /BitsPerComponent 8'
                f' /Filter /FlateDecode /Length {len(mask_bytes)} >>\n'
                f'stream\n'
            ).encode()
            new_obj_bytes += mask_hdr + mask_bytes + b'\nendstream\nendobj\n'

        # RGB image XObject (JPEG / DCTDecode).
        hdr = (
            f'{num} 0 obj\n'
            f'<< /Type /XObject /Subtype /Image'
            f' /Width {e["px_w"]} /Height {e["px_h"]}'
            f' /ColorSpace /DeviceRGB /BitsPerComponent 8'
            f' /Filter /DCTDecode /Length {len(e["img_bytes"])}'
            f'{smask_ref} >>\n'
            f'stream\n'
        ).encode()
        new_obj_bytes += hdr + e['img_bytes'] + b'\nendstream\nendobj\n'

        c  = math.cos(e['rot_z']); s  = math.sin(e['rot_z'])
        pw = e['pw'];              ph = e['ph']
        cx = e['cx'];              cy = e['cy']
        a  =  c * pw; b_ =  s * pw
        cc = -s * ph; d  =  c * ph
        # (cx, cy) is the bottom-left corner of the image rectangle in PDF points.
        # The cm matrix maps [0,1]² to the image, so the translation component
        # is exactly the bottom-left corner.
        ex = cx
        ey = cy
        draw += f'q\n{a:.3f} {b_:.3f} {cc:.3f} {d:.3f} {ex:.3f} {ey:.3f} cm\n/{name} Do\nQ\n'.encode()
    draw += b'Q'
    return new_obj_bytes, xobj_refs, draw, next_num


def _embed_image_empties(filepath, image_empties_behind, image_empties_front,
                         min_x, min_y, frame_w, frame_h, width_pt, height_pt):
    """Embed Image Empty objects into an already-written PDF file.

    Image Empties whose Z position is below all GP objects are drawn before
    the GP content stream (behind); those at or above are drawn after (front).

    The function:
      1. Converts each Image Empty to a placement record (`_build_image_entries`).
      2. Creates PDF Image XObjects + optional /SMask objects (`_make_image_draw`).
      3. Inserts the new objects into the PDF byte stream before the xref table.
      4. Adds /XObject resource references to the page dictionary.
      5. Wraps the first content stream with behind-draw … GP-content … front-draw.
      6. Rebuilds the xref table."""
    entries_behind = _build_image_entries(
        image_empties_behind, min_x, min_y, frame_w, frame_h, width_pt, height_pt)
    entries_front  = _build_image_entries(
        image_empties_front,  min_x, min_y, frame_w, frame_h, width_pt, height_pt)
    if not entries_behind and not entries_front:
        return

    with open(filepath, 'rb') as f:
        data = f.read()

    obj_nums = [int(m.group(1)) for m in _re.finditer(rb'(\d+)\s+0\s+obj', data)]
    if not obj_nums:
        return
    next_num = max(obj_nums) + 1

    new_obj_bytes = b''
    all_xobj_refs = []

    # Build behind-images first so their object numbers are lower.
    behind_objs, behind_refs, draw_behind, next_num = _make_image_draw(
        entries_behind, next_num, width_pt, height_pt)
    new_obj_bytes += behind_objs
    all_xobj_refs += behind_refs

    front_objs, front_refs, draw_front, _ = _make_image_draw(
        entries_front, next_num, width_pt, height_pt)
    new_obj_bytes += front_objs
    all_xobj_refs += front_refs

    # Add image XObject references to the page /Resources dictionary.
    xobj_dict = b'<< ' + b' '.join(all_xobj_refs) + b' >>'
    if b'/XObject' in data:
        data = _re.sub(rb'/XObject\s*<<',
                       b'/XObject << ' + b' '.join(all_xobj_refs) + b' ',
                       data, count=1)
    else:
        data = _re.sub(rb'/Resources\s*<<',
                       b'/Resources << /XObject ' + xobj_dict + b' ',
                       data, count=1)

    # Insert new XObject bytes just before the xref table.
    xref_m = _re.search(rb'\nxref\b', data)
    if not xref_m:
        return
    body_end = xref_m.start() + 1
    data = data[:body_end] + new_obj_bytes + data[body_end:]

    # Sandwich the GP content stream between the behind and front draw commands.
    parts = _re.split(rb'(stream\r?\n)(.*?)(\r?\nendstream)', data, flags=_re.DOTALL)
    if len(parts) >= 5:
        seg      = parts[0]
        s_open   = parts[1]
        old_body = parts[2]
        s_close  = parts[3]
        new_body = draw_behind + b'\n' + old_body + b'\n' + draw_front
        seg      = _re.sub(rb'/Length\s+\d+', f'/Length {len(new_body)}'.encode(), seg)
        data     = seg + s_open + new_body + s_close + b''.join(parts[4:])

    data = _rebuild_xref(data)
    with open(filepath, 'wb') as f:
        f.write(data)


# ── Main export logic ─────────────────────────────────────────────────────────

def _export_frame_to_pdf(frame_obj, filepath, scene):
    """Export grease pencil objects inside frame_obj to a PDF at filepath.

    Two-pass approach:
      Pass 1 — Export only an invisible anchor stroke at the exact frame corners
               to measure how Haru maps world-space coordinates to PDF points.
      Pass 2 — Export all GP objects inside the frame, plus an extended anchor
               that covers both the frame and all GP bounds.  Re-read the anchor's
               maximum coordinates to derive the precise scale + translation needed
               to fit the GP content into the frame page.

    After GP export, Image Empties inside the frame are embedded as JPEG XObjects.

    Returns (ok: bool, msg: str)."""
    min_x, min_y, max_x, max_y = _frame_bounds(frame_obj)
    frame_w = max_x - min_x
    frame_h = max_y - min_y

    scale_length = scene.unit_settings.scale_length
    frame_w_mm = frame_w * scale_length * 1000
    frame_h_mm = frame_h * scale_length * 1000

    image_empties = [o for o in scene.objects
                     if o.type == 'EMPTY' and o.empty_display_type == 'IMAGE'
                     and o.data is not None]
    gp_objects, temp_drawing_objs = _objects_in_frame(min_x, min_y, max_x, max_y, scene)
    if not gp_objects:
        for o in temp_drawing_objs:
            data = o.data
            bpy.data.objects.remove(o, do_unlink=True)
            if data.users == 0:
                bpy.data.grease_pencils.remove(data)
        return False, f"No grease pencil objects found inside '{frame_obj.name}'"

    # Orthographic camera centred on the frame, pointing down –Z.
    cam_data = bpy.data.cameras.new("_mastro_pdf_cam")
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = frame_h
    cam_obj = bpy.data.objects.new("_mastro_pdf_cam", cam_data)
    scene.collection.objects.link(cam_obj)
    cam_obj.location = ((min_x + max_x) / 2, (min_y + max_y) / 2, 100)
    cam_obj.rotation_euler = (0, 0, 0)

    prev_selected = [o for o in bpy.data.objects if o.select_get()]
    prev_active   = bpy.context.view_layer.objects.active
    prev_scene    = _setup_scene(scene, cam_obj, frame_w_mm, frame_h_mm)

    try:
        # ── Pass 1: anchor-only export ────────────────────────────────────
        # Export a single invisible stroke at the four frame corners.
        # By parsing its Haru coordinates we learn the exact mapping:
        #   world_coord * haru_k + haru_margin = haru_coord
        frame_corners = [(min_x, min_y, 0), (max_x, min_y, 0),
                         (max_x, max_y, 0), (min_x, max_y, 0)]
        anchor_obj1, anchor_data1 = _make_anchor(scene, frame_corners)

        for o in bpy.data.objects:
            o.select_set(False)
        anchor_obj1.select_set(True)
        bpy.context.view_layer.objects.active = anchor_obj1

        # Hide all other GP objects so only the anchor is exported.
        hidden_pass1 = []
        for o in bpy.data.objects:
            if o.type == 'GREASEPENCIL' and o is not anchor_obj1:
                hidden_pass1.append((o, o.hide_viewport, o.hide_render))
                o.hide_viewport = True
                o.hide_render   = True

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp_path = tmp.name
        _gp_export_pdf(tmp_path)

        for o, vp, rn in hidden_pass1:
            o.hide_viewport = vp
            o.hide_render   = rn

        bpy.data.objects.remove(anchor_obj1, do_unlink=True)
        bpy.data.grease_pencils.remove(anchor_data1)

        anchor_haru = _read_anchor_haru_bounds(tmp_path)
        os.unlink(tmp_path)

        if anchor_haru is None:
            return False, "Could not parse calibration anchor stream"

        ah_min_x, ah_min_y, ah_max_x, ah_max_y = anchor_haru
        haru_margin_x = ah_min_x
        haru_margin_y = ah_min_y
        haru_k_x = (ah_max_x - ah_min_x) / frame_w
        haru_k_y = (ah_max_y - ah_min_y) / frame_h

        # Initial scale estimates (will be refined after pass 2).
        width_pt  = frame_w_mm * 72.0 / 25.4
        height_pt = frame_h_mm * 72.0 / 25.4
        scale_x = width_pt  / (ah_max_x - ah_min_x)
        scale_y = height_pt / (ah_max_y - ah_min_y)

        # ── Pass 2: full GP export ────────────────────────────────────────
        # The anchor in pass 2 covers the union of the frame and all GP strokes.
        # This ensures Haru places all content inside one coordinate space; we
        # then read the anchor's maximum to recover the precise scale.
        all_min_x, all_min_y = min_x, min_y
        all_max_x, all_max_y = max_x, max_y
        for obj in gp_objects:
            ox1, oy1, ox2, oy2 = _gp_world_bounds(obj, scene)
            all_min_x = min(all_min_x, ox1)
            all_min_y = min(all_min_y, oy1)
            all_max_x = max(all_max_x, ox2)
            all_max_y = max(all_max_y, oy2)

        frame_x_haru = haru_margin_x + (min_x - all_min_x) * haru_k_x
        frame_y_haru = haru_margin_y + (min_y - all_min_y) * haru_k_y

        ext_corners = [(all_min_x, all_min_y, 0), (all_max_x, all_min_y, 0),
                       (all_max_x, all_max_y, 0), (all_min_x, all_max_y, 0)]
        anchor_obj2, anchor_data2 = _make_anchor(scene, ext_corners)

        gp_set = set(gp_objects) | {anchor_obj2}
        for o in bpy.data.objects:
            o.select_set(False)
        anchor_obj2.select_set(True)
        for o in gp_objects:
            o.select_set(True)
        bpy.context.view_layer.objects.active = anchor_obj2

        hidden_pass2 = []
        for o in bpy.data.objects:
            if o.type == 'GREASEPENCIL' and o not in gp_set:
                hidden_pass2.append((o, o.hide_viewport, o.hide_render))
                o.hide_viewport = True
                o.hide_render   = True

        _gp_export_pdf(filepath)

        for o, vp, rn in hidden_pass2:
            o.hide_viewport = vp
            o.hide_render   = rn

        bpy.data.objects.remove(anchor_obj2, do_unlink=True)
        bpy.data.grease_pencils.remove(anchor_data2)

        # Refine calibration from the pass-2 anchor.
        p2_max_x, p2_max_y = _read_max_haru_coords(filepath)
        if p2_max_x is not None:
            ah2_min_x = p2_max_x - (all_max_x - all_min_x) * haru_k_x
            ah2_min_y = p2_max_y - (all_max_y - all_min_y) * haru_k_y
            frame_x_haru = ah2_min_x + (min_x - all_min_x) * haru_k_x
            frame_y_haru = ah2_min_y + (min_y - all_min_y) * haru_k_y
            scale_x = width_pt  / (frame_w * haru_k_x)
            scale_y = height_pt / (frame_h * haru_k_y)

        # Rewrite MediaBox and clip/scale the GP content stream.
        _fix_mediabox(filepath, width_pt, height_pt, frame_x_haru, frame_y_haru, scale_x, scale_y)

        # Embed Image Empties: split by Z depth relative to GP content.
        gp_z_values = [o.matrix_world.translation.z for o in gp_objects]
        gp_z_min    = min(gp_z_values) if gp_z_values else 0.0
        imgs_behind = [o for o in image_empties if o.matrix_world.translation.z < gp_z_min]
        imgs_front  = [o for o in image_empties if o.matrix_world.translation.z >= gp_z_min]
        _embed_image_empties(filepath, imgs_behind, imgs_front,
                             min_x, min_y, frame_w, frame_h, width_pt, height_pt)
        success, msg = True, ""

    except Exception as e:
        success, msg = False, str(e)

    _restore_scene(scene, prev_scene)
    for o in bpy.data.objects:
        o.select_set(False)
    for o in prev_selected:
        o.select_set(True)
    bpy.context.view_layer.objects.active = prev_active

    bpy.data.objects.remove(cam_obj,  do_unlink=True)
    bpy.data.cameras.remove(cam_data)

    for o in temp_drawing_objs:
        data = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if data.users == 0:
            bpy.data.grease_pencils.remove(data)

    return success, msg


# ── Platform file opener ──────────────────────────────────────────────────────

def _open_file(filepath):
    import sys
    if sys.platform == 'win32':
        os.startfile(filepath)
    elif sys.platform == 'darwin':
        subprocess.Popen(['open', filepath])
    else:
        subprocess.Popen(['xdg-open', filepath])


# ── Operator ──────────────────────────────────────────────────────────────────

class OBJECT_OT_Export_Mastro_Frame_PDF(Operator, ExportHelper):
    """Export grease pencil objects inside the active MaStro frame to PDF"""
    bl_idname = "object.mastro_export_frame_pdf"
    bl_label = "Export Frame PDF"
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = ".pdf"
    filter_glob: StringProperty(default="*.pdf", options={'HIDDEN'})

    open_after: BoolProperty(
        name="Open after export",
        description="Open the exported PDF with the system default viewer",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (
            obj is not None and
            obj.type == 'EMPTY' and
            obj.get("MaStro frame")
        )

    def invoke(self, context, event):
        self.filepath = bpy.path.ensure_ext(context.active_object.name, ".pdf")
        return super().invoke(context, event)

    def execute(self, context):
        frame_obj = context.active_object
        filepath  = bpy.path.abspath(self.filepath)

        ok, msg = _export_frame_to_pdf(frame_obj, filepath, context.scene)
        if not ok:
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}

        if self.open_after:
            try:
                _open_file(filepath)
            except Exception as e:
                self.report({'WARNING'}, f"Could not open PDF: {e}")

        self.report({'INFO'}, f"Exported PDF: {filepath}")
        return {'FINISHED'}
