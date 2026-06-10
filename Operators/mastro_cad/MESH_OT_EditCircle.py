"""Edit Circle / Arc operator.

Alt+G on a circle or arc vertex/edge:

  Radius handle  : mouse → change radius + rotation; wheel → resolution (n_total)
  Center handle  : mouse → translate whole shape
  Arc handles (> <): mouse → extend/trim arc endpoints step by step;
                     wheel → resolution; arc span stays fixed, endpoints don't move

Ctrl  : disable snap while held
LMB / Enter : confirm
RMB / ESC   : cancel
"""

import math
import bpy
import bmesh
from bpy_extras.view3d_utils import (location_3d_to_region_2d,
                                     region_2d_to_origin_3d,
                                     region_2d_to_vector_3d)
import gpu
from gpu_extras.batch import batch_for_shader

from ...Utils.mastro_cad.cad.circle_utils import (check_circle, get_circle_layers,
                                       ensure_circle_layers, set_circle_attrs,
                                       circle_plane_axes, arc_circumcenter_world)
from ...Utils.mastro_cad.cad.snap_utils import SnapContext
from .CAD_mixin import CadMixin, CAD_CHAR_MAP
from ...Utils.mastro_cad.cad.constants import HANDLE_SIZE_PX, HANDLE_GRAB_RADIUS_PX
from ...Utils.mastro_cad.cad.gpu_utils import draw_dotted_line

_TWO_PI = 2.0 * math.pi
_circle_edit_draw_handle = None
_arc_prop_updating = False   # prevents circular updates between arc_span and chord


def _update_chord(self, context):
    global _arc_prop_updating
    if _arc_prop_updating:
        return
    _arc_prop_updating = True
    if self.radius > 1e-8:
        if self.chord < 1e-8:
            self.arc_span = _TWO_PI          # chord = 0 → full circle
        else:
            half  = min(1.0, self.chord / (2.0 * self.radius))
            span1 = 2.0 * math.asin(half)   # first half:  0 → π
            span2 = _TWO_PI - span1          # second half: 2π → π
            # Pick the solution closest to the current arc_span.
            if abs(self.arc_span - span2) < abs(self.arc_span - span1):
                self.arc_span = span2
            else:
                self.arc_span = span1
    _arc_prop_updating = False


def _update_arc_span(self, context):
    global _arc_prop_updating
    if _arc_prop_updating:
        return
    _arc_prop_updating = True
    self.chord = 2.0 * self.radius * math.sin(self.arc_span / 2.0)
    _arc_prop_updating = False


class MESH_OT_MaStroCad_EditCircle(CadMixin, bpy.types.Operator):
    """Edit a tagged circle or arc — radius, move, and arc endpoints."""
    bl_idname  = "mastrocad.edit_circle"
    bl_label   = "Edit Circle"
    bl_options = {'REGISTER', 'UNDO'}

    # ── F9 properties ─────────────────────────────────────────────────────────
    radius: bpy.props.FloatProperty(
        name="Radius", min=1e-4, default=1.0, unit='LENGTH')
    n_total: bpy.props.IntProperty(
        name="Segments", min=3, max=256, default=16)
    arc_span: bpy.props.FloatProperty(
        name="Arc Span", min=math.radians(1), max=_TWO_PI,
        default=math.radians(350), subtype='ANGLE',
        update=_update_arc_span)
    chord: bpy.props.FloatProperty(
        name="Chord", min=0.0, default=1.0, unit='LENGTH',
        update=_update_chord)
    # Hidden: fillet arc flag — restricts F9 to resolution only.
    is_fillet_prop: bpy.props.BoolProperty(options={'HIDDEN'})
    # Hidden: full-circle flag — avoids float32 precision issues with arc_span≈2π.
    is_full_prop: bpy.props.BoolProperty(options={'HIDDEN'})
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        import math as _m
        if self.is_fillet_prop:
            layout.prop(self, 'n_total', text="Segments")
        else:
            layout.prop(self, 'radius')
            layout.prop(self, 'n_total', text="Segments")
            layout.prop(self, 'arc_span')
            layout.prop(self, 'chord')
    # Hidden: world position of arc midpoint for orientation preservation in F9.
    f9_mid_x: bpy.props.FloatProperty(options={'HIDDEN'})
    f9_mid_y: bpy.props.FloatProperty(options={'HIDDEN'})
    f9_mid_z: bpy.props.FloatProperty(options={'HIDDEN'})

    _draw_handle    = None
    _center         = None
    _radius         = 0.0
    _n_total        = 16      # full-circle resolution (snapping grid)
    _right          = None
    _up             = None
    _plane_normal   = None
    # _handle_angle: angle of the "base" direction (= where vertex index 0 sits
    #                on the full circle grid).  Does NOT equal the radius handle
    #                angle unless arc_start_angle + arc_span/2 == 0.
    _handle_angle   = 0.0
    _handle_world   = None    # world position of radius handle (= arc midpoint)
    _preview_pts    = None
    _snap           = None
    _snap_hit       = None
    _snap_disabled  = False
    _number_input   = ""
    # mode: 'RADIUS' | 'MOVE' | 'ARC_START' | 'ARC_END'
    _mode           = 'RADIUS'
    # Arc geometry stored as float angles (independent of n_total).
    # _arc_start_angle: CCW offset of the > endpoint from _handle_angle (radians).
    # _arc_span: CCW angular span of the arc (radians, 0 < span <= 2π).
    # Full circle: _arc_span == _TWO_PI.
    _arc_start_angle = math.pi
    _arc_span        = _TWO_PI
    _is_full_circle  = True
    _is_fillet       = False   # True when editing a fillet arc (resolution-only)
    # Saved arc state for C toggle (full circle ↔ arc)
    _saved_arc_start = math.pi
    _saved_arc_span  = math.radians(350)   # default when first switching to arc with A
    # Original state for selection restoration
    _vert_indices      = None
    _edge_indices      = None
    _orig_n_total      = 0
    _orig_arc_start    = 0.0
    _orig_arc_span     = _TWO_PI
    _orig_is_full      = True
    _vert_sel_by_pos   = None
    _edge_sel_by_pos   = None
    _active_pos        = None
    _active_is_edge    = False

    # ── Arc geometry helpers ──────────────────────────────────────────────────

    def _vertex_r(self):
        # Edge-midpoint grab: _radius is the chord radius (center→midpoint).
        # Compensate to get the circumscribed vertex radius, exactly as the
        # creation operator does for midpoint snap.
        if getattr(self, '_handle_is_edge', False):
            n = self._n_arc_edges()
            if n > 0:
                return self._radius / math.cos(math.pi / n)
        return self._radius

    def _pt_at_angle(self, angle):
        """World point on the circle at absolute angle `angle`, at vertex radius."""
        r = self._vertex_r()
        return (self._center
                + self._right * math.cos(angle) * r
                + self._up    * math.sin(angle) * r)

    def _pt_at_angle_handle(self, angle):
        """World point at handle radius (= _radius) at absolute angle `angle`."""
        r = self._radius
        return (self._center
                + self._right * math.cos(angle) * r
                + self._up    * math.sin(angle) * r)

    def _arc_start_world(self):
        return self._pt_at_angle_handle(self._arc_start_angle)

    def _arc_end_world(self):
        return self._pt_at_angle_handle(self._arc_start_angle + self._arc_span)

    def _arc_mid_world(self):
        """Geometric midpoint on the circle — used for radius and rotation computation."""
        return self._pt_at_angle(self._arc_start_angle + self._arc_span / 2)

    def _arc_handle_visual(self):
        """Visual position of the radius handle — on the actual polyline edge.

        For even n_e: coincides with the center vertex (on the circle).
        For odd n_e: midpoint of the center edge (chord, inside the circle).
        """
        n_e = self._n_arc_edges()
        mid_idx = n_e // 2
        a0 = self._arc_start_angle + self._arc_span * mid_idx / n_e
        if n_e % 2 == 0:
            return self._pt_at_angle(a0)
        a1 = self._arc_start_angle + self._arc_span * (mid_idx + 1) / n_e
        return (self._pt_at_angle(a0) + self._pt_at_angle(a1)) * 0.5

    def _n_arc_edges(self):
        """Integer number of edges in the current arc."""
        if self._is_full_circle:
            return self._n_total
        return max(1, round(self._arc_span / _TWO_PI * self._n_total))

    def _compute_preview_pts(self):
        n_e = self._n_arc_edges()
        n_v = n_e if self._is_full_circle else n_e + 1
        pts = []
        if self._is_full_circle and n_e > 0:
            if getattr(self, '_handle_is_edge', False):
                # Edge-midpoint grab: edge _edge_grab_idx midpoint tracks handle_angle.
                # base = handle_angle - (ei + 0.5) * step  →  no rotation on invoke.
                ei   = getattr(self, '_edge_grab_idx', n_e // 2)
                base = self._handle_angle - (ei + 0.5) * _TWO_PI / n_e
            else:
                # Vertex grab: vertex n//2 lands at handle_angle.
                base = self._handle_angle - (n_e // 2) * _TWO_PI / n_e
        else:
            base = self._arc_start_angle
        for i in range(n_v):
            if self._is_full_circle:
                a = base + _TWO_PI * i / n_e
            else:
                a = base + self._arc_span * i / n_e
            pts.append(self._pt_at_angle(a))
        return pts

    def _mouse_to_angle(self, mouse_2d, context):
        """Absolute angle on the circle plane under the mouse."""
        raw = self._mouse_on_plane(context, mouse_2d)
        if raw is None:
            return None
        d = raw - self._center
        return math.atan2(d.dot(self._up), d.dot(self._right))

    # ── GPU preview (POST_VIEW) ───────────────────────────────────────────────

    def _draw_preview(self, context):
        try:
            pts     = self._preview_pts
            handle  = self._handle_world
            center  = self._center
            is_full = self._is_full_circle
            mode    = self._mode
        except ReferenceError:
            MESH_OT_MaStroCad_EditCircle._gc_cleanup()
            return
        if not pts:
            return

        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        shader.bind()
        gpu.state.blend_set('ALPHA')
        gpu.state.depth_test_set('NONE')

        n    = len(pts)
        segs = []
        if is_full:
            for i in range(n):
                segs.extend([pts[i], pts[(i + 1) % n]])
        else:
            for i in range(n - 1):
                segs.extend([pts[i], pts[i + 1]])
        gpu.state.line_width_set(1.5)
        shader.uniform_float("color", (1.0, 0.6, 0.0, 0.8))
        batch_for_shader(shader, 'LINES', {"pos": segs}).draw(shader)

        if center is not None and handle is not None and mode == 'RADIUS' and not self._is_fillet:
            vis = handle if self._is_full_circle else self._arc_handle_visual()
            draw_dotted_line(center, vis, context)

        gpu.state.depth_test_set('LESS_EQUAL')
        gpu.state.blend_set('NONE')

    # ── GPU handles (POST_PIXEL) ──────────────────────────────────────────────

    def _draw_handles(self, context):
        try:
            handle      = self._handle_world
            center      = self._center
            snap_hit    = self._snap_hit
            mode        = self._mode
            arc_start_w = self._arc_start_world()
            arc_end_w   = self._arc_end_world()
        except ReferenceError:
            return
        if handle is None or center is None:
            return

        rv3d   = context.region_data
        region = context.region
        if rv3d is None or region is None:
            return

        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        shader.bind()
        gpu.state.blend_set('ALPHA')

        from ...Utils.mastro_cad.cad.constants import HANDLE_THICK_PADDING_PX
        from ...Utils.mastro_cad.cad.gpu_utils import radius_to_pixels
        obj = context.active_object
        thick_px = 0.0
        if obj is not None:
            import bmesh as _bm
            bm_tmp = _bm.from_edit_mesh(obj.data)
            thick_layer = bm_tmp.edges.layers.float.get("mastro_drawing_thickness")
            if thick_layer is not None:
                bm_tmp.edges.ensure_lookup_table()
                sel_edges = [e for e in bm_tmp.edges if e.select]
                if sel_edges:
                    max_thick = max(e[thick_layer] for e in sel_edges)
                    thick_px = radius_to_pixels(context, max_thick) if max_thick > 0.0 else 0.0
        s = max(HANDLE_SIZE_PX, thick_px + HANDLE_THICK_PADDING_PX)
        gpu.state.line_width_set(2.0)

        def _square(pt_world):
            co_2d = location_3d_to_region_2d(region, rv3d, pt_world)
            if co_2d is None:
                return
            x, y = co_2d
            verts   = [(x-s, y-s), (x+s, y-s), (x+s, y+s), (x-s, y+s)]
            indices = ((0, 1), (1, 2), (2, 3), (3, 0))
            batch_for_shader(shader, 'LINES',
                             {"pos": verts}, indices=indices).draw(shader)

        def _circle_handle(pt_world):
            co_2d = location_3d_to_region_2d(region, rv3d, pt_world)
            if co_2d is None:
                return
            x, y   = co_2d
            segs   = 12
            verts  = [(x + s * math.cos(math.pi * 2 * i / segs),
                       y + s * math.sin(math.pi * 2 * i / segs))
                      for i in range(segs)]
            lines  = []
            for i in range(segs):
                lines.extend([verts[i], verts[(i + 1) % segs]])
            batch_for_shader(shader, 'LINES', {"pos": lines}).draw(shader)

        grabbed_world = {
            'RADIUS':    handle,
            'MOVE':      center,
            'ARC_START': arc_start_w,
            'ARC_END':   arc_end_w,
        }.get(mode, handle)

        snapping = snap_hit is not None and self._snap is not None

        shader.uniform_float("color", (1.0, 0.6, 0.0, 1.0))

        if self._is_fillet:
            # Fillet: circle handle at active vertex (visually distinct from square).
            if snap_hit is not None and self._snap is not None:
                self._snap.draw_indicator(snap_hit, context)
            else:
                _circle_handle(handle)
            gpu.state.blend_set('NONE')
            return

        is_full = self._is_full_circle
        vis_handle = handle if is_full else self._arc_handle_visual()
        handles = [
            (handle,      lambda: _square(vis_handle)),
            (center,      lambda: _circle_handle(center)),
        ]
        if not is_full:
            handles += [
                (arc_start_w, lambda: _circle_handle(arc_start_w)),
                (arc_end_w,   lambda: _circle_handle(arc_end_w)),
            ]
        for pt, draw_fn in handles:
            if snapping and pt is grabbed_world:
                continue
            draw_fn()

        if snapping:
            self._snap.draw_indicator(snap_hit, context)

        gpu.state.line_width_set(1.0)
        gpu.state.blend_set('NONE')

    # ── Plane projection ──────────────────────────────────────────────────────

    def _mouse_on_plane(self, context, mouse_2d):
        rv3d   = context.region_data
        region = context.region
        if rv3d is None or region is None:
            return None
        ray_o = region_2d_to_origin_3d(region, rv3d, mouse_2d)
        ray_d = region_2d_to_vector_3d(region, rv3d, mouse_2d)
        denom = ray_d.dot(self._plane_normal)
        if abs(denom) > 1e-8:
            t = ((self._center.dot(self._plane_normal) -
                  ray_o.dot(self._plane_normal)) / denom)
            return ray_o + ray_d * t
        from bpy_extras.view3d_utils import region_2d_to_location_3d
        return region_2d_to_location_3d(region, rv3d, mouse_2d, self._center)

    # ── Preview update ────────────────────────────────────────────────────────

    def _update_preview(self, context, mouse_2d, update_handle=True):
        if self._mode == 'MOVE':
            if update_handle:
                raw_pt  = self._mouse_on_plane(context, mouse_2d)
                snapped = (self._snap.snap(mouse_2d, context, raw_world=raw_pt)
                           if self._snap and not self._snap_disabled else None)
                self._snap_hit = snapped
                self._center   = snapped if snapped is not None else raw_pt
            if self._is_full_circle:
                self._handle_world = self._pt_at_angle_handle(self._handle_angle)
            else:
                self._handle_world = self._arc_mid_world()
        else:  # RADIUS
            if update_handle:
                raw_pt  = self._mouse_on_plane(context, mouse_2d)
                snapped = (self._snap.snap(mouse_2d, context,
                                           raw_world=raw_pt,
                                           origin_world=self._center,
                                           perp_center=self._center)
                           if self._snap and not self._snap_disabled else None)
                ref = snapped if snapped is not None else raw_pt
                self._snap_hit = snapped

                d  = ref - self._center
                dx = d.dot(self._right)
                dy = d.dot(self._up)
                mouse_angle = math.atan2(dy, dx)
                self._handle_angle = mouse_angle
                if not self._is_full_circle:
                    # Arc: rotate so the midpoint follows the mouse.
                    self._arc_start_angle = mouse_angle - self._arc_span / 2
                if self._number_input:
                    r = self.eval_number(self._number_input)
                    if r is not None:
                        self._radius = abs(r)
                else:
                    self._radius = math.sqrt(dx * dx + dy * dy)

            if self._is_full_circle:
                self._handle_world = self._pt_at_angle_handle(self._handle_angle)
            else:
                self._handle_world = self._arc_mid_world()

        self._preview_pts = self._compute_preview_pts()
        self._update_header(context)

    def _update_arc_handle(self, context, mouse_2d):
        """Drag an arc endpoint freely along the circle."""
        snapped = self._mouse_to_angle(mouse_2d, context)
        if snapped is None:
            return

        arc_end_unwrapped = self._arc_start_angle + self._arc_span

        if self._mode == 'ARC_START':
            new_span = (arc_end_unwrapped - snapped) % _TWO_PI
            if new_span < 1e-8:
                return  # degenerate
            self._arc_start_angle = snapped % _TWO_PI
            self._arc_span        = new_span
        else:  # ARC_END
            new_span = (snapped - self._arc_start_angle) % _TWO_PI
            if new_span < 1e-8:
                return  # degenerate
            self._arc_span = new_span

        self._is_full_circle = abs(self._arc_span - _TWO_PI) < 1e-8
        self._refresh_preview(context)

    def _refresh_preview(self, context):
        """Recompute preview after a parameter change (n_total, arc_span, A).

        Fillet arcs: endpoints stay fixed at their hidden-vertex positions;
        interior vertices redistribute at avg_r — same logic as _apply fillet.

        Regular circles/arcs: recompute from the current handle world position
        in 3D (no screen round-trip), then rebuild via _compute_preview_pts.
        """
        if self._is_fillet and self._vert_indices:
            # Read actual endpoint positions from the hidden mesh vertices.
            obj = context.active_object
            bm  = bmesh.from_edit_mesh(obj.data)
            bm.verts.ensure_lookup_table()
            mw     = obj.matrix_world
            mw_inv = mw.inverted()
            old_verts = [bm.verts[i] for i in self._vert_indices]
            avg_r = (sum((mw @ v.co - self._center).length for v in old_verts)
                     / len(old_verts))
            d0 = (mw @ old_verts[0].co) - self._center
            a0 = math.atan2(d0.dot(self._up), d0.dot(self._right))
            d1 = (mw @ old_verts[-1].co) - self._center
            a1 = math.atan2(d1.dot(self._up), d1.dot(self._right))
            f_span = (a1 - a0) % _TWO_PI
            if f_span < 1e-8:
                f_span = _TWO_PI
            n_e = self._n_arc_edges()      # arc edges, consistent with header/apply

            def _fpt(i):
                a = a0 + f_span * i / n_e
                return (self._center
                        + self._right * math.cos(a) * avg_r
                        + self._up    * math.sin(a) * avg_r)

            self._preview_pts = [_fpt(i) for i in range(n_e + 1)]
            self._handle_world = self._preview_pts[len(self._preview_pts) // 2]
        else:
            if (self._handle_world is not None
                    and self._mode not in {'ARC_START', 'ARC_END', 'MOVE'}):
                d  = self._handle_world - self._center
                dx = d.dot(self._right)
                dy = d.dot(self._up)
                mouse_angle = math.atan2(dy, dx)
                self._handle_angle = (mouse_angle
                                      - self._arc_start_angle
                                      - self._arc_span / 2)
                if not self._number_input:
                    self._radius = math.sqrt(dx * dx + dy * dy)
            self._handle_world = self._arc_mid_world()
            self._preview_pts  = self._compute_preview_pts()
        self._update_header(context)

    def _update_header(self, context, modifier=None):
        if self._is_fillet:
            context.area.header_text_set(
                f"Edit Fillet Arc  |  Segments: {self._n_arc_edges()}")
            self.set_status(context, modifier,
                mouse=[("Confirm", 'MOUSE_LMB'), None, ("Cancel", 'MOUSE_RMB')],
                ctrl_mouse=[("Resolution", 'MOUSE_MMB_SCROLL')],
            )
            return
        if self._mode == 'MOVE':
            c = self._center
            context.area.header_text_set(
                f"Move Circle  |  ({c.x:.4f}, {c.y:.4f}, {c.z:.4f})")
            self.set_status(context, modifier,
                mouse=[("Confirm", 'MOUSE_LMB'), None, ("Cancel", 'MOUSE_RMB')],
                alt_keys=[("Edit Circle/Arc", 'EVENT_G')],
            )
        elif self._mode in {'ARC_START', 'ARC_END'}:
            deg = math.degrees(self._arc_span)
            context.area.header_text_set(
                f"Edit Arc  |  Span: {deg:.1f}°  |  Segments: {self._n_arc_edges()}")
            self.set_status(context, modifier,
                mouse=[("Confirm", 'MOUSE_LMB'), None, ("Cancel", 'MOUSE_RMB')],
                ctrl_mouse=[("Resolution", 'MOUSE_MMB_SCROLL')],
                keys=[("Circle", 'EVENT_A')],
                alt_keys=[("Edit Circle/Arc", 'EVENT_G')],
            )
        else:  # RADIUS
            r_str = self._number_input if self._number_input else f"{self._radius:.4f}"
            if self._is_full_circle:
                label = "Circle"
                n_str = f"Segments: {self._n_total}"
            else:
                label = f"Arc {math.degrees(self._arc_span):.1f}°"
                n_str = f"Segments: {self._n_arc_edges()}"
            context.area.header_text_set(
                f"Edit {label}  |  Radius: {r_str}  |  {n_str}")
            self.set_status(context, modifier,
                mouse=[("Confirm", 'MOUSE_LMB'), None, ("Cancel", 'MOUSE_RMB')],
                ctrl_mouse=[("Resolution", 'MOUSE_MMB_SCROLL')],
                keys=[("Arc/Circle", 'EVENT_A')],
                alt_keys=[("Edit Circle/Arc", 'EVENT_G')],
            )

    # ── Mesh helpers ──────────────────────────────────────────────────────────

    def _set_hidden(self, obj, hidden):
        self.set_geometry_hidden(obj, self._vert_indices, self._edge_indices, hidden)

    def _apply(self, context):
        obj    = context.active_object
        bm     = bmesh.from_edit_mesh(obj.data)
        mw     = obj.matrix_world
        mw_inv = mw.inverted()
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()

        old_verts = [bm.verts[i] for i in self._vert_indices]
        old_edges = [bm.edges[i] for i in self._edge_indices]
        if not self._is_fillet:
            for v in old_verts: v.hide_set(False)
            for e in old_edges: e.hide_set(False)

        # Capture drawing attrs before any deletion (refs become invalid after).
        from ...Utils.mastro_cad.cad.cad_utils import get_attr_layers
        attr_layers = get_attr_layers(bm)
        saved_attrs = ({name: old_edges[0][layer]
                        for name, layer in attr_layers.items()}
                       if attr_layers and old_edges else {})

        if self._is_fillet:
            # Compute avg_r BEFORE deletion (references become invalid after).
            avg_r = (sum((mw @ v.co - self._center).length for v in old_verts)
                     / len(old_verts))
            if old_verts[1:-1]:
                bmesh.ops.delete(bm, geom=old_verts[1:-1], context='VERTS')
            bm.verts.ensure_lookup_table()
            bm.edges.ensure_lookup_table()
        else:
            bmesh.ops.delete(bm, geom=old_edges + old_verts, context='VERTS')

        layers = ensure_circle_layers(bm)
        pts    = self._preview_pts
        n_pts  = len(pts)

        if self._is_fillet:
            # avg_r was computed before deletion (see above).
            a0  = self._handle_angle + self._arc_start_angle
            n_e = max(1, round(self._arc_span / _TWO_PI * self._n_total))

            def _arc_pt(idx):
                a = a0 + self._arc_span * idx / n_e
                return (self._center
                        + self._right * math.cos(a) * avg_r
                        + self._up    * math.sin(a) * avg_r)

            all_pts = [_arc_pt(i) for i in range(n_e + 1)]

            # Reposition endpoints to the exact equiangular position.
            old_verts[0].co  = mw_inv @ all_pts[0]
            old_verts[-1].co = mw_inv @ all_pts[-1]

            inner = [bm.verts.new(mw_inv @ p) for p in all_pts[1:-1]]
            verts = [old_verts[0]] + inner + [old_verts[-1]]
            edges = [bm.edges.new((verts[i], verts[i + 1]))
                     for i in range(len(verts) - 1)]
        else:
            verts = [bm.verts.new(mw_inv @ p) for p in pts]
            if self._is_full_circle:
                edges = [bm.edges.new((verts[i], verts[(i + 1) % n_pts]))
                         for i in range(n_pts)]
            else:
                edges = [bm.edges.new((verts[i], verts[i + 1]))
                         for i in range(n_pts - 1)]

        tag = b"Fillet" if self._is_fillet else b"Circle"
        set_circle_attrs(bm, verts, edges, self._n_total, layers=layers,
                         type_tag=tag)

        if saved_attrs:
            attr_layers = get_attr_layers(bm)
            if attr_layers:
                for e in edges:
                    for name, layer in attr_layers.items():
                        e[layer] = saved_attrs[name]

        shape_unchanged = (self._n_total        == self._orig_n_total     and
                           abs(self._arc_start_angle - self._orig_arc_start) < 1e-8 and
                           abs(self._arc_span        - self._orig_arc_span)  < 1e-8)
        # For full circles, arc_start_angle=π shifts vertex 0 to the opposite
        # side, so chain-position restoration lands on the wrong vertex.
        # Always use the mid-vertex path for full circles.
        if shape_unchanged and not self._is_full_circle:
            for i, v in enumerate(verts):
                v.select = (self._vert_sel_by_pos[i]
                            if i < len(self._vert_sel_by_pos) else False)
            for i, e in enumerate(edges):
                e.select = (self._edge_sel_by_pos[i]
                            if i < len(self._edge_sel_by_pos) else False)
            if self._active_pos is not None:
                if self._active_is_edge and self._active_pos < len(edges):
                    bm.select_history.add(edges[self._active_pos])
                elif not self._active_is_edge and self._active_pos < len(verts):
                    bm.select_history.add(verts[self._active_pos])
        else:
            if (self._is_full_circle and getattr(self, '_handle_is_edge', False)
                    and self._edge_grab_idx < len(edges)):
                e_sel = edges[self._edge_grab_idx]
                e_sel.select = True
                bm.select_history.add(e_sel)
            else:
                mid = verts[len(verts) // 2]
                mid.select = True
                bm.select_history.add(mid)

        bmesh.update_edit_mesh(obj.data)

        # Store state for F9 panel.
        self.radius         = self._radius
        # For arcs, store arc segment count in n_total so the F9 panel shows
        # the number of visible segments, not the full-circle resolution.
        self.n_total        = self._n_total if self._is_full_circle else self._n_arc_edges()
        self.arc_span       = self._arc_span
        self.chord          = 2.0 * self._radius * math.sin(self._arc_span / 2.0)
        self.is_fillet_prop = self._is_fillet
        self.is_full_prop   = self._is_full_circle
        mid = self._arc_mid_world()
        self.f9_mid_x, self.f9_mid_y, self.f9_mid_z = mid.x, mid.y, mid.z

    def _restore(self, context):
        if self._is_fillet:
            return   # geometry was never hidden
        obj = context.active_object
        bm  = bmesh.from_edit_mesh(obj.data)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        for i in self._vert_indices:
            bm.verts[i].hide_set(False)
        for i in self._edge_indices:
            bm.edges[i].hide_set(False)
        bmesh.update_edit_mesh(obj.data)

    def _remove_handlers(self):
        global _circle_edit_draw_handle
        if self._draw_handle is not None:
            for h in self._draw_handle:
                bpy.types.SpaceView3D.draw_handler_remove(h, 'WINDOW')
            self._draw_handle        = None
            _circle_edit_draw_handle = None

    def _tag_redraw(self, context):
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

    # ── Modal ─────────────────────────────────────────────────────────────────

    def modal(self, context, event):
        if self.left_edit_mode(context, self._started_in_edit):
            self._remove_handlers()
            self.clear_status(context)
            context.area.header_text_set(None)
            return {'CANCELLED'}
        nav = self.pass_through_navigation(event)
        if nav is not None:
            return nav
        mouse_2d = (event.mouse_region_x, event.mouse_region_y)
        modifier = self.modifier_from_event(event)

        if event.type in {'LEFT_CTRL', 'RIGHT_CTRL', 'LEFT_SHIFT', 'RIGHT_SHIFT'}:
            self._update_header(context, modifier)
            return {'RUNNING_MODAL'}

        if event.alt:
            self._update_header(context, modifier)
            return {'PASS_THROUGH'}

        if self._is_fillet:
            # Fillet arcs: only resolution (Ctrl+wheel) is editable.
            if event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE'} and event.value == 'PRESS':
                if not event.ctrl:
                    return {'PASS_THROUGH'}
                n_old = self._n_total
                n_new = (min(n_old + 1, 256) if event.type == 'WHEELUPMOUSE'
                         else max(n_old - 1, 3))
                if n_new != n_old:
                    self._n_total = n_new
                self._refresh_preview(context)
                self._tag_redraw(context)
            elif event.type in {'RET', 'NUMPAD_ENTER', 'LEFTMOUSE'} and event.value == 'PRESS':
                self._apply(context)
                self._remove_handlers()
                self.clear_status(context)
                context.area.header_text_set(None)
                return {'FINISHED'}
            elif event.type in {'RIGHTMOUSE', 'ESC'} and event.value == 'PRESS':
                self._restore(context)
                self._remove_handlers()
                self.clear_status(context)
                context.area.header_text_set(None)
                return {'CANCELLED'}
            return {'RUNNING_MODAL'}

        if event.type in {'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE'}:
            self.maybe_rebuild_snap(context)
            self._snap_disabled = event.ctrl
            if self._mode in {'ARC_START', 'ARC_END'}:
                self._update_arc_handle(context, mouse_2d)
            else:
                self._update_preview(context, mouse_2d, update_handle=True)
            self._tag_redraw(context)

        elif event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE'} and event.value == 'PRESS':
            if not event.ctrl:
                return {'PASS_THROUGH'}
            up = event.type == 'WHEELUPMOUSE'
            if self._is_fillet:
                n_arc = self._n_arc_edges()
                n_arc = min(n_arc + 1, 256) if up else max(n_arc - 1, 1)
                span  = self._arc_span if self._arc_span > 1e-8 else 1e-8
                self._n_total = max(3, round(n_arc * _TWO_PI / span))
            else:
                n_old = self._n_total
                n_new = (min(n_old + 1, 256) if up else max(n_old - 1, 3))
                if n_new != n_old:
                    self._n_total = n_new
            self._refresh_preview(context)
            self._tag_redraw(context)

        elif event.type == 'A' and event.value == 'PRESS':
            # Current midpoint offset (= where the radius handle sits).
            cur_mid = (self._arc_start_angle + self._arc_span / 2) % _TWO_PI
            if self._is_full_circle:
                # Switch to arc: open symmetrically around current midpoint.
                new_span              = self._saved_arc_span
                self._arc_start_angle = (cur_mid - new_span / 2) % _TWO_PI
                self._arc_span        = new_span
                self._is_full_circle  = False
            else:
                # Switch to full circle: save span, keep midpoint.
                self._saved_arc_span  = self._arc_span
                self._arc_start_angle = (cur_mid - math.pi) % _TWO_PI
                self._arc_span        = _TWO_PI
                self._is_full_circle  = True
            # Keep radius or move handle; never stay on arc handles after toggle.
            if self._mode in {'ARC_START', 'ARC_END'}:
                self._mode = 'RADIUS'
            self._refresh_preview(context)
            self._tag_redraw(context)

        elif event.value == 'PRESS' and event.type in CAD_CHAR_MAP:
            if self._mode == 'RADIUS':
                self._number_input += CAD_CHAR_MAP[event.type]
                self._update_preview(context, mouse_2d, update_handle=True)
                self._tag_redraw(context)

        elif event.value == 'PRESS' and event.type == 'BACK_SPACE':
            if self._mode == 'RADIUS' and self._number_input:
                self._number_input = self._number_input[:-1]
                self._update_preview(context, mouse_2d, update_handle=True)
                self._tag_redraw(context)

        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            self._apply(context)
            self._remove_handlers()
            self.clear_status(context)
            context.area.header_text_set(None)
            return {'FINISHED'}

        elif event.type in {'RET', 'NUMPAD_ENTER'} and event.value == 'PRESS':
            self._apply(context)
            self._remove_handlers()
            self.clear_status(context)
            context.area.header_text_set(None)
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'} and event.value == 'PRESS':
            self._restore(context)
            self._remove_handlers()
            self.clear_status(context)
            context.area.header_text_set(None)
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    # ── Execute (F9 re-apply) ─────────────────────────────────────────────────

    def execute(self, context):
        """Re-apply with current F9 properties on the selected circle/arc."""
        obj = context.active_object
        if obj is None or context.mode != 'EDIT_MESH':
            return {'CANCELLED'}

        bm = bmesh.from_edit_mesh(obj.data)
        active = self.active_seed(bm)
        if active is None:
            return {'CANCELLED'}

        ok, chain_verts, chain_edges, is_closed = check_circle(bm, active)
        if not ok:
            return {'CANCELLED'}

        mw     = obj.matrix_world
        mw_inv = mw.inverted()
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()

        # Determine handle reference from active element.
        if isinstance(active, bmesh.types.BMVert) and active in chain_verts:
            handle_world = mw @ active.co
        else:
            handle_world = mw @ chain_verts[len(chain_verts) // 2].co

        center = arc_circumcenter_world(chain_verts, mw)
        right, up, normal, _ = circle_plane_axes(chain_verts, mw,
                                                  handle_world, center)
        d  = handle_world - center
        handle_angle = math.atan2(d.dot(up), d.dot(right))

        # Full circle: arc_span ≈ 2π.  Tolerance 1e-6 covers both float32
        # drift (~1.7e-7) and the case where the user sets span to 360° in F9.
        full = abs(self.arc_span - _TWO_PI) < 1e-6

        if full:
            n   = self.n_total   # full circle: n_total = n_edges directly
            n_e = n
        else:
            # n_total in F9 = arc segment count; full-circle n derived separately.
            n_e = self.n_total
            arc_sp_rad = max(math.radians(1), min(self.arc_span, _TWO_PI - 1e-6))
            n = max(3, round(n_e * _TWO_PI / arc_sp_rad))

        r   = self.radius

        # Project stored midpoint world position onto the circle plane to get
        # the reference angle — independent of any handle_angle computation.
        from mathutils import Vector
        mid_world = Vector((self.f9_mid_x, self.f9_mid_y, self.f9_mid_z))
        d_mid     = mid_world - center
        if d_mid.length > 1e-8:
            mid_angle = math.atan2(d_mid.dot(up), d_mid.dot(right))
        else:
            mid_angle = handle_angle   # fallback: use active element

        if full:
            arc_sp    = _TWO_PI
            arc_start = (mid_angle - math.pi) % _TWO_PI   # gap opposite midpoint
        else:
            arc_sp    = max(math.radians(1), min(self.arc_span, _TWO_PI - 1e-8))
            arc_start = (mid_angle - arc_sp / 2) % _TWO_PI

        # n_e already set above: n for full circle, n_e (from panel) for arcs.
        n_v = n_e if full else n_e + 1
        pts = []
        for i in range(n_v):
            a = arc_start + (_TWO_PI * i / n_e if full else arc_sp * i / n_e)
            pts.append(center + right * math.cos(a) * r + up * math.sin(a) * r)

        old_verts = [v for v in chain_verts]
        old_edges = [e for e in chain_edges]

        if self.is_fillet_prop:
            # Fillet: keep endpoints, redistribute interior verts at avg radius.
            avg_r = (sum((mw @ v.co - center).length for v in old_verts)
                     / len(old_verts))
            d0    = (mw @ old_verts[0].co) - center
            a0    = math.atan2(d0.dot(up), d0.dot(right))
            d1    = (mw @ old_verts[-1].co) - center
            a1    = math.atan2(d1.dot(up), d1.dot(right))
            f_span = (a1 - a0) % _TWO_PI
            if f_span < 1e-8:
                f_span = _TWO_PI
            # n_total in F9 = arc segment count directly.
            n_e   = self.n_total
            # Full-circle resolution needed for set_circle_attrs layer.
            n     = max(3, round(n_e * _TWO_PI / f_span))

            # ensure_circle_layers BEFORE geometry ops to avoid invalidation
            layers = ensure_circle_layers(bm)
            if old_verts[1:-1]:
                bmesh.ops.delete(bm, geom=old_verts[1:-1], context='VERTS')
            bm.verts.ensure_lookup_table()
            bm.edges.ensure_lookup_table()

            def _fpt(i):
                a = a0 + f_span * i / n_e
                return center + right * math.cos(a) * avg_r + up * math.sin(a) * avg_r

            all_pts = [_fpt(i) for i in range(n_e + 1)]
            old_verts[0].co  = mw_inv @ all_pts[0]
            old_verts[-1].co = mw_inv @ all_pts[-1]
            inner = [bm.verts.new(mw_inv @ p) for p in all_pts[1:-1]]
            verts = [old_verts[0]] + inner + [old_verts[-1]]
            edges = [bm.edges.new((verts[i], verts[i + 1]))
                     for i in range(len(verts) - 1)]
            set_circle_attrs(bm, verts, edges, n, layers=layers, type_tag=b"Fillet")
            mid_e = edges[len(edges) // 2]
            mid_e.select = True
            bm.select_history.add(mid_e)
        else:
            layers = ensure_circle_layers(bm)
            for v in old_verts: v.hide_set(False)
            for e in old_edges: e.hide_set(False)
            bmesh.ops.delete(bm, geom=old_edges + old_verts, context='VERTS')
            verts = [bm.verts.new(mw_inv @ p) for p in pts]
            edges = ([bm.edges.new((verts[i], verts[(i + 1) % n_v])) for i in range(n_v)]
                     if full else
                     [bm.edges.new((verts[i], verts[i + 1])) for i in range(n_v - 1)])
            set_circle_attrs(bm, verts, edges, n, layers=layers)
            mid = verts[len(verts) // 2]
            mid.select = True
            bm.select_history.add(mid)

        bmesh.update_edit_mesh(obj.data)
        return {'FINISHED'}

    # ── Poll + Invoke ─────────────────────────────────────────────────────────

    @classmethod
    def poll(cls, context):
        return (context.mode == 'EDIT_MESH'
                and context.active_object is not None)

    def invoke(self, context, event):
        self._started_in_edit = context.mode == 'EDIT_MESH'
        obj = context.active_object
        bm  = bmesh.from_edit_mesh(obj.data)

        active = self.active_seed(bm)
        if active is None:
            self.report({'WARNING'}, "Select an edge or vertex first")
            return {'CANCELLED'}

        ok, chain_verts, chain_edges, is_closed = check_circle(bm, active,
                                                               mark_boundaries=True)
        if not ok:
            return {'CANCELLED'}

        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()

        # Detect fillet arcs — they get resolution-only editing.
        from ...Utils.mastro_cad.cad.circle_utils import CIRCLE_TYPES, ensure_circle_layers, set_circle_attrs
        layers = get_circle_layers(bm)
        is_tagged_fillet = (layers is not None and
                            chain_verts[0][layers[0]] == b"Fillet")

        if is_tagged_fillet and not is_closed:
            # Check if the arc is still connected to fillet edges.
            # An endpoint is "connected" if it has at least one edge NOT in
            # CIRCLE_TYPES (i.e., a non-arc edge from the original fillet).
            et   = layers[3]  # edge type layer
            es_l = layers[4]  # edge status layer
            def _has_non_circle(v):
                # es=0 on a circle-typed edge means it was a boundary (e.g. trimmed
                # arc edge after fillet-on-fillet) — treat as non-circle endpoint.
                return any(e[et] not in CIRCLE_TYPES or e[es_l] == 0
                           for e in v.link_edges)
            still_fillet = _has_non_circle(chain_verts[0]) or _has_non_circle(chain_verts[-1])
            if not still_fillet:
                # Arc is now standalone — demote to regular Circle tag.
                cl = ensure_circle_layers(bm)
                n_stored = chain_verts[0][layers[2]]
                set_circle_attrs(bm, chain_verts, chain_edges, n_stored,
                                 layers=cl, type_tag=b"Circle")
                bmesh.update_edit_mesh(obj.data)
                is_tagged_fillet = False

        self._is_fillet = is_tagged_fillet
        self._vert_indices = [v.index for v in chain_verts]
        self._edge_indices = [e.index for e in chain_edges]

        self._vert_sel_by_pos = [v.select for v in chain_verts]
        self._edge_sel_by_pos = [e.select for e in chain_edges]
        active_el = bm.select_history.active
        if isinstance(active_el, bmesh.types.BMVert) and active_el in chain_verts:
            self._active_pos     = chain_verts.index(active_el)
            self._active_is_edge = False
        elif isinstance(active_el, bmesh.types.BMEdge) and active_el in chain_edges:
            self._active_pos     = chain_edges.index(active_el)
            self._active_is_edge = True
        else:
            self._active_pos = None

        mw = obj.matrix_world

        self._handle_is_edge = False
        self._edge_grab_idx  = 0

        if isinstance(active, bmesh.types.BMVert) and active in chain_verts:
            handle_world = mw @ active.co
        elif isinstance(active, bmesh.types.BMEdge) and active in chain_edges and is_closed:
            # Full circle edge grab: use edge midpoint; _radius = chord radius,
            # _vertex_r compensates with /cos(π/n). No rotation on invoke.
            ei = chain_edges.index(active)
            v0, v1 = active.verts
            handle_world = mw @ ((v0.co + v1.co) / 2)
            self._handle_is_edge = True
            self._edge_grab_idx  = ei
        else:
            handle_world = mw @ chain_verts[len(chain_verts) // 2].co

        circumcenter = arc_circumcenter_world(chain_verts, mw)
        right, up, normal, _ = circle_plane_axes(chain_verts, mw,
                                                  handle_world, circumcenter)

        self._center       = circumcenter
        self._right        = right
        self._up           = up
        self._plane_normal = normal

        d  = handle_world - circumcenter
        dx = d.dot(right)
        dy = d.dot(up)
        self._radius = math.sqrt(dx * dx + dy * dy)

        # ── Initialise arc angles ─────────────────────────────────────────────
        if is_closed:
            n = len(chain_edges)
            self._n_total = n
            # Radius handle (= user's selected vertex) is at the midpoint.
            # Arc start/end handles are on the opposite side.
            # _handle_angle = angle of user's handle.
            # arc_start_angle = π (opposite), arc_span = 2π (full circle).
            self._handle_angle    = math.atan2(dy, dx)
            self._arc_start_angle = (self._handle_angle - math.pi) % _TWO_PI
            self._arc_span        = _TWO_PI
            self._is_full_circle  = True
        else:
            layers = get_circle_layers(bm)
            stored = chain_verts[0][layers[2]] if layers else 0
            n      = stored if stored >= len(chain_verts) else len(chain_verts)
            self._n_total = n

            n_chain = len(chain_verts)
            arc_len = n_chain - 1   # number of arc edges

            self._handle_angle = math.atan2(dy, dx)

            # _arc_start_angle: absolute angle of the first arc vertex.
            v0_world = mw @ chain_verts[0].co
            d0 = v0_world - circumcenter
            self._arc_start_angle = math.atan2(d0.dot(up), d0.dot(right))
            self._arc_span        = arc_len * _TWO_PI / n
            self._is_full_circle  = abs(self._arc_span - _TWO_PI) < 1e-8

        self._orig_n_total   = self._n_total
        self._orig_arc_start = self._arc_start_angle
        self._orig_arc_span  = self._arc_span
        self._orig_is_full   = self._is_full_circle

        # ── Pick handle to grab ───────────────────────────────────────────────
        rv3d     = context.region_data
        mouse_2d = (event.mouse_region_x, event.mouse_region_y)

        def _dist_2d(pt_world):
            pt_2d = location_3d_to_region_2d(context.region, rv3d, pt_world)
            if pt_2d is None:
                return float('inf')
            return math.sqrt((mouse_2d[0] - pt_2d.x) ** 2 +
                             (mouse_2d[1] - pt_2d.y) ** 2)

        # For fillet arcs, the handle is at the active element position
        # (where cad_handles draws the circle). For regular arcs/circles,
        # it's at the geometric midpoint.
        if self._is_fillet:
            self._handle_world = handle_world
        else:
            self._handle_world = self._arc_mid_world()
        arc_start_w        = self._arc_start_world()
        arc_end_w          = self._arc_end_world()

        # For full circles, arc handles are not exposed — use A to switch to arc.
        # Edge grab: grab zone is the edge midpoint (= handle_world on invoke).
        radius_grab = handle_world if self._handle_is_edge else self._handle_world
        dists = {
            'RADIUS': _dist_2d(radius_grab),
            'MOVE':   _dist_2d(circumcenter),
        }
        if not self._is_full_circle:
            dists['ARC_START'] = _dist_2d(arc_start_w)
            dists['ARC_END']   = _dist_2d(arc_end_w)
        best = min(dists, key=dists.get)
        if dists[best] > HANDLE_GRAB_RADIUS_PX:
            return {'CANCELLED'}
        self._mode = best

        self._snap_hit     = None
        self._number_input = ""
        # Fillet: build initial preview from actual hidden vertex positions
        # so it matches the real arc geometry from _apply_fillet.
        if self._is_fillet:
            self._refresh_preview(context)
        else:
            self._preview_pts = self._compute_preview_pts()

        if not self._is_fillet:
            # Hide arc geometry so snap KDTree excludes own vertices.
            # For fillet arcs we skip this: hiding end0/end1 also hides the
            # adjacent fillet edges (Blender hides edges with hidden verts).
            self._set_hidden(obj, True)
            context.view_layer.update()
        self._snap = SnapContext(context, select_modes=())

        global _circle_edit_draw_handle
        h3d = bpy.types.SpaceView3D.draw_handler_add(
            self._draw_preview, (context,), 'WINDOW', 'POST_VIEW')
        h2d = bpy.types.SpaceView3D.draw_handler_add(
            self._draw_handles, (context,), 'WINDOW', 'POST_PIXEL')
        self._draw_handle        = (h3d, h2d)
        _circle_edit_draw_handle = self._draw_handle

        self._update_header(context)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
