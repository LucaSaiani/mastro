import bpy
import os
import re as _re
import subprocess
import tempfile
import mathutils
from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty
from bpy_extras.io_utils import ExportHelper
from ..Utils.pdf_merge import merge as pdf_merge

_LOG_PATH = "/tmp/mastro_pdf_debug.log"
_log_file = None

def _log(msg):
    print(msg)
    if _log_file:
        _log_file.write(msg + "\n")
        _log_file.flush()

def _open_log():
    global _log_file
    _log_file = open(_LOG_PATH, "w")

def _close_log():
    global _log_file
    if _log_file:
        _log_file.close()
        _log_file = None


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
        except Exception as e:
            _log(f"[MaStro PDF] _gp_world_bounds stroke access failed for {obj.name}: {e}")
    if xs:
        _log(f"[MaStro PDF] {obj.name}: {len(xs)} points found, "
             f"x=[{min(xs):.3f},{max(xs):.3f}] y=[{min(ys):.3f},{max(ys):.3f}]")
    else:
        _log(f"[MaStro PDF] {obj.name}: no points found, falling back to bound_box")
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


def _log_blender_to_haru(gp_objects, scene, all_min_x, all_min_y, haru_margin_x, haru_margin_y, haru_k_x, haru_k_y, label="", max_pts=10):
    """For each GP object print world-space stroke points alongside expected Haru coords."""
    _log(f"[MaStro PDF] {label} — Blender→Haru mapping (first {max_pts} pts per object):")
    for obj in gp_objects:
        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_obj  = obj.evaluated_get(depsgraph)
        world     = eval_obj.matrix_world
        frame_num = scene.frame_current
        pts = []
        for layer in eval_obj.data.layers:
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
                        pts.append(co)
            except Exception:
                pass
        _log(f"[MaStro PDF]   {obj.name}: {len(pts)} points")
        for co in pts[:max_pts]:
            hx = haru_margin_x + (co.x - all_min_x) * haru_k_x
            hy = haru_margin_y + (co.y - all_min_y) * haru_k_y
            _log(f"[MaStro PDF]     world=({co.x:.4f},{co.y:.4f})  →  haru_expected=({hx:.3f},{hy:.3f})")


def _log_pdf_streams(filepath, label, max_coords=30):
    """Parse PDF content streams and print the first path coordinates in Haru units."""
    with open(filepath, 'rb') as f:
        data = f.read()
    parts = _re.split(rb'(stream\r?\n)(.*?)(\r?\nendstream)', data, flags=_re.DOTALL)
    n_streams = (len(parts) - 1) // 4
    _log(f"[MaStro PDF] {label}: {n_streams} stream(s)")
    coord_re = _re.compile(
        rb'([-+]?[0-9]*\.?[0-9]+)\s+([-+]?[0-9]*\.?[0-9]+)\s+([mlcMLC])'
    )
    for si in range(n_streams):
        body = parts[1 + si * 4 + 1]
        matches = coord_re.findall(body)
        if not matches:
            continue
        _log(f"[MaStro PDF]   stream {si}: {len(matches)} path ops, first {min(len(matches), max_coords)}:")
        for x, y, op in matches[:max_coords]:
            _log(f"[MaStro PDF]     {op.decode()} ({float(x):.3f}, {float(y):.3f})")


def _export_frame_to_pdf(frame_obj, filepath, scene):
    """Export grease pencil contents of frame_obj to filepath. Returns (ok, msg)."""
    _open_log()
    min_x, min_y, max_x, max_y = _frame_bounds(frame_obj)
    frame_w = max_x - min_x
    frame_h = max_y - min_y

    scale_length = scene.unit_settings.scale_length
    frame_w_mm = frame_w * scale_length * 1000
    frame_h_mm = frame_h * scale_length * 1000

    gp_objects = _objects_in_frame(min_x, min_y, max_x, max_y, scene)
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
        bpy.ops.wm.grease_pencil_export_pdf(filepath=tmp_path,
                                             selected_object_type='SELECTED')

        for o, vp, rn in hidden_pass1:
            o.hide_viewport = vp
            o.hide_render   = rn

        bpy.data.objects.remove(anchor_obj1, do_unlink=True)
        bpy.data.grease_pencils.remove(anchor_data1)

        anchor_haru = _read_anchor_haru_bounds(tmp_path)
        _log_pdf_streams(tmp_path, "Pass 1 (calibration)")
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

        _log(f"[MaStro PDF] Frame world:  min=({min_x:.4f},{min_y:.4f})  max=({max_x:.4f},{max_y:.4f})  "
              f"w={frame_w:.4f} ({frame_w_mm:.1f}mm)  h={frame_h:.4f} ({frame_h_mm:.1f}mm)")
        _log(f"[MaStro PDF] Calibration:  anchor Haru=({ah_min_x:.3f},{ah_min_y:.3f})-({ah_max_x:.3f},{ah_max_y:.3f})  "
              f"margin=({haru_margin_x:.3f},{haru_margin_y:.3f})  K_x={haru_k_x:.4f}  K_y={haru_k_y:.4f}")
        _log(f"[MaStro PDF] Target page:  {width_pt:.3f} x {height_pt:.3f} pt  "
              f"scale_x={scale_x:.6f}  scale_y={scale_y:.6f}")

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

        _log(f"[MaStro PDF] GP union bbox: min=({all_min_x:.4f},{all_min_y:.4f})  "
              f"max=({all_max_x:.4f},{all_max_y:.4f})")
        _log(f"[MaStro PDF] Frame offset in Haru: x={frame_x_haru:.3f}  y={frame_y_haru:.3f}  "
              f"(world offset: dx={min_x-all_min_x:.4f}  dy={min_y-all_min_y:.4f})")

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

        bpy.ops.wm.grease_pencil_export_pdf(filepath=filepath,
                                             selected_object_type='SELECTED')

        for o, vp, rn in hidden_pass2:
            o.hide_viewport = vp
            o.hide_render   = rn

        bpy.data.objects.remove(anchor_obj2, do_unlink=True)
        bpy.data.grease_pencils.remove(anchor_data2)

        _log_pdf_streams(filepath, "Pass 2 (before fix)")
        p2_max_x, p2_max_y = _read_max_haru_coords(filepath)
        if p2_max_x is not None:
            # Anchor top-right = stream max; anchor bottom-left derived from K (pass 1).
            ah2_min_x = p2_max_x - (all_max_x - all_min_x) * haru_k_x
            ah2_min_y = p2_max_y - (all_max_y - all_min_y) * haru_k_y
            frame_x_haru = ah2_min_x + (min_x - all_min_x) * haru_k_x
            frame_y_haru = ah2_min_y + (min_y - all_min_y) * haru_k_y
            scale_x = width_pt  / (frame_w * haru_k_x)
            scale_y = height_pt / (frame_h * haru_k_y)
            _log(f"[MaStro PDF] Pass 2 anchor: max=({p2_max_x:.3f},{p2_max_y:.3f})  "
                 f"min=({ah2_min_x:.3f},{ah2_min_y:.3f})")
            _log(f"[MaStro PDF] Pass 2 corrected: frame_haru=({frame_x_haru:.3f},{frame_y_haru:.3f})  "
                 f"scale=({scale_x:.6f},{scale_y:.6f})")
            _log_blender_to_haru(gp_objects, scene, all_min_x, all_min_y,
                                  ah2_min_x, ah2_min_y, haru_k_x, haru_k_y,
                                  label="Pass 2 corrected")

        _fix_mediabox(filepath, width_pt, height_pt, frame_x_haru, frame_y_haru, scale_x, scale_y)
        success, msg = True, ""

    except Exception as e:
        success, msg = False, str(e)
    finally:
        _close_log()

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

    _log(f"[MaStro PDF] scale=({scale_x:.4f},{scale_y:.4f})  "
          f"translate=({tx:.2f},{ty:.2f})  streams patched: {n_streams}")

    with open(filepath, 'wb') as f:
        f.write(data)


def _merge_pdfs(input_paths, output_path):
    try:
        pdf_merge(input_paths, output_path)
        return True, ""
    except Exception as e:
        return False, str(e)


def _open_file(filepath):
    import sys
    if sys.platform == 'win32':
        os.startfile(filepath)
    elif sys.platform == 'darwin':
        subprocess.Popen(['open', filepath])
    else:
        subprocess.Popen(['xdg-open', filepath])


class OBJECT_OT_Export_Mastro_Frame_PDF(Operator, ExportHelper):
    """Export grease pencil objects inside MaStro frame(s) to PDF"""
    bl_idname = "object.mastro_export_frame_pdf"
    bl_label = "Export Frame PDF"
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = ".pdf"
    filter_glob: StringProperty(default="*.pdf", options={'HIDDEN'})

    bind_pages: BoolProperty(
        name="Bind all frames",
        description="Export every MaStro frame in the scene and merge into a single PDF "
                    "(requires ghostscript; ignored if only one frame exists)",
        default=False,
    )

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

    def draw(self, context):
        layout = self.layout
        all_frames = [o for o in bpy.data.objects
                      if o.type == 'MESH' and o.data.get("MaStro frame")]
        row = layout.row()
        row.prop(self, "bind_pages")
        row.enabled = len(all_frames) > 1
        layout.prop(self, "open_after")

    def execute(self, context):
        scene = context.scene
        filepath = bpy.path.abspath(self.filepath)

        all_frames = [o for o in bpy.data.objects
                      if o.type == 'MESH' and o.data.get("MaStro frame")]

        if self.bind_pages and len(all_frames) > 1:
            tmp_dir  = tempfile.mkdtemp()
            tmp_pdfs = []
            errors   = []

            for i, frame_obj in enumerate(all_frames):
                tmp_path = os.path.join(tmp_dir, f"_mastro_frame_{i}.pdf")
                ok, msg = _export_frame_to_pdf(frame_obj, tmp_path, scene)
                if ok:
                    tmp_pdfs.append(tmp_path)
                else:
                    errors.append(f"'{frame_obj.name}': {msg}")

            if not tmp_pdfs:
                self.report({'ERROR'}, "No frames could be exported: " + "; ".join(errors))
                return {'CANCELLED'}

            if errors:
                self.report({'WARNING'}, "Some frames skipped: " + "; ".join(errors))

            ok, msg = _merge_pdfs(tmp_pdfs, filepath)
            for p in tmp_pdfs:
                try: os.remove(p)
                except OSError: pass
            try: os.rmdir(tmp_dir)
            except OSError: pass

            if not ok:
                self.report({'ERROR'}, f"PDF merge failed: {msg}")
                return {'CANCELLED'}

        else:
            out_dir = os.path.dirname(filepath)
            errors  = []
            exported = []
            for frame_obj in all_frames:
                out_path = os.path.join(out_dir, bpy.path.ensure_ext(frame_obj.name, ".pdf"))
                ok, msg = _export_frame_to_pdf(frame_obj, out_path, scene)
                if ok:
                    exported.append(out_path)
                else:
                    errors.append(f"'{frame_obj.name}': {msg}")

            if not exported:
                self.report({'ERROR'}, "No frames could be exported: " + "; ".join(errors))
                return {'CANCELLED'}
            if errors:
                self.report({'WARNING'}, "Some frames skipped: " + "; ".join(errors))

            filepath = exported[0]
            if self.open_after:
                for path in exported:
                    try:
                        _open_file(path)
                    except Exception as e:
                        self.report({'WARNING'}, f"Could not open PDF: {e}")

        self.report({'INFO'}, f"Exported PDF: {filepath}")

        if self.open_after and self.bind_pages:
            try:
                _open_file(filepath)
            except Exception as e:
                self.report({'WARNING'}, f"Could not open PDF: {e}")

        return {'FINISHED'}
