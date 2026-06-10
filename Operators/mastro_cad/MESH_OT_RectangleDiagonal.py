import bpy
import bmesh
from mathutils import Vector
from bpy_extras.view3d_utils import (region_2d_to_location_3d,
                                     location_3d_to_region_2d,
                                     region_2d_to_origin_3d,
                                     region_2d_to_vector_3d)
import gpu
from gpu_extras.batch import batch_for_shader

from ...Utils.mastro_cad.cad.rect_utils import HANDLE_SIZE_PX
from ...Utils.mastro_cad.cad.snap_utils import SnapContext
from .CAD_mixin import RectMixin, RECT_CHAR_MAP

_rect_draw_handle = None   # creation operator preview (GC-safe module handle)


# ── Rectangle creation operator ───────────────────────────────────────────────

class MESH_OT_MaStroCad_RectangleDiagonal(RectMixin, bpy.types.Operator):
    """Draw a rectangle by clicking two opposite diagonal corners.

    Works in edit mode (adds geometry to active mesh) and object mode
    (creates a new mesh object with its origin at the diagonal centre).
    The rectangle lies on the view plane at the depth of the first click.
    """
    bl_idname  = "mastrocad.rectangle_diagonal"
    bl_label   = "Rectangle"
    bl_options = {'REGISTER', 'UNDO'}

    _draw_handle    = None
    _first_pt       = None
    _second_pt      = None
    _rect_corners   = None
    _right          = None
    _up             = None
    _plane_normal   = None
    _snap           = None
    _snap_hit       = None
    _snap_disabled  = False
    _number_input   = ""    # "width;height" numeric buffer (comma = decimal)

    # ── GPU preview (POST_VIEW) ───────────────────────────────────────────────

    def _draw_preview(self, context):
        try:
            corners = self._rect_corners
        except ReferenceError:
            global _rect_draw_handle
            if _rect_draw_handle is not None:
                bpy.types.SpaceView3D.draw_handler_remove(_rect_draw_handle, 'WINDOW')
                _rect_draw_handle = None
            return
        if not corners:
            return
        p1, p4, p2, p3 = corners
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        batch  = batch_for_shader(shader, 'LINES',
                                  {"pos": [p1, p4, p4, p2, p2, p3, p3, p1]})
        shader.bind()
        shader.uniform_float("color", (1.0, 0.6, 0.0, 0.8))
        gpu.state.line_width_set(1.5)
        gpu.state.blend_set('ALPHA')
        gpu.state.depth_test_set('NONE')
        batch.draw(shader)
        gpu.state.depth_test_set('LESS_EQUAL')
        gpu.state.blend_set('NONE')


    def _update_header(self, context):
        if self._first_pt is None:
            context.area.header_text_set(
                "Rectangle  |  click first corner  |  ESC cancel")
        else:
            val = self._number_input if self._number_input else "move mouse"
            context.area.header_text_set(
                f"Rectangle  |  W;H or move mouse: {val}  |  Enter/LMB confirm  |  ESC cancel")

    # ── Geometry ──────────────────────────────────────────────────────────────

    def _compute_corners(self, p1, p2):
        """Return (p1, p4, p2_proj, p3) projected onto the drawing plane."""
        d  = p2 - p1
        dx = d.dot(self._right)
        dy = d.dot(self._up)
        # Project p2 onto the plane so off-plane snap hits don't deform the rect.
        p2_proj = p1 + self._right * dx + self._up * dy
        return p1, p1 + self._right * dx, p2_proj, p1 + self._up * dy

    def _project(self, context, mouse_2d, depth_pt):
        return self.project_to_plane(context, mouse_2d,
                                     self._plane_normal, depth_pt,
                                     self._right, self._up)

    def _update_preview(self, context, mouse_2d):
        if self._first_pt is None:
            return
        raw_pt  = self._project(context, mouse_2d, self._first_pt)
        snapped = (self._snap.snap(mouse_2d, context,
                                   raw_world=raw_pt,
                                   origin_world=self._first_pt)
                   if self._snap and not self._snap_disabled else None)
        self._snap_hit  = snapped
        mouse_pt        = snapped if snapped is not None else raw_pt

        # Parse numeric input "width;height" and override mouse position.
        # Comma is treated as decimal separator (European locale).
        if self._number_input and self._right is not None:
            from ...Utils.mastro_cad.cad.cad_utils import safe_eval
            parts = self._number_input.split(';')
            def _eval(s): return safe_eval(s.strip().replace(',', '.')) if s.strip() else None
            w = _eval(parts[0])
            h = _eval(parts[1]) if len(parts) > 1 else None
            d  = mouse_pt - self._first_pt
            sx = 1 if d.dot(self._right) >= 0 else -1
            sy = 1 if d.dot(self._up)    >= 0 else -1
            dx = sx * abs(w) if w is not None else d.dot(self._right)
            dy = sy * abs(h) if h is not None else d.dot(self._up)
            mouse_pt = self._first_pt + self._right * dx + self._up * dy

        self._second_pt    = mouse_pt
        self._rect_corners = self._compute_corners(self._first_pt, self._second_pt)

    def _do_apply(self, context):
        if self._rect_corners is None:
            return
        p1, p4, p2, p3 = self._rect_corners
        self._apply_rectangle(context, [p1, p4, p2, p3])

    def _remove_draw_handler(self):
        global _rect_draw_handle
        self._remove_handlers()
        _rect_draw_handle = None

    # ── Modal ─────────────────────────────────────────────────────────────────

    def modal(self, context, event):
        try:
            return self._modal_impl(context, event)
        except ReferenceError:
            global _rect_draw_handle
            if _rect_draw_handle is not None:
                for h in _rect_draw_handle:
                    bpy.types.SpaceView3D.draw_handler_remove(h, 'WINDOW')
                _rect_draw_handle = None
            return {'CANCELLED'}

    def _modal_impl(self, context, event):
        if self.left_edit_mode(context, self._started_in_edit):
            self._remove_draw_handler()
            context.area.header_text_set(None)
            return {'CANCELLED'}
        nav = self.pass_through_navigation(event)
        if nav is not None:
            return nav
        mouse_2d = (event.mouse_region_x, event.mouse_region_y)
        if event.type in {'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE'}:
            self.maybe_rebuild_snap(context)
            self._snap_disabled = event.ctrl
            if self._first_pt is not None:
                self._update_preview(context, mouse_2d)
            else:
                raw_pt = self._project(context, mouse_2d, self.depth_reference(context))
                snapped = (self._snap.snap(mouse_2d, context, raw_world=raw_pt)
                           if self._snap and not self._snap_disabled else None)
                self._snap_hit = snapped
            context.area.tag_redraw()

        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            mouse_2d = (event.mouse_region_x, event.mouse_region_y)
            if self._first_pt is None:
                raw_pt = self._project(context, mouse_2d, self.depth_reference(context))
                snapped = self._snap.snap(mouse_2d, context) if self._snap else None
                self._first_pt = snapped if snapped is not None else raw_pt
                # Capture axes once while context is guaranteed to be the 3D view.
                rv3d            = context.space_data.region_3d
                self._right, self._up = self.orient_axes(context, rv3d)
                self._plane_normal = self._right.cross(self._up).normalized()
                self._snap_hit  = snapped
                self._update_preview(context, mouse_2d)
                self._number_input = ""
                self._update_header(context)
            else:
                # Use snapped position if available, else the last previewed point.
                self._second_pt    = self._snap_hit or self._second_pt
                self._rect_corners = self._compute_corners(self._first_pt, self._second_pt)
                self._remove_draw_handler()
                self._do_apply(context)
                context.area.header_text_set(None)
                return {'FINISHED'}

        elif event.value == 'PRESS' and self._first_pt is not None and self._right is not None:
            if event.type in RECT_CHAR_MAP:
                self._number_input += RECT_CHAR_MAP[event.type]
                self._update_preview(context, (event.mouse_region_x, event.mouse_region_y))
                self._update_header(context)
                context.area.tag_redraw()
            elif event.type == 'BACK_SPACE' and self._number_input:
                self._number_input = self._number_input[:-1]
                self._update_preview(context, (event.mouse_region_x, event.mouse_region_y))
                self._update_header(context)
                context.area.tag_redraw()

        if event.type in {'RET', 'NUMPAD_ENTER'} and event.value == 'PRESS' \
                and self._first_pt is not None and self._rect_corners is not None:
            self._remove_draw_handler()
            self._do_apply(context)
            context.area.header_text_set(None)
            return {'FINISHED'}

        if event.type in {'RIGHTMOUSE', 'ESC'} and event.value == 'PRESS':
            self._remove_draw_handler()
            context.area.header_text_set(None)
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self._started_in_edit = context.mode == 'EDIT_MESH'
        self._first_pt     = None
        self._second_pt    = None
        self._rect_corners = None
        self._snap_hit     = None
        self._number_input = ""
        self._snap         = SnapContext(context)

        global _rect_draw_handle
        _rect_draw_handle = self._register_handlers(context)

        context.area.header_text_set("Rectangle  |  click first corner  |  ESC cancel")
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
