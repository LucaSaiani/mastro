import bpy
import struct
import zlib
import os

_preview_coll = None
_CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")

WIDE_W    = 512
WIDE_H    = 512

CURVE_LENGTH_MM   = 20.0
LINE_THICKNESS_MM =  0.5

# Cartesian coords, x and y in [0,1], (0,0) = bottom-left.
_CTRL = [
    (0.101, 0.203),
    (0.139, 0.360),
    (0.227, 0.535),
    (0.347, 0.551),
    (0.355, 0.344),
    (0.418, 0.256),
    (0.544, 0.299),
    (0.758, 0.542),
    (0.940, 0.819),
]


def _catmull_rom(p0, p1, p2, p3, t):
    return 0.5 * (
        2*p1
        + (-p0 + p2) * t
        + (2*p0 - 5*p1 + 4*p2 - p3) * t*t
        + (-p0 + 3*p1 - 3*p2 + p3) * t*t*t
    )


def _build_y_table(width=WIDE_W, height=WIDE_H, margin=0.05):
    """Y pixel for each x in [0, width). Cartesian _CTRL → image coords."""
    pts    = _CTRL
    p0_ext = 2*pts[0][1]  - pts[1][1]
    pN_ext = 2*pts[-1][1] - pts[-2][1]
    ys     = [p0_ext] + [p[1] for p in pts] + [pN_ext]
    n_segs = len(pts) - 1
    table  = []
    for x in range(width):
        x_norm = x / (width - 1)
        seg_f  = x_norm * n_segs
        seg    = min(int(seg_f), n_segs - 1)
        t      = seg_f - seg
        y_norm = _catmull_rom(ys[seg], ys[seg+1], ys[seg+2], ys[seg+3], t)
        y_norm = max(margin, min(1 - margin, y_norm))
        table.append(int((1 - y_norm) * (height - 1)))
    return table


def _build_arc_table(y_table):
    """Cumulative arc length in pixels for each x in y_table."""
    arc = [0.0]
    for x in range(1, WIDE_W):
        dy = y_table[x] - y_table[x - 1]
        arc.append(arc[-1] + (1 + dy*dy) ** 0.5)
    return arc


def _arc_to_xy(arc_table, y_table, s):
    """Interpolate (x_float, y_float) on the curve at arc-length s."""
    lo, hi = 0, len(arc_table) - 1
    while lo < hi - 1:
        mid = (lo + hi) // 2
        if arc_table[mid] <= s:
            lo = mid
        else:
            hi = mid
    t = ((s - arc_table[lo]) / (arc_table[hi] - arc_table[lo])
         if arc_table[hi] > arc_table[lo] else 0.0)
    return lo + t, y_table[lo] + t * (y_table[hi] - y_table[lo])


def _tangent(y_table, xf):
    """Unit tangent vector at curve position xf (float x in wide coords)."""
    x = max(1, min(round(xf), len(y_table) - 2))
    dx = 2.0
    dy = float(y_table[x + 1] - y_table[x - 1])
    length = (dx*dx + dy*dy) ** 0.5
    return dx / length, dy / length


def _fill_polygon(pixels, width, height, polygon, color=(255, 255, 255)):
    """Scanline fill for a polygon (list of (x, y) float pairs)."""
    if len(polygon) < 3:
        return
    r, g, b = color
    pixel = [r, g, b, 255]
    min_y = max(0, int(min(p[1] for p in polygon)))
    max_y = min(height - 1, int(max(p[1] for p in polygon)) + 1)
    n = len(polygon)
    for y in range(min_y, max_y + 1):
        xs = []
        for i in range(n):
            x1, y1 = polygon[i]
            x2, y2 = polygon[(i + 1) % n]
            if (y1 <= y < y2) or (y2 <= y < y1):
                xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            for x in range(max(0, round(xs[i])), min(width, round(xs[i + 1]) + 1)):
                pixels[(y * width + x) * 4:(y * width + x) * 4 + 4] = pixel


def _stroke_segment(pixels, width, height, y_table, arc_table, s_start, s_end, x_start, radius, color=(255, 255, 255)):
    """Render one dash as a filled polygon with square ends."""
    N = max(2, int(s_end - s_start) + 1)
    left_pts, right_pts = [], []
    for i in range(N):
        s = s_start + (s_end - s_start) * i / (N - 1)
        xf, yf = _arc_to_xy(arc_table, y_table, s)
        tx, ty = _tangent(y_table, xf)
        nx, ny = -ty, tx
        left_pts.append( (xf - x_start + nx * radius, yf + ny * radius))
        right_pts.append((xf - x_start - nx * radius, yf - ny * radius))
    _fill_polygon(pixels, width, height, left_pts + list(reversed(right_pts)), color)


def _render(pixels, width, height, y_table, arc_table, seq, x_start=0,
            color=(255, 255, 255), thickness_mm=LINE_THICKNESS_MM):
    """Draw dash pattern as filled polygons with square ends."""
    arc_total  = arc_table[-1]
    scale      = arc_total / CURVE_LENGTH_MM if arc_total > 0 else 1.0
    radius     = max(1, round(thickness_mm * scale / 2))

    arc_begin  = arc_table[x_start]
    arc_finish = arc_table[min(x_start + width - 1, len(arc_table) - 1)]

    if not seq:
        _stroke_segment(pixels, width, height, y_table, arc_table,
                        arc_begin, arc_finish, x_start, radius, color)
        return

    cycle     = [(i % 2 == 0, max(1, round(v * scale))) for i, v in enumerate(seq)]
    cycle_len = sum(n for _, n in cycle)

    s = arc_begin
    while s < arc_finish:
        arc_pos = s % cycle_len
        acc = 0
        for dash, n in cycle:
            if arc_pos < acc + n:
                seg_end = min(s + (n - (arc_pos - acc)), arc_finish)
                if dash:
                    _stroke_segment(pixels, width, height, y_table, arc_table,
                                    s, seg_end, x_start, radius, color)
                s = seg_end
                break
            acc += n


def _png_bytes(pixels, width, height):
    def _chunk(tag, data):
        payload = tag + data
        return struct.pack('>I', len(data)) + payload + struct.pack('>I', zlib.crc32(payload) & 0xFFFFFFFF)
    sig  = b'\x89PNG\r\n\x1a\n'
    ihdr = _chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0))
    raw  = b''.join(b'\x00' + bytes(pixels[y * width * 4:(y + 1) * width * 4]) for y in range(height))
    idat = _chunk(b'IDAT', zlib.compress(raw, 6))
    iend = _chunk(b'IEND', b'')
    return sig + ihdr + idat + iend


def _make_wide_png(seq, color=(255, 255, 255), thickness_mm=LINE_THICKNESS_MM):
    y_table   = _build_y_table(WIDE_W, WIDE_H)
    arc_table = _build_arc_table(y_table)
    pixels    = bytearray(WIDE_W * WIDE_H * 4)
    _render(pixels, WIDE_W, WIDE_H, y_table, arc_table, seq, x_start=0,
            color=color, thickness_mm=thickness_mm)
    return _png_bytes(pixels, WIDE_W, WIDE_H)


def _icon_paths(pattern_id):
    tile = os.path.join(_CACHE_DIR, f"{pattern_id}_tile.png")
    wide = os.path.join(_CACHE_DIR, f"{pattern_id}_wide.png")
    return tile, wide


def invalidate_icon(pattern_id):
    """Call this from line_style_properties update callbacks to force icon regeneration."""
    tile, wide = _icon_paths(pattern_id)
    for path in (tile, wide):
        if os.path.exists(path):
            os.remove(path)
    # Also remove all colored variants (keys start with "{pattern_id}_wide_")
    prefix = f"{pattern_id}_wide"
    if _preview_coll is not None:
        keys_to_remove = [k for k in _preview_coll.keys() if k == f"{pattern_id}_tile" or k.startswith(prefix)]
        for key in keys_to_remove:
            del _preview_coll[key]
    # Remove cached colored PNG files
    colored_prefix = os.path.join(_CACHE_DIR, f"{pattern_id}_wide_")
    for fname in os.listdir(_CACHE_DIR) if os.path.isdir(_CACHE_DIR) else []:
        if fname.startswith(f"{pattern_id}_wide_"):
            try:
                os.remove(os.path.join(_CACHE_DIR, fname))
            except OSError:
                pass


def _load_icon(pcoll, key, path, png_fn):
    os.makedirs(_CACHE_DIR, exist_ok=True)
    if not os.path.exists(path):
        with open(path, 'wb') as fh:
            fh.write(png_fn())
        if key in pcoll:
            del pcoll[key]
    if key not in pcoll:
        pcoll.load(key, path, 'IMAGE')
    return pcoll[key].icon_id


def get_wide_icon_id(pattern):
    pcoll = _preview_coll
    if pcoll is None or pattern.pattern_id < 0:
        return 0
    seq = pattern.to_sequence()
    pid = pattern.pattern_id
    _, wide = _icon_paths(pid)
    return _load_icon(pcoll, f"{pid}_wide", wide, lambda: _make_wide_png(seq))


def get_color_swatch_icon_id(color_rgb=(255, 255, 255)):
    """Return icon_id for a solid-color 32×32 rectangle. Cached like line icons."""
    pcoll = _preview_coll
    if pcoll is None:
        return 0
    r, g, b = color_rgb
    key  = f"swatch_{r:02x}{g:02x}{b:02x}"
    path = os.path.join(_CACHE_DIR, f"{key}.png")
    def _make():
        pixels = bytearray([r, g, b, 255] * 32 * 32)
        return _png_bytes(pixels, 32, 32)
    return _load_icon(pcoll, key, path, _make)


_CUSTOM_PATTERN_ICON_KEY = "custom_pattern"
_CUSTOM_PATTERN_ICON_PATH = os.path.join(os.path.dirname(__file__), "custom_pattern.png")


def get_custom_pattern_icon_id():
    """Return icon_id for the static custom-pattern PNG (Icons/custom_pattern.png).

    The file is loaded once into _preview_coll and cached by key.
    Replace the PNG file on disk and reload the addon to update the icon.
    """
    pcoll = _preview_coll
    if pcoll is None:
        return 0
    key = _CUSTOM_PATTERN_ICON_KEY
    if key not in pcoll:
        if not os.path.exists(_CUSTOM_PATTERN_ICON_PATH):
            return 0
        pcoll.load(key, _CUSTOM_PATTERN_ICON_PATH, 'IMAGE')
    return pcoll[key].icon_id


def get_wide_icon_id_colored(pattern, color_rgb=(255, 255, 255), thickness_mm=LINE_THICKNESS_MM):
    """Return icon_id for pattern rendered with a specific color and thickness.

    color_rgb: (r, g, b) integers 0-255.
    thickness_mm: pen thickness in mm.
    Each unique (pattern, color, thickness) combination gets its own cached file.
    """
    pcoll = _preview_coll
    if pcoll is None or pattern.pattern_id < 0:
        return 0
    r, g, b = color_rgb
    pid = pattern.pattern_id
    key  = f"{pid}_wide_{r:02x}{g:02x}{b:02x}_{thickness_mm:.2f}"
    path = os.path.join(_CACHE_DIR, f"{key}.png")
    seq  = pattern.to_sequence()
    return _load_icon(pcoll, key, path,
                      lambda: _make_wide_png(seq, (r, g, b), thickness_mm))


def register():
    global _preview_coll
    _preview_coll = bpy.utils.previews.new()


def unregister():
    global _preview_coll
    if _preview_coll is not None:
        bpy.utils.previews.remove(_preview_coll)
        _preview_coll = None
