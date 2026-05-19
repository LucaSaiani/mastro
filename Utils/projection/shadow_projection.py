import math
from mathutils import Vector


def _cam_basis(camera):
    m = camera.matrix_world
    return (
        m.to_translation(),
        -Vector(m.col[2][:3]).normalized(),   # forward  (-Z)
         Vector(m.col[0][:3]).normalized(),   # right    (+X)
         Vector(m.col[1][:3]).normalized(),   # up       (+Y)
    )


def _clip_near(verts_ws, cam_loc, cam_fwd, near):
    """Sutherland-Hodgman clip of a 3-D polygon against the camera near plane."""
    out = []
    n = len(verts_ws)
    for i in range(n):
        C = verts_ws[i]
        P = verts_ws[i - 1]
        cd = (C - cam_loc).dot(cam_fwd)
        pd = (P - cam_loc).dot(cam_fwd)
        c_in = cd >= near
        p_in = pd >= near
        if c_in:
            if not p_in:
                denom = cd - pd
                if abs(denom) > 1e-12:
                    t = (near - pd) / denom
                    out.append(P.lerp(C, t))
            out.append(C)
        elif p_in:
            denom = cd - pd
            if abs(denom) > 1e-12:
                t = (near - pd) / denom
                out.append(P.lerp(C, t))
    return out


def _world_to_uv(verts_ws, cam_loc, cam_fwd, cam_right, cam_up):
    result = []
    for p in verts_ws:
        v     = p - cam_loc
        depth = v.dot(cam_fwd)
        result.append((v.dot(cam_right) / depth, v.dot(cam_up) / depth))
    return result


def _uv_to_world(u, v, cam_loc, cam_fwd, cam_right, cam_up, dist):
    return cam_loc + cam_fwd * dist + cam_right * (u * dist) + cam_up * (v * dist)


def _viewport_half_planes(camera, scene):
    d      = camera.data
    aspect = scene.render.resolution_x / max(scene.render.resolution_y, 1)
    fit    = d.sensor_fit
    if fit == 'VERTICAL' or (fit == 'AUTO' and aspect < 1.0):
        hv = math.tan(d.angle / 2)
        hu = hv * aspect
    else:
        hu = math.tan(d.angle / 2)
        hv = hu / aspect
    # (nx, ny, bound): inside region is nx*u + ny*v <= bound
    return [( 1, 0, hu), (-1, 0, hu), (0,  1, hv), (0, -1, hv)]


def _sh_clip_2d(poly_uv, half_planes):
    """Sutherland-Hodgman 2-D clip of a polygon against a list of half-planes."""
    output = list(poly_uv)
    for nx, ny, bound in half_planes:
        if not output:
            return []
        inp    = output[:]
        output = []
        n      = len(inp)
        for j in range(n):
            P    = inp[j]
            S    = inp[j - 1]
            P_in = nx * P[0] + ny * P[1] <= bound
            S_in = nx * S[0] + ny * S[1] <= bound
            if P_in:
                if not S_in:
                    denom = nx * (P[0] - S[0]) + ny * (P[1] - S[1])
                    if abs(denom) > 1e-12:
                        t = (bound - nx * S[0] - ny * S[1]) / denom
                        output.append((S[0] + t * (P[0] - S[0]),
                                       S[1] + t * (P[1] - S[1])))
                output.append(P)
            elif S_in:
                denom = nx * (P[0] - S[0]) + ny * (P[1] - S[1])
                if abs(denom) > 1e-12:
                    t = (bound - nx * S[0] - ny * S[1]) / denom
                    output.append((S[0] + t * (P[0] - S[0]),
                                   S[1] + t * (P[1] - S[1])))
    return output
