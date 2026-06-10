import bpy
import bmesh
from bpy_extras.view3d_utils import (region_2d_to_location_3d,
                                     location_3d_to_region_2d,
                                     region_2d_to_origin_3d,
                                     region_2d_to_vector_3d)
import gpu
from gpu_extras.batch import batch_for_shader

from ...Utils.mastro_cad.cad.rect_utils import (check_rect, rect_local_axes,
                                     compute_new_corners, HANDLE_SIZE_PX)
from ...Utils.mastro_cad.cad.constants  import HANDLE_GRAB_RADIUS_PX
from ...Utils.mastro_cad.cad.snap_utils import SnapContext
from .CAD_mixin import CadMixin

_rect_edit_draw_handle = None


def _screen_dist(co_2d, pt_world, rv3d, region):
    pt_2d = location_3d_to_region_2d(region, rv3d, pt_world)
    if pt_2d is None:
        return float('inf')
    dx, dy = co_2d[0] - pt_2d[0], co_2d[1] - pt_2d[1]
    return (dx*dx + dy*dy) ** 0.5


class MESH_OT_MaStroCad_EditRectangle(CadMixin, bpy.types.Operator):
    """Edit a tagged rectangle by dragging its diagonal handles.

    Invoked with Alt+G when a rectangle edge/vertex is active.
    Grabs the nearest handle immediately, hides the mesh geometry and
    shows a GPU-only preview while dragging.  Click to confirm, ESC to cancel.
    """
    bl_idname  = "mastrocad.edit_rectangle"
    bl_label   = "Edit Rectangle"
    bl_options = {'REGISTER', 'UNDO'}

    _draw_handle  = None
    _corners      = None   # [p0,p1,p2,p3] world Vectors — live preview
    _grabbed_idx  = None   # which handle (0-3) is grabbed
    _x_axis       = None   # rectangle local axes in world space
    _y_axis       = None
    _normal       = None
    _plane_pt     = None   # point on rectangle plane for ray cast
    _vert_indices    = None   # stored as indices (bmesh refs are invalidated by ops)
    _edge_indices    = None
    _vert_sel_saved  = None   # {idx: bool} selection state at invoke
    _edge_sel_saved  = None
    _active_idx      = None   # index of select_history.active at invoke
    _active_is_edge  = False
    _snap            = None
    _snap_hit        = None

    # ── GPU preview ───────────────────────────────────────────────────────────

    def _draw_outline(self, context):
        """POST_VIEW — rectangle outline."""
        try:
            corners = self._corners
        except ReferenceError:
            return
        if not corners or context.region_data is None:
            return
        p0, p1, p2, p3 = corners
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        batch  = batch_for_shader(shader, 'LINES',
                                  {"pos": [p0, p1, p1, p2, p2, p3, p3, p0]})
        shader.bind()
        shader.uniform_float("color", (1.0, 0.6, 0.0, 0.8))
        gpu.state.line_width_set(1.5)
        gpu.state.blend_set('ALPHA')
        gpu.state.depth_test_set('NONE')
        batch.draw(shader)
        gpu.state.depth_test_set('LESS_EQUAL')
        gpu.state.blend_set('NONE')

    def _draw_handles(self, context):
        """POST_PIXEL — hollow handle squares; snap indicator replaces grabbed one."""
        try:
            corners  = self._corners
            snap_hit = self._snap_hit
        except ReferenceError:
            return
        if not corners:
            return
        rv3d   = context.region_data
        region = context.region
        if rv3d is None:
            return
        shader   = gpu.shader.from_builtin('UNIFORM_COLOR')
        shader.bind()
        gpu.state.blend_set('ALPHA')
        s        = HANDLE_SIZE_PX
        snapping = snap_hit is not None

        for i in range(4):
            if snapping and i == self._grabbed_idx:
                continue   # snap indicator takes over this position
            co_2d = location_3d_to_region_2d(region, rv3d, corners[i])
            if co_2d is None:
                continue
            x, y    = co_2d
            verts   = [(x-s,y-s),(x+s,y-s),(x+s,y+s),(x-s,y+s)]
            indices = ((0,1),(1,2),(2,3),(3,0))
            batch   = batch_for_shader(shader, 'LINES',
                                       {"pos": verts}, indices=indices)
            shader.uniform_float("color", (1.0, 0.6, 0.0, 1.0))
            batch.draw(shader)

        if snapping and self._snap is not None:
            self._snap.draw_indicator(snap_hit, context)

        gpu.state.blend_set('NONE')

    # ── Plane projection ──────────────────────────────────────────────────────

    def _mouse_on_plane(self, context, mouse_2d):
        rv3d   = context.region_data
        region = context.region
        if rv3d is None or region is None:
            return None
        ray_o = region_2d_to_origin_3d(region, rv3d, mouse_2d)
        ray_d = region_2d_to_vector_3d(region, rv3d, mouse_2d)
        denom = ray_d.dot(self._normal)
        if abs(denom) > 1e-8:
            t = (self._plane_pt.dot(self._normal) - ray_o.dot(self._normal)) / denom
            return ray_o + ray_d * t
        return region_2d_to_location_3d(region, rv3d, mouse_2d, self._plane_pt)

    # ── Mesh helpers ──────────────────────────────────────────────────────────

    def _set_hidden(self, obj, hidden, context=None):
        self.set_geometry_hidden(obj, self._vert_indices, self._edge_indices, hidden)
        if hidden and context is not None:
            self._snap = SnapContext(context, select_modes=('VERT',))

    def _apply(self, context):
        if not self._corners or not self._vert_indices:
            return
        obj    = context.active_object
        bm     = bmesh.from_edit_mesh(obj.data)
        mw_inv = obj.matrix_world.inverted()
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        for idx, pt in zip(self._vert_indices, self._corners):
            v = bm.verts[idx]
            v.hide_set(False)
            v.co     = mw_inv @ pt
            v.select = self._vert_sel_saved.get(idx, False)
        for idx in self._edge_indices:
            e = bm.edges[idx]
            e.hide_set(False)
            e.select = self._edge_sel_saved.get(idx, False)

        # Restore active element.
        if self._active_idx is not None:
            if self._active_is_edge:
                bm.select_history.add(bm.edges[self._active_idx])
            else:
                bm.select_history.add(bm.verts[self._active_idx])

        bmesh.update_edit_mesh(obj.data)

    def _remove_handlers(self):
        global _rect_edit_draw_handle
        if self._draw_handle is not None:
            for h in self._draw_handle:
                bpy.types.SpaceView3D.draw_handler_remove(h, 'WINDOW')
            self._draw_handle      = None
            _rect_edit_draw_handle = None

    def _tag_redraw(self, context):
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

    # ── Modal ─────────────────────────────────────────────────────────────────

    def modal(self, context, event):
        if self.left_edit_mode(context, self._started_in_edit):
            if self._grabbed_idx is not None:
                self._set_hidden(context.active_object, False)
            self._remove_handlers()
            context.area.header_text_set(None)
            self.clear_status(context)
            return {'CANCELLED'}
        nav = self.pass_through_navigation(event)
        if nav is not None:
            return nav

        mouse_2d = (event.mouse_region_x, event.mouse_region_y)

        if event.type in {'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE'}:
            if self._grabbed_idx is not None:
                raw_pt  = self._mouse_on_plane(context, mouse_2d)
                snapped = (self._snap.snap(mouse_2d, context,
                                           raw_world=raw_pt,
                                           origin_world=self._plane_pt)
                           if self._snap and not event.ctrl else None)
                self._snap_hit = snapped
                p_new = snapped if snapped is not None else raw_pt
                if p_new is not None:
                    gi    = self._grabbed_idx
                    fixed = self._corners[(gi + 2) % 4]
                    new_c = compute_new_corners(p_new, fixed, self._x_axis, self._y_axis)
                    rot   = (4 - gi) % 4
                    self._corners = new_c[rot:] + new_c[:rot]
                self._tag_redraw(context)

        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            if self._grabbed_idx is None:
                rv3d  = context.region_data
                dists = [_screen_dist(mouse_2d, self._corners[i], rv3d, context.region)
                         for i in range(4)]
                if min(dists) > HANDLE_GRAB_RADIUS_PX:
                    self._remove_handlers()
                    context.area.header_text_set(None)
                    self.clear_status(context)
                    return {'FINISHED'}
                self._grabbed_idx = dists.index(min(dists))
                self._set_hidden(context.active_object, True, context)
                context.view_layer.update()
                context.area.header_text_set(
                    "Edit Rectangle  |  move mouse  |  LMB confirm  |  ESC cancel")
            else:
                self._apply(context)
                self._remove_handlers()
                context.area.header_text_set(None)
                self.clear_status(context)
                return {'FINISHED'}
            self._tag_redraw(context)

        elif event.type in {'RIGHTMOUSE', 'ESC'} and event.value == 'PRESS':
            if self._grabbed_idx is not None:
                self._set_hidden(context.active_object, False)
            self._remove_handlers()
            context.area.header_text_set(None)
            self.clear_status(context)
            return {'FINISHED'}

        return {'RUNNING_MODAL'}

    # ── Setup ─────────────────────────────────────────────────────────────────

    @classmethod
    def poll(cls, context):
        return (super().poll(context)
                and context.mode == 'EDIT_MESH'
                and context.active_object is not None)

    def invoke(self, context, event):
        self._started_in_edit = context.mode == 'EDIT_MESH'
        obj = context.active_object
        bm  = bmesh.from_edit_mesh(obj.data)

        active = self.active_seed(bm)
        if active is None:
            self.report({'WARNING'}, "Select an edge or vertex first")
            return {'CANCELLED'}

        ok, chain_verts, chain_edges = check_rect(bm, active)
        if not ok:
            return {'CANCELLED'}

        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        self._vert_indices = [v.index for v in chain_verts]
        self._edge_indices = [e.index for e in chain_edges]

        # Save selection state to restore after apply.
        self._vert_sel_saved = {v.index: v.select for v in chain_verts}
        self._edge_sel_saved = {e.index: e.select for e in chain_edges}
        active_el = bm.select_history.active
        if isinstance(active_el, bmesh.types.BMVert) and active_el in chain_verts:
            self._active_idx     = active_el.index
            self._active_is_edge = False
        elif isinstance(active_el, bmesh.types.BMEdge) and active_el in chain_edges:
            self._active_idx     = active_el.index
            self._active_is_edge = True
        else:
            self._active_idx = None

        mw = obj.matrix_world
        self._x_axis, self._y_axis, self._normal = rect_local_axes(chain_verts, mw)
        self._plane_pt = mw @ chain_verts[0].co
        self._corners  = [mw @ v.co for v in chain_verts]
        self._snap_hit = None
        self._snap     = SnapContext(context, select_modes=('VERT',))

        # Grab nearest handle immediately (Blender-style: key → action).
        rv3d     = context.region_data
        mouse_2d = (event.mouse_region_x, event.mouse_region_y)
        dists    = [_screen_dist(mouse_2d, self._corners[i], rv3d, context.region)
                    for i in range(4)]
        self._grabbed_idx = dists.index(min(dists))
        self._set_hidden(obj, True, context)
        context.view_layer.update()

        global _rect_edit_draw_handle
        h3d = bpy.types.SpaceView3D.draw_handler_add(
            self._draw_outline, (context,), 'WINDOW', 'POST_VIEW')
        h2d = bpy.types.SpaceView3D.draw_handler_add(
            self._draw_handles, (context,), 'WINDOW', 'POST_PIXEL')
        self._draw_handle      = (h3d, h2d)
        _rect_edit_draw_handle = self._draw_handle

        context.area.header_text_set(
            "Edit Rectangle  |  move mouse  |  LMB confirm  |  ESC cancel")
        self.set_status(context,
            mouse=[("Confirm", 'MOUSE_LMB'), None, ("Cancel", 'MOUSE_RMB')],
            alt_keys=[("Edit Rectangle", 'EVENT_G')],
        )
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
