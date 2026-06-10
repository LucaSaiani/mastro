# =============================================================================
#  Tolerance constants — centralised to avoid magic numbers scattered in code
# =============================================================================

_TOL_COLINEAR   = 1e-4   # max point-to-line distance for colinearity tests
_TOL_PARALLEL   = 1e-5   # max cross-product length for parallelism tests
_TOL_DEGENERATE = 1e-9   # min edge length to be considered non-degenerate
_TOL_SNAP_SELF  = 1e-4   # min ray parameter to skip self-intersection in snap
_TOL_RAY_DENOM  = 1e-12  # min |denominator| for 2D ray/segment intersection
_EPSILON        = 1e-6   # general-purpose small value (triangle tests, NDC)
_MIN_SEG_LEN    = 1e-4   # min segment length to be considered non-degenerate
_COORD_QUANTIZE = 1e5    # quantization factor for 2D vertex position hashing:
                         # coordinates are multiplied by this value and truncated
                         # to int, giving ~0.01mm resolution at unit scale