"""Shared base mixin for all MaStroCad creation operators.

CadMixin — generic logic shared by every operator (circles, rectangles, arcs, …):
  poll()               — VIEW_3D only
  _draw_snap()         — POST_PIXEL snap indicator
  _register_handlers() — add POST_VIEW + POST_PIXEL draw handlers
  _remove_handlers()   — remove handlers
  _gc_cleanup()        — GC-safe handler removal from ReferenceError blocks
  set_status()         — workspace footer with icon labels
  clear_status()       — clear workspace footer
  depth_reference()    — world-space depth hint for perspective projection
  get_plane_normal()   — drawing-plane normal from transform orientation
  orient_axes()        — (right, up) axes from transform orientation
  project_to_plane()   — ray-plane intersection with fallback
  eval_number()        — safe_eval with comma-as-decimal support

RectMixin(CadMixin) — adds rectangle-specific geometry creation:
  _apply_rectangle()   — create mesh geometry from 4 world-space corners

Key → character maps:
  CAD_CHAR_MAP   — digits, operators, decimal separator (used by all operators)
  RECT_CHAR_MAP  — CAD_CHAR_MAP + semicolon separator for W;H input (rectangles)
"""

import bpy
import bmesh
from mathutils import Vector
from bpy_extras.view3d_utils import region_2d_to_location_3d

from ...Utils.mastro_cad.cad.cad_utils import (get_attr_layers, copy_drawing_attrs,
    assign_drawing_layer_to_edges,
                                    ray_plane_intersect, safe_eval)
from ...Utils.mastro_cad.cad.rect_utils import set_rect_attrs, ensure_rect_layers


# ── Key → character maps ──────────────────────────────────────────────────────

# Base map: digits, arithmetic operators, decimal separators.
# Shared by all numeric-input operators (circle radius, rectangle dimensions…).
CAD_CHAR_MAP = {
    'NUMPAD_0':'0','NUMPAD_1':'1','NUMPAD_2':'2','NUMPAD_3':'3',
    'NUMPAD_4':'4','NUMPAD_5':'5','NUMPAD_6':'6','NUMPAD_7':'7',
    'NUMPAD_8':'8','NUMPAD_9':'9',
    'ZERO':'0','ONE':'1','TWO':'2','THREE':'3','FOUR':'4',
    'FIVE':'5','SIX':'6','SEVEN':'7','EIGHT':'8','NINE':'9',
    'PERIOD':'.','NUMPAD_PERIOD':'.',
    'MINUS':'-', 'NUMPAD_MINUS': '-',
    'COMMA':',', 'NUMPAD_COMMA' : ',',
    'PLUS':'+','NUMPAD_PLUS':'+',
    'SLASH':'/','NUMPAD_SLASH':'/',
    'ASTERIX':'*','NUMPAD_ASTERIX':'*',
}

# Rectangle extension: adds semicolon as W;H dimension separator.
RECT_CHAR_MAP = {**CAD_CHAR_MAP, 'SEMI_COLON': ';'}


# ── CadMixin ──────────────────────────────────────────────────────────────────

class CadMixin:
    """Generic behaviour shared by all MaStroCad creation operators."""

    # ── Poll ──────────────────────────────────────────────────────────────────

    @classmethod
    def poll(cls, context):
        if context.area is None:
            return True   # popup-menu context: area not set, trust the menu
        return context.area.type == 'VIEW_3D'

    # ── GPU snap indicator (POST_PIXEL) ───────────────────────────────────────

    def _draw_snap(self, context):
        try:
            snap_hit = self._snap_hit
        except ReferenceError:
            return
        if snap_hit is not None and self._snap is not None:
            self._snap.draw_indicator(snap_hit, context)

    # ── Draw handler management ───────────────────────────────────────────────

    # Class-level handle — survives GC of the operator instance, used for
    # cleanup in the ReferenceError branch of _draw_preview.
    _class_draw_handle = None

    def _register_handlers(self, context):
        """Register POST_VIEW + POST_PIXEL handlers and cache at class level."""
        h3d = bpy.types.SpaceView3D.draw_handler_add(
            self._draw_preview, (context,), 'WINDOW', 'POST_VIEW')
        h2d = bpy.types.SpaceView3D.draw_handler_add(
            self._draw_snap,    (context,), 'WINDOW', 'POST_PIXEL')
        self._draw_handle = (h3d, h2d)
        type(self)._class_draw_handle = self._draw_handle
        return self._draw_handle

    def _remove_handlers(self):
        """Remove draw handlers and clear the class-level cache."""
        if self._draw_handle is not None:
            for h in self._draw_handle:
                bpy.types.SpaceView3D.draw_handler_remove(h, 'WINDOW')
            self._draw_handle = None
        type(self)._class_draw_handle = None

    @classmethod
    def _gc_cleanup(cls):
        """Call from _draw_preview's ReferenceError block when instance is GC'd."""
        h = cls._class_draw_handle
        if h is not None:
            for x in (h if isinstance(h, tuple) else (h,)):
                bpy.types.SpaceView3D.draw_handler_remove(x, 'WINDOW')
            cls._class_draw_handle = None

    # ── Status bar ────────────────────────────────────────────────────────────

    @staticmethod
    def set_status(context, modifier=None, *,
                   mouse=(),       ctrl_mouse=(),  alt_mouse=(),  shift_mouse=(),
                   keys=(),        ctrl_keys=(),   alt_keys=(),   shift_keys=()):
        """Set the workspace footer showing all available commands.

        Render order: mouse → ctrl_mouse → alt_mouse → shift_mouse →
                      keys  → ctrl_keys  → alt_keys  → shift_keys

        All groups are always visible. Modified groups are prefixed with the
        modifier icon. Each group is a list of:
          (text, icon)            — plain command
          (text, icon, active)    — toggle: appends (ON)/(OFF) to text
          None                    — separator
          float                   — separator with factor
        """
        _MOD_ICONS = {'CTRL': 'EVENT_CTRL', 'ALT': 'EVENT_ALT', 'SHIFT': 'EVENT_SHIFT'}

        def _draw_items(layout, items, prefix_icon=None):
            for item in items:
                if item is None:
                    layout.separator()
                    continue
                if isinstance(item, (int, float)):
                    layout.separator(factor=item)
                    continue
                if prefix_icon:
                    layout.label(text="", icon=prefix_icon)
                    layout.separator(factor=0.3)
                if len(item) == 3:
                    text, icon, active = item
                    suffix = " (ON)" if active else " (OFF)"
                    layout.label(text=text + suffix, icon=icon)
                else:
                    layout.label(text=item[0], icon=item[1])

        groups = [
            (mouse,       None),
            (ctrl_mouse,  'CTRL'),
            (alt_mouse,   'ALT'),
            (shift_mouse, 'SHIFT'),
            (keys,        None),
            (ctrl_keys,   'CTRL'),
            (alt_keys,    'ALT'),
            (shift_keys,  'SHIFT'),
        ]

        def _fn(header, ctx):
            layout = header.layout
            first = True
            for items, mod in groups:
                if not items:
                    continue
                if not first:
                    layout.separator()
                first = False
                _draw_items(layout, items,
                            prefix_icon=_MOD_ICONS[mod] if mod else None)
        context.workspace.status_text_set(_fn)

    @staticmethod
    def modifier_from_event(event):
        """Return 'CTRL', 'ALT', 'SHIFT', or None based on held modifier keys."""
        if event.ctrl:  return 'CTRL'
        if event.alt:   return 'ALT'
        if event.shift: return 'SHIFT'
        return None

    @staticmethod
    def clear_status(context):
        """Clear the workspace footer."""
        context.workspace.status_text_set(None)

    def pass_through_navigation(self, event):
        """Return PASS_THROUGH set if event is a viewport navigation event.

        Sets _nav_pending so the next MOUSEMOVE rebuilds the snap KDTree
        (screen coords are stale after zoom/pan/orbit).
        """
        if event.type == 'MIDDLEMOUSE' or (
                event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE'} and not event.ctrl):
            self._nav_pending = True
            return {'PASS_THROUGH'}
        if event.type == 'TAB':
            return {'PASS_THROUGH'}
        return None

    @staticmethod
    def left_edit_mode(context, started_in_edit):
        """True if operator started in edit mode but mode has since changed."""
        return started_in_edit and context.mode != 'EDIT_MESH'

    def maybe_rebuild_snap(self, context):
        """Rebuild snap KDTree if a navigation event occurred since last call."""
        if getattr(self, '_nav_pending', False):
            snap = getattr(self, '_snap', None)
            if snap is not None:
                snap.rebuild(context)
            self._nav_pending = False

    # ── Depth reference ───────────────────────────────────────────────────────

    @staticmethod
    def depth_reference(context):
        """World-space depth hint for the first-click projection in perspective.

        Edit mode  → active object origin.
        Other modes → 3D cursor location.
        """
        if context.mode == 'EDIT_MESH' and context.active_object:
            return context.active_object.matrix_world.translation.copy()
        return context.scene.cursor.location.copy()

    # ── Orientation helpers ───────────────────────────────────────────────────

    @staticmethod
    def get_plane_normal(context, rv3d):
        """Drawing-plane normal from the active transform orientation."""
        from mathutils import Matrix, Vector
        vm        = rv3d.view_matrix.inverted()
        v_forward = vm.col[2].to_3d().normalized()
        slot      = context.scene.transform_orientation_slots[0]
        if slot.type == 'VIEW' or abs(v_forward.z) < 1e-6:
            return v_forward
        if slot.type == 'GLOBAL':
            return Vector((0, 0, 1))
        if slot.type == 'LOCAL' and context.active_object:
            return context.active_object.matrix_world \
                       .to_3x3().normalized().col[2].to_3d().normalized()
        if slot.type == 'CURSOR':
            return context.scene.cursor.matrix.to_3x3().col[2].to_3d().normalized()
        co = getattr(slot, 'custom_orientation', None)
        if co:
            return co.matrix.col[2].to_3d().normalized()
        return Vector((0, 0, 1))

    @staticmethod
    def orient_axes(context, rv3d):
        """(right, up) world-space axes from the active transform orientation."""
        from mathutils import Matrix, Vector
        vm        = rv3d.view_matrix.inverted()
        v_right   = vm.col[0].to_3d().normalized()
        v_up      = vm.col[1].to_3d().normalized()
        v_forward = vm.col[2].to_3d().normalized()
        slot      = context.scene.transform_orientation_slots[0]
        if slot.type == 'VIEW' or abs(v_forward.z) < 1e-6:
            return v_right, v_up
        if slot.type == 'GLOBAL':
            mat = Matrix.Identity(3)
        elif slot.type == 'LOCAL' and context.active_object:
            mat = context.active_object.matrix_world.to_3x3().normalized()
        elif slot.type == 'CURSOR':
            mat = context.scene.cursor.matrix.to_3x3()
        elif slot.type == 'NORMAL':
            mat = Matrix.Identity(3)
        else:
            co  = slot.custom_orientation
            mat = co.matrix.copy() if co else Matrix.Identity(3)
        return Vector(mat.col[0]).normalized(), Vector(mat.col[1]).normalized()

    @staticmethod
    def project_to_plane(context, mouse_2d, plane_normal, ref_pt,
                         right=None, up=None):
        """Project mouse ray onto the plane defined by plane_normal / ref_pt.

        When plane_normal is None the active transform orientation is used to
        derive it, so ray_plane_intersect is always preferred over the view-
        space fallback.  This ensures the correct world Z in perspective view
        even before the first click has established the drawing plane.
        """
        if plane_normal is None:
            rv3d = getattr(context.space_data, 'region_3d', None)
            if rv3d is not None:
                if right is None or up is None:
                    right_t, up_t = CadMixin.orient_axes(context, rv3d)
                    if right is None:
                        right = right_t
                    if up is None:
                        up = up_t
                plane_normal = right.cross(up).normalized()

        if plane_normal and ref_pt:
            if right is None or up is None:
                n    = plane_normal
                up_v = Vector((0, 1, 0)) if abs(n.dot(Vector((0, 1, 0)))) < 0.9 \
                       else Vector((1, 0, 0))
                right = n.cross(up_v).normalized()
                up    = n.cross(right).normalized()
            pt = ray_plane_intersect(context, mouse_2d,
                                     (right, up, plane_normal), ref_pt)
            if pt is not None:
                return pt
        return region_2d_to_location_3d(
            context.region, context.space_data.region_3d, mouse_2d, ref_pt)

    # ── Active seed ───────────────────────────────────────────────────────────

    @staticmethod
    def active_seed(bm):
        """Return a BMEdge or BMVert to use as validation seed, or None.

        Priority: select_history.active → single selected vert → single
        selected edge → first selected vert → first selected edge.
        Vertex takes priority over edge when multiple modes are active.
        """
        active = bm.select_history.active
        if isinstance(active, (bmesh.types.BMEdge, bmesh.types.BMVert)):
            return active
        sel_verts = [v for v in bm.verts if v.select]
        sel_edges = [e for e in bm.edges if e.select]
        if len(sel_verts) == 1:
            return sel_verts[0]
        if len(sel_edges) == 1:
            return sel_edges[0]
        if sel_verts:
            return sel_verts[0]
        if sel_edges:
            return sel_edges[0]
        return None

    # ── Geometry hide/unhide ──────────────────────────────────────────────────

    @staticmethod
    def set_geometry_hidden(obj, vert_indices, edge_indices, hidden):
        """Hide or unhide a set of vertices and edges by index.

        Must be called in EDIT_MESH mode.  Does NOT create/destroy SnapContext —
        callers are responsible for building a fresh SnapContext after hiding so
        the snap KDTree excludes the now-hidden elements.
        """
        bm = bmesh.from_edit_mesh(obj.data)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        for i in vert_indices:
            bm.verts[i].hide_set(hidden)
        for i in edge_indices:
            bm.edges[i].hide_set(hidden)
        bmesh.update_edit_mesh(obj.data)

    # ── Numeric input helper ──────────────────────────────────────────────────

    @staticmethod
    def eval_number(s):
        """Parse a numeric expression; treat comma as decimal separator."""
        return safe_eval(s.replace(',', '.')) if s.strip() else None


# ── RectMixin ─────────────────────────────────────────────────────────────────

class RectMixin(CadMixin):
    """Adds rectangle geometry creation to CadMixin."""

    def _apply_rectangle(self, context, corners, center=None):
        """Create rectangle mesh from 4 world-space corners.

        corners : [p0, p1, p2, p3] in CCW order.
        center  : explicit origin for object-mode creation; defaults to bbox centre.
        """
        if center is None:
            center = sum(corners, corners[0] * 0) / 4

        if context.mode == 'EDIT_MESH' and context.active_object:
            obj    = context.active_object
            bm     = bmesh.from_edit_mesh(obj.data)
            mw_inv = obj.matrix_world.inverted()
            # Layers must be created before geometry — any new layer invalidates
            # all existing bmesh element references.
            rect_layers = ensure_rect_layers(bm)
            verts = [bm.verts.new(mw_inv @ c) for c in corners]
            edges = []
            for i in range(4):
                ne = bm.edges.new((verts[i], verts[(i + 1) % 4]))
                ne.select = True
                edges.append(ne)
            set_rect_attrs(bm, verts, edges, layers=rect_layers)
            assign_drawing_layer_to_edges(context, obj, bm, edges)
            bmesh.update_edit_mesh(obj.data)
        else:
            local_corners = [c - center for c in corners]
            bm = bmesh.new()
            rect_layers = ensure_rect_layers(bm)
            verts = [bm.verts.new(c) for c in local_corners]
            edges = [bm.edges.new((verts[i], verts[(i + 1) % 4]))
                     for i in range(4)]
            set_rect_attrs(bm, verts, edges, layers=rect_layers)
            mesh = bpy.data.meshes.new("Rectangle")
            bm.to_mesh(mesh)
            bm.free()
            new_obj          = bpy.data.objects.new("Rectangle", mesh)
            new_obj.location = center
            context.collection.objects.link(new_obj)
            context.view_layer.objects.active = new_obj
            new_obj.select_set(True)
