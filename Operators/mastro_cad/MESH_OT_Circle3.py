"""Circle-from-3-inputs creation operator.

Each click accumulates geometric constraints in a pool:
  - click on empty space  → point constraint
  - click on an edge      → edge (tangent-line) constraint
  - click on a vertex     → point constraint + all incident edge constraints
  - type a number         → floating radius (replaces mouse as third constraint)

At each moment ALL compatible triples of constraints from the pool are solved
and drawn as white dotted circles; the highlighted (orange) one is nearest to
the mouse.  Clicking (non-edge / non-vertex) or Enter/Space confirms it.

Dispatch table — for each (n_points, n_edges) triple:
  PPP → circle_3p_2d          EEE → circle_ttt_2d
  PPE → circle_t2p_2d         PP+R → circle_2pr_2d
  PEE → circle_ttp_all        EE+R → circle_ttr_all
  EEE → circle_ttt_2d         PE+R → circle_lpr_2d
  PP+mouse → circle_3p_2d     PE+mouse → circle_t2p_2d
  EE+mouse → circle_ttp_all

Wheel ↑↓ : segment count
Backspace : remove last click (or last radius digit)
ESC / RMB : cancel
Enter     : confirm highlighted solution
"""

import bpy
import bmesh
import math
import itertools
from mathutils import Vector
import gpu
from gpu_extras.batch import batch_for_shader
from bpy_extras.view3d_utils import location_3d_to_region_2d

from ...Utils.mastro_cad.cad.cad_utils   import assign_drawing_layer_to_edges
from ...Utils.mastro_cad.cad.circle_utils import (ensure_circle_layers, set_circle_attrs,
                                       circle_points,
                                       circle_3p_2d, circle_2pr_2d,
                                       circle_t2p_2d, circle_lpr_2d,
                                       circle_ttr_all, circle_ttp_all,
                                       circle_ttt_2d)
from ...Utils.mastro_cad.cad.constants    import MAX_CIRCLE_RADIUS
from ...Utils.mastro_cad.cad.snap_utils   import SnapContext
from ...Utils.mastro_cad.cad.gpu_utils    import draw_dotted_polyline
from .CAD_mixin               import CadMixin, CAD_CHAR_MAP

_circle3_draw_handle = None


def _label(n_points, n_edges, third=""):
    parts = ["Point"] * n_points + ["Tangent"] * n_edges
    if third:
        parts.append(third)
    return " + ".join(parts)


def _used_edge_cids(*constraints):
    """frozenset of click_ids used as edge constraints in this combination."""
    return frozenset(c['click_id'] for c in constraints if c['type'] == 'edge')


def _solve_triple(c0, c1, c2):
    """Return a list of (cx, cy, r, label, used_edge_cids) for a constraint triple."""
    pts  = [c for c in (c0, c1, c2) if c['type'] == 'point']
    eds  = [c for c in (c0, c1, c2) if c['type'] == 'edge']
    np, ne = len(pts), len(eds)
    lbl = _label(np, ne)
    ue  = _used_edge_cids(c0, c1, c2)

    if np == 3:
        r = circle_3p_2d(*pts[0]['pt_2d'], *pts[1]['pt_2d'], *pts[2]['pt_2d'])
        return [(r[0], r[1], r[2], lbl, ue)] if r else []
    if np == 2 and ne == 1:
        return [(cx, cy, r, lbl, ue)
                for cx, cy, r in circle_t2p_2d(eds[0]['edge_2d'], pts[0]['pt_2d'], pts[1]['pt_2d'])]
    if np == 1 and ne == 2:
        return [(cx, cy, r, lbl, ue)
                for cx, cy, r in circle_ttp_all(eds[0]['edge_2d'], eds[1]['edge_2d'], pts[0]['pt_2d'])]
    if np == 0 and ne == 3:
        return [(cx, cy, r, lbl, ue)
                for cx, cy, r in circle_ttt_2d(eds[0]['edge_2d'], eds[1]['edge_2d'], eds[2]['edge_2d'])]
    return []


def _solve_pair_with_mouse(c0, c1, mouse_2d):
    """Return a list of (cx, cy, r, label, used_edge_cids) for a pair + mouse point."""
    pts  = [c for c in (c0, c1) if c['type'] == 'point']
    eds  = [c for c in (c0, c1) if c['type'] == 'edge']
    np, ne = len(pts), len(eds)
    mp  = mouse_2d
    lbl = _label(np, ne, "Point")
    ue  = _used_edge_cids(c0, c1)

    if np == 2:
        r = circle_3p_2d(*pts[0]['pt_2d'], *pts[1]['pt_2d'], *mp)
        return [(r[0], r[1], r[2], lbl, ue)] if r else []
    if np == 1 and ne == 1:
        return [(cx, cy, r, lbl, ue)
                for cx, cy, r in circle_t2p_2d(eds[0]['edge_2d'], pts[0]['pt_2d'], mp)]
    if np == 0 and ne == 2:
        return [(cx, cy, r, lbl, ue)
                for cx, cy, r in circle_ttp_all(eds[0]['edge_2d'], eds[1]['edge_2d'], mp)]
    return []


def _solve_pair_with_radius(c0, c1, r):
    """Return a list of (cx, cy, r, label, used_edge_cids) for a pair + fixed radius."""
    pts  = [c for c in (c0, c1) if c['type'] == 'point']
    eds  = [c for c in (c0, c1) if c['type'] == 'edge']
    np, ne = len(pts), len(eds)
    lbl = _label(np, ne, "Radius")
    ue  = _used_edge_cids(c0, c1)

    if np == 2:
        return [(cx, cy, r, lbl, ue)
                for cx, cy in circle_2pr_2d(*pts[0]['pt_2d'], *pts[1]['pt_2d'], r)]
    if np == 1 and ne == 1:
        return [(cx, cy, r, lbl, ue)
                for cx, cy, r in circle_lpr_2d(eds[0]['edge_2d'], pts[0]['pt_2d'], r)]
    if np == 0 and ne == 2:
        return [(cx, cy, r, lbl, ue)
                for cx, cy, r in circle_ttr_all(eds[0]['edge_2d'], eds[1]['edge_2d'], r)]
    return []


class MESH_OT_MaStroCad_Circle3(CadMixin, bpy.types.Operator):
    """Draw a circle by accumulating point/edge constraints and optionally a radius.

    Click edges for tangent constraints, vertices for point+edge, empty space
    for points.  All compatible circles are shown as dotted white previews;
    move near one and click or press Enter to confirm.
    """
    bl_idname  = "mastrocad.circle3"
    bl_label   = "Circle (3 Inputs)"
    bl_options = {'REGISTER', 'UNDO'}

    # ── Modal state ───────────────────────────────────────────────────────────
    _right         = None
    _up            = None
    _plane_normal  = None
    _plane_ref_pt  = None

    # Pool of atomic constraints (each dict has 'type', 'click_id', and data).
    # Multiple constraints can share the same click_id (vertex click).
    _pool          = None   # list of constraint dicts
    _click_count   = 0      # number of clicks so far (for grouping backspace)

    _radius_input  = ""
    _typed_radius  = 0.0

    _solutions     = None
    _hover_idx     = -1
    _show_extra    = False   # True = show non-tangent solutions, False = tangent-first

    _segments      = 32
    _selecting     = False   # True = solutions locked, next click confirms
    _snap          = None
    _snap_hit      = None
    _snap_disabled = False
    _hover_edge    = None    # (p0_world, p1_world) of edge under snap cursor, or None
    _draw_handle   = None
    _mouse_2d      = None

    # ── Plane helpers ─────────────────────────────────────────────────────────

    def _init_plane(self, context, world_pt):
        rv3d = context.space_data.region_3d
        self._right, self._up = self.orient_axes(context, rv3d)
        self._plane_normal = self._right.cross(self._up).normalized()
        self._plane_ref_pt = world_pt.copy()

    def _to_2d(self, world_pt):
        return (world_pt.dot(self._right), world_pt.dot(self._up))

    def _to_3d(self, x, y):
        return (self._right * x + self._up * y
                + self._plane_normal * self._plane_ref_pt.dot(self._plane_normal))

    def _mouse_to_world(self, context, mouse_2d):
        return self.project_to_plane(context, mouse_2d, self._plane_normal,
                                      self._plane_ref_pt, self._right, self._up)

    # ── Edge / vertex detection ───────────────────────────────────────────────

    def _find_edge_at_world(self, context, world_pt, threshold=0.01):
        """Return (p0_world, p1_world) of the nearest non-hidden edge, or (None, None)."""
        best_d = float('inf')
        best_verts = (None, None)

        active   = context.active_object
        candidates = [o for o in context.scene.objects
                      if o.visible_get() and o.type == 'MESH']

        for obj in candidates:
            mw     = obj.matrix_world
            mw_inv = mw.inverted()
            local  = mw_inv @ world_pt
            is_edit = (context.mode == 'EDIT_MESH' and obj == active)

            bm = bmesh.from_edit_mesh(obj.data) if is_edit else bmesh.new()
            if not is_edit:
                bm.from_mesh(obj.data)

            for e in bm.edges:
                if e.hide:
                    continue
                a, b = e.verts[0].co.copy(), e.verts[1].co.copy()
                ab   = b - a
                ab2  = ab.dot(ab)
                if ab2 < 1e-14:
                    continue
                t       = max(0.0, min(1.0, (local - a).dot(ab) / ab2))
                closest = a + ab * t
                d = (mw @ closest - world_pt).length
                if d < best_d:
                    best_d = d
                    best_verts = (mw @ a, mw @ b)

            if not is_edit:
                bm.free()

        if best_d < threshold:
            return best_verts
        return None, None

    def _find_all_edges_at_vertex(self, context, world_pt, threshold=0.01):
        """Return list of (p0_world, p1_world) for all edges incident to the
        nearest vertex within threshold distance."""
        result = []

        active     = context.active_object
        candidates = [o for o in context.scene.objects
                      if o.visible_get() and o.type == 'MESH']

        for obj in candidates:
            mw     = obj.matrix_world
            mw_inv = mw.inverted()
            local  = mw_inv @ world_pt
            is_edit = (context.mode == 'EDIT_MESH' and obj == active)

            bm = bmesh.from_edit_mesh(obj.data) if is_edit else bmesh.new()
            if not is_edit:
                bm.from_mesh(obj.data)

            # Find nearest vertex.
            best_v, best_d = None, float('inf')
            for v in bm.verts:
                if v.hide:
                    continue
                d = (mw @ v.co - world_pt).length
                if d < best_d:
                    best_d, best_v = d, v

            if best_v is not None and best_d < threshold:
                for e in best_v.link_edges:
                    if e.hide:
                        continue
                    a = mw @ e.verts[0].co
                    b = mw @ e.verts[1].co
                    result.append((a, b))

            if not is_edit:
                bm.free()

        return result

    # ── Pool management ───────────────────────────────────────────────────────

    def _make_edge_constraint(self, p0_world, p1_world, click_id):
        return {
            'type':     'edge',
            'click_id': click_id,
            'edge_2d':  (self._to_2d(p0_world), self._to_2d(p1_world)),
            'p0_world': p0_world,
            'p1_world': p1_world,
        }

    def _make_point_constraint(self, world_pt, click_id):
        return {
            'type':     'point',
            'click_id': click_id,
            'pt_2d':    self._to_2d(world_pt),
            'world':    world_pt.copy(),
        }

    def _add_click(self, context, world_pt, snap_type):
        """Dispatch a click to the right constraint(s) and add to pool."""
        cid = self._click_count
        self._click_count += 1

        if snap_type == 'VERTEX' or snap_type == 'MIDPOINT':
            incident = self._find_all_edges_at_vertex(context, world_pt)
            self._pool.append(self._make_point_constraint(world_pt, cid))
            for p0, p1 in incident:
                self._pool.append(self._make_edge_constraint(p0, p1, cid))

        elif snap_type == 'EDGE':
            p0, p1 = self._find_edge_at_world(context, world_pt, threshold=float('inf'))
            if p0 is not None:
                self._pool.append(self._make_edge_constraint(p0, p1, cid))
            else:
                self._pool.append(self._make_point_constraint(world_pt, cid))

        else:
            self._pool.append(self._make_point_constraint(world_pt, cid))

    def _pop_last_click(self):
        """Remove all constraints from the last click."""
        if not self._pool:
            return
        last_cid = self._pool[-1]['click_id']
        self._pool = [c for c in self._pool if c['click_id'] != last_cid]
        self._click_count -= 1

    # ── Solution computation ──────────────────────────────────────────────────

    def _compute_solutions(self, mouse_2d=None):
        if self._right is None:
            self._solutions = []
            return

        pool    = self._pool
        n       = len(pool)
        has_r   = self._typed_radius > 1e-8
        raw     = []

        n_clicks = self._click_count

        if n_clicks >= 3 and not has_r:
            for triple in itertools.combinations(pool, 3):
                raw.extend(_solve_triple(*triple))
        elif n_clicks < 3 and not has_r and mouse_2d is not None and n >= 2:
            for pair in itertools.combinations(pool, 2):
                raw.extend(_solve_pair_with_mouse(*pair, mouse_2d))

        if n_clicks < 3 and has_r and n >= 2:
            for pair in itertools.combinations(pool, 2):
                raw.extend(_solve_pair_with_radius(*pair, self._typed_radius))

        # Deduplicate on (cx, cy, r); keep first occurrence.
        seen = []
        tol  = 1e-4
        for cx, cy, r, lbl, ue in raw:
            if 1e-6 < r <= MAX_CIRCLE_RADIUS:
                if not any(abs(cx - sx) < tol and abs(cy - sy) < tol and abs(r - sr) < tol
                           for sx, sy, sr, *_ in seen):
                    seen.append((cx, cy, r, lbl, ue))

        # Split into tangent (all edge-capable clicks used as tangent) and extra.
        edge_cids = frozenset(c['click_id'] for c in pool if c['type'] == 'edge')
        if edge_cids:
            tangent = [s for s in seen if edge_cids.issubset(s[4])]
            extra   = [s for s in seen if not edge_cids.issubset(s[4])]
        else:
            tangent, extra = seen, []

        self._solutions_tangent = tangent
        self._solutions_extra   = extra
        self._solutions = extra if self._show_extra else tangent

    def _update_hover(self, mouse_2d):
        if not self._solutions or mouse_2d is None:
            self._hover_idx = -1
            return
        mx, my  = mouse_2d
        best_i  = 0
        best_d  = float('inf')
        for i, (cx, cy, r, *_) in enumerate(self._solutions):
            dx, dy = mx - cx, my - cy
            d      = abs(math.sqrt(dx*dx + dy*dy) - r)
            if d < best_d:
                best_d, best_i = d, i
        self._hover_idx = best_i

    # ── Apply ─────────────────────────────────────────────────────────────────

    def _apply(self, context):
        if self._hover_idx < 0 or not self._solutions:
            return
        cx, cy, r, _lbl, *_ = self._solutions[self._hover_idx]
        center    = self._to_3d(cx, cy)
        n         = self._segments
        pts       = circle_points(center, r, n, self._right, self._up, phase=0.0)

        if context.mode == 'EDIT_MESH' and context.active_object:
            obj    = context.active_object
            bm     = bmesh.from_edit_mesh(obj.data)
            mw_inv = obj.matrix_world.inverted()
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
            local_pts = [p - center for p in pts]
            bm        = bmesh.new()
            layers    = ensure_circle_layers(bm)
            verts     = [bm.verts.new(p) for p in local_pts]
            edges     = [bm.edges.new((verts[i], verts[(i + 1) % n])) for i in range(n)]
            set_circle_attrs(bm, verts, edges, n, layers=layers)
            mesh             = bpy.data.meshes.new("Circle")
            bm.to_mesh(mesh)
            bm.free()
            new_obj          = bpy.data.objects.new("Circle", mesh)
            new_obj.location = center
            context.collection.objects.link(new_obj)
            context.view_layer.objects.active = new_obj
            new_obj.select_set(True)

    # ── GPU draw ──────────────────────────────────────────────────────────────

    def _draw_preview(self, context):
        """POST_VIEW: dotted white for all solutions, solid orange for highlighted."""
        try:
            solutions  = self._solutions
            hover_idx  = self._hover_idx
            pool       = self._pool
            right      = self._right
            hover_edge = self._hover_edge
        except ReferenceError:
            global _circle3_draw_handle
            if _circle3_draw_handle is not None:
                for h in _circle3_draw_handle:
                    try:
                        bpy.types.SpaceView3D.draw_handler_remove(h, 'WINDOW')
                    except Exception:
                        pass
                _circle3_draw_handle = None
            return

        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        shader.bind()
        gpu.state.blend_set('ALPHA')
        gpu.state.depth_test_set('NONE')

        # Draw hover edge preview (snap is on an edge but not yet clicked).
        if hover_edge and hover_edge[0] is not None:
            p0, p1 = hover_edge
            seg = p1 - p0
            seg_len = seg.length
            if seg_len > 1e-8:
                d = seg / seg_len
                shader.uniform_float("color", (1.0, 0.0, 0.0, 0.35))
                gpu.state.line_width_set(1.0)
                batch_for_shader(shader, 'LINES',
                                 {"pos": [p0 - d * 100.0, p1 + d * 100.0]}).draw(shader)

        if right is None:
            gpu.state.depth_test_set('LESS_EQUAL')
            gpu.state.blend_set('NONE')
            return

        # Draw edge constraints: actual segment in orange, projection in red.
        if pool:
            from mathutils import Vector as _V
            _EXT = 100.0  # extension in metres for the projected line
            gpu.state.line_width_set(1.0)
            for c in pool:
                if c['type'] != 'edge':
                    continue
                p0, p1 = c['p0_world'], c['p1_world']
                seg = p1 - p0
                seg_len = seg.length
                if seg_len < 1e-8:
                    continue
                d = seg / seg_len
                far0 = p0 - d * _EXT
                far1 = p1 + d * _EXT
                # Red projected infinite line.
                shader.uniform_float("color", (1.0, 0.0, 0.0, 0.5))
                batch_for_shader(shader, 'LINES', {"pos": [far0, far1]}).draw(shader)
                # Orange actual segment on top.
                shader.uniform_float("color", (1.0, 0.7, 0.3, 0.9))
                batch_for_shader(shader, 'LINES', {"pos": [p0, p1]}).draw(shader)

        # Draw solution circles.
        selecting = self._selecting
        n_segments = self._segments
        if solutions:
            for i, (cx, cy, r, _lbl, *_) in enumerate(solutions):
                center_w = self._to_3d(cx, cy)
                if selecting and i == hover_idx:
                    # Highlighted: solid orange, segment count follows wheel.
                    pts  = circle_points(center_w, r, n_segments,
                                         self._right, self._up, phase=0.0)
                    segs = []
                    for j in range(n_segments):
                        segs.extend([pts[j], pts[(j + 1) % n_segments]])
                    gpu.state.line_width_set(1.5)
                    shader.uniform_float("color", (1.0, 0.6, 0.0, 0.9))
                    batch_for_shader(shader, 'LINES', {"pos": segs}).draw(shader)
                else:
                    # Others: white dotted at fixed resolution.
                    pts = circle_points(center_w, r, 64,
                                        self._right, self._up, phase=0.0)
                    draw_dotted_polyline(pts, closed=True, context=context)

        gpu.state.depth_test_set('LESS_EQUAL')
        gpu.state.blend_set('NONE')

    def _draw_inputs_2d(self, context):
        """POST_PIXEL: X marks for fixed point inputs."""
        try:
            pool  = self._pool
            right = self._right
        except ReferenceError:
            return

        if not pool or right is None:
            return

        region = context.region
        rv3d   = context.region_data
        if rv3d is None:
            return

        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        shader.bind()
        gpu.state.blend_set('ALPHA')
        shader.uniform_float("color", (1.0, 0.7, 0.3, 0.9))
        gpu.state.line_width_set(1.5)
        s = 6

        for c in pool:
            if c['type'] == 'point':
                co_2d = location_3d_to_region_2d(region, rv3d, c['world'])
                if co_2d is None:
                    continue
                x, y  = co_2d
                verts = [(x - s, y - s), (x + s, y + s),
                         (x + s, y - s), (x - s, y + s)]
                batch_for_shader(shader, 'LINES', {"pos": verts},
                                 indices=[(0, 1), (2, 3)]).draw(shader)

        gpu.state.blend_set('NONE')

    # ── Header / status ───────────────────────────────────────────────────────

    def _update_header(self, context, modifier=None):
        n_clicks = self._click_count
        n_pool   = len(self._pool) if self._pool else 0
        n_s      = len(self._solutions) if self._solutions else 0

        # Radius: typed > hovered solution > —
        if self._radius_input:
            r_s = self._radius_input
        elif self._typed_radius > 1e-8:
            r_s = f"{self._typed_radius:.4f}"
        elif self._solutions and 0 <= self._hover_idx < n_s:
            r_s = f"{self._solutions[self._hover_idx][2]:.4f}"
        else:
            r_s = "—"

        sol_s     = f"  |  {n_s} solutions" if n_s else ""
        hover_lbl = ""
        if self._selecting and self._solutions and 0 <= self._hover_idx < n_s:
            hover_lbl = f"  →  {self._solutions[self._hover_idx][3]}"

        has_extra   = bool(getattr(self, '_solutions_extra',   []))
        has_tangent = bool(getattr(self, '_solutions_tangent', []))
        set_lbl = ""
        if has_extra or has_tangent:
            set_lbl = "  |  EXTRA" if self._show_extra else "  |  tangent"

        phase = "  |  SELECT" if self._selecting else ""
        context.area.header_text_set(
            f"Circle (3 Inputs)  |  {n_clicks} clicks ({n_pool} constraints)  "
            f"|  Radius: {r_s}  |  Segments: {self._segments}{sol_s}{set_lbl}{phase}{hover_lbl}")

        x_label = "Extra Solutions" if not self._show_extra else "Tangents"
        self.set_status(context, modifier,
            mouse=[("Confirm", 'MOUSE_LMB'), None, ("Cancel", 'MOUSE_RMB')],
            ctrl_mouse=[("Resolution", 'MOUSE_MMB_SCROLL')],
            keys=[
                ("Undo Click", 'EVENT_BACKSPACE'),
                None,
                (x_label,      'EVENT_X'),
            ],
        )

    # ── Handler removal ───────────────────────────────────────────────────────

    def _remove_draw_handlers(self, context=None):
        global _circle3_draw_handle
        if self._draw_handle is not None:
            for h in self._draw_handle:
                bpy.types.SpaceView3D.draw_handler_remove(h, 'WINDOW')
            self._draw_handle = None
            type(self)._class_draw_handle = None
        _circle3_draw_handle = None
        if context is not None:
            self.clear_status(context)

    # ── Modal ─────────────────────────────────────────────────────────────────

    def modal(self, context, event):
        try:
            return self._modal_impl(context, event)
        except ReferenceError:
            self._remove_draw_handlers()
            return {'CANCELLED'}

    def _modal_impl(self, context, event):
        if self.left_edit_mode(context, self._started_in_edit):
            self._remove_draw_handlers(context)
            context.area.header_text_set(None)
            return {'CANCELLED'}
        nav = self.pass_through_navigation(event)
        if nav is not None:
            return nav

        mouse_2d = (event.mouse_region_x, event.mouse_region_y)
        modifier = self.modifier_from_event(event)

        # ── Modifier key press/release → update footer only ───────────────────
        if event.alt:
            self._update_header(context, modifier)
            return {'PASS_THROUGH'}

        if event.type in {'LEFT_CTRL', 'RIGHT_CTRL',
                          'LEFT_SHIFT', 'RIGHT_SHIFT'}:
            self._update_header(context, modifier)
            return {'RUNNING_MODAL'}

        # ── Mouse move ────────────────────────────────────────────────────────
        if event.type in {'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE'}:
            self.maybe_rebuild_snap(context)
            self._snap_disabled = event.ctrl

            if self._right is not None:
                raw_w   = self._mouse_to_world(context, mouse_2d)
                snapped = (self._snap.snap(mouse_2d, context, raw_world=raw_w)
                           if self._snap and not self._snap_disabled else None)
                eff_w   = snapped if snapped is not None else raw_w
                self._snap_hit = snapped
                self._mouse_2d = self._to_2d(eff_w)
                snap_type = self._snap.last_type if self._snap else None
                if snap_type == 'EDGE':
                    self._hover_edge = self._find_edge_at_world(
                        context, eff_w, threshold=float('inf'))
                else:
                    self._hover_edge = (None, None)
                if not self._selecting:
                    self._compute_solutions(self._mouse_2d)
                self._update_hover(self._mouse_2d)
                self._update_header(context, modifier)
            else:
                raw_w   = self.project_to_plane(context, mouse_2d, None,
                                                 self.depth_reference(context),
                                                 None, None)
                snapped = (self._snap.snap(mouse_2d, context, raw_world=raw_w)
                           if self._snap and not self._snap_disabled else None)
                self._snap_hit = snapped
                snap_type_pre = self._snap.last_type if self._snap else None
                if snap_type_pre == 'EDGE':
                    self._hover_edge = self._find_edge_at_world(
                        context, snapped if snapped is not None else raw_w,
                        threshold=float('inf'))
                else:
                    self._hover_edge = (None, None)

            context.area.tag_redraw()

        # ── Left click ────────────────────────────────────────────────────────
        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            if self._selecting:
                self._apply(context)
                self._remove_draw_handlers(context)
                context.area.header_text_set(None)
                return {'FINISHED'}

            if self._right is None:
                raw_w = self.project_to_plane(context, mouse_2d, None,
                                               self.depth_reference(context),
                                               None, None)
            else:
                raw_w = self._mouse_to_world(context, mouse_2d)

            snapped   = (self._snap.snap(mouse_2d, context, raw_world=raw_w)
                         if self._snap and not self._snap_disabled else None)
            world_pt  = snapped if snapped is not None else raw_w
            snap_type = self._snap.last_type if self._snap else None

            if self._right is None:
                self._init_plane(context, world_pt)
                self._mouse_2d = self._to_2d(world_pt)

            if (self._solutions and self._hover_idx >= 0
                    and snap_type not in ('VERTEX', 'MIDPOINT', 'EDGE')):
                self._selecting = True
                self._update_header(context, modifier)
                context.area.tag_redraw()
                return {'RUNNING_MODAL'}

            self._add_click(context, world_pt, snap_type)
            self._compute_solutions(self._mouse_2d)
            self._update_hover(self._mouse_2d)
            if self._click_count >= 3:
                self._compute_solutions(mouse_2d=None)
                self._update_hover(self._mouse_2d)
                if self._solutions:
                    self._selecting = True
            self._update_header(context, modifier)
            context.area.tag_redraw()

        # ── Enter / Space → confirm ───────────────────────────────────────────
        elif event.type in {'RET', 'NUMPAD_ENTER', 'SPACE'} and event.value == 'PRESS':
            if self._solutions and self._hover_idx >= 0:
                self._apply(context)
                self._remove_draw_handlers(context)
                context.area.header_text_set(None)
                return {'FINISHED'}

        # ── Navigation passthrough (MMB for pan/rotate) ──────────────────────
        elif event.type == 'MIDDLEMOUSE':
            return {'PASS_THROUGH'}

        # ── Wheel → segment count (Ctrl) or passthrough (zoom) ───────────────
        elif event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE'} and event.value == 'PRESS':
            if event.ctrl and self._right is not None:
                self._segments = (min(self._segments + 1, 256)
                                  if event.type == 'WHEELUPMOUSE'
                                  else max(self._segments - 1, 3))
                self._update_header(context, modifier)
                context.area.tag_redraw()
            else:
                return {'PASS_THROUGH'}

        # ── Numeric radius input ──────────────────────────────────────────────
        elif event.value == 'PRESS' and event.type in CAD_CHAR_MAP:
            self._radius_input += CAD_CHAR_MAP[event.type]
            val = self.eval_number(self._radius_input)
            self._typed_radius = abs(val) if val is not None else 0.0
            self._compute_solutions(self._mouse_2d)
            self._update_hover(self._mouse_2d)
            self._update_header(context)
            context.area.tag_redraw()

        # ── Backspace → undo radius digit or last click ───────────────────────
        elif event.type == 'BACK_SPACE' and event.value == 'PRESS':
            if self._selecting:
                self._selecting = False
                self._update_header(context)
                context.area.tag_redraw()
                return {'RUNNING_MODAL'}
            if self._radius_input:
                self._radius_input = self._radius_input[:-1]
                val = self.eval_number(self._radius_input)
                self._typed_radius = abs(val) if val is not None else 0.0
            elif self._pool:
                self._pop_last_click()
                if not self._pool:
                    self._right        = None
                    self._up           = None
                    self._plane_normal = None
                    self._plane_ref_pt = None
                    self._mouse_2d     = None
            self._compute_solutions(self._mouse_2d)
            self._update_hover(self._mouse_2d)
            self._update_header(context, modifier)
            context.area.tag_redraw()

        # ── X → toggle tangent / extra solutions ─────────────────────────────
        elif event.type == 'X' and event.value == 'PRESS':
            self._show_extra = not self._show_extra
            self._solutions = (self._solutions_extra if self._show_extra
                               else self._solutions_tangent)
            self._update_hover(self._mouse_2d)
            self._update_header(context, modifier)
            context.area.tag_redraw()

        # ── Cancel ────────────────────────────────────────────────────────────
        elif event.type in {'RIGHTMOUSE', 'ESC'} and event.value == 'PRESS':
            self._remove_draw_handlers(context)
            context.area.header_text_set(None)
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    # ── Invoke ────────────────────────────────────────────────────────────────

    def invoke(self, context, event):
        self._started_in_edit = context.mode == 'EDIT_MESH'
        self._right         = None
        self._up            = None
        self._plane_normal  = None
        self._plane_ref_pt  = None
        self._pool          = []
        self._click_count   = 0
        self._radius_input  = ""
        self._typed_radius  = 0.0
        self._solutions          = []
        self._solutions_tangent  = []
        self._solutions_extra    = []
        self._hover_idx          = -1
        self._show_extra         = False
        self._segments           = 32
        self._selecting          = False
        self._snap_hit      = None
        self._snap_disabled = False
        self._hover_edge    = (None, None)
        self._mouse_2d      = None
        self._snap          = SnapContext(context, select_modes=())
        if self._snap._enabled and not self._snap._do_edge:
            self._snap._do_edge = True
            self._snap._build(context)

        global _circle3_draw_handle
        h3d = bpy.types.SpaceView3D.draw_handler_add(
            self._draw_preview,   (context,), 'WINDOW', 'POST_VIEW')
        h2d = bpy.types.SpaceView3D.draw_handler_add(
            self._draw_snap,      (context,), 'WINDOW', 'POST_PIXEL')
        h2b = bpy.types.SpaceView3D.draw_handler_add(
            self._draw_inputs_2d, (context,), 'WINDOW', 'POST_PIXEL')
        self._draw_handle            = (h3d, h2d, h2b)
        type(self)._class_draw_handle = self._draw_handle
        _circle3_draw_handle          = self._draw_handle

        self._update_header(context)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
