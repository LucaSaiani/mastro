"""Trim/extend selected edges to the active (knife) edge.

The active edge is the knife (cutting reference). All other selected edges
are candidates: edges that intersect the knife are trimmed or extended to
meet it; the part on the mouse-click side is kept.

  CROSS  : candidate physically crosses the knife line → split at intersection,
           discard the part on the opposite side from the mouse.
  EXTEND : candidate is entirely on one side of the knife line → extend the
           nearest endpoint to reach the knife (only if on the mouse side).

Controls:
  LMB       : confirm
  RMB / ESC : cancel
  I         : toggle infinite knife (knife line extends beyond its endpoints)
  C         : toggle coplanar-only (3D intersection) vs screen projection (apparent)
"""

import bpy
import bmesh
from bpy_extras.view3d_utils import location_3d_to_region_2d
import gpu
from gpu_extras.batch import batch_for_shader

from ...Utils.mastro_cad.cad.cad_utils import (compute_trim_candidates, signed_dist_2d,
                                    copy_bm_edge_attrs, copy_bm_vert_attrs)
from ...Utils.mastro_cad.cad.gpu_utils import draw_dotted_line
from .CAD_mixin             import CadMixin

_trim_draw_handle = None


class MESH_OT_MaStroCad_Trim(CadMixin, bpy.types.Operator):
    """Trim or extend selected edges to the active (knife) edge."""
    bl_idname  = "mastrocad.trim"
    bl_label   = "Trim / Extend"
    bl_options = {'REGISTER', 'UNDO'}

    infinite_knife: bpy.props.BoolProperty(
        name="Infinite Knife",
        description="Extend the knife edge to an infinite line",
        default=False,
    )
    coplanar_only: bpy.props.BoolProperty(
        name="Coplanar Only",
        description="Only trim edges that are truly coplanar with the knife. "
                    "Off: use screen-space projection (apparent intersections in the viewport)",
        default=True,
    )

    # ── Modal state ───────────────────────────────────────────────────────────
    _draw_handle    = None
    _knife_world    = None   # (v0_world, v1_world) world-space endpoints of knife
    _knife_2d       = None   # (v0_2d, v1_2d) screen-space endpoints of knife
    _candidates_raw = None   # raw input list; preserved to allow recompute on toggle
    _candidates     = None   # list of candidate dicts from compute_trim_candidates
    _mouse_side     = 1      # +1 or -1: which side of the knife line the mouse is on
    _preview        = None   # dict with 'keep', 'remove', 'extend' segment lists

    # ── Poll ──────────────────────────────────────────────────────────────────

    @classmethod
    def poll(cls, context):
        if not CadMixin.poll(context):
            return False
        return (context.mode == 'EDIT_MESH'
                and context.active_object is not None)

    # ── GPU draw ──────────────────────────────────────────────────────────────

    def _draw_preview(self, context):
        try:
            preview = self._preview
            knife   = self._knife_world
        except ReferenceError:
            # Operator was GC'd while the handler is still registered.
            global _trim_draw_handle
            if _trim_draw_handle is not None:
                for h in _trim_draw_handle:
                    try:
                        bpy.types.SpaceView3D.draw_handler_remove(h, 'WINDOW')
                    except Exception:
                        pass
                _trim_draw_handle = None
            return

        if knife is None:
            return

        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        shader.bind()
        gpu.state.blend_set('ALPHA')
        gpu.state.depth_test_set('NONE')

        # Knife edge — orange, slightly thicker for visibility.
        gpu.state.line_width_set(2.0)
        shader.uniform_float("color", (1.0, 0.6, 0.0, 0.9))
        batch_for_shader(shader, 'LINES',
                         {"pos": [knife[0], knife[1]]}).draw(shader)

        if preview:
            gpu.state.line_width_set(1.5)
            # Parts that will be kept — white.
            if preview.get('keep'):
                shader.uniform_float("color", (1.0, 1.0, 1.0, 0.85))
                batch_for_shader(shader, 'LINES',
                                 {"pos": preview['keep']}).draw(shader)
            # Parts that will be removed (CROSS) — red.
            if preview.get('remove'):
                shader.uniform_float("color", (1.0, 0.2, 0.2, 0.9))
                batch_for_shader(shader, 'LINES',
                                 {"pos": preview['remove']}).draw(shader)

        gpu.state.depth_test_set('LESS_EQUAL')
        gpu.state.blend_set('NONE')

        # Extension segments (EXTEND) — dotted, drawn last so they stay on top.
        if preview:
            for p0, p1 in preview.get('extend', []):
                draw_dotted_line(p0, p1, context)

    # ── Preview ───────────────────────────────────────────────────────────────

    def _update_preview(self, mouse_x, mouse_y, context=None):
        """Recompute the visual preview based on current mouse position.

        Sets _mouse_side (+1 or -1) from the signed distance of the mouse to
        the knife line, then classifies each candidate into keep/remove/extend.
        """
        if self._knife_2d is None or self._candidates is None:
            return

        k0 = self._knife_2d[0];  k1 = self._knife_2d[1]

        # signed_dist_2d > 0 means "left of k0→k1"; the mouse side is whichever
        # half-plane contains the mouse.
        mouse_sign = signed_dist_2d(mouse_x, mouse_y, k0[0], k0[1], k1[0], k1[1])
        self._mouse_side = 1 if mouse_sign >= 0 else -1

        keep_segs    = []   # white solid lines
        remove_segs  = []   # red solid lines (part being cut off)
        extend_pairs = []   # dotted lines (gap being filled by extension)

        for cand in self._candidates:
            v0 = cand['v0_world'];  v1 = cand['v1_world']
            ctype = cand['type']

            if ctype in ('SKIP', 'PARALLEL'):
                keep_segs.extend([v0, v1])
                continue

            point = cand['point']
            v0_2d = cand.get('v0_2d')
            v1_2d = cand.get('v1_2d')

            if point is None or v0_2d is None or v1_2d is None:
                keep_segs.extend([v0, v1])
                continue

            if ctype == 'CROSS':
                # Candidate physically crosses the knife. The vertex on the same
                # side as the mouse is kept; the opposite side is removed.
                sign_v0 = signed_dist_2d(v0_2d[0], v0_2d[1], k0[0], k0[1], k1[0], k1[1])
                sign_v1 = signed_dist_2d(v1_2d[0], v1_2d[1], k0[0], k0[1], k1[0], k1[1])
                if sign_v0 * self._mouse_side >= sign_v1 * self._mouse_side:
                    v_keep, v_remove = v0, v1
                else:
                    v_keep, v_remove = v1, v0
                keep_segs.extend([v_keep, point])
                remove_segs.extend([point, v_remove])

            else:  # EXTEND
                # Candidate is entirely on one side of the knife line. Only
                # extend if it is on the KEEP side (same as mouse). If it is on
                # the opposite side there is nothing to do.
                mid_sign = signed_dist_2d(
                    (v0_2d[0] + v1_2d[0]) * 0.5, (v0_2d[1] + v1_2d[1]) * 0.5,
                    k0[0], k0[1], k1[0], k1[1])
                if mid_sign * self._mouse_side <= 0:
                    keep_segs.extend([v0, v1])
                    continue
                # The endpoint nearest to the intersection is determined by
                # t_cand: t > 1 means the intersection is beyond v1, t < 0
                # means it is before v0.
                t = cand.get('t_cand', 0.0)
                if t > 1.0:
                    v_near, v_far = v1, v0
                else:
                    v_near, v_far = v0, v1
                keep_segs.extend([v_far, v_near])
                extend_pairs.append((v_near, point))

        self._preview = {'keep': keep_segs, 'remove': remove_segs,
                         'extend': extend_pairs}

    # ── Apply ─────────────────────────────────────────────────────────────────

    def _apply(self, context):
        """Write the trim/extend result into the BMesh.

        Index maps are built once BEFORE any modification to prevent index reuse
        bugs: after delete+create cycles, a new edge may receive the same index
        as a deleted one, causing a later candidate to operate on the wrong edge.
        """
        k0 = self._knife_2d[0];  k1 = self._knife_2d[1]

        # Build per-object lookup maps once, before any modifications.
        obj_data = {}
        for oi, (obj, bm) in enumerate(self._per_obj):
            bm.edges.ensure_lookup_table()
            bm.verts.ensure_lookup_table()
            obj_data[oi] = {
                'obj':       obj,
                'bm':        bm,
                'mw_inv':    obj.matrix_world.inverted(),
                'edge_map':  {e.index: e for e in bm.edges},
                'vert_map':  {v.index: v for v in bm.verts},
                'last_edge': None,
            }

        for ci, cand in enumerate(self._candidates):
            ctype = cand['type']
            if ctype in ('SKIP', 'PARALLEL'):
                continue

            oi    = self._candidates_obj[ci]
            od    = obj_data[oi]
            bm    = od['bm']
            mw_inv = od['mw_inv']

            edge  = od['edge_map'].get(cand['edge_idx'])
            if edge is None or not edge.is_valid:
                continue

            v_at_0 = od['vert_map'].get(cand['v0_idx'])
            v_at_1 = od['vert_map'].get(cand['v1_idx'])
            if v_at_0 is None or v_at_1 is None:
                continue

            point_world = cand['point']
            v0_2d = cand.get('v0_2d')
            v1_2d = cand.get('v1_2d')
            if point_world is None or v0_2d is None or v1_2d is None:
                continue

            if ctype == 'CROSS':
                sign_v0 = signed_dist_2d(v0_2d[0], v0_2d[1], k0[0], k0[1], k1[0], k1[1])
                sign_v1 = signed_dist_2d(v1_2d[0], v1_2d[1], k0[0], k0[1], k1[0], k1[1])
                if sign_v0 * self._mouse_side >= sign_v1 * self._mouse_side:
                    v_keep, v_remove = v_at_0, v_at_1
                else:
                    v_keep, v_remove = v_at_1, v_at_0

            else:  # EXTEND
                mid_sign = signed_dist_2d(
                    (v0_2d[0] + v1_2d[0]) * 0.5, (v0_2d[1] + v1_2d[1]) * 0.5,
                    k0[0], k0[1], k1[0], k1[1])
                if mid_sign * self._mouse_side <= 0:
                    continue
                t = cand.get('t_cand', 0.0)
                if t > 1.0:
                    v_keep, v_remove = v_at_0, v_at_1
                else:
                    v_keep, v_remove = v_at_1, v_at_0

            point_local = mw_inv @ point_world

            if ctype == 'CROSS':
                remove_vert = len(v_remove.link_edges) == 1
                v_new = bm.verts.new(point_local)
                copy_bm_vert_attrs(bm, v_remove, v_new)
                new_edge = bm.edges.new((v_keep, v_new))
                copy_bm_edge_attrs(bm, edge, new_edge)
                bm.edges.remove(edge)
                if remove_vert:
                    bm.verts.remove(v_remove)
                od['last_edge'] = new_edge

            else:  # EXTEND
                if len(v_remove.link_edges) > 1:
                    v_new = bm.verts.new(point_local)
                    copy_bm_vert_attrs(bm, v_remove, v_new)
                    new_edge = bm.edges.new((v_keep, v_new))
                    copy_bm_edge_attrs(bm, edge, new_edge)
                    bmesh.ops.delete(bm, geom=[edge], context='EDGES')
                    od['last_edge'] = new_edge
                else:
                    v_remove.co = point_local
                    od['last_edge'] = edge

        for oi, (obj, bm) in enumerate(self._per_obj):
            bm.edges.ensure_lookup_table()
            last = obj_data[oi]['last_edge']
            if last is not None and last.is_valid:
                bm.select_history.clear()
                bm.select_history.add(last)
            bmesh.update_edit_mesh(obj.data)

    # ── Header / footer ───────────────────────────────────────────────────────

    def _update_header(self, context, modifier=None):
        inf = "ON" if self.infinite_knife else "OFF"
        cop = "ON" if self.coplanar_only  else "OFF"
        context.area.header_text_set(
            f"Trim/Extend  |  Infinite knife: {inf}  |  Coplanar: {cop}")
        self.set_status(context, modifier,
            mouse=[("Trim Side", 'MOUSE_LMB'), None, ("Cancel", 'MOUSE_RMB')],
            keys=[
                ("Infinite Knife", 'EVENT_I', self.infinite_knife),
                None,
                ("Coplanar Only",  'EVENT_C', self.coplanar_only),
            ],
        )

    # ── Recompute after option toggle ─────────────────────────────────────────

    def _recompute(self, context, mouse_x, mouse_y):
        """Rebuild candidate intersection data and refresh the preview.

        Called when the user toggles infinite_knife or coplanar_only so that
        the candidate classification reflects the new settings.
        """
        self._candidates = compute_trim_candidates(
            self._knife_world[0], self._knife_world[1],
            self._candidates_raw,
            self.infinite_knife, self.coplanar_only, context,
        )
        region = context.region
        rv3d   = context.space_data.region_3d
        for cand in self._candidates:
            cand['v0_2d'] = location_3d_to_region_2d(region, rv3d, cand['v0_world'])
            cand['v1_2d'] = location_3d_to_region_2d(region, rv3d, cand['v1_world'])
        self._update_preview(mouse_x, mouse_y)

    # ── Modal ─────────────────────────────────────────────────────────────────

    def modal(self, context, event):
        try:
            return self._modal_impl(context, event)
        except ReferenceError:
            self._remove_handlers()
            return {'CANCELLED'}

    def _modal_impl(self, context, event):
        if self.left_edit_mode(context, self._started_in_edit):
            self._remove_handlers()
            context.area.header_text_set(None)
            self.clear_status(context)
            return {'CANCELLED'}

        nav = self.pass_through_navigation(event)
        if nav is not None:
            return nav

        modifier = self.modifier_from_event(event)
        mouse_x  = event.mouse_region_x
        mouse_y  = event.mouse_region_y

        if event.type in {'LEFT_CTRL', 'RIGHT_CTRL', 'LEFT_ALT', 'RIGHT_ALT',
                          'LEFT_SHIFT', 'RIGHT_SHIFT'}:
            self._update_header(context, modifier)
            return {'RUNNING_MODAL'}

        if event.type in {'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE'}:
            self._update_preview(mouse_x, mouse_y)
            context.area.tag_redraw()

        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            self._apply(context)
            self._remove_handlers()
            context.area.header_text_set(None)
            self.clear_status(context)
            return {'FINISHED'}

        elif event.type == 'I' and event.value == 'PRESS':
            self.infinite_knife = not self.infinite_knife
            self._recompute(context, mouse_x, mouse_y)
            self._update_header(context, modifier)
            context.area.tag_redraw()

        elif event.type == 'C' and event.value == 'PRESS':
            self.coplanar_only = not self.coplanar_only
            self._recompute(context, mouse_x, mouse_y)
            self._update_header(context, modifier)
            context.area.tag_redraw()

        elif event.type in {'RIGHTMOUSE', 'ESC'} and event.value == 'PRESS':
            self._remove_handlers()
            context.area.header_text_set(None)
            self.clear_status(context)
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    # ── Execute (Shift+R repeat) ──────────────────────────────────────────────

    def execute(self, context):
        """Re-launch the modal operator for Shift+R repeat."""
        return self.invoke(context, None)

    # ── Invoke ────────────────────────────────────────────────────────────────

    def invoke(self, context, event):
        self._started_in_edit = context.mode == 'EDIT_MESH'
        # Collect all meshes in edit mode.
        self._per_obj = [
            (obj, bmesh.from_edit_mesh(obj.data))
            for obj in context.objects_in_mode
            if obj.type == 'MESH'
        ]
        for _, bm in self._per_obj:
            bm.edges.ensure_lookup_table()
            bm.verts.ensure_lookup_table()

        # Find the knife: the active edge in any of the bmeshes.
        knife_obj = knife_bm = knife_edge = None
        for obj, bm in self._per_obj:
            ae = bm.select_history.active
            if isinstance(ae, bmesh.types.BMEdge) and ae.select:
                knife_obj, knife_bm, knife_edge = obj, bm, ae
                break

        if knife_edge is None:
            self.report({'WARNING'},
                        "Set the knife edge as active (Shift+click it last)")
            return {'CANCELLED'}

        mw       = knife_obj.matrix_world
        knife_v0 = mw @ knife_edge.verts[0].co
        knife_v1 = mw @ knife_edge.verts[1].co
        self._knife_world = (knife_v0, knife_v1)

        region = context.region
        rv3d   = context.space_data.region_3d
        k2d_0  = location_3d_to_region_2d(region, rv3d, knife_v0)
        k2d_1  = location_3d_to_region_2d(region, rv3d, knife_v1)
        if k2d_0 is None or k2d_1 is None:
            self.report({'WARNING'}, "Knife edge not visible in viewport")
            return {'CANCELLED'}
        self._knife_2d = (k2d_0, k2d_1)

        # Collect candidates: all selected edges except the knife, across all objects.
        knife_obj_bm_id = id(knife_bm)
        knife_edge_idx  = knife_edge.index
        self._candidates_raw = []
        self._candidates_obj = []   # parallel list: obj index per candidate
        for oi, (obj, bm) in enumerate(self._per_obj):
            obj_mw = obj.matrix_world
            for e in bm.edges:
                if not e.select:
                    continue
                if id(bm) == knife_obj_bm_id and e.index == knife_edge_idx:
                    continue
                v0_w = obj_mw @ e.verts[0].co
                v1_w = obj_mw @ e.verts[1].co
                self._candidates_raw.append(
                    (v0_w, v1_w, e.index, e.verts[0].index, e.verts[1].index))
                self._candidates_obj.append(oi)

        if not self._candidates_raw:
            self.report({'WARNING'}, "No candidate edges selected (besides the knife)")
            return {'CANCELLED'}

        # Compute intersection data and enrich candidates with screen coords.
        self._candidates = compute_trim_candidates(
            knife_v0, knife_v1, self._candidates_raw,
            self.infinite_knife, self.coplanar_only, context,
        )
        for cand in self._candidates:
            cand['v0_2d'] = location_3d_to_region_2d(region, rv3d, cand['v0_world'])
            cand['v1_2d'] = location_3d_to_region_2d(region, rv3d, cand['v1_world'])

        mx = event.mouse_region_x if event is not None else 0
        my = event.mouse_region_y if event is not None else 0
        self._update_preview(mx, my)

        global _trim_draw_handle
        h3d = bpy.types.SpaceView3D.draw_handler_add(
            self._draw_preview, (context,), 'WINDOW', 'POST_VIEW')
        self._draw_handle = (h3d,)
        _trim_draw_handle = self._draw_handle

        self._update_header(context)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def _remove_handlers(self):
        global _trim_draw_handle
        if self._draw_handle is not None:
            for h in self._draw_handle:
                bpy.types.SpaceView3D.draw_handler_remove(h, 'WINDOW')
            self._draw_handle = None
        _trim_draw_handle = None
