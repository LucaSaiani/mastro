# ── Snap types implemented ────────────────────────────────────────────────────
#
#   VERTEX        — snap to nearest visible vertex (KDTree in screen space)
#   EDGE_MIDPOINT — snap to edge midpoints (added to same KDTree at build time)
#   EDGE          — snap to nearest point on any edge; candidate edges are
#                   pre-filtered via midpoint KDTree (O(log n + k), not O(n))
#   INCREMENT     — snap to grid increment (round world pos to grid size)
#
# ── Snap types NOT implemented ────────────────────────────────────────────────
#
#   FACE          — snap to face surface (requires ray-face intersection)
#   VOLUME        — snap inside volumes (not relevant for 2D CAD workflow)
#   PERPENDICULAR — context-dependent, no clear operator to bind it to yet
#   PARALLEL      — snap along a direction parallel to an existing edge
#   INTERSECTION  — user builds the point manually, vertex snap handles it
#   ANGULAR       — not in Blender natively
#   TANGENT       — mastroCad has no arc edges yet
#
# ── Activation rule ───────────────────────────────────────────────────────────
#
#   In EDIT_MESH mode, snap activates only when in VERTEX select mode.
#   In edge select mode the user relies on Blender's native edge slide (G-G).
#   In object mode snap is always available (based on tool_settings.use_snap).
#
# ── Usage ─────────────────────────────────────────────────────────────────────
#
#   ctx = SnapContext(context)           # build at operator invoke
#   world_pt = ctx.snap(mouse_2d, context)   # call on every MOUSEMOVE
#   # returns snapped Vector or None (fall back to raw mouse projection)
#
#   For visual feedback, call ctx.draw_indicator(co_world, context) from a
#   POST_PIXEL draw handler when snap returns a non-None value.
#
# ─────────────────────────────────────────────────────────────────────────────

import gpu
import mathutils
from mathutils import Vector
from mathutils.kdtree import KDTree
from bpy_extras.view3d_utils import location_3d_to_region_2d
from gpu_extras.batch import batch_for_shader


from .constants import SNAP_RADIUS_PX, SNAP_RADIUS_EDGE_PX


class SnapContext:
    """Builds spatial indices from visible mesh geometry and answers snap queries.

    Instantiate once at operator invoke (when the scene geometry is static),
    then call snap() on every MOUSEMOVE.
    """

    def __init__(self, context, select_modes=('VERT',), exclude=None):
        """
        select_modes: tuple of select modes in which snap is active in EDIT_MESH.
          'VERT'  — vertex select mode  (mesh_select_mode[0])
          'EDGE'  — edge select mode    (mesh_select_mode[1])
          'FACE'  — face select mode    (mesh_select_mode[2])
          ()      — always active regardless of select mode

        Examples:
          SnapContext(context)                        # vertex only (default)
          SnapContext(context, ('VERT', 'EDGE'))      # vertex or edge
          SnapContext(context, ())                    # always active
        exclude: dict {obj: {'verts': set_of_indices, 'edges': set_of_indices}}
          Geometry to exclude from snap targets — used to prevent snapping
          to the element being edited (e.g. the rectangle's own 4 edges).
        """
        self._enabled          = False
        self._do_vertex        = False
        self._do_midpoint      = False
        self._do_edge          = False
        self._do_perpendicular = False
        self.last_type         = None

        ts = context.scene.tool_settings
        if not ts.use_snap:
            return

        if context.mode == 'EDIT_MESH' and select_modes:
            mode_map = {'VERT': 0, 'EDGE': 1, 'FACE': 2}
            active   = [ts.mesh_select_mode[mode_map[m]]
                        for m in select_modes if m in mode_map]
            if not any(active):
                return

        elems = ts.snap_elements
        self._do_vertex       = 'VERTEX'        in elems
        self._do_midpoint     = 'EDGE_MIDPOINT' in elems
        self._do_edge         = 'EDGE'          in elems
        self._do_perpendicular = 'EDGE_PERPENDICULAR' in elems
        self._do_increment    = 'INCREMENT'     in elems
        self._do_grid         = 'GRID'          in elems

        try:
            self._grid_step = context.space_data.overlay.grid_scale
        except Exception:
            self._grid_step = 1.0

        if not (self._do_vertex or self._do_midpoint or self._do_edge
                or self._do_perpendicular or self._do_increment or self._do_grid):
            return

        self._enabled = True
        self._kd           = None
        self._points_world = []
        self._points_type  = []
        self._edges_world  = []
        self._exclude      = exclude or {}

        self._build(context)

    def rebuild(self, context):
        """Rebuild snap data after viewport navigation (zoom, pan, orbit)."""
        if self._enabled:
            self._build(context)

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self, context):
        """Collect geometry from visible mesh objects, respecting Blender's
        snap Target Selection flags (Include Active / Edited / Non-Edited /
        Exclude Non-Selectable).
        """
        if context.space_data is None:
            return
        region = context.region
        if region is None:
            return
        rv3d = context.space_data.region_3d
        if rv3d is None:
            return

        ts          = context.scene.tool_settings
        active_obj  = context.active_object
        # Read target-selection flags (use getattr for forward compatibility).
        snap_self       = getattr(ts, 'use_snap_self',            True)
        snap_edit       = getattr(ts, 'use_snap_edit',            True)
        snap_nonedit    = getattr(ts, 'use_snap_nonedit',         True)
        snap_selectable = not getattr(ts, 'use_snap_selectable_only', False)

        raw_points   = []
        self._edges_world = []   # [(va, vb), ...] for edge nearest-point scan
        depsgraph    = context.evaluated_depsgraph_get()

        for obj in context.visible_objects:
            if obj.type != 'MESH':
                continue

            # Apply Target Selection filter.
            if obj == active_obj:
                if not snap_self:
                    continue
            elif obj.mode == 'EDIT':
                if not snap_edit:
                    continue
            else:
                if not snap_nonedit:
                    continue
            if not snap_selectable and not obj.select_get():
                continue
            mw = obj.matrix_world

            # Use bmesh for objects in edit mode so we get the live state
            # (including hidden flags) rather than the stale depsgraph mesh.
            if obj.mode == 'EDIT':
                import bmesh as _bmesh
                bm = _bmesh.from_edit_mesh(obj.data)
                bm.verts.ensure_lookup_table()
                bm.edges.ensure_lookup_table()
                ex       = self._exclude.get(obj, {})
                ex_verts = ex.get('verts', set())
                ex_edges = ex.get('edges', set())
                vert_world = [mw @ v.co for v in bm.verts
                              if not v.hide and v.index not in ex_verts]
                vi_map = {}
                wi = 0
                for v in bm.verts:
                    if not v.hide and v.index not in ex_verts:
                        vi_map[v.index] = wi
                        wi += 1
                edge_pairs = [(vi_map[e.verts[0].index], vi_map[e.verts[1].index])
                              for e in bm.edges
                              if not e.hide
                              and e.index not in ex_edges
                              and e.verts[0].index in vi_map
                              and e.verts[1].index in vi_map]
            else:
                obj_eval   = obj.evaluated_get(depsgraph)
                mesh       = obj_eval.data
                vert_world = [mw @ v.co for v in mesh.vertices]
                edge_pairs = [(e.vertices[0], e.vertices[1]) for e in mesh.edges]

            if self._do_vertex:
                for co_w in vert_world:
                    co_s = location_3d_to_region_2d(region, rv3d, co_w)
                    if co_s is not None:
                        raw_points.append((co_s, co_w.copy(), 'VERTEX', None))

            if self._do_midpoint or self._do_edge or self._do_perpendicular:
                for i0, i1 in edge_pairs:
                    va = vert_world[i0]
                    vb = vert_world[i1]
                    if self._do_edge or self._do_perpendicular:
                        self._edges_world.append((va.copy(), vb.copy()))
                    if self._do_midpoint:
                        mid_w = (va + vb) / 2
                        mid_s = location_3d_to_region_2d(region, rv3d, mid_w)
                        if mid_s is not None:
                            raw_points.append((mid_s, mid_w.copy(), 'MIDPOINT', None))

        if not raw_points:
            return

        kd = KDTree(len(raw_points))
        for i, (co_s, co_w, ptype, _extra) in enumerate(raw_points):
            kd.insert((co_s.x, co_s.y, 0.0), i)
            self._points_world.append(co_w)
            self._points_type.append(ptype)
        kd.balance()
        self._kd = kd

    # ── Query ─────────────────────────────────────────────────────────────────

    def snap(self, mouse_2d, context, raw_world=None, origin_world=None,
             perp_center=None):
        """Return the snapped world Vector, or None if no geometric snap found.

        raw_world    : current mouse position in world space (for GRID snap).
        origin_world : drag start position in world space (for INCREMENT snap).
        perp_center  : world Vector — centre of a circle.  When provided and
                       PERPENDICULAR snap is enabled in Blender settings, also
                       checks each edge for the foot of the perpendicular from
                       perp_center.  Only meaningful for circle operators.
        Priority: vertex → midpoint → perpendicular → edge → grid → increment.
        """
        if not self._enabled:
            return None

        self.last_type = None
        mx, my = mouse_2d

        # ── Vertex / midpoint via KDTree ──────────────────────────────────────
        if self._kd is not None:
            _co, index, dist = self._kd.find((mx, my, 0.0))
            if dist <= SNAP_RADIUS_PX:
                ptype = self._points_type[index]
                if ptype == 'VERTEX' and self._do_vertex:
                    self.last_type = 'VERTEX'
                    return self._points_world[index]
                if ptype == 'MIDPOINT' and self._do_midpoint:
                    self.last_type = 'MIDPOINT'
                    return self._points_world[index]

        # ── Perpendicular snap — foot of perp from circle centre to each edge ───
        # Active only when Blender's PERPENDICULAR element is enabled AND a
        # circle centre is provided.  Independent of EDGE snap.
        if self._do_perpendicular and perp_center is not None and self._edges_world:
            region = context.region
            rv3d   = context.region_data or context.space_data.region_3d
            if rv3d is not None:
                best_dist  = float(SNAP_RADIUS_PX)
                best_world = None
                for va, vb in self._edges_world:
                    d      = vb - va
                    len_sq = d.dot(d)
                    if len_sq < 1e-12:
                        continue
                    t = (perp_center - va).dot(d) / len_sq
                    if t < 0.0 or t > 1.0:
                        continue   # foot is outside the segment
                    foot   = va + d * t
                    foot_2d = location_3d_to_region_2d(region, rv3d, foot)
                    if foot_2d is None:
                        continue
                    dist = ((mx - foot_2d.x) ** 2 + (my - foot_2d.y) ** 2) ** 0.5
                    if dist < best_dist:
                        best_dist  = dist
                        best_world = foot
                if best_world is not None:
                    self.last_type = 'PERPENDICULAR'
                    return best_world

        # ── Edge nearest-point — linear scan of all edges ─────────────────────
        if self._do_edge and self._edges_world:
            region = context.region
            rv3d   = context.region_data or context.space_data.region_3d
            if rv3d is None:
                return None

            best_dist  = float(SNAP_RADIUS_EDGE_PX)
            best_world = None
            mouse_v    = Vector((mx, my, 0.0))
            r          = SNAP_RADIUS_EDGE_PX

            for va, vb in self._edges_world:
                sa = location_3d_to_region_2d(region, rv3d, va)
                sb = location_3d_to_region_2d(region, rv3d, vb)
                if sa is None or sb is None:
                    continue
                # Bounding-box rejection: skip if edge bbox doesn't overlap
                # the snap circle — avoids the exact test on distant edges.
                if (mx < min(sa.x, sb.x) - r or mx > max(sa.x, sb.x) + r or
                    my < min(sa.y, sb.y) - r or my > max(sa.y, sb.y) + r):
                    continue
                sa3 = Vector((sa.x, sa.y, 0.0))
                sb3 = Vector((sb.x, sb.y, 0.0))
                pt_3d, fac = mathutils.geometry.intersect_point_line(
                    mouse_v, sa3, sb3)
                fac  = max(0.0, min(1.0, fac))
                dist = (mouse_v - pt_3d).length
                if dist < best_dist:
                    best_dist  = dist
                    best_world = va.lerp(vb, fac)

            if best_world is not None:
                self.last_type = 'EDGE'
                return best_world

        # ── Grid snap — absolute viewport grid ────────────────────────────────
        if self._do_grid and raw_world is not None:
            s = self._grid_step
            if s > 1e-10:
                snapped = Vector(round(c / s) * s for c in raw_world)
                self.last_type = 'INCREMENT'
                return snapped

        # ── Increment snap — grid relative to drag origin ─────────────────────
        if self._do_increment and raw_world is not None and origin_world is not None:
            s = self._grid_step
            if s > 1e-10:
                delta   = raw_world - origin_world
                snapped = origin_world + Vector(round(c / s) * s for c in delta)
                self.last_type = 'INCREMENT'
                return snapped

        return None

    # ── Visual indicator ──────────────────────────────────────────────────────

    def draw_indicator(self, co_world, context):
        """Draw a white snap indicator at co_world (POST_PIXEL).

        Shape depends on last_type:
          VERTEX   → square
          MIDPOINT → triangle
          EDGE     → hourglass (two horizontal bars + crossing diagonals)
        """
        region = context.region
        rv3d   = context.region_data
        if rv3d is None:
            return
        co_2d = location_3d_to_region_2d(region, rv3d, co_world)
        if co_2d is None:
            return

        x, y   = co_2d
        s      = 8
        color  = (1.0, 1.0, 1.0, 1.0)
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        shader.bind()
        gpu.state.blend_set('ALPHA')

        snap_type = self.last_type

        if snap_type == 'MIDPOINT':
            verts   = [(x - s, y - s), (x + s, y - s), (x, y + s)]
            indices = ((0, 1), (1, 2), (2, 0))
        elif snap_type == 'EDGE':
            verts   = [(x-s, y+s), (x+s, y+s), (x+s, y-s), (x-s, y-s)]
            indices = ((0, 1),   # top bar
                       (3, 2),   # bottom bar
                       (0, 2),   # diagonal TL→BR
                       (1, 3))   # diagonal TR→BL
        elif snap_type == 'PERPENDICULAR':
            # Right-angle indicator: two sides of a square + a small corner mark
            h = s * 0.5   # half-size corner
            verts   = [(x - s, y - s), (x - s, y + s), (x + s, y + s),
                       (x - s + h, y - s), (x - s + h, y - s + h), (x - s, y - s + h)]
            indices = ((0, 1), (1, 2),          # two sides of the right angle
                       (3, 4), (4, 5))          # small corner square
        else:  # VERTEX
            verts   = [(x-s, y-s), (x+s, y-s), (x+s, y+s), (x-s, y+s)]
            indices = ((0, 1), (1, 2), (2, 3), (3, 0))

        batch = batch_for_shader(shader, 'LINES', {"pos": verts}, indices=indices)
        shader.uniform_float("color", color)
        batch.draw(shader)

        # Centre dot.
        gpu.state.point_size_set(4)
        batch2 = batch_for_shader(shader, 'POINTS', {"pos": [(x, y)]})
        shader.uniform_float("color", color)
        batch2.draw(shader)

        gpu.state.blend_set('NONE')
