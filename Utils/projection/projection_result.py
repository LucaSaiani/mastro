from dataclasses import dataclass, field

# =============================================================================
#  ObjectProjection — structured container for per-object projection bmeshes
# =============================================================================

@dataclass
class ObjectProjection:
    """
    Holds the four per-category bmeshes produced by the projection step for
    a single source object, plus temporary vertex-cache dicts used when
    injecting intersection curves.

    Category relationships:
        bm_visible  ⊇  bm_silhouette        (visible is the complete superset)
        bm_hidden   ⊇  bm_silhouette_hidden  (hidden  is the complete superset)

    All bmesh fields are None when the corresponding category produced no
    geometry, or when the feature is disabled in props.
    """

    # ── Geometry bmeshes ──────────────────────────────────────────────────────
    bm_visible:           object = None   # BMesh | None
    bm_silhouette:        object = None   # BMesh | None
    bm_hidden:            object = None   # BMesh | None
    bm_silhouette_hidden: object = None   # BMesh | None
    bm_section:           object = None   # BMesh | None  (clip plane section lines)

    # ── Temporary vertex caches for intersection curve injection ──────────────
    # Populated on demand by _merge_intersections_into_results; not used
    # elsewhere and freed implicitly when the ObjectProjection is discarded.
    vc_vis: dict = field(default_factory=dict)  # (int,int) → BMVert in bm_visible
    vc_hid: dict = field(default_factory=dict)  # (int,int) → BMVert in bm_hidden

    def free_all(self):
        """Free all bmeshes that are still alive."""
        for bm in (self.bm_visible, self.bm_silhouette,
                   self.bm_hidden, self.bm_silhouette_hidden,
                   self.bm_section):
            if bm is not None:
                bm.free()
        self.bm_visible           = None
        self.bm_silhouette        = None
        self.bm_hidden            = None
        self.bm_silhouette_hidden = None
        self.bm_section           = None