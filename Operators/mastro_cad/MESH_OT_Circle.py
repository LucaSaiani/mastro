"""Circle creation operator — centro + raggio.

Click 1 : center (with snap)
Move    : radius preview; segments shown as a closed polyline
Click 2 : confirm
Enter   : confirm
ESC     : cancel

Wheel ↑↓  : increase / decrease segment count (min 3, max 256)
Tab        : cycle snap target — VERTEX (vertices on circle) ↔ MIDPOINT
             (edge midpoints on circle, vertices slightly outside — useful for
             regular polygons where you want a given inscribed radius)
Ctrl       : disable snap while held
Digits/,/. : numeric radius input (comma = decimal separator, European locale)
Backspace  : delete last character
"""

import bpy
import bmesh
import math
from mathutils import Vector
import gpu
from gpu_extras.batch import batch_for_shader
from bpy_extras.view3d_utils import (region_2d_to_location_3d,
                                     location_3d_to_region_2d)

from ...Utils.mastro_cad.cad.cad_utils import assign_drawing_layer_to_edges
from ...Utils.mastro_cad.cad.circle_utils import (ensure_circle_layers, set_circle_attrs,
                                       circle_points)
from ...Utils.mastro_cad.cad.snap_utils import SnapContext
from .CAD_mixin import CadMixin, CAD_CHAR_MAP
from ...Utils.mastro_cad.cad.gpu_utils import draw_dotted_line

_circle_draw_handle = None   # GC-safe module-level reference


class MESH_OT_MaStroCad_Circle(CadMixin, bpy.types.Operator):
    """Draw a circle by clicking the center then dragging the radius.

    Works in both Edit Mode (adds geometry to the active mesh) and Object Mode
    (creates a new mesh object). The circle lies on the view plane at the depth
    of the first click, respecting the active transform orientation.
    """
    bl_idname  = "mastrocad.circle"
    bl_label   = "Circle"
    bl_options = {'REGISTER', 'UNDO'}

    _draw_handle   = None
    _center        = None       # world Vector
    _right         = None       # circle-plane X axis (world)
    _up            = None       # circle-plane Y axis (world)
    _plane_normal  = None
    _radius        = 0.0
    _segments      = 16
    _preview_pts   = None       # list of world Vectors (closed loop preview)
    _ref_pt        = None       # effective mouse target (snap or raw)
    _snap          = None
    _snap_hit      = None
    _snap_disabled = False
    _snap_target   = 'VERTEX'   # 'VERTEX' or 'MIDPOINT'
    _number_input  = ""         # raw numeric buffer for radius

    # ── GPU preview (POST_VIEW) ───────────────────────────────────────────────

    def _draw_preview(self, context):
        try:
            pts = self._preview_pts
            ref = self._ref_pt
            cen = self._center
        except ReferenceError:
            MESH_OT_MaStroCad_Circle._gc_cleanup()
            return
        if not pts:
            return

        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        shader.bind()
        gpu.state.blend_set('ALPHA')
        gpu.state.depth_test_set('NONE')

        # Circle outline (closed polyline).
        n    = len(pts)
        segs = []
        for i in range(n):
            segs.extend([pts[i], pts[(i + 1) % n]])
        gpu.state.line_width_set(1.5)
        shader.uniform_float("color", (1.0, 0.6, 0.0, 0.8))
        batch_for_shader(shader, 'LINES', {"pos": segs}).draw(shader)

        # Dotted radius line from center to current reference point.
        if cen is not None and ref is not None:
            draw_dotted_line(cen, ref, context)

        gpu.state.depth_test_set('LESS_EQUAL')
        gpu.state.blend_set('NONE')

    # ── Header + footer ───────────────────────────────────────────────────────

    def _update_header(self, context, modifier=None):
        if self._center is None:
            context.area.header_text_set("Circle  |  Click center")
            self.set_status(context, modifier,
                mouse=[("Set center", 'MOUSE_LMB'), None, ("Cancel", 'MOUSE_RMB')],
            )
        else:
            r_str   = self._number_input if self._number_input else f"{self._radius:.4f}"
            tgt_lbl = "Vertex" if self._snap_target == 'VERTEX' else "Edge Midpoint"
            context.area.header_text_set(
                f"Circle  |  R: {r_str}  |  Segments: {self._segments}  |  {tgt_lbl}")
            self.set_status(context, modifier,
                mouse=[("Confirm", 'MOUSE_LMB'), None, ("Cancel", 'MOUSE_RMB')],
                ctrl_mouse=[("Resolution", 'MOUSE_MMB_SCROLL')],
                keys=[(f"Reference ({tgt_lbl})", 'EVENT_Q')],
            )

    # ── Preview update ────────────────────────────────────────────────────────

    def _update_preview(self, context, mouse_2d):
        if self._center is None:
            return

        raw_pt  = self.project_to_plane(context, mouse_2d, self._plane_normal,
                                         self._center, self._right, self._up)
        snapped = (self._snap.snap(mouse_2d, context,
                                   raw_world=raw_pt,
                                   origin_world=self._center,
                                   perp_center=self._center)
                   if self._snap and not self._snap_disabled else None)
        ref_world = snapped if snapped is not None else raw_pt

        # Project ref_world onto the drawing plane via right/up decomposition.
        # This ensures correct radius even when the snap point lies off-plane
        # (e.g. snapping to geometry on a different Z level in perspective view).
        d  = ref_world - self._center
        dx = d.dot(self._right)
        dy = d.dot(self._up)
        mouse_angle = math.atan2(dy, dx)

        # Radius: override with numeric input when present.
        if self._number_input:
            r = self.eval_number(self._number_input)
            if r is not None:
                self._radius = abs(r)
        else:
            self._radius = math.sqrt(dx * dx + dy * dy)

        # ref_pt: the anchor point in the mouse direction, ON the drawing plane.
        # Vertex mode  → this IS vertex 0  (line goes to a vertex).
        # Midpoint mode → this IS midpoint 0 (line goes to edge centre).
        self._ref_pt = (self._center
                        + self._right * math.cos(mouse_angle) * self._radius
                        + self._up    * math.sin(mouse_angle) * self._radius)

        # snap_hit drives the snap indicator — use the plane-projected ref_pt so
        # the indicator draws at the same screen position as the circle geometry,
        # also in perspective view where the raw snap point may be off-plane.
        self._snap_hit = self._ref_pt if snapped is not None else None

        # Phase: how the polygon is rotated.
        # Vertex mode  → vertex 0 at mouse_angle.
        # Midpoint mode→ midpoint of edge 0 at mouse_angle, so vertex 0 is π/n earlier.
        if self._snap_target == 'VERTEX':
            phase        = mouse_angle
            vertex_r     = self._radius
        else:
            phase        = mouse_angle - math.pi / self._segments
            # Compensate: if midpoints must sit at _radius from centre, vertices
            # must be farther out by 1/cos(π/n).
            vertex_r     = self._radius / math.cos(math.pi / self._segments)

        self._preview_pts = circle_points(
            self._center, vertex_r, self._segments,
            self._right, self._up, phase=phase)

        self._update_header(context)

    # ── Apply: write geometry to mesh ────────────────────────────────────────

    def _apply_circle(self, context):
        if not self._preview_pts or self._radius < 1e-8:
            return
        pts = self._preview_pts
        n   = len(pts)

        if context.mode == 'EDIT_MESH' and context.active_object:
            obj     = context.active_object
            bm      = bmesh.from_edit_mesh(obj.data)
            mw_inv  = obj.matrix_world.inverted()
            # Layers BEFORE geometry (new layer invalidates all refs).
            layers = ensure_circle_layers(bm)
            verts = [bm.verts.new(mw_inv @ p) for p in pts]
            edges = []
            for i in range(n):
                e = bm.edges.new((verts[i], verts[(i + 1) % n]))
                e.select = True
                edges.append(e)
            set_circle_attrs(bm, verts, edges, n, layers=layers)
            assign_drawing_layer_to_edges(context, obj, bm, edges)
            bmesh.update_edit_mesh(obj.data)
        else:
            center    = self._center
            local_pts = [p - center for p in pts]
            bm        = bmesh.new()
            layers    = ensure_circle_layers(bm)
            verts     = [bm.verts.new(p) for p in local_pts]
            edges     = [bm.edges.new((verts[i], verts[(i + 1) % n]))
                         for i in range(n)]
            set_circle_attrs(bm, verts, edges, n, layers=layers)
            mesh             = bpy.data.meshes.new("Circle")
            bm.to_mesh(mesh)
            bm.free()
            new_obj          = bpy.data.objects.new("Circle", mesh)
            new_obj.location = center
            context.collection.objects.link(new_obj)
            context.view_layer.objects.active = new_obj
            new_obj.select_set(True)

    def _remove_draw_handler(self, context=None):
        global _circle_draw_handle
        self._remove_handlers()
        _circle_draw_handle = None
        if context is not None:
            self.clear_status(context)

    # ── Modal ─────────────────────────────────────────────────────────────────

    def modal(self, context, event):
        try:
            return self._modal_impl(context, event)
        except ReferenceError:
            global _circle_draw_handle
            if _circle_draw_handle is not None:
                for h in _circle_draw_handle:
                    bpy.types.SpaceView3D.draw_handler_remove(h, 'WINDOW')
                _circle_draw_handle = None
            return {'CANCELLED'}

    def _modal_impl(self, context, event):
        if self.left_edit_mode(context, self._started_in_edit):
            self._remove_draw_handler(context)
            context.area.header_text_set(None)
            return {'CANCELLED'}
        nav = self.pass_through_navigation(event)
        if nav is not None:
            return nav
        mouse_2d = (event.mouse_region_x, event.mouse_region_y)
        modifier = self.modifier_from_event(event)

        if event.alt:
            self._update_header(context, modifier)
            return {'PASS_THROUGH'}

        if event.type in {'LEFT_CTRL', 'RIGHT_CTRL',
                          'LEFT_SHIFT', 'RIGHT_SHIFT'}:
            self._update_header(context, modifier)
            return {'RUNNING_MODAL'}

        if event.type in {'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE'}:
            self.maybe_rebuild_snap(context)
            self._snap_disabled = event.ctrl
            if self._center is not None:
                self._update_preview(context, mouse_2d)
            else:
                raw_pt = self.project_to_plane(
                    context, mouse_2d, None, self.depth_reference(context), None, None)
                snapped = (self._snap.snap(mouse_2d, context, raw_world=raw_pt)
                           if self._snap and not self._snap_disabled else None)
                self._snap_hit = snapped
            context.area.tag_redraw()

        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            if self._center is None:
                # First click — set center.
                raw_pt  = self.project_to_plane(
                    context, mouse_2d, None, self.depth_reference(context), None, None)
                snapped = (self._snap.snap(mouse_2d, context, raw_world=raw_pt)
                           if self._snap and not event.ctrl else None)
                self._center       = snapped if snapped is not None else raw_pt
                self._snap_hit     = snapped
                rv3d               = context.space_data.region_3d
                self._right, self._up = self.orient_axes(context, rv3d)
                self._plane_normal = self._right.cross(self._up).normalized()
                self._number_input = ""
                self._update_preview(context, mouse_2d)
                context.area.tag_redraw()
            else:
                # Second click — confirm.
                self._update_preview(context, mouse_2d)
                self._remove_draw_handler(context)
                self._apply_circle(context)
                context.area.header_text_set(None)
                return {'FINISHED'}

        elif event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE'} and event.value == 'PRESS':
            if event.ctrl and self._center is not None:
                self._segments = (min(self._segments + 1, 256)
                                  if event.type == 'WHEELUPMOUSE'
                                  else max(self._segments - 1, 3))
                self._update_preview(context, mouse_2d)
                context.area.tag_redraw()
            else:
                return {'PASS_THROUGH'}

        elif event.value == 'PRESS' and self._center is not None:
            if event.type == 'Q':
                self._snap_target = ('MIDPOINT' if self._snap_target == 'VERTEX'
                                     else 'VERTEX')
                self._update_preview(context, mouse_2d)
                context.area.tag_redraw()
            elif event.type in CAD_CHAR_MAP:
                self._number_input += CAD_CHAR_MAP[event.type]
                self._update_preview(context, mouse_2d)
                context.area.tag_redraw()
            elif event.type == 'BACK_SPACE' and self._number_input:
                self._number_input = self._number_input[:-1]
                self._update_preview(context, mouse_2d)
                context.area.tag_redraw()

        if (event.type in {'RET', 'NUMPAD_ENTER'} and event.value == 'PRESS'
                and self._center is not None and self._preview_pts):
            self._remove_draw_handler()
            self._apply_circle(context)
            context.area.header_text_set(None)
            return {'FINISHED'}

        if event.type in {'RIGHTMOUSE', 'ESC'} and event.value == 'PRESS':
            self._remove_draw_handler(context)
            context.area.header_text_set(None)
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self._started_in_edit = context.mode == 'EDIT_MESH'
        self._center        = None
        self._right         = None
        self._up            = None
        self._plane_normal  = None
        self._radius        = 0.0
        self._segments      = 16
        self._preview_pts   = None
        self._ref_pt        = None
        self._snap_hit      = None
        self._snap_disabled = False
        self._snap_target   = 'VERTEX'
        self._number_input  = ""
        # select_modes=() means snap is active regardless of current select mode,
        # so the circle can snap to other objects in any edit context.
        self._snap          = SnapContext(context, select_modes=())

        global _circle_draw_handle
        _circle_draw_handle = self._register_handlers(context)

        self._update_header(context)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
