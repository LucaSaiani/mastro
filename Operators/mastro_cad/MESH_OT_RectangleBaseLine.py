import bpy
from mathutils import Vector
import gpu
from gpu_extras.batch import batch_for_shader

from ...Utils.mastro_cad.cad.snap_utils import SnapContext
from .CAD_mixin import RectMixin, RECT_CHAR_MAP


class MESH_OT_MaStroCad_RectangleBaseLine(RectMixin, bpy.types.Operator):
    """Draw a rectangle by defining a base line then the width.

    Click 1 — base line start
    Click 2 — base line end  (sets rectangle X axis)
    Click 3 — width          (perpendicular to base line; sign follows mouse)
    """
    bl_idname  = "mastrocad.rectangle_baseline"
    bl_label   = "Rectangle (Base Line)"
    bl_options = {'REGISTER', 'UNDO'}

    _draw_handle   = None
    _p1            = None
    _p2            = None
    _mouse_pt      = None   # live mouse position for base-line preview
    _plane_normal  = None
    _base_dir      = None
    _perp          = None
    _corners       = None
    _snap          = None
    _snap_hit      = None
    _snap_disabled = False
    _number_input  = ""     # typed length (phase 1→2) or width (phase 2→3)

    # ── GPU preview ───────────────────────────────────────────────────────────

    def _draw_preview(self, context):
        try:
            corners  = self._corners
            p1       = self._p1
            mouse_pt = self._mouse_pt
        except ReferenceError:
            MESH_OT_MaStroCad_RectangleBaseLine._gc_cleanup()
            return

        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        shader.bind()
        gpu.state.blend_set('ALPHA')
        gpu.state.depth_test_set('NONE')
        gpu.state.line_width_set(1.5)
        shader.uniform_float("color", (1.0, 0.6, 0.0, 0.8))

        if corners:
            a, b, c, d = corners
            batch_for_shader(shader, 'LINES',
                             {"pos": [a, b, b, c, c, d, d, a]}).draw(shader)
        elif p1 and mouse_pt:
            batch_for_shader(shader, 'LINES',
                             {"pos": [p1, mouse_pt]}).draw(shader)

        gpu.state.depth_test_set('LESS_EQUAL')
        gpu.state.blend_set('NONE')

    # ── Header ────────────────────────────────────────────────────────────────

    def _update_header(self, context):
        val = self._number_input if self._number_input else "move mouse"
        if self._p1 is None:
            context.area.header_text_set(
                "Rectangle  |  click base line start  |  ESC cancel")
        elif self._p2 is None:
            context.area.header_text_set(
                f"Rectangle  |  Length: {val}  |  click base line end  |  ESC cancel")
        else:
            context.area.header_text_set(
                f"Rectangle  |  Width: {val}  |  click to confirm  |  ESC cancel")

    # ── Preview ───────────────────────────────────────────────────────────────

    def _update_preview(self, context, mouse_2d):
        if self._p2 is None:
            return
        raw_pt     = self.project_to_plane(context, mouse_2d, self._plane_normal, self._p1)
        snapped    = (self._snap.snap(mouse_2d, context, raw_world=raw_pt,
                                      origin_world=self._p1)
                      if self._snap and not self._snap_disabled else None)
        self._snap_hit = snapped
        mouse_3d   = snapped if snapped is not None else raw_pt
        mouse_proj = (mouse_3d - self._p1).dot(self._perp)
        num        = self.eval_number(self._number_input)
        if num is not None:
            sign  = 1 if mouse_proj >= 0 else -1
            width = sign * abs(num)
        else:
            width = mouse_proj
        self._corners = [self._p1,
                         self._p2,
                         self._p2 + self._perp * width,
                         self._p1 + self._perp * width]

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
            if self._p1 is None:
                raw_pt = self.project_to_plane(
                    context, mouse_2d, None, self.depth_reference(context))
                snapped = (self._snap.snap(mouse_2d, context, raw_world=raw_pt)
                           if self._snap and not self._snap_disabled else None)
                self._snap_hit = snapped
            elif self._p2 is None:
                raw_pt  = self.project_to_plane(context, mouse_2d,
                                                self._plane_normal, self._p1)
                snapped = (self._snap.snap(mouse_2d, context, raw_world=raw_pt,
                                           origin_world=self._p1)
                           if self._snap and not event.ctrl else None)
                # Project snap hit onto drawing plane (snap may be on a different Z).
                if snapped is not None:
                    _d = snapped - self._p1
                    snapped = snapped - self._plane_normal * _d.dot(self._plane_normal)
                self._snap_hit = snapped
                pt = snapped if snapped is not None else raw_pt
                num = self.eval_number(self._number_input)
                if num is not None:
                    d = pt - self._p1
                    if d.length > 1e-8:
                        self._mouse_pt = self._p1 + d.normalized() * num
                else:
                    self._mouse_pt = pt
                self._corners = None
            elif self._p2 is not None:
                self._update_preview(context, mouse_2d)
            context.area.tag_redraw()

        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            raw_pt  = self.project_to_plane(context, mouse_2d, self._plane_normal,
                                             self._p1 if self._p1 else self.depth_reference(context))
            snapped = (self._snap.snap(mouse_2d, context, raw_world=raw_pt,
                                       origin_world=self._p1)
                       if self._snap and not event.ctrl else None)
            pt = snapped if snapped is not None else raw_pt
            self._snap_hit = snapped

            if self._p1 is None:
                self._p1           = pt
                self._plane_normal = self.get_plane_normal(
                    context, context.space_data.region_3d)
                self._number_input = ""
                self._update_header(context)

            elif self._p2 is None:
                confirmed = self._mouse_pt if self._mouse_pt else pt
                if (confirmed - self._p1).length < 1e-6:
                    return {'RUNNING_MODAL'}
                self._p2       = confirmed
                self._base_dir = (self._p2 - self._p1).normalized()
                self._perp     = self._plane_normal.cross(self._base_dir).normalized()
                self._number_input = ""
                self._update_header(context)

            else:
                self._update_preview(context, mouse_2d)
                self._remove_handlers()
                self._apply_rectangle(context, self._corners)
                context.area.header_text_set(None)
                return {'FINISHED'}

            context.area.tag_redraw()

        elif event.value == 'PRESS' and self._p1 is not None:
            if event.type in RECT_CHAR_MAP:
                self._number_input += RECT_CHAR_MAP[event.type]
                if self._p2 is not None:
                    self._update_preview(context, mouse_2d)
                self._update_header(context)
                context.area.tag_redraw()
            elif event.type == 'BACK_SPACE' and self._number_input:
                self._number_input = self._number_input[:-1]
                if self._p2 is not None:
                    self._update_preview(context, mouse_2d)
                self._update_header(context)
                context.area.tag_redraw()

        if event.type in {'RET', 'NUMPAD_ENTER'} and event.value == 'PRESS' \
                and self._corners is not None:
            self._remove_handlers()
            self._apply_rectangle(context, self._corners)
            context.area.header_text_set(None)
            return {'FINISHED'}

        if event.type in {'RIGHTMOUSE', 'ESC'} and event.value == 'PRESS':
            self._remove_handlers()
            context.area.header_text_set(None)
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self._started_in_edit = context.mode == 'EDIT_MESH'
        self._p1            = None
        self._p2            = None
        self._mouse_pt      = None
        self._plane_normal  = None
        self._base_dir      = None
        self._perp          = None
        self._corners       = None
        self._snap_hit      = None
        self._snap_disabled = False
        self._number_input  = ""
        self._snap          = SnapContext(context)

        self._register_handlers(context)

        self._update_header(context)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
