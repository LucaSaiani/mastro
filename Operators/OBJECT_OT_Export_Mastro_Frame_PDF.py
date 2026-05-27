import bpy
import os
import subprocess
import tempfile
import mathutils
from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty
from bpy_extras.io_utils import ExportHelper
from ..Utils.pdf_merge import merge as pdf_merge


def _frame_bounds(obj):
    """Return (min_x, min_y, max_x, max_y) in world space from a frame mesh."""
    world = obj.matrix_world
    coords = [world @ v.co for v in obj.data.vertices]
    xs = [c.x for c in coords]
    ys = [c.y for c in coords]
    return min(xs), min(ys), max(xs), max(ys)


def _objects_in_frame(min_x, min_y, max_x, max_y):
    """Return grease pencil objects whose bounding box overlaps the frame XY bounds."""
    result = []
    for obj in bpy.data.objects:
        if obj.type != 'GREASEPENCIL':
            continue
        world = obj.matrix_world
        wc = [world @ mathutils.Vector(c) for c in obj.bound_box]
        if (max(c.x for c in wc) >= min_x and min(c.x for c in wc) <= max_x and
                max(c.y for c in wc) >= min_y and min(c.y for c in wc) <= max_y):
            result.append(obj)
    return result


def _export_frame_to_pdf(frame_obj, filepath, scene):
    """Export grease pencil contents of frame_obj to filepath. Returns True on success."""
    min_x, min_y, max_x, max_y = _frame_bounds(frame_obj)
    frame_w = max_x - min_x
    frame_h = max_y - min_y

    # Physical size in mm (1 Blender unit = scale_length metres = scale_length*1000 mm)
    scale_length = scene.unit_settings.scale_length
    frame_w_mm = frame_w * scale_length * 1000
    frame_h_mm = frame_h * scale_length * 1000
    print(f"[MaStro PDF] frame_w={frame_w:.4f} world units  ({frame_w_mm:.1f} mm)  "
          f"frame_h={frame_h:.4f} ({frame_h_mm:.1f} mm)  unit_scale={scale_length}")

    gp_objects = [o for o in bpy.data.objects if o.type == 'GREASEPENCIL']
    if not gp_objects:
        return False, f"No grease pencil objects found inside '{frame_obj.name}'"

    # Anchor strokes at frame corners force Haru's bbox origin to (min_x, min_y),
    # so frame_x_haru = frame_y_haru = 0 always.
    HARU_K = 300.0
    frame_x_haru = 0.0
    frame_y_haru = 0.0

    # Temporary orthographic camera centred on the frame
    cam_data = bpy.data.cameras.new("_mastro_pdf_cam")
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = frame_h

    cam_obj = bpy.data.objects.new("_mastro_pdf_cam", cam_data)
    scene.collection.objects.link(cam_obj)
    cam_obj.location = ((min_x + max_x) / 2, (min_y + max_y) / 2, 100)
    cam_obj.rotation_euler = (0, 0, 0)

    # Invisible anchor stroke at frame corners — forces the exporter's stroke
    # bounding box to coincide with the frame boundary.
    anchor_data = bpy.data.grease_pencils.new("_mastro_pdf_anchor")
    layer   = anchor_data.layers.new("anchor")
    frame_d = layer.frames.new(scene.frame_current)
    drawing = frame_d.drawing
    drawing.add_strokes([4])
    stroke = drawing.strokes[0]
    stroke.cyclic = True
    for i, co in enumerate([(min_x, min_y, 0), (max_x, min_y, 0),
                             (max_x, max_y, 0), (min_x, max_y, 0)]):
        stroke.points[i].position = mathutils.Vector(co)
        stroke.points[i].opacity  = 0.001
        stroke.points[i].radius   = 0.001

    anchor_obj = bpy.data.objects.new("_mastro_pdf_anchor", anchor_data)
    scene.collection.objects.link(anchor_obj)

    # Save and override scene settings
    prev_camera   = scene.camera
    prev_x        = scene.render.resolution_x
    prev_y        = scene.render.resolution_y
    prev_pct      = scene.render.resolution_percentage
    prev_aspect_x = scene.render.pixel_aspect_x
    prev_aspect_y = scene.render.pixel_aspect_y

    scene.camera = cam_obj
    scene.render.resolution_percentage = 100
    scene.render.pixel_aspect_x = 1.0
    scene.render.pixel_aspect_y = 1.0
    scene.render.resolution_x = max(1, int(round(frame_w_mm)))
    scene.render.resolution_y = max(1, int(round(frame_h_mm)))

    # Select only objects inside frame + anchor
    prev_selected = [o for o in bpy.data.objects if o.select_get()]
    prev_active   = bpy.context.view_layer.objects.active

    # Deselect all; select only frame GP objects + anchor
    for o in bpy.data.objects:
        o.select_set(False)
    anchor_obj.select_set(True)
    for o in gp_objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = anchor_obj

    # Hide all GP objects NOT in the frame so the exporter cannot include them
    gp_set = set(gp_objects) | {anchor_obj}
    hidden_objects = []  # list of (obj, prev_hide_viewport, prev_hide_render)
    for o in bpy.data.objects:
        if o.type == 'GREASEPENCIL' and o not in gp_set:
            hidden_objects.append((o, o.hide_viewport, o.hide_render))
            o.hide_viewport = True
            o.hide_render = True

    try:
        bpy.ops.wm.grease_pencil_export_pdf(
            filepath=filepath,
            selected_object_type='SELECTED',
        )
        _fix_mediabox(filepath, frame_w_mm, frame_h_mm,
                      frame_x_haru, frame_y_haru, HARU_K, frame_w, frame_h)
        success, msg = True, ""
    except Exception as e:
        success, msg = False, str(e)

    # Restore everything
    for o, prev_vp, prev_render in hidden_objects:
        o.hide_viewport = prev_vp
        o.hide_render = prev_render

    scene.camera = prev_camera
    scene.render.resolution_x = prev_x
    scene.render.resolution_y = prev_y
    scene.render.resolution_percentage = prev_pct
    scene.render.pixel_aspect_x = prev_aspect_x
    scene.render.pixel_aspect_y = prev_aspect_y

    for o in bpy.data.objects:
        o.select_set(False)
    for o in prev_selected:
        o.select_set(True)
    bpy.context.view_layer.objects.active = prev_active

    bpy.data.objects.remove(cam_obj,    do_unlink=True)
    bpy.data.cameras.remove(cam_data)
    bpy.data.objects.remove(anchor_obj, do_unlink=True)
    bpy.data.grease_pencils.remove(anchor_data)

    return success, msg


def _fix_mediabox(filepath, width_mm, height_mm,
                  frame_x_haru=0.0, frame_y_haru=0.0,
                  haru_k=300.0, frame_w_world=None, frame_h_world=None):
    """Fix MediaBox and scale/translate content streams to match physical dimensions."""
    import re as _re

    width_pt  = width_mm  * 72.0 / 25.4
    height_pt = height_mm * 72.0 / 25.4

    with open(filepath, 'rb') as f:
        data = f.read()

    # Read the actual MediaBox written by Haru to get the real coordinate space.
    mb_match = _re.search(rb'/MediaBox\s*\[\s*([0-9.+-]+)\s+([0-9.+-]+)\s+([0-9.+-]+)\s+([0-9.+-]+)\s*\]', data)
    if mb_match:
        haru_w = float(mb_match.group(3)) - float(mb_match.group(1))
        haru_h = float(mb_match.group(4)) - float(mb_match.group(2))
        scale_x = width_pt  / haru_w if haru_w else 1.0
        scale_y = height_pt / haru_h if haru_h else 1.0
        tx = -frame_x_haru * scale_x
        ty = -frame_y_haru * scale_y
        print(f"[MaStro PDF] Haru MediaBox=({haru_w:.1f} x {haru_h:.1f} pt)  "
              f"target=({width_pt:.1f} x {height_pt:.1f} pt)  "
              f"scale=({scale_x:.4f},{scale_y:.4f})")
    else:
        scale_x = scale_y = 1.0
        tx = ty = 0.0
        print("[MaStro PDF] WARNING: could not read MediaBox from exported PDF")

    # Replace MediaBox and CropBox
    new_box = f'[0 0 {width_pt:.3f} {height_pt:.3f}]'.encode()
    data = _re.sub(rb'/MediaBox\s*\[[^\]]+\]', b'/MediaBox ' + new_box, data)
    data = _re.sub(rb'/CropBox\s*\[[^\]]+\]',  b'/CropBox '  + new_box, data)

    # Wrap content streams: clip to page, then scale+translate so frame = full page.
    # Clip is set in device/pt space BEFORE the cm transform.
    prefix = (
        f'q\n'
        f'0 0 {width_pt:.3f} {height_pt:.3f} re W n\n'
        f'{scale_x:.6f} 0 0 {scale_y:.6f} {tx:.3f} {ty:.3f} cm\n'
    ).encode()
    print(f"[MaStro PDF] scale=({scale_x:.4f},{scale_y:.4f})  "
          f"translate=({tx:.2f},{ty:.2f})  frame_haru=({frame_x_haru:.2f},{frame_y_haru:.2f})")
    suffix = b''

    # Split on stream/endstream boundaries (handles \r\n or \n)
    # Wrap content streams with clip + scale transform.
    # We do NOT update /Length — PDF viewers scan for 'endstream' when /Length is wrong,
    # which means they read our full patched content including prefix and suffix.
    parts = _re.split(rb'(stream\r?\n)(.*?)(\r?\nendstream)', data, flags=_re.DOTALL)
    if len(parts) > 1:
        out = bytearray(parts[0])
        i = 1
        while i < len(parts):
            body     = parts[i + 1]
            new_body = prefix + body + suffix
            out += parts[i] + new_body + parts[i + 2]
            if i + 3 < len(parts):
                out += parts[i + 3]
            i += 4
        data = bytes(out)

    print(f"[MaStro PDF] scale_x={scale_x:.4f} scale_y={scale_y:.4f}  "
          f"streams patched: {(len(parts)-1)//4}")

    with open(filepath, 'wb') as f:
        f.write(data)


def _merge_pdfs(input_paths, output_path):
    """Merge PDFs using pure Python. Returns (success, error_message)."""
    try:
        pdf_merge(input_paths, output_path)
        return True, ""
    except Exception as e:
        return False, str(e)


def _open_file(filepath):
    """Open a file with the system default application."""
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
            ok, msg = _export_frame_to_pdf(context.active_object, filepath, scene)
            if not ok:
                self.report({'ERROR' if msg else 'WARNING'},
                            msg or "No grease pencil objects found inside the frame")
                return {'CANCELLED'}

        self.report({'INFO'}, f"Exported PDF: {filepath}")

        if self.open_after:
            try:
                _open_file(filepath)
            except Exception as e:
                self.report({'WARNING'}, f"Could not open PDF: {e}")

        return {'FINISHED'}
