# ── MaStroCad UI constants ────────────────────────────────────────────────────
# Edit these values to tune visual feedback and interaction feel.

# Handle squares drawn at vertices / edge midpoints (half-size in pixels).
HANDLE_SIZE_PX = 8

# Extra padding (pixels) added to handle size when a thick drawing layer is present,
# so the handle is always visible around thick vertex/edge indicators.
HANDLE_THICK_PADDING_PX = 10

# Pixel radius within which the edit handle grab is activated (Alt+G).
HANDLE_GRAB_RADIUS_PX = 96

# Pixel radius for vertex / midpoint snap.
SNAP_RADIUS_PX = 32

# Tighter pixel radius for edge nearest-point snap.
SNAP_RADIUS_EDGE_PX = 24

# Maximum circle radius accepted by Circle3 operator (meters).
# Solutions with radius > this value are discarded as "at infinity".
MAX_CIRCLE_RADIUS = 1000.0

# ── Dotted line style (radius, offset guideline, Circle3 preview) ─────────────
DOTTED_COLOR = (0.8, 0.8, 0.8, 0.9)
DOTTED_SCALE = 15.0

# ── Drawing mesh edit-mode selection overlay ──────────────────────────────────
# GPU lines drawn over GP strokes to make selected edges visible in edit mode.
# Alpha < 1 keeps the GP stroke faintly readable underneath.
DRAWING_SEL_COLOR       = (1.0, 0.6, 0.0, 0.7)   # selected edge (orange)
DRAWING_ACTIVE_COLOR    = (1.0, 1.0, 1.0, 0.8)   # active edge (white)
DRAWING_SEL_LINE_WIDTH  = 2.5                      # pixels, independent of mastro_drawing_thickness
