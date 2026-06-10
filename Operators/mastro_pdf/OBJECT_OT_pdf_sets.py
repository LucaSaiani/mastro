import bpy
import os
import subprocess
import sys
from bpy.types import Operator
from bpy.props import StringProperty

from .OBJECT_OT_Export_Mastro_Frame_PDF import _export_frame_to_pdf
from ...Utils.mastro_pdf.pdf_merge import merge as pdf_merge


def _open_file(path):
    if sys.platform == "win32":
        os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


def _all_frames(context):
    return [o for o in context.scene.objects
            if o.type == 'MESH' and o.data.get("MaStro frame")]


class MASTRO_OT_PdfSetAdd(Operator):
    bl_idname  = "mastro.pdf_set_add"
    bl_label   = "Add PDF Set"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        pp = context.scene.mastro_pdf_props
        s = pp.pdf_sets.add()
        s.name = "PDF Set"
        pp.active_set_index = len(pp.pdf_sets) - 1
        return {'FINISHED'}


class MASTRO_OT_PdfSetRemove(Operator):
    bl_idname  = "mastro.pdf_set_remove"
    bl_label   = "Remove PDF Set"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        pp = context.scene.mastro_pdf_props
        idx = pp.active_set_index
        if idx < 0 or idx >= len(pp.pdf_sets):
            return {'CANCELLED'}
        pp.pdf_sets.remove(idx)
        pp.active_set_index = max(0, idx - 1)
        return {'FINISHED'}


class MASTRO_OT_PdfSetDuplicate(Operator):
    bl_idname  = "mastro.pdf_set_duplicate"
    bl_label   = "Duplicate PDF Set"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        pp = context.scene.mastro_pdf_props
        idx = pp.active_set_index
        if idx < 0 or idx >= len(pp.pdf_sets):
            return {'CANCELLED'}
        src = pp.pdf_sets[idx]
        dst = pp.pdf_sets.add()
        dst.name = src.name + " Copy"
        dst.bind_pages = src.bind_pages
        for item in src.frames:
            dst.frames.add().frame_name = item.frame_name
        pp.active_set_index = len(pp.pdf_sets) - 1
        return {'FINISHED'}


class MASTRO_OT_PdfSetMoveUp(Operator):
    bl_idname  = "mastro.pdf_set_move_up"
    bl_label   = "Move PDF Set Up"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        pp = context.scene.mastro_pdf_props
        idx = pp.active_set_index
        if idx <= 0:
            return {'CANCELLED'}
        pp.pdf_sets.move(idx, idx - 1)
        pp.active_set_index = idx - 1
        return {'FINISHED'}


class MASTRO_OT_PdfSetMoveDown(Operator):
    bl_idname  = "mastro.pdf_set_move_down"
    bl_label   = "Move PDF Set Down"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        pp = context.scene.mastro_pdf_props
        idx = pp.active_set_index
        if idx >= len(pp.pdf_sets) - 1:
            return {'CANCELLED'}
        pp.pdf_sets.move(idx, idx + 1)
        pp.active_set_index = idx + 1
        return {'FINISHED'}


class MASTRO_OT_PdfSetToggleFrame(Operator):
    bl_idname  = "mastro.pdf_set_toggle_frame"
    bl_label   = "Toggle Frame in PDF Set"
    bl_options = {'REGISTER', 'UNDO'}

    frame_name: StringProperty()

    def execute(self, context):
        pp = context.scene.mastro_pdf_props
        idx = pp.active_set_index
        if idx < 0 or idx >= len(pp.pdf_sets):
            return {'CANCELLED'}
        s = pp.pdf_sets[idx]
        for i, item in enumerate(s.frames):
            if item.frame_name == self.frame_name:
                s.frames.remove(i)
                return {'FINISHED'}
        s.frames.add().frame_name = self.frame_name
        return {'FINISHED'}


class MASTRO_OT_PdfSetExport(Operator):
    bl_idname  = "mastro.pdf_set_export"
    bl_label   = "Export PDF"
    bl_options = {'REGISTER'}

    directory: bpy.props.StringProperty(subtype='DIR_PATH')
    open_after: bpy.props.BoolProperty(
        name="Open after export",
        description="Open the exported PDF(s) with the system default viewer",
        default=True,
    )

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        pp  = context.scene.mastro_pdf_props
        idx = pp.active_set_index
        if idx < 0 or idx >= len(pp.pdf_sets):
            self.report({'WARNING'}, "No active PDF set.")
            return {'CANCELLED'}

        pdf_set = pp.pdf_sets[idx]
        member_names = {item.frame_name for item in pdf_set.frames}
        frames = [o for o in _all_frames(context) if o.name in member_names]

        if not frames:
            self.report({'WARNING'}, "No frames in set.")
            return {'CANCELLED'}

        directory = bpy.path.abspath(self.directory)
        open_after = self.open_after

        if pdf_set.bind_pages:
            import tempfile
            tmp_paths = []
            for frame in frames:
                tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
                tmp.close()
                _export_frame_to_pdf(frame, tmp.name, context.scene)
                tmp_paths.append(tmp.name)
            out_path = os.path.join(directory, pdf_set.name + ".pdf")
            pdf_merge(tmp_paths, out_path)
            for p in tmp_paths:
                try:
                    os.remove(p)
                except OSError:
                    pass
            if open_after:
                _open_file(out_path)
            self.report({'INFO'}, f"Exported: {out_path}")
        else:
            out_paths = []
            for frame in frames:
                out_path = os.path.join(directory, frame.name + ".pdf")
                _export_frame_to_pdf(frame, out_path, context.scene)
                out_paths.append(out_path)
            if open_after:
                for p in out_paths:
                    _open_file(p)
            self.report({'INFO'}, f"Exported {len(frames)} PDF(s) to {directory}")

        return {'FINISHED'}
