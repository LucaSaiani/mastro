import bpy
from mathutils import Vector
import gpu
from gpu_extras.batch import batch_for_shader

from ...Utils.mastro_cad.cad.snap_utils import SnapContext
from .CAD_mixin import RectMixin, RECT_CHAR_MAP


class MESH_OT_MaStroCad_RectangleCenter(RectMixin, bpy.types.Operator):
    """Draw a rectangle by clicking the center then a corner.

    Click 1 — center
    Click 2 — corner  (or type W;H for exact half/full dimensions)
    H toggles half vs full dimension input mode.
    """
    bl_idname  = "mastrocad.rectangle_center"
    bl_label   = "Rectangle (Center)"
    bl_options = {'REGISTER', 'UNDO'}

    _draw_handle   = None
    _center        = None
    _right         = None
    _up            = None
    _plane_normal  = None
    _rect_corners  = None
    _snap          = None
    _snap_hit      = None
    _snap_disabled = False
    _number_input  = ""     # "w;h" — comma = decimal, semicolon = separator
    _half_mode     = True   # True = half-dimensions, False = full dimensions

    # ── GPU preview ───────────────────────────────────────────────────────────

    def _draw_preview(self, context):
        try:
            corners = self._rect_corners
        except ReferenceError:
            MESH_OT_MaStroCad_RectangleCenter._gc_cleanup()
            return
        if not corners:
            return
        a, b, c, d = corners
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        shader.bind()
        shader.uniform_float("color", (1.0, 0.6, 0.0, 0.8))
        gpu.state.line_width_set(1.5)
        gpu.state.blend_set('ALPHA')
        gpu.state.depth_test_set('NONE')
        batch_for_shader(shader, 'LINES',
                         {"pos": [a, b, b, c, c, d, d, a]}).draw(shader)
        gpu.state.depth_test_set('LESS_EQUAL')
        gpu.state.blend_set('NONE')

    # ── Header ────────────────────────────────────────────────────────────────

    def _update_header(self, context):
        if self._center is None:
            context.area.header_text_set(
                "Rectangle  |  click center  |  ESC cancel")
        else:
            half = "ON" if self._half_mode else "OFF"
            val  = self._number_input if self._number_input else "move mouse"
            context.area.header_text_set(
                f"Rectangle  |  W;H or move mouse: {val}"
                f"  |  H  Half: {half}  |  Enter/LMB confirm  |  ESC cancel")

    # ── Preview ───────────────────────────────────────────────────────────────

    def _update_preview(self, context, mouse_2d):
        if self._center is None:
            return
        raw_pt  = self.project_to_plane(context, mouse_2d, self._plane_normal,
                                         self._center, self._right, self._up)
        snapped = (self._snap.snap(mouse_2d, context, raw_world=raw_pt,
                                   origin_world=self._center)
                   if self._snap and not self._snap_disabled else None)
        self._snap_hit = snapped
        corner = snapped if snapped is not None else raw_pt

        d  = corner - self._center
        sx = 1 if d.dot(self._right) >= 0 else -1
        sy = 1 if d.dot(self._up)    >= 0 else -1

        parts = self._number_input.split(';')
        hw = self.eval_number(parts[0])
        hu = self.eval_number(parts[1]) if len(parts) > 1 else None
        div    = 1.0 if self._half_mode else 2.0
        half_w = sx * abs(hw) / div if hw is not None else d.dot(self._right)
        half_h = sy * abs(hu) / div if hu is not None else d.dot(self._up)

        c  = self._center
        r  = self._right * half_w
        u  = self._up    * half_h
        self._rect_corners = [c - r - u, c + r - u, c + r + u, c - r + u]

    # ── Modal ─────────────────────────────────────────────────────────────────

    def modal(self, context, event):
        if self.left_edit_mode(context, self._started_in_edit):
            self._remove_handlers()
            context.area.header_text_set(None)
            return {'CANCELLED'}
        nav = self.pass_through_navigation(event)
        if nav is not None:
            return nav
        mouse_2d = (event.mouse_region_x, event.mouse_region_y)

        if event.type in {'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE'}:
            self.maybe_rebuild_snap(context)
            self._snap_disabled = event.ctrl
            if self._center is not None:
                self._update_preview(context, mouse_2d)
            else:
                raw_pt = self.project_to_plane(
                    context, mouse_2d, None, self.depth_reference(context),
                    self._right, self._up)
                snapped = (self._snap.snap(mouse_2d, context, raw_world=raw_pt)
                           if self._snap and not self._snap_disabled else None)
                self._snap_hit = snapped
            context.area.tag_redraw()

        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            raw_pt  = self.project_to_plane(context, mouse_2d, self._plane_normal,
                                             self._center if self._center
                                             else self.depth_reference(context),
                                             self._right, self._up)
            snapped = (self._snap.snap(mouse_2d, context, raw_world=raw_pt)
                       if self._snap and not event.ctrl else None)
            pt = snapped if snapped is not None else raw_pt
            self._snap_hit = snapped

            if self._center is None:
                self._center = pt
                rv3d = context.space_data.region_3d
                self._right, self._up = self.orient_axes(context, rv3d)
                self._plane_normal    = self._right.cross(self._up).normalized()
                self._number_input    = ""
                self._update_header(context)
            else:
                self._update_preview(context, mouse_2d)
                self._remove_handlers()
                self._apply_rectangle(context, self._rect_corners)
                context.area.header_text_set(None)
                return {'FINISHED'}

            context.area.tag_redraw()

        elif event.value == 'PRESS' and self._center is not None:
            if event.type == 'H':
                self._half_mode = not self._half_mode
                self._update_preview(context, mouse_2d)
                self._update_header(context)
                context.area.tag_redraw()
            elif event.type in RECT_CHAR_MAP:
                self._number_input += RECT_CHAR_MAP[event.type]
                self._update_preview(context, mouse_2d)
                self._update_header(context)
                context.area.tag_redraw()
            elif event.type == 'BACK_SPACE' and self._number_input:
                self._number_input = self._number_input[:-1]
                self._update_preview(context, mouse_2d)
                self._update_header(context)
                context.area.tag_redraw()

        if event.type in {'RET', 'NUMPAD_ENTER'} and event.value == 'PRESS' \
                and self._rect_corners is not None:
            self._remove_handlers()
            self._apply_rectangle(context, self._rect_corners)
            context.area.header_text_set(None)
            return {'FINISHED'}

        if event.type in {'RIGHTMOUSE', 'ESC'} and event.value == 'PRESS':
            self._remove_handlers()
            context.area.header_text_set(None)
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self._started_in_edit = context.mode == 'EDIT_MESH'
        self._center        = None
        self._right         = None
        self._up            = None
        self._plane_normal  = None
        self._rect_corners  = None
        self._snap_hit      = None
        self._snap_disabled = False
        self._number_input  = ""
        self._half_mode     = True
        self._snap          = SnapContext(context)

        self._register_handlers(context)

        self._update_header(context)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
