import bpy
import bmesh
from mathutils import Vector
from bpy_extras.view3d_utils import region_2d_to_location_3d
import gpu
from gpu_extras.batch import batch_for_shader

from ...Utils.mastro_cad.cad.cad_utils import (
    compute_plane,
    sort_edges_into_chains,
    build_chain_geo,
    apply_offset_to_geo,
    copy_bm_edge_attrs,
    nearest_src_edge,
    format_length,
)
from ...Utils.mastro_cad.cad.gpu_utils import draw_dotted_line
from ...Utils.mastro_cad.cad.snap_utils import SnapContext
from .CAD_mixin import CadMixin, CAD_CHAR_MAP


class MESH_OT_MaStroCad_Offset(bpy.types.Operator):
    """Offset selected edges by a distance, creating parallel edges.

    The offset plane is detected automatically from the selection geometry:
    the local axis with the smallest spread is used as the plane normal,
    so flat geometry is always offset within its own plane.
    Shapely handles mitre joins at corners.
    """
    bl_idname  = "mastrocad.offset"
    bl_label   = "Offset Edge"
    bl_options = {'REGISTER', 'UNDO'}

    distance: bpy.props.FloatProperty(
        name="Distance",
        description="Offset distance in scene units",
        default=0.1,
        subtype='DISTANCE',
    )
    connect_ends: bpy.props.BoolProperty(
        name="Connect Ends",
        description="Add edges connecting the endpoints of original and offset chains",
        default=False,
    )

    # ── Modal state ────────────────────────────────────────────────────────────
    _center_world  = None
    _number_input  = ""
    _draw_handle   = None
    _preview_verts = []
    _cached_chains  = None
    _cached_tol     = 0.001
    _cached_geo     = None
    _cached_perp    = None

    _last_seg       = None   # (chain_idx, seg_idx) of last valid interior projection
    _snap           = None
    _snap_hit       = None

    # ── GPU preview ───────────────────────────────────────────────────────────

    def _draw_snap(self, context):
        try:
            snap_hit = self._snap_hit
        except ReferenceError:
            return
        if snap_hit is not None and self._snap is not None:
            self._snap.draw_indicator(snap_hit, context)

    def _draw_preview(self, context):
        try:
            preview = self._preview_verts
        except ReferenceError:
            return

        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        gpu.state.blend_set('ALPHA')
        gpu.state.depth_test_set('NONE')
        shader.bind()

        if preview:
            coords = [co for pair in preview for co in pair]
            batch  = batch_for_shader(shader, 'LINES', {"pos": coords})
            shader.uniform_float("color", (1.0, 0.6, 0.0, 0.8))
            gpu.state.line_width_set(1.5)
            batch.draw(shader)


        gpu.state.depth_test_set('LESS_EQUAL')
        gpu.state.blend_set('NONE')

    def _update_preview(self, context):
        if not self._cached_geo:
            self._preview_verts = []
            return
        per_chain_edges, caps = apply_offset_to_geo(
            self._cached_geo, self.distance, self.connect_ends)
        self._preview_verts = [
            p for ce in per_chain_edges for p in ce] + [
            (c[0], c[1]) for c in caps]

    # ── Geometry ──────────────────────────────────────────────────────────────

    @classmethod
    def poll(cls, context):
        return (context.mode == 'EDIT_MESH' and
                context.active_object is not None)

    def _get_selected_edges(self, context):
        """Return list of (obj, bm, selected_edges) for all objects in edit mode."""
        result = []
        for obj in context.objects_in_mode:
            if obj.type != 'MESH':
                continue
            bm = bmesh.from_edit_mesh(obj.data)
            bm.edges.ensure_lookup_table()
            sel = [e for e in bm.edges if e.select]
            if sel:
                result.append((obj, bm, sel))
        return result

    @staticmethod
    def _chain_from_active(bm, sel):
        """Return the subset of sel reachable from the active edge without
        crossing vertices that have bmesh degree > 2.

        Degree is counted in the full bmesh (all edges, not just selected ones).
        A vertex at a junction (degree > 2) stops the walk; degree-1 and degree-2
        vertices let the chain continue.
        Falls back to all of sel when there is no active edge.
        """
        ae = bm.select_history.active
        if not isinstance(ae, bmesh.types.BMEdge) or ae not in sel:
            ae = sel[0] if sel else None
        if ae is None:
            return sel

        sel_set = set(sel)
        # Build adjacency within selected edges only.
        vert_to_sel_edges = {}
        for e in sel:
            for v in e.verts:
                vert_to_sel_edges.setdefault(v, []).append(e)

        visited = {ae}
        queue   = [ae]
        while queue:
            e = queue.pop()
            for v in e.verts:
                if len(v.link_edges) > 2:
                    continue
                for ne in vert_to_sel_edges.get(v, []):
                    if ne not in visited:
                        visited.add(ne)
                        queue.append(ne)
        return list(visited)

    def _build_caches(self, context, per_obj):
        """Build all cached data from the current selection across all objects.

        per_obj: list of (obj, bm, selected_edges) from _get_selected_edges.
        Chains are built per-object (to avoid index collisions between bmeshes)
        then merged; each chain carries 'obj_index' to route new verts back.
        """
        self._cached_tol = 0.001
        all_chains = []
        for oi, (obj, bm, sel) in enumerate(per_obj):
            mw     = obj.matrix_world
            chain_edges = self._chain_from_active(bm, sel)
            chains = sort_edges_into_chains(chain_edges, mw)
            for ch in chains:
                ch['obj_index'] = oi
            all_chains.extend(chains)
        self._cached_chains = all_chains
        self._cached_geo    = build_chain_geo(
            self._cached_chains, context, self._cached_tol)
        if self._cached_geo:
            cg       = self._cached_geo[0]
            edge_dir = (cg['pts'][1] - cg['pts'][0]).normalized() \
                       if len(cg['pts']) >= 2 else Vector((1, 0, 0))
            p = cg['normal'].cross(edge_dir)
            self._cached_perp = p.normalized() if p.length > 1e-8 \
                                 else Vector((1.0, 0.0, 0.0))

    def _do_offset(self, context):
        per_obj = self._get_selected_edges(context)
        if not per_obj:
            return

        # Find active chain per object (each bmesh has its own select_history).
        active_chain_per_obj = {}  # oi -> ci
        if self._cached_chains:
            for oi, (obj, bm, sel) in enumerate(per_obj):
                ae = bm.select_history.active
                if not isinstance(ae, bmesh.types.BMEdge):
                    active_chain_per_obj[oi] = next(
                        (ci for ci, ch in enumerate(self._cached_chains)
                         if ch.get('obj_index') == oi), None)
                    continue
                for ci, chain in enumerate(self._cached_chains):
                    if chain.get('obj_index') != oi:
                        continue
                    if ae.index in (i for i in chain.get('src_edges', [])
                                    if i is not None):
                        active_chain_per_obj[oi] = ci
                        break

        per_chain_edges, caps = apply_offset_to_geo(
            self._cached_geo, self.distance, self.connect_ends)

        # Deselect everything and resolve source-edge refs before modifying bmeshes.
        for obj, bm, sel in per_obj:
            for v in bm.verts:
                v.select = False
            for e in bm.edges:
                e.select = False
            bm.select_history.clear()
            bm.select_flush(False)
            bm.edges.ensure_lookup_table()

        resolved_src = {}
        for ci, chain in enumerate(self._cached_chains):
            oi   = chain.get('obj_index', 0)
            bm   = per_obj[oi][1]
            idxs = chain.get('src_edges', [])
            resolved_src[ci] = [
                bm.edges[i] if (i is not None and i < len(bm.edges)) else None
                for i in idxs
            ]

        active_new_edge_per_obj = {}  # oi -> new BMEdge

        for ci, chain_edges in enumerate(per_chain_edges):
            if not chain_edges:
                continue
            oi         = self._cached_chains[ci].get('obj_index', 0)
            obj, bm, _ = per_obj[oi]
            mw_inv     = obj.matrix_world.inverted()

            verts = [bm.verts.new(mw_inv @ chain_edges[0][0])]
            for a, b in chain_edges:
                verts.append(bm.verts.new(mw_inv @ b))
            for v in verts:
                v.select = True

            src_edges = resolved_src.get(ci, [])
            for ki in range(len(chain_edges)):
                ne = bm.edges.new((verts[ki], verts[ki + 1]))
                ne.select = True
                if ki == 0 and ci == active_chain_per_obj.get(oi):
                    active_new_edge_per_obj[oi] = ne
                src = nearest_src_edge(ki, chain_edges, src_edges) if src_edges else None
                if src is not None:
                    copy_bm_edge_attrs(bm, src, ne)

        for cap_i, cap_item in enumerate(caps):
            a, b = cap_item[0], cap_item[1]
            ci   = cap_i // 2
            oi   = self._cached_chains[ci].get('obj_index', 0) if ci < len(self._cached_chains) else 0
            obj, bm, _ = per_obj[oi]
            mw_inv = obj.matrix_world.inverted()
            va = bm.verts.new(mw_inv @ a)
            vb = bm.verts.new(mw_inv @ b)
            ne = bm.edges.new((va, vb))
            va.select = vb.select = ne.select = True
            if len(cap_item) > 2:
                src_list = resolved_src.get(ci, [])
                src_idx  = cap_item[2]
                src = src_list[min(src_idx, len(src_list) - 1)] if src_list else None
                if src is not None:
                    copy_bm_edge_attrs(bm, src, ne)

        for oi, (obj, bm, _) in enumerate(per_obj):
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
            bm.edges.ensure_lookup_table()
            ae = active_new_edge_per_obj.get(oi)
            if ae and ae.is_valid:
                bm.select_history.add(ae)
            bmesh.update_edit_mesh(obj.data)

    # ── UI ────────────────────────────────────────────────────────────────────

    def _update_header(self, context, modifier=None):
        dist_str = self._number_input if self._number_input else format_length(context, self.distance)
        conn_str = "ON" if self.connect_ends else "OFF"
        context.area.header_text_set(f"Offset  |  Distance: {dist_str}  |  Connect ends: {conn_str}")
        CadMixin.set_status(context, modifier,
            mouse=[("Confirm", 'MOUSE_LMB'), None, ("Cancel", 'MOUSE_RMB')],
            keys=[("Connect Ends", 'EVENT_C', self.connect_ends)],
        )

    # ── Modal ─────────────────────────────────────────────────────────────────

    def modal(self, context, event):
        if CadMixin.left_edit_mode(context, self._started_in_edit):
            self._remove_draw_handler()
            context.area.header_text_set(None)
            CadMixin.clear_status(context)
            return {'CANCELLED'}
        nav = CadMixin.pass_through_navigation(self, event)
        if nav is not None:
            return nav
        modifier = CadMixin.modifier_from_event(event)
        if event.alt:
            self._update_header(context, modifier)
            return {'PASS_THROUGH'}

        if event.type in {'LEFT_CTRL', 'RIGHT_CTRL',
                          'LEFT_SHIFT', 'RIGHT_SHIFT'}:
            self._update_header(context, modifier)
            return {'RUNNING_MODAL'}
        if event.type in {'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE'}:
            CadMixin.maybe_rebuild_snap(self, context)
            if not self._number_input and self._cached_chains:
                mouse = (event.mouse_region_x, event.mouse_region_y)
                if self._cached_geo:
                    cg = self._cached_geo[0]
                    plane_axes = (cg['x_axis'], cg['y_axis'], cg['normal'])
                    from ...Utils.mastro_cad.cad.cad_utils import ray_plane_intersect, min_dist_point_to_chains
                    raw_3d = ray_plane_intersect(
                        context, mouse, plane_axes, cg['pts'][0])
                    snapped = (self._snap.snap(mouse, context, raw_world=raw_3d)
                               if self._snap and not event.ctrl else None)
                    self._snap_hit = snapped
                    mouse_3d = snapped if snapped is not None else raw_3d
                    normal  = cg['normal']
                    dist    = 0.0
                    closest = None
                    # Always run global search.
                    g_dist, g_closest, g_ci, g_si = min_dist_point_to_chains(
                        mouse_3d, self._cached_chains, normal)

                    if self._last_seg is not None:
                        lci, lsi = self._last_seg
                        chain  = self._cached_chains[lci]
                        pts    = chain['pts']
                        n_segs = len(pts) - 1

                        # Always check bisectors first — crossing one means we
                        # must switch edge even if t would still be valid.
                        def _bisector_at(B, ab_vec, bc_vec):
                            if ab_vec.length < 1e-8 or bc_vec.length < 1e-8:
                                return None
                            side_ab  = normal.cross(ab_vec.normalized())
                            side_bc  = normal.cross(bc_vec.normalized())
                            bisector = side_ab + side_bc
                            if bisector.length < 1e-8:
                                return None
                            return normal.cross(bisector.normalized())

                        # Check bisector at end of lsi (corner toward lsi+1).
                        if lsi + 1 < n_segs:
                            B  = pts[lsi + 1]
                            ab = B - pts[lsi]
                            bc = pts[lsi + 2] - B
                            bis_perp = _bisector_at(B, ab, bc)
                            if bis_perp is not None:
                                sign_a  = (pts[lsi] - B).dot(bis_perp)
                                sign_pt = (mouse_3d  - B).dot(bis_perp)
                                if sign_a * sign_pt < 0:
                                    lsi += 1
                                    self._last_seg = (lci, lsi)

                        # Check bisector at start of lsi (corner toward lsi-1).
                        if lsi > 0:
                            B  = pts[lsi]
                            ab = B - pts[lsi - 1]
                            bc = pts[lsi + 1] - B
                            bis_perp = _bisector_at(B, ab, bc)
                            if bis_perp is not None:
                                sign_c  = (pts[lsi + 1] - B).dot(bis_perp)
                                sign_pt = (mouse_3d    - B).dot(bis_perp)
                                if sign_c * sign_pt < 0:
                                    lsi -= 1
                                    self._last_seg = (lci, lsi)

                        # Compute perpendicular on the (possibly updated) segment.
                        a = pts[lsi]
                        b = pts[lsi + 1]
                        ab = b - a;  ab_len = ab.length
                        if ab_len > 1e-8:
                            ab_n    = ab / ab_len
                            t       = (mouse_3d - a).dot(ab_n)
                            dist    = ab.cross(mouse_3d - a).dot(normal) / ab_len
                            closest = a + ab_n * t

                        # If global result is on a different segment and clearly
                        # closer (half the distance), trust global and switch.
                        if (g_closest is not None and
                                (g_ci, g_si) != (lci, lsi) and
                                abs(g_dist) < abs(dist) * 0.5):
                            dist    = g_dist
                            closest = g_closest
                            self._last_seg = (g_ci, g_si)
                    else:
                        # No active segment yet: use global result.
                        dist    = g_dist
                        closest = g_closest
                        if g_closest is not None:
                            self._last_seg = (g_ci, g_si)
                    self.distance = dist
                else:
                    raw_3d = region_2d_to_location_3d(
                        context.region, context.space_data.region_3d,
                        mouse, self._center_world)
                    snapped = (self._snap.snap(mouse, context, raw_world=raw_3d)
                               if self._snap and not event.ctrl else None)
                    self._snap_hit = snapped
                    mouse_3d = snapped if snapped is not None else raw_3d
                    self.distance = (mouse_3d - self._center_world).dot(self._cached_perp)
            self._update_preview(context)
            self._update_header(context, modifier)
            context.area.tag_redraw()

        elif event.value == 'PRESS' and event.type in CAD_CHAR_MAP:
            self._number_input += CAD_CHAR_MAP[event.type]
            from ...Utils.mastro_cad.cad.cad_utils import safe_eval
            val = safe_eval(self._number_input)
            if val is not None:
                self.distance = val
            self._update_preview(context)
            self._update_header(context, modifier)
            context.area.tag_redraw()

        elif event.type == 'BACK_SPACE' and event.value == 'PRESS':
            self._number_input = self._number_input[:-1]
            if self._number_input:
                from ...Utils.mastro_cad.cad.cad_utils import safe_eval
                val = safe_eval(self._number_input)
                if val is not None:
                    self.distance = val
            self._update_preview(context)
            self._update_header(context, modifier)
            context.area.tag_redraw()

        elif event.type == 'C' and event.value == 'PRESS':
            self.connect_ends = not self.connect_ends
            self._update_preview(context)
            self._update_header(context, modifier)
            context.area.tag_redraw()

        elif event.type in {'RET', 'NUMPAD_ENTER', 'LEFTMOUSE'} and event.value == 'PRESS':
            self._remove_draw_handler()
            self._do_offset(context)
            context.area.header_text_set(None)
            CadMixin.clear_status(context)
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'} and event.value == 'PRESS':
            self._remove_draw_handler()
            context.area.header_text_set(None)
            CadMixin.clear_status(context)
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self._started_in_edit = context.mode == 'EDIT_MESH'
        per_obj = self._get_selected_edges(context)
        if not per_obj:
            self.report({'WARNING'}, "Select at least one edge")
            return {'CANCELLED'}

        all_midpoints = [
            obj.matrix_world @ ((e.verts[0].co + e.verts[1].co) * 0.5)
            for obj, bm, sel in per_obj for e in sel
        ]
        self._center_world = sum(all_midpoints, Vector((0.0, 0.0, 0.0))) / len(all_midpoints)

        self._number_input  = ""
        self._preview_verts = []
        self.distance       = 0.0
        self._snap_hit      = None
        self._last_seg      = None
        self._snap          = SnapContext(context, select_modes=('VERT', 'EDGE'))
        self._build_caches(context, per_obj)

        h3d = bpy.types.SpaceView3D.draw_handler_add(
            self._draw_preview, (context,), 'WINDOW', 'POST_VIEW')
        h2d = bpy.types.SpaceView3D.draw_handler_add(
            self._draw_snap, (context,), 'WINDOW', 'POST_PIXEL')
        self._draw_handle = (h3d, h2d)

        self._update_header(context)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def _remove_draw_handler(self):
        if self._draw_handle is not None:
            for h in self._draw_handle:
                bpy.types.SpaceView3D.draw_handler_remove(h, 'WINDOW')
            self._draw_handle = None

    def execute(self, context):
        """Called by Shift+R — rebuilds caches from current selection."""
        per_obj = self._get_selected_edges(context)
        if not per_obj:
            self.report({'WARNING'}, "Select at least one edge")
            return {'CANCELLED'}
        self._build_caches(context, per_obj)
        self._do_offset(context)
        return {'FINISHED'}
