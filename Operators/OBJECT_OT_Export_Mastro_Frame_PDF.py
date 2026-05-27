import bpy
import os
import re as _re
import subprocess
import tempfile
import mathutils
from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty
from bpy_extras.io_utils import ExportHelper


def _frame_bounds(obj):
    """Return (min_x, min_y, max_x, max_y) in world space from a frame mesh."""
    world = obj.matrix_world
    coords = [world @ v.co for v in obj.data.vertices]
    xs = [c.x for c in coords]
    ys = [c.y for c in coords]
    return min(xs), min(ys), max(xs), max(ys)


def _gp_world_bounds(obj, scene):
    """Return (min_x, min_y, max_x, max_y) from actual GP stroke points in world space.
    Uses the evaluated object so modifiers and transforms are applied.
    Falls back to obj.bound_box if no strokes are found."""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj  = obj.evaluated_get(depsgraph)
    world     = eval_obj.matrix_world
    frame_num = scene.frame_current
    xs, ys = [], []
    for layer in eval_obj.data.layers:
        # Find the frame at or before frame_current
        best = None
        for f in layer.frames:
            if f.frame_number == frame_num:
                best = f
                break
            if f.frame_number < frame_num:
                best = f  # keep advancing — will end up being the last one before current
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
    # fallback
    wc = [world @ mathutils.Vector(c) for c in eval_obj.bound_box]
    return min(c.x for c in wc), min(c.y for c in wc), max(c.x for c in wc), max(c.y for c in wc)


def _objects_in_frame(min_x, min_y, max_x, max_y, scene):
    """Return grease pencil objects whose stroke bounds overlap the frame XY bounds."""
    result = []
    for obj in bpy.data.objects:
        if obj.type != 'GREASEPENCIL':
            continue
        ox1, oy1, ox2, oy2 = _gp_world_bounds(obj, scene)
        if ox2 >= min_x and ox1 <= max_x and oy2 >= min_y and oy1 <= max_y:
            result.append(obj)
    return result


def _image_empties_in_frame(min_x, min_y, max_x, max_y, scene):
    """Log Image Empty objects that overlap the frame XY bounds."""
    import math
    log = open("/tmp/mastro_image_debug.log", "w")
    for obj in scene.objects:
        if obj.type != 'EMPTY' or obj.empty_display_type != 'IMAGE':
            continue
        if obj.data is None:
            continue
        w = obj.matrix_world
        pos = w.translation
        # Image Empty size is controlled by empty_display_size (half-size in each axis)
        # and actual pixel dims via obj.data.size
        sx = w.to_scale().x * obj.empty_display_size
        sy = w.to_scale().y * obj.empty_display_size
        rot_z = math.degrees(w.to_euler().z)
        px_w, px_h = obj.data.size
        log.write(f"[Image Empty] {obj.name}\n")
        log.write(f"  pos=({pos.x:.4f}, {pos.y:.4f}, {pos.z:.4f})\n")
        log.write(f"  display_size={obj.empty_display_size:.4f}  scale=({w.to_scale().x:.4f}, {w.to_scale().y:.4f})\n")
        log.write(f"  world_size=({sx:.4f}, {sy:.4f}) BU\n")
        log.write(f"  rot_z={rot_z:.2f} deg\n")
        log.write(f"  pixels=({px_w}, {px_h})\n")
        log.write(f"  filepath={obj.data.filepath!r}\n")
        in_frame = (pos.x + sx >= min_x and pos.x - sx <= max_x and
                    pos.y + sy >= min_y and pos.y - sy <= max_y)
        log.write(f"  in_frame={in_frame}\n\n")
    log.close()


def _read_mediabox(filepath):
    """Return (w, h) in Haru points from the first MediaBox in the PDF."""
    with open(filepath, 'rb') as f:
        data = f.read()
    m = _re.search(rb'/MediaBox\s*\[\s*([0-9.+-]+)\s+([0-9.+-]+)\s+([0-9.+-]+)\s+([0-9.+-]+)\s*\]', data)
    if m:
        return float(m.group(3)) - float(m.group(1)), float(m.group(4)) - float(m.group(2))
    return None, None


def _make_anchor(scene, corners):
    """Create and link an invisible GP anchor object with one stroke through corners."""
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
    """Call grease_pencil_export_pdf forcing camera view in the active VIEW_3D."""
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
    """Override scene camera and render resolution; return previous values."""
    prev = (scene.camera,
            scene.render.resolution_x, scene.render.resolution_y,
            scene.render.resolution_percentage,
            scene.render.pixel_aspect_x, scene.render.pixel_aspect_y)
    scene.camera = cam_obj
    scene.render.resolution_percentage = 100
    scene.render.pixel_aspect_x = 1.0
    scene.render.pixel_aspect_y = 1.0
    scene.render.resolution_x = max(1, int(round(frame_w_mm)))
    scene.render.resolution_y = max(1, int(round(frame_h_mm)))
    return prev


def _restore_scene(scene, prev):
    (scene.camera,
     scene.render.resolution_x, scene.render.resolution_y,
     scene.render.resolution_percentage,
     scene.render.pixel_aspect_x, scene.render.pixel_aspect_y) = prev


def _read_anchor_haru_bounds(filepath):
    """Parse the first content stream and return (min_x, min_y, max_x, max_y)
    of m/l path commands — reliable only for pass 1 (anchor-only stream)."""
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
    In pass 2 the anchor covers the full union bbox so its top-right corner
    is always the stream maximum — GP strokes are strictly inside."""
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



def _export_frame_to_pdf(frame_obj, filepath, scene):
    """Export grease pencil contents of frame_obj to filepath. Returns (ok, msg)."""
    min_x, min_y, max_x, max_y = _frame_bounds(frame_obj)
    frame_w = max_x - min_x
    frame_h = max_y - min_y

    scale_length = scene.unit_settings.scale_length
    frame_w_mm = frame_w * scale_length * 1000
    frame_h_mm = frame_h * scale_length * 1000

    _image_empties_in_frame(min_x, min_y, max_x, max_y, scene)
    image_empties = [o for o in scene.objects
                     if o.type == 'EMPTY' and o.empty_display_type == 'IMAGE'
                     and o.data is not None]
    gp_objects    = _objects_in_frame(min_x, min_y, max_x, max_y, scene)
    if not gp_objects:
        return False, f"No grease pencil objects found inside '{frame_obj.name}'"

    # Orthographic camera centred on the frame
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
        # ── Pass 1: anchor-only export to measure the exact Haru coordinate scale ──
        frame_corners = [(min_x, min_y, 0), (max_x, min_y, 0),
                         (max_x, max_y, 0), (min_x, max_y, 0)]
        anchor_obj1, anchor_data1 = _make_anchor(scene, frame_corners)

        for o in bpy.data.objects:
            o.select_set(False)
        anchor_obj1.select_set(True)
        bpy.context.view_layer.objects.active = anchor_obj1

        # Hide ALL GP objects so only the anchor is exported
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

        width_pt  = frame_w_mm * 72.0 / 25.4
        height_pt = frame_h_mm * 72.0 / 25.4
        scale_x = width_pt  / (ah_max_x - ah_min_x)
        scale_y = height_pt / (ah_max_y - ah_min_y)

        # ── Pass 2: export frame content with extended anchor ──
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

        p2_max_x, p2_max_y = _read_max_haru_coords(filepath)
        if p2_max_x is not None:
            # Anchor top-right = stream max; anchor bottom-left derived from K (pass 1).
            ah2_min_x = p2_max_x - (all_max_x - all_min_x) * haru_k_x
            ah2_min_y = p2_max_y - (all_max_y - all_min_y) * haru_k_y
            frame_x_haru = ah2_min_x + (min_x - all_min_x) * haru_k_x
            frame_y_haru = ah2_min_y + (min_y - all_min_y) * haru_k_y
            scale_x = width_pt  / (frame_w * haru_k_x)
            scale_y = height_pt / (frame_h * haru_k_y)

        _fix_mediabox(filepath, width_pt, height_pt, frame_x_haru, frame_y_haru, scale_x, scale_y)

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

    return success, msg


def _rebuild_xref(data):
    """Rebuild xref table and startxref after binary patching changed object offsets."""
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
    """Rewrite MediaBox and wrap content streams with clip + scale transform."""
    tx = -frame_x_haru * scale_x
    ty = -frame_y_haru * scale_y

    with open(filepath, 'rb') as f:
        data = f.read()

    new_box = f'[0 0 {width_pt:.3f} {height_pt:.3f}]'.encode()
    data = _re.sub(rb'/MediaBox\s*\[[^\]]+\]', b'/MediaBox ' + new_box, data)
    data = _re.sub(rb'/CropBox\s*\[[^\]]+\]',  b'/CropBox '  + new_box, data)

    prefix = (
        f'q\n'
        f'0 0 {width_pt:.3f} {height_pt:.3f} re W n\n'
        f'{scale_x:.6f} 0 0 {scale_y:.6f} {tx:.3f} {ty:.3f} cm\n'
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



def _crop_with_blender(img_path, crop_l, crop_u, crop_r, crop_b, rot_z, obj_name):
    """Load an image via bpy.data.images, crop/rotate, save as JPEG, return (bytes, w, h)."""
    import math, tempfile
    tmp_img  = None
    crop_img = None
    loaded   = False
    try:
        # Reuse already-loaded image if possible.
        src_img = next((i for i in bpy.data.images
                        if bpy.path.abspath(i.filepath) == img_path), None)
        if src_img is None:
            src_img = bpy.data.images.load(img_path)
            loaded = True

        src_img.update()
        px_w, px_h = src_img.size

        # Blender pixels: RGBA float, Y=0 at BOTTOM.
        # PIL crop coords (crop_l, crop_u, crop_r, crop_b) have Y=0 at TOP.
        # Convert top-down row indices to Blender's bottom-up:
        bl_y0 = px_h - crop_b   # first Blender row (bottom of visible strip)
        bl_y1 = px_h - crop_u   # last  Blender row (exclusive)
        new_w = crop_r - crop_l
        new_h = crop_b - crop_u

        src = src_img.pixels[:]   # flat RGBA float tuple
        dst = []
        for bl_y in range(bl_y0, bl_y1):
            row_start = (bl_y * px_w + crop_l) * 4
            dst.extend(src[row_start: row_start + new_w * 4])

        crop_img = bpy.data.images.new("_mastro_crop_tmp", new_w, new_h, alpha=False)
        crop_img.pixels = dst

        if rot_z != 0.0:
            # Rotation not yet implemented via Blender pixels; warn and skip.
            with open("/tmp/mastro_image_debug.log", "a") as dbg:
                dbg.write(f"  [warn] rotation not applied for {obj_name}\n")

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            tmp_path = f.name
        crop_img.file_format   = 'JPEG'
        crop_img.filepath_raw  = tmp_path
        crop_img.save()

        with open(tmp_path, 'rb') as f:
            data = f.read()
        os.unlink(tmp_path)
        return data, new_w, new_h

    except Exception as e:
        with open("/tmp/mastro_image_debug.log", "a") as dbg:
            dbg.write(f"  [crop error for {obj_name}]: {e}\n")
        return None, 0, 0
    finally:
        if crop_img is not None:
            bpy.data.images.remove(crop_img)
        if loaded and src_img is not None:
            bpy.data.images.remove(src_img)


def _build_image_entries(empties, min_x, min_y, frame_w, frame_h, width_pt, height_pt):
    import math, io
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
        aspect = px_h / px_w
        # In Blender, empty_display_size controls the HEIGHT of the image.
        # Width = height / aspect.
        world_h = obj.empty_display_size * abs(sy)
        world_w = world_h / aspect

        # empty_image_offset: (0,0) = bottom-left at origin (Blender default).
        ox, oy = tuple(getattr(obj, 'empty_image_offset', (0.0, 0.0)))
        img_bl_x = pos.x + ox * world_w
        img_bl_y = pos.y + oy * world_h

        # Intersection of image bounds with frame bounds.
        vis_x1 = max(img_bl_x, min_x);  vis_x2 = min(img_bl_x + world_w, max_x)
        vis_y1 = max(img_bl_y, min_y);  vis_y2 = min(img_bl_y + world_h, max_y)
        if vis_x2 <= vis_x1 or vis_y2 <= vis_y1:
            continue

        # Fraction of the image that is visible.
        fx1 = (vis_x1 - img_bl_x) / world_w;  fx2 = (vis_x2 - img_bl_x) / world_w
        fy1 = (vis_y1 - img_bl_y) / world_h;  fy2 = (vis_y2 - img_bl_y) / world_h

        # PIL pixel crop box.  PIL y=0 is the TOP of the image; Blender y=0 is the BOTTOM.
        # World fy=0 (bottom) → PIL row px_h; world fy=1 (top) → PIL row 0.
        crop_l = int(fx1 * px_w);  crop_r = int(fx2 * px_w)
        crop_u = int((1.0 - fy2) * px_h);  crop_b = int((1.0 - fy1) * px_h)
        # Clamp to valid pixel range.
        crop_l = max(0, crop_l);  crop_r = min(px_w, crop_r)
        crop_u = max(0, crop_u);  crop_b = min(px_h, crop_b)
        if crop_r <= crop_l or crop_b <= crop_u:
            continue

        # PDF position and size of the visible (cropped) portion.
        cx = (vis_x1 - min_x) / frame_w * width_pt
        cy = (vis_y1 - min_y) / frame_h * height_pt
        pw = (vis_x2 - vis_x1) / frame_w * width_pt
        ph = (vis_y2 - vis_y1) / frame_h * height_pt

        with open("/tmp/mastro_image_debug.log", "a") as dbg:
            dbg.write(f"[embed] {obj.name}: offset=({ox:.3f},{oy:.3f}) "
                      f"img_bl=({img_bl_x:.4f},{img_bl_y:.4f}) world=({world_w:.4f},{world_h:.4f})\n")
            dbg.write(f"  visible world: ({vis_x1:.4f},{vis_y1:.4f})→({vis_x2:.4f},{vis_y2:.4f})\n")
            dbg.write(f"  pixel crop: l={crop_l} u={crop_u} r={crop_r} b={crop_b} / {px_w}×{px_h}\n")
            dbg.write(f"  pdf: cx={cx:.2f} cy={cy:.2f} pw={pw:.2f} ph={ph:.2f} "
                      f"page=({width_pt:.2f},{height_pt:.2f})\n\n")

        img_path = bpy.path.abspath(obj.data.filepath)
        if not os.path.isfile(img_path):
            continue

        needs_crop = (crop_l > 0 or crop_u > 0 or crop_r < px_w or crop_b < px_h)
        ext = os.path.splitext(img_path)[1].lower()

        if needs_crop or rot_z != 0.0 or ext not in ('.jpg', '.jpeg'):
            img_bytes, px_w, px_h = _crop_with_blender(
                img_path, crop_l, crop_u, crop_r, crop_b,
                rot_z, obj.name)
            rot_z = 0.0
            if img_bytes is None:
                continue
        else:
            with open(img_path, 'rb') as fi:
                img_bytes = fi.read()

        result.append({'img_bytes': img_bytes, 'px_w': px_w, 'px_h': px_h,
                       'cx': cx, 'cy': cy, 'pw': pw, 'ph': ph, 'rot_z': rot_z})
    return result


def _make_image_draw(entries, start_num, width_pt, height_pt):
    import math
    new_obj_bytes = b''
    xobj_refs     = []
    draw          = (f'q\n0 0 {width_pt:.3f} {height_pt:.3f} re W n\n').encode()
    for i, e in enumerate(entries):
        num  = start_num + i
        name = f'Im{num}'
        xobj_refs.append(f'/{name} {num} 0 R'.encode())
        hdr = (
            f'{num} 0 obj\n'
            f'<< /Type /XObject /Subtype /Image'
            f' /Width {e["px_w"]} /Height {e["px_h"]}'
            f' /ColorSpace /DeviceRGB /BitsPerComponent 8'
            f' /Filter /DCTDecode /Length {len(e["img_bytes"])} >>\n'
            f'stream\n'
        ).encode()
        new_obj_bytes += hdr + e['img_bytes'] + b'\nendstream\nendobj\n'
        c  = math.cos(e['rot_z']); s  = math.sin(e['rot_z'])
        pw = e['pw'];              ph = e['ph']
        cx = e['cx'];              cy = e['cy']
        a  =  c * pw; b_ =  s * pw
        cc = -s * ph; d  =  c * ph
        # cx,cy is the image's bottom-left corner in PDF space.
        # The cm matrix maps the unit square [0,1]x[0,1] to the image rectangle,
        # so (ex, ey) is the PDF position of that bottom-left corner.
        ex = cx
        ey = cy
        draw += f'q\n{a:.3f} {b_:.3f} {cc:.3f} {d:.3f} {ex:.3f} {ey:.3f} cm\n/{name} Do\nQ\n'.encode()
    draw += b'Q'
    return new_obj_bytes, xobj_refs, draw


def _embed_image_empties(filepath, image_empties_behind, image_empties_front,
                         min_x, min_y, frame_w, frame_h, width_pt, height_pt):
    """Embed Image Empty objects into the PDF: behind group before GP stream, front group after."""
    entries_behind = _build_image_entries(image_empties_behind, min_x, min_y, frame_w, frame_h, width_pt, height_pt)
    entries_front  = _build_image_entries(image_empties_front,  min_x, min_y, frame_w, frame_h, width_pt, height_pt)
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

    behind_objs, behind_refs, draw_behind = _make_image_draw(entries_behind, next_num, width_pt, height_pt)
    new_obj_bytes += behind_objs
    all_xobj_refs += behind_refs
    next_num += len(entries_behind)

    front_objs, front_refs, draw_front = _make_image_draw(entries_front, next_num, width_pt, height_pt)
    new_obj_bytes += front_objs
    all_xobj_refs += front_refs

    # Update page /XObject resources
    xobj_dict = b'<< ' + b' '.join(all_xobj_refs) + b' >>'
    if b'/XObject' in data:
        data = _re.sub(rb'/XObject\s*<<', b'/XObject << ' + b' '.join(all_xobj_refs) + b' ', data, count=1)
    else:
        data = _re.sub(rb'/Resources\s*<<', b'/Resources << /XObject ' + xobj_dict + b' ', data, count=1)

    # Insert new XObject bytes before xref
    xref_m = _re.search(rb'\nxref\b', data)
    if not xref_m:
        return
    body_end = xref_m.start() + 1
    data = data[:body_end] + new_obj_bytes + data[body_end:]

    # Wrap first content stream: behind | GP | front
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


def _open_file(filepath):
    import sys
    if sys.platform == 'win32':
        os.startfile(filepath)
    elif sys.platform == 'darwin':
        subprocess.Popen(['open', filepath])
    else:
        subprocess.Popen(['xdg-open', filepath])


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
            obj.type == 'MESH' and
            obj.data.get("MaStro frame")
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
