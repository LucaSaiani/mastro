"""Utilities for rectangle creation, attribute tagging, and validation.

A rectangle is identified by custom bmesh attributes on its vertices and edges:
  vertices: mastro_cad_type (string), mastro_cad_status (int)
  edges:    mastro_cad_type_EDGE (string), mastro_cad_status_EDGE (int)
  value:    type = b"Rectangle", status = 1 (valid) or 0 (invalidated)

Validation checks (in order, first failure marks the offending elements invalid):
  1. Closed chain of exactly 4 edges, all tagged Rectangle + status=1
  2. Each vertex linked to exactly 2 rectangle edges
  3. All four corners are at 90 degrees (adjacent edges perpendicular)
  4. All four vertices are coplanar
"""

import bmesh
from mathutils import Vector

ATTR_TYPE        = "mastro_cad_type"
ATTR_STATUS      = "mastro_cad_status"
ATTR_TYPE_EDGE   = "mastro_cad_type_EDGE"
ATTR_STATUS_EDGE = "mastro_cad_status_EDGE"
from .constants import HANDLE_SIZE_PX


# ── Attribute helpers ─────────────────────────────────────────────────────────

def ensure_rect_layers(bm):
    """Get or create the four mastro_cad attribute layers."""
    vt = bm.verts.layers.string.get(ATTR_TYPE)        or bm.verts.layers.string.new(ATTR_TYPE)
    vs = bm.verts.layers.int.get(ATTR_STATUS)         or bm.verts.layers.int.new(ATTR_STATUS)
    et = bm.edges.layers.string.get(ATTR_TYPE_EDGE)   or bm.edges.layers.string.new(ATTR_TYPE_EDGE)
    es = bm.edges.layers.int.get(ATTR_STATUS_EDGE)    or bm.edges.layers.int.new(ATTR_STATUS_EDGE)
    return vt, vs, et, es


def get_rect_layers(bm):
    """Return (vt, vs, et, es) or None if any layer is missing."""
    vt = bm.verts.layers.string.get(ATTR_TYPE)
    vs = bm.verts.layers.int.get(ATTR_STATUS)
    et = bm.edges.layers.string.get(ATTR_TYPE_EDGE)
    es = bm.edges.layers.int.get(ATTR_STATUS_EDGE)
    if not all([vt, vs, et, es]):
        return None
    return vt, vs, et, es


def set_rect_attrs(bm, verts, edges, layers=None):
    """Tag verts and edges as belonging to a valid rectangle.

    layers: pre-obtained (vt, vs, et, es) tuple.  When None, ensure_rect_layers
    is called internally — but NOTE that calling ensure_rect_layers after geometry
    has been created invalidates all bmesh element references.  Always pass the
    layers obtained BEFORE creating geometry.
    """
    vt, vs, et, es = layers if layers is not None else ensure_rect_layers(bm)
    for v in verts:
        v[vt] = b"Rectangle"
        v[vs] = 1
    for e in edges:
        e[et] = b"Rectangle"
        e[es] = 1


# ── Chain traversal ───────────────────────────────────────────────────────────

def _walk_rect_chain(bm, start_v, layers):
    """Walk a closed chain of 4 rectangle edges from start_v.

    Returns (chain_verts, chain_edges) if successful, or (None, None).
    Does NOT modify the mesh — purely reads attributes.
    """
    vt, vs, et, es = layers
    chain_verts, chain_edges = [], []
    v, prev_e = start_v, None

    for step in range(4):
        if not v[vs] or v[vt] != b"Rectangle":
            return None, None
        chain_verts.append(v)
        cands = [e for e in v.link_edges
                 if e != prev_e and e[es] and e[et] == b"Rectangle"]
        # At step 0 prev_e is None so both rect edges are candidates — either
        # direction traverses the full loop.  From step 1 onward exactly 1 is expected.
        if not cands or (step > 0 and len(cands) != 1):
            return None, None
        e = cands[0]
        chain_edges.append(e)
        prev_e = e
        v = e.other_vert(v)

    if v != start_v:
        return None, None
    return chain_verts, chain_edges


# ── Read-only check (used by the draw handler) ────────────────────────────────

def check_rect(bm, seed):
    """Read-only rectangle check starting from seed (BMVert or BMEdge).

    Returns (True, chain_verts, chain_edges) if all conditions pass,
    or (False, None, None) — never modifies the mesh.
    """
    from .cad_utils import are_coplanar

    layers = get_rect_layers(bm)
    if layers is None:
        return False, None, None

    vt, vs, et, es = layers
    start_v = seed.verts[0] if isinstance(seed, bmesh.types.BMEdge) else seed

    chain_verts, chain_edges = _walk_rect_chain(bm, start_v, layers)
    if chain_verts is None:
        return False, None, None

    # Check 2: each vertex linked to exactly 2 rectangle edges.
    for v in chain_verts:
        n = len([e for e in v.link_edges if e[es] and e[et] == b"Rectangle"])
        if n != 2:
            return False, None, None

    # Check 3: coplanar (in local space — sufficient for detecting deformation).
    pts = [v.co.copy() for v in chain_verts]
    cop = are_coplanar(pts, tol=1e-4)
    if not cop:
        return False, None, None

    # Check 4: perpendicular corners.
    for i in range(4):
        v_corner = chain_verts[(i + 1) % 4]
        e0, e1   = chain_edges[i], chain_edges[(i + 1) % 4]
        d0 = (e0.other_vert(v_corner).co - v_corner.co).normalized()
        d1 = (e1.other_vert(v_corner).co - v_corner.co).normalized()
        dot = abs(d0.dot(d1))
        if dot > 0.01:
            return False, None, None

    return True, chain_verts, chain_edges


# ── Validating check (used by the edit operator — marks failures) ─────────────

def validate_rect(bm, seed, mw=None):
    """Full rectangle validation; marks failing elements with status=0.

    mw: optional world matrix — used for coplanarity check in world space.
    Returns (True, chain_verts, chain_edges) or (False, None, None).
    """
    from .cad_utils import are_coplanar

    layers = get_rect_layers(bm)
    if layers is None:
        return False, None, None

    vt, vs, et, es = layers
    start_v = seed.verts[0] if isinstance(seed, bmesh.types.BMEdge) else seed

    # Check 1: walk the chain.
    chain_verts, chain_edges = _walk_rect_chain(bm, start_v, layers)
    if chain_verts is None:
        start_v[vs] = 0
        return False, None, None

    # Check 2: connectivity.
    for v in chain_verts:
        if len([e for e in v.link_edges if e[es] and e[et] == b"Rectangle"]) != 2:
            v[vs] = 0
            return False, None, None

    # Check 3: coplanar.
    pts = [v.co.copy() for v in chain_verts]
    if mw:
        pts = [mw @ p for p in pts]
    if not are_coplanar(pts, tol=1e-4):
        for v in chain_verts:
            v[vs] = 0
        return False, None, None

    # Check 4: perpendicularity.
    for i in range(4):
        v_corner = chain_verts[(i + 1) % 4]
        e0, e1   = chain_edges[i], chain_edges[(i + 1) % 4]
        d0 = (e0.other_vert(v_corner).co - v_corner.co).normalized()
        d1 = (e1.other_vert(v_corner).co - v_corner.co).normalized()
        if abs(d0.dot(d1)) > 0.01:
            v_corner[vs] = 0
            return False, None, None

    return True, chain_verts, chain_edges


# ── Geometry helpers ──────────────────────────────────────────────────────────

def rect_local_axes(chain_verts, mw=None):
    """Derive the rectangle's local X, Y axes and normal from its corners.

    chain_verts: [v0, v1, v2, v3] — v0→v1 is one edge, v1→v2 another.
    mw:          optional world matrix.
    Returns (x_axis, y_axis, normal) as normalized Vectors (world space).
    """
    pts = [v.co.copy() for v in chain_verts]
    if mw:
        pts = [mw @ p for p in pts]
    v0, v1, v2, v3 = pts
    x_axis = (v1 - v0).normalized()
    y_axis = (v3 - v0).normalized()
    normal = x_axis.cross(y_axis).normalized()
    return x_axis, y_axis, normal


def compute_new_corners(p_dragged, p_fixed, x_axis, y_axis):
    """Recompute rectangle corners when one diagonal corner is dragged.

    p_fixed stays; p_dragged is the new position of the opposite corner.
    Returns [p_dragged, p_new1, p_fixed, p_new2] matching the original chain order
    (v0, v1, v2, v3 where v0-v2 and v1-v3 are the two diagonals).
    """
    d     = p_dragged - p_fixed
    p_new1 = p_fixed + x_axis * d.dot(x_axis)
    p_new2 = p_fixed + y_axis * d.dot(y_axis)
    return [p_dragged, p_new1, p_fixed, p_new2]
