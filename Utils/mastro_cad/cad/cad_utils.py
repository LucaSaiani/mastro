"""Shared geometric and CAD utilities for MaStroCad operators."""

import ast
import operator as _op
import bpy
from mathutils import Vector
from bpy_extras.view3d_utils import location_3d_to_region_2d


# ── Length display formatting ─────────────────────────────────────────────────

# Conversion factor to metres, and display suffix, for each fixed
# scene.unit_settings.length_unit (everything except 'ADAPTIVE').
_LENGTH_UNIT_TO_METERS = {
    'KILOMETERS':  1000.0,
    'METERS':      1.0,
    'CENTIMETERS': 0.01,
    'MILLIMETERS': 0.001,
    'MICROMETERS': 1e-6,
    'MILES':       1609.344,
    'FEET':        0.3048,
    'INCHES':      0.0254,
    'THOU':        2.54e-5,
}
_LENGTH_UNIT_SUFFIX = {
    'KILOMETERS': 'km', 'METERS': 'm', 'CENTIMETERS': 'cm',
    'MILLIMETERS': 'mm', 'MICROMETERS': 'µm',
    'MILES': 'mi', 'FEET': 'ft', 'INCHES': 'in', 'THOU': 'thou',
}


def format_length(context, value):
    """Format a length (in Blender scene units) for display in headers.

    Honors the scene's configured display unit (Scene Properties > Units)
    instead of bpy.utils.units.to_string()'s automatic unit switching,
    which jumps between e.g. cm/m as the value's magnitude changes and
    reads as inconsistent in a live-updating header. Only when the scene
    unit is explicitly set to "Adaptive" (or units are off) do we fall
    back to that automatic behaviour.
    """
    unit_settings = context.scene.unit_settings
    system = unit_settings.system
    if system == 'NONE':
        return f"{value:.4f}"

    length_unit = unit_settings.length_unit
    scale = _LENGTH_UNIT_TO_METERS.get(length_unit)
    if scale is None:   # 'ADAPTIVE' or an unrecognised value
        return bpy.utils.units.to_string(system, 'LENGTH', value)

    meters = value * unit_settings.scale_length
    displayed = meters / scale
    suffix = _LENGTH_UNIT_SUFFIX.get(length_unit, '')
    return f"{displayed:.4f} {suffix}"


# ── Safe arithmetic expression evaluator ─────────────────────────────────────

_OPERATORS = {
    ast.Add:  _op.add,
    ast.Sub:  _op.sub,
    ast.Mult: _op.mul,
    ast.Div:  _op.truediv,
    ast.USub: _op.neg,
}


def _eval_node(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](_eval_node(node.operand))
    raise ValueError(f"Unsupported node: {type(node)}")


def safe_eval(expr):
    """Safely evaluate an arithmetic expression (+, -, *, /).

    Returns a float or None if the expression is invalid/incomplete.

    MERGE NOTE: mastro already has an equivalent implementation in
    Operators/MESH_OT_Move_Active_Vertex.py (safe_eval + eval_node).
    When merging mastroCad into mastro, consolidate both into a single
    shared location (e.g. mastro/Utils/cad_utils.py) and update all
    imports. The implementations are functionally identical.
    """
    if not expr or expr in {'.', ',', '-', '+', '*', '/'}:
        return None
    try:
        return float(_eval_node(ast.parse(expr.replace(',', '.'), mode='eval').body))
    except Exception:
        return None


# ── Plane detection ───────────────────────────────────────────────────────────

def compute_plane(pts, context, obj=None):
    """Compute projection axes (x_axis, y_axis, normal) for a set of 3D points.

    Detects the plane from LOCAL coordinates: the axis with the smallest
    spread in local space is used as the plane normal.  This correctly handles
    geometry that is flat along a non-world axis (e.g. local Y=const).

    Falls back to _plane_from_points for degenerate cases.
    Returns (x_axis, y_axis, normal) all in world space.
    """
    if obj is None and context is not None:
        obj = context.active_object

    if len(pts) < 2:
        return _view_axes(context)

    if obj is not None:
        try:
            mw     = obj.matrix_world
            mw_inv = mw.inverted()
            local  = [mw_inv @ p for p in pts]
            lxs    = [p.x for p in local]
            lys    = [p.y for p in local]
            lzs    = [p.z for p in local]
            spreads  = [max(lxs)-min(lxs), max(lys)-min(lys), max(lzs)-min(lzs)]
            min_axis = spreads.index(min(spreads))
            basis    = [Vector((1,0,0)), Vector((0,1,0)), Vector((0,0,1))]
            ln       = basis[min_axis]
            lx       = basis[(min_axis + 1) % 3]
            ly       = basis[(min_axis + 2) % 3]
            rot3     = mw.to_3x3()
            return (
                (rot3 @ lx).normalized(),
                (rot3 @ ly).normalized(),
                (rot3 @ ln).normalized(),
            )
        except Exception:
            pass

    return _plane_from_points(pts, context)


def _plane_from_points(pts, context):
    """Fit a plane from 3+ non-collinear points. Falls back to view if collinear."""
    rv3d     = context.space_data.region_3d if context else None
    view_dir = (rv3d.view_rotation @ Vector((0.0, 0.0, -1.0))) if rv3d \
               else Vector((0, -1, 0))

    p0 = pts[0]
    normal = None
    for pi in pts[1:]:
        d1 = (pi - p0)
        if d1.length < 1e-8:
            continue
        d1.normalize()
        for pj in pts[1:]:
            d2 = (pj - p0)
            if d2.length < 1e-8:
                continue
            d2.normalize()
            n = d1.cross(d2)
            if n.length > 1e-6:
                normal = n.normalized()
                break
        if normal:
            break

    if normal is None:
        tol = 1e-6
        xs, ys, zs = [p.x for p in pts], [p.y for p in pts], [p.z for p in pts]
        if max(xs) - min(xs) < tol:
            normal = Vector((1.0, 0.0, 0.0))
        elif max(ys) - min(ys) < tol:
            normal = Vector((0.0, 1.0, 0.0))
        elif max(zs) - min(zs) < tol:
            normal = Vector((0.0, 0.0, 1.0))
        else:
            edge_dir = (pts[-1] - pts[0]).normalized()
            normal   = edge_dir.cross(view_dir)
            if normal.length < 1e-8:
                return _view_axes(context)
            normal.normalize()

    if normal.dot(view_dir) > 0:
        normal = -normal

    edge_dir = (pts[1] - pts[0]).normalized()
    x_axis   = edge_dir - normal * edge_dir.dot(normal)
    if x_axis.length < 1e-8:
        x_axis = normal.cross(Vector((0, 0, 1)))
        if x_axis.length < 1e-8:
            x_axis = normal.cross(Vector((1, 0, 0)))
    x_axis.normalize()
    return x_axis, normal.cross(x_axis).normalized(), normal


def _view_axes(context):
    """Fallback: return view plane axes."""
    rv3d   = context.space_data.region_3d
    normal = rv3d.view_rotation @ Vector((0, 0, 1))
    x_axis = rv3d.view_rotation @ Vector((1, 0, 0))
    return x_axis, normal.cross(x_axis).normalized(), normal


def are_coplanar(pts, tol=1e-4):
    """Return True if all points lie in the same plane within tol.

    Uses the first 3 non-collinear points to define the plane, then checks
    that all remaining points are within tol of it.
    Returns True for fewer than 3 points (trivially coplanar).
    """
    if len(pts) < 3:
        return True

    p0 = pts[0]
    normal = None
    for i in range(1, len(pts)):
        d1 = (pts[i] - p0)
        if d1.length < 1e-8:
            continue
        d1.normalize()
        for j in range(i + 1, len(pts)):
            d2 = (pts[j] - p0)
            if d2.length < 1e-8:
                continue
            d2.normalize()
            n = d1.cross(d2)
            if n.length > 1e-6:
                normal = n.normalized()
                break
        if normal:
            break

    if normal is None:
        return True  # All collinear — trivially coplanar.

    d = p0.dot(normal)
    return all(abs(p.dot(normal) - d) <= tol for p in pts)


# ── View ray / plane intersection ────────────────────────────────────────────

def min_dist_point_to_chains(pt, chains, normal):
    """Return the signed minimum distance from pt to the nearest edge in chains.

    Sign convention: positive if pt is to the LEFT of the nearest edge
    (left = the direction of normal.cross(edge_dir)).

    pt     : Vector (3D world-space, on the geometry plane)
    chains : list of chain dicts (must contain 'pts')
    normal : Vector — plane normal, used for sign determination
    Returns (float, Vector|None).
    """
    best_signed   = None
    best_closest  = None
    best_chain_i  = None
    best_seg_i    = None

    for ci, chain in enumerate(chains):
        pts        = chain['pts']
        start_free = chain.get('start_free', False)
        end_free   = chain.get('end_free',   False)
        n_segs     = len(pts) - 1
        for i in range(n_segs):
            a, b   = pts[i], pts[i + 1]
            ab     = b - a
            ab_len = ab.length
            if ab_len < 1e-8:
                continue
            ab_n = ab / ab_len
            t    = (pt - a).dot(ab_n)
            # Skip if outside the segment, unless this is a free endpoint
            # (degree-1 vertex) where the projection extends beyond the tip.
            t_lo = None if (i == 0        and start_free) else 0.0
            t_hi = None if (i == n_segs-1 and end_free)   else ab_len
            if t_lo is not None and t < t_lo:
                continue
            if t_hi is not None and t > t_hi:
                continue
            closest = a + ab_n * t
            signed  = ab.cross(pt - a).dot(normal) / ab_len
            if best_signed is None or abs(signed) < abs(best_signed):
                best_signed  = signed
                best_closest = closest
                best_chain_i = ci
                best_seg_i   = i

    return (best_signed if best_signed is not None else 0.0,
            best_closest, best_chain_i, best_seg_i)


def ray_plane_intersect(context, mouse_px, plane_axes, plane_pt):
    """Intersect the view ray through mouse_px with the given plane.

    plane_axes : (x_axis, y_axis, normal) — normal defines the plane orientation
    plane_pt   : any 3D world-space point on the plane (for depth computation)

    Returns the 3D world-space intersection, or falls back to
    region_2d_to_location_3d if the ray is nearly parallel to the plane.
    """
    from bpy_extras.view3d_utils import (region_2d_to_origin_3d,
                                          region_2d_to_vector_3d,
                                          region_2d_to_location_3d)
    _, _, normal = plane_axes
    rv3d       = context.space_data.region_3d
    region     = context.region
    ray_origin = region_2d_to_origin_3d(region, rv3d, mouse_px)
    ray_dir    = region_2d_to_vector_3d(region, rv3d, mouse_px)
    denom = ray_dir.dot(normal)
    if abs(denom) > 1e-8:
        d = plane_pt.dot(normal)
        t = (d - ray_origin.dot(normal)) / denom
        return ray_origin + ray_dir * t
    return region_2d_to_location_3d(region, rv3d, mouse_px, plane_pt)


# ── 2D / 3D projection ────────────────────────────────────────────────────────

def to_2d(v, x_axis, y_axis):
    """Project a 3D world-space point onto a plane defined by x_axis/y_axis."""
    return (v.dot(x_axis), v.dot(y_axis))


def to_3d(x, y, x_axis, y_axis, normal, depth):
    """Reconstruct a 3D point from 2D coordinates and depth along the normal."""
    return x_axis * x + y_axis * y + normal * depth


def depth_for_chain(pts_3d, normal):
    """Per-vertex signed depths along the plane normal (all equal for flat chains)."""
    return [p.dot(normal) for p in pts_3d]


# ── 2D geometry helpers ───────────────────────────────────────────────────────

def nearest_seg(x, y, coords_2d):
    """Find the nearest point on a 2D polyline. Returns (t, segment_index)."""
    best_t, best_seg, best_dist = 0.0, 0, float('inf')
    for i in range(len(coords_2d) - 1):
        ax, ay = coords_2d[i]
        bx, by = coords_2d[i + 1]
        dx, dy = bx - ax, by - ay
        sq = dx * dx + dy * dy
        t  = 0.0 if sq < 1e-16 else max(0.0, min(1.0, ((x-ax)*dx+(y-ay)*dy) / sq))
        cx, cy = ax + t*dx, ay + t*dy
        dist = (x-cx)**2 + (y-cy)**2
        if dist < best_dist:
            best_dist, best_t, best_seg = dist, t, i
    return best_t, best_seg


def reconstruct_3d_delta(off_coords, coords_2d, pts_3d, x_axis, y_axis):
    """Reconstruct 3D positions for non-flat chains by delta-lifting.

    For each Shapely output point: find the nearest original segment,
    interpolate the original 3D position, then apply the 2D offset delta
    via the plane axes.  Preserves the original depth structure exactly.
    """
    result = []
    for ox, oy in off_coords:
        t, seg  = nearest_seg(ox, oy, coords_2d)
        orig_3d = pts_3d[seg] + t * (pts_3d[seg + 1] - pts_3d[seg])
        a2, b2  = coords_2d[seg], coords_2d[seg + 1]
        ix = a2[0] + t * (b2[0] - a2[0])
        iy = a2[1] + t * (b2[1] - a2[1])
        result.append(orig_3d + x_axis * (ox - ix) + y_axis * (oy - iy))
    return result


# ── Chain topology ────────────────────────────────────────────────────────────

def sort_edges_into_chains(edges, mw):
    """Group selected edges into ordered chains of world-space 3D points.

    Returns a list of dicts:
      {'pts': [Vector, ...], 'closed': bool, 'src_edges': [int|None, ...]}

    src_edges stores the bmesh edge INDEX for each segment (not references,
    to avoid stale-ref errors when the bmesh is modified later).
    """
    adj = {}
    for e in edges:
        i0, i1 = e.verts[0].index, e.verts[1].index
        adj.setdefault(i0, []).append((i1, e))
        adj.setdefault(i1, []).append((i0, e))

    visited_edges = set()
    chains = []

    for start_edge in edges:
        if id(start_edge) in visited_edges:
            continue

        def walk(v_idx, prev_idx):
            verts = []
            while True:
                verts.append(v_idx)
                nbrs = [(nxt, e) for nxt, e in adj.get(v_idx, [])
                        if nxt != prev_idx and id(e) not in visited_edges]
                if len(nbrs) != 1:
                    break
                nxt, e = nbrs[0]
                visited_edges.add(id(e))
                prev_idx, v_idx = v_idx, nxt
            return verts

        visited_edges.add(id(start_edge))
        i0, i1 = start_edge.verts[0].index, start_edge.verts[1].index

        fwd = walk(i1, i0)
        bwd = walk(i0, i1)
        bwd.reverse()
        ordered = bwd + fwd

        last, first = ordered[-1], ordered[0]
        if last == first and len(ordered) > 2:
            ordered = ordered[:-1]
            closed  = True
        else:
            closed = any(nxt == first for nxt, e in adj.get(last, [])
                         if id(e) not in visited_edges)
            if closed:
                for nxt, e in adj.get(last, []):
                    if nxt == first:
                        visited_edges.add(id(e))

        idx_to_vert = {v.index: v for e in edges for v in e.verts}
        pts = [mw @ idx_to_vert[i].co for i in ordered]

        edge_idx_map = {frozenset([e.verts[0].index, e.verts[1].index]): e.index
                        for e in edges}
        src_edges = [edge_idx_map.get(frozenset([ordered[i], ordered[i+1]]))
                     for i in range(len(ordered) - 1)]
        if closed:
            src_edges.append(edge_idx_map.get(frozenset([ordered[-1], ordered[0]])))

        if len(pts) >= 2:
            # Free endpoints: degree 1 in the selection — safe to extend projection.
            start_free = not closed and len(adj.get(ordered[0],  [])) == 1
            end_free   = not closed and len(adj.get(ordered[-1], [])) == 1
            chains.append({'pts': pts, 'closed': closed, 'src_edges': src_edges,
                           'start_free': start_free, 'end_free': end_free})

    return chains


# ── Shapely offset ────────────────────────────────────────────────────────────

def build_chain_geo(chains, context, tol):
    """Pre-compute Shapely geometry and projection data for all chains.

    Uses compute_plane() to detect the offset plane from the full selection.
    All chains share the same axes so that individually collinear chains
    (e.g. two parallel vertical edges) collectively define the correct plane.

    Returns a list of dicts, one per chain:
      'shapely_geom', 'closed', 'x_axis', 'y_axis', 'normal',
      'coords_2d', 'depths', 'pts'
    """
    from shapely.geometry import LineString, LinearRing

    all_pts     = [p for c in chains for p in c['pts']]
    # For a single chain with 2 pts (one edge), the automatic plane detection
    # is ambiguous — use the view normal to get the correct offset plane.
    if len(all_pts) == 2:
        shared_axes = _view_axes(context)
    else:
        shared_axes = compute_plane(all_pts, context)

    result = []
    for chain in chains:
        pts, closed            = chain['pts'], chain['closed']
        x_axis, y_axis, normal = shared_axes
        coords_2d = [to_2d(v, x_axis, y_axis) for v in pts]
        depths    = depth_for_chain(pts, normal)

        try:
            geom = LinearRing(coords_2d) if closed else LineString(coords_2d)
        except Exception:
            geom = None

        result.append({
            'shapely_geom': geom,
            'closed':    closed,
            'x_axis':    x_axis,
            'y_axis':    y_axis,
            'normal':    normal,
            'coords_2d': coords_2d,
            'depths':    depths,
            'pts':       pts,
        })
    return result


def apply_offset_to_geo(chain_geos, distance, connect_ends):
    """Apply the offset distance to pre-built Shapely geometries.

    Called every MOUSEMOVE with the current distance; only Shapely's
    offset_curve / buffer is recomputed — axes and projections are reused.

    Returns (per_chain_edges, connect_pairs) where:
      per_chain_edges : list of lists of (Vector, Vector) world-space pairs
      connect_pairs   : list of (Vector, Vector, src_idx) cap edge tuples
    """
    from shapely.geometry import Polygon, MultiLineString
    per_chain_edges = []
    connect_pairs   = []

    for cg in chain_geos:
        geom               = cg['shapely_geom']
        closed             = cg['closed']
        x_axis, y_axis     = cg['x_axis'], cg['y_axis']
        normal, coords_2d  = cg['normal'], cg['coords_2d']
        depths, pts        = cg['depths'], cg['pts']

        if geom is None or geom.is_empty:
            per_chain_edges.append([])
            continue

        try:
            if closed:
                buffered = Polygon(geom).buffer(distance, join_style='mitre',
                                                cap_style='flat')
                if buffered.is_empty or not hasattr(buffered, 'exterior'):
                    per_chain_edges.append([])
                    continue
                off_coords = list(buffered.exterior.coords)
            else:
                offset_ls = geom.offset_curve(distance, join_style='mitre')
                if offset_ls.is_empty:
                    per_chain_edges.append([])
                    continue
                if isinstance(offset_ls, MultiLineString):
                    off_coords = [c for g in offset_ls.geoms
                                  for c in list(g.coords)]
                else:
                    off_coords = list(offset_ls.coords)
        except Exception:
            per_chain_edges.append([])
            continue

        if len(off_coords) < 2:
            per_chain_edges.append([])
            continue

        if max(depths) - min(depths) < 1e-6:
            off_3d = [to_3d(x, y, x_axis, y_axis, normal, depths[0])
                      for x, y in off_coords]
        else:
            off_3d = reconstruct_3d_delta(off_coords, coords_2d, pts,
                                          x_axis, y_axis)

        chain_edges = [(off_3d[i], off_3d[i + 1])
                       for i in range(len(off_3d) - 1)]
        per_chain_edges.append(chain_edges)

        if connect_ends and not closed:
            connect_pairs.append((pts[0],  off_3d[0],  0))
            connect_pairs.append((pts[-1], off_3d[-1], len(pts) - 2))

    return per_chain_edges, connect_pairs


# ── MaStro drawing attribute copy ────────────────────────────────────────────

# Map from mastroDraw attribute type strings to BMesh layer collection names.
_ATTR_TYPE_TO_BM = {
    "INT":     "int",
    "FLOAT":   "float",
    "BOOLEAN": "bool",
    "STRING":  "string",
}


# Mirror of mastroDraw.Utils.add_attributes_drawing.drawing_attribute_set.
# Keep in sync when merging into mastro — at that point replace with a direct
# import from the shared module.
_DRAWING_ATTRIBUTE_SET = [
    {"attr": "mastro_drawing_layer",        "attr_type": "INT",     "attr_domain": "EDGE"},
    {"attr": "mastro_drawing_thickness",    "attr_type": "FLOAT",   "attr_domain": "EDGE"},
    {"attr": "mastro_drawing_style_l1",     "attr_type": "FLOAT",   "attr_domain": "EDGE"},
    {"attr": "mastro_drawing_style_g1",     "attr_type": "FLOAT",   "attr_domain": "EDGE"},
    {"attr": "mastro_drawing_style_l2",     "attr_type": "FLOAT",   "attr_domain": "EDGE"},
    {"attr": "mastro_drawing_style_g2",     "attr_type": "FLOAT",   "attr_domain": "EDGE"},
    {"attr": "mastro_drawing_style_l3",     "attr_type": "FLOAT",   "attr_domain": "EDGE"},
    {"attr": "mastro_drawing_style_g3",     "attr_type": "FLOAT",   "attr_domain": "EDGE"},
    {"attr": "mastro_drawing_black",        "attr_type": "BOOLEAN", "attr_domain": "EDGE"},
    {"attr": "mastro_drawing_black_switch", "attr_type": "BOOLEAN", "attr_domain": "EDGE"},
    {"attr": "mastro_drawing_visibile",     "attr_type": "BOOLEAN", "attr_domain": "EDGE"},
    {"attr": "mastro_drawing_resample",     "attr_type": "BOOLEAN", "attr_domain": "EDGE"},
]


def get_attr_layers(bm):
    """Return {attr_name: layer} for all MaStro drawing edge attributes in bm."""
    layers = {}
    for entry in _DRAWING_ATTRIBUTE_SET:
        bm_type = _ATTR_TYPE_TO_BM.get(entry["attr_type"])
        if bm_type is None:
            continue
        layer = getattr(bm.edges.layers, bm_type).get(entry["attr"])
        if layer is not None:
            layers[entry["attr"]] = layer
    return layers


def copy_drawing_attrs(src_edge, dst_edge, attr_layers):
    """Copy all MaStro drawing attributes from src_edge to dst_edge."""
    for layer in attr_layers.values():
        dst_edge[layer] = src_edge[layer]


def nearest_src_edge(ki, chain_edges, src_edges):
    """Map output edge index ki to the best source edge.

    1-to-1 when counts match; fractional-position mapping otherwise
    (handles inward offsets where Shapely collapses short edges).
    """
    if not src_edges:
        return None
    n_out, n_src = len(chain_edges), len(src_edges)
    if n_out == n_src:
        return src_edges[ki]
    t = ki / max(n_out - 1, 1)
    return src_edges[min(int(round(t * (n_src - 1))), n_src - 1)]


# ── Trim / extend math ────────────────────────────────────────────────────────

def signed_dist_2d(px, py, k0x, k0y, k1x, k1y):
    """Signed 2D cross product: >0 if (px,py) is left of k0→k1."""
    return (k1x - k0x) * (py - k0y) - (k1y - k0y) * (px - k0x)


def _seg_intersect_param(p0x, p0y, p1x, p1y, q0x, q0y, q1x, q1y):
    """Parametric intersection of two 2D lines. Returns (t_p, t_q) or None if parallel.

    t values are unclamped: t ∈ [0,1] means the crossing is within the segment,
    outside [0,1] means it is on the infinite extension.
    """
    dx = p1x - p0x;  dy = p1y - p0y
    ex = q1x - q0x;  ey = q1y - q0y
    cross = dx * ey - dy * ex
    if abs(cross) < 1e-10:
        return None
    fx = q0x - p0x;  fy = q0y - p0y
    return (fx * ey - fy * ex) / cross, (fx * dy - fy * dx) / cross


def _closest_params_3d(p0, kd, q0, cd):
    """Closest-approach parameters (t_knife, t_cand) for two 3D rays, or None if parallel.

    For truly coplanar (intersecting) lines the closest-approach distance is zero
    and pt_knife == pt_cand. For skew lines the caller checks the gap and SKIPs if
    it exceeds the coplanarity tolerance.
    """
    a = kd.dot(kd);  b = kd.dot(cd);  e = cd.dot(cd)
    denom = a * e - b * b
    if abs(denom) < 1e-12:
        return None
    r = p0 - q0
    c = kd.dot(r);  f = cd.dot(r)
    return (b * f - c * e) / denom, (a * f - b * c) / denom


def compute_trim_candidates(knife_w0, knife_w1, candidates_raw,
                             infinite_knife, coplanar_only, context):
    """Compute trim/extend classification for each candidate edge against the knife.

    candidates_raw: list of (v0_world, v1_world, edge_idx, v0_idx, v1_idx)

    infinite_knife: if False, only process candidates whose intersection lies
        within the knife's physical segment (t_knife ∈ [0,1]). If True, the
        knife acts as an infinite line (any t_knife).

    coplanar_only: if True, use 3D closest-approach (skips non-coplanar edges).
        If False, use screen-space 2D projection (handles apparent intersections
        between edges on different planes).

    Returns a list of dicts with keys:
      edge_idx, v0_idx, v1_idx, v0_world, v1_world, v0_2d, v1_2d,
      type: 'CROSS'   – candidate physically crosses the knife line
                        (t_cand ∈ [0,1]); split at intersection point.
            'EXTEND'  – candidate is on one side and its extension meets the
                        knife (t_cand outside [0,1]); move nearest endpoint.
            'PARALLEL'– no intersection (parallel lines).
            'SKIP'    – degenerate or outside knife scope.
      t_cand: parameter on the candidate at the intersection (None if no intersection).
      point:  world-space intersection point (None if no intersection).
    """
    region = context.region
    rv3d   = context.space_data.region_3d

    knife_2d_0 = location_3d_to_region_2d(region, rv3d, knife_w0)
    knife_2d_1 = location_3d_to_region_2d(region, rv3d, knife_w1)
    kd     = knife_w1 - knife_w0
    k_len2 = kd.dot(kd)
    results = []

    for v0_w, v1_w, edge_idx, v0_idx, v1_idx in candidates_raw:
        cd     = v1_w - v0_w
        c_len2 = cd.dot(cd)
        v0_2d  = location_3d_to_region_2d(region, rv3d, v0_w)
        v1_2d  = location_3d_to_region_2d(region, rv3d, v1_w)
        base   = dict(edge_idx=edge_idx, v0_idx=v0_idx, v1_idx=v1_idx,
                      v0_world=v0_w, v1_world=v1_w,
                      v0_2d=v0_2d, v1_2d=v1_2d, t_cand=None, point=None)

        if k_len2 < 1e-14 or c_len2 < 1e-14:
            results.append({**base, 'type': 'SKIP'});  continue

        if coplanar_only:
            res = _closest_params_3d(knife_w0, kd, v0_w, cd)
            if res is None:
                results.append({**base, 'type': 'PARALLEL'});  continue
            t_knife, t_cand = res
            pt_knife = knife_w0 + kd * t_knife
            pt_cand  = v0_w    + cd * t_cand
            if (pt_knife - pt_cand).length > 1e-4:
                results.append({**base, 'type': 'SKIP'});  continue
            if not infinite_knife and (t_knife < -1e-4 or t_knife > 1.0 + 1e-4):
                results.append({**base, 'type': 'SKIP'});  continue
            point  = (pt_knife + pt_cand) * 0.5
            ctype  = 'CROSS' if -1e-4 <= t_cand <= 1.0 + 1e-4 else 'EXTEND'
            t_cand = max(0.0, min(1.0, t_cand)) if ctype == 'CROSS' else t_cand
        else:
            if any(x is None for x in (knife_2d_0, knife_2d_1, v0_2d, v1_2d)):
                results.append({**base, 'type': 'SKIP'});  continue
            res2d = _seg_intersect_param(
                knife_2d_0[0], knife_2d_0[1], knife_2d_1[0], knife_2d_1[1],
                v0_2d[0],      v0_2d[1],      v1_2d[0],      v1_2d[1])
            if res2d is None:
                results.append({**base, 'type': 'PARALLEL'});  continue
            t_knife_2d, t_cand = res2d
            if not infinite_knife and (t_knife_2d < -1e-4 or t_knife_2d > 1.0 + 1e-4):
                results.append({**base, 'type': 'SKIP'});  continue
            point  = v0_w + cd * t_cand
            ctype  = 'CROSS' if -1e-4 <= t_cand <= 1.0 + 1e-4 else 'EXTEND'
            t_cand = max(0.0, min(1.0, t_cand)) if ctype == 'CROSS' else t_cand

        results.append({**base, 'type': ctype, 't_cand': t_cand, 'point': point})

    return results


def compute_edge_cuts(target_w0, target_w1,
                      other_edges_world, coplanar_only, context):
    """Find all intersection points along a target edge from a set of other edges.

    This is the inverse of compute_trim_candidates: the target edge is the
    candidate and every other edge is a potential knife.  Only intersections
    within the target segment (t_target ∈ [0, 1]) are returned.

    other_edges_world: iterable of (v0_world, v1_world) pairs.

    Returns a list of (t, point_world) sorted by t, with duplicates removed.
    t=0 is target_w0, t=1 is target_w1.
    """
    region = context.region
    rv3d   = context.space_data.region_3d

    td  = target_w1 - target_w0
    t_len2 = td.dot(td)
    if t_len2 < 1e-14:
        return []

    target_2d_0 = location_3d_to_region_2d(region, rv3d, target_w0)
    target_2d_1 = location_3d_to_region_2d(region, rv3d, target_w1)

    cuts = []

    for v0_w, v1_w in other_edges_world:
        kd     = v1_w - v0_w
        k_len2 = kd.dot(kd)
        if k_len2 < 1e-14:
            continue

        if coplanar_only:
            # 3D closest-approach: target is the candidate, other edge is knife.
            res = _closest_params_3d(target_w0, td, v0_w, kd)
            if res is None:
                continue
            t_target, t_knife = res
            if not (-1e-4 <= t_target <= 1.0 + 1e-4):
                continue
            if not (-1e-4 <= t_knife <= 1.0 + 1e-4):
                continue
            pt_target = target_w0 + td * t_target
            pt_knife  = v0_w     + kd * t_knife
            if (pt_target - pt_knife).length > 1e-4:
                continue
            point = (pt_target + pt_knife) * 0.5
            t_clamped = max(0.0, min(1.0, t_target))
        else:
            # Screen-space projection.
            v0_2d = location_3d_to_region_2d(region, rv3d, v0_w)
            v1_2d = location_3d_to_region_2d(region, rv3d, v1_w)
            if any(x is None for x in (target_2d_0, target_2d_1, v0_2d, v1_2d)):
                continue
            res2d = _seg_intersect_param(
                target_2d_0[0], target_2d_0[1], target_2d_1[0], target_2d_1[1],
                v0_2d[0],       v0_2d[1],       v1_2d[0],       v1_2d[1])
            if res2d is None:
                continue
            t_target, t_knife = res2d
            if not (-1e-4 <= t_target <= 1.0 + 1e-4):
                continue
            if not (-1e-4 <= t_knife <= 1.0 + 1e-4):
                continue
            point = target_w0 + td * t_target
            t_clamped = max(0.0, min(1.0, t_target))

        cuts.append((t_clamped, point))

    # Sort, remove duplicates, and strip endpoint hits (t ≈ 0 or t ≈ 1).
    # Endpoint hits come from edges that share a vertex with the target — they
    # are angular connections, not interior cuts.  Keeping them would create
    # zero-length edges in _apply_delete_segment.
    cuts.sort(key=lambda x: x[0])
    deduped = []
    for t, pt in cuts:
        if t < 1e-4 or t > 1.0 - 1e-4:
            continue   # skip endpoint connections
        if not deduped or abs(t - deduped[-1][0]) > 1e-4:
            deduped.append((t, pt))
    return deduped


def copy_bm_edge_attrs(bm, src, dst):
    """Copy all custom edge data layers (string, int, float, bool) from src to dst."""
    for coll in (bm.edges.layers.string, bm.edges.layers.int,
                 bm.edges.layers.float, bm.edges.layers.bool):
        for layer in coll.values():
            try:
                dst[layer] = src[layer]
            except Exception:
                pass


def copy_bm_vert_attrs(bm, src, dst):
    """Copy all custom vertex data layers (string, int, float, bool) from src to dst."""
    for coll in (bm.verts.layers.string, bm.verts.layers.int,
                 bm.verts.layers.float, bm.verts.layers.bool):
        for layer in coll.values():
            try:
                dst[layer] = src[layer]
            except Exception:
                pass


def assign_drawing_layer_to_edges(context, obj, bm, edges):
    """If obj is a MaStro drawing mesh, assign the active layer's drawing
    attributes to each edge in *edges*.

    Delegates to depsgraph_handlers._assign_layer_to_edge which already
    handles the layer lookup and attribute writing.  Calling this after
    creating new geometry in a creation operator (Circle, Rectangle, …)
    ensures that the new edges inherit the currently selected drawing layer.
    """
    if not obj.data.get("MaStro drawing mesh"):
        return
    from ...Handlers.depsgraph_handlers import _assign_layer_to_edge  # local import: avoids circular deps
    scene = context.scene
    for e in edges:
        if e.is_valid:
            _assign_layer_to_edge(scene, bm, e)
