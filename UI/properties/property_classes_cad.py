import bpy
from bpy.types import PropertyGroup
from bpy.props import (IntProperty,
                       StringProperty,
                       BoolProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       EnumProperty,
)


# =============================================================================
# Pens
# =============================================================================
STANDARD_PENS = [
    {"thickness": 0.10, "color": (0.30, 0.04, 0.04, 1.0), "default": False},  # bordeaux
    {"thickness": 0.13, "color": (0.40, 0.10, 0.60, 1.0), "default": False},  # viola
    {"thickness": 0.18, "color": (0.80, 0.05, 0.05, 1.0), "default": True },  # rosso
    {"thickness": 0.20, "color": (0.75, 0.55, 0.05, 1.0), "default": False},  # oro
    {"thickness": 0.25, "color": (0.67, 0.67, 0.67, 1.0), "default": True },  # argento
    {"thickness": 0.30, "color": (0.30, 0.40, 0.05, 1.0), "default": False},  # verde oliva
    {"thickness": 0.35, "color": (0.95, 0.93, 0.65, 1.0), "default": True },  # giallo
    {"thickness": 0.40, "color": (0.90, 0.45, 0.05, 1.0), "default": False},  # arancione
    {"thickness": 0.50, "color": (0.40, 0.20, 0.05, 1.0), "default": True },  # marrone
    {"thickness": 0.60, "color": (0.65, 0.75, 0.85, 1.0), "default": False},  # azzurro
    {"thickness": 0.70, "color": (0.05, 0.20, 0.80, 1.0), "default": True },  # blu
    {"thickness": 0.80, "color": (0.81, 0.95, 0.62, 1.0), "default": False},  # verde menta
    {"thickness": 1.00, "color": (0.80, 0.35, 0.05, 1.0), "default": True },  # arancione scuro
    {"thickness": 1.40, "color": (0.30, 0.60, 0.95, 1.0), "default": False},  # blu cielo
    {"thickness": 2.00, "color": (0.50, 0.15, 0.10, 1.0), "default": False},  # marrone rossiccio
]


def _resort_pen(self, context):
    """Re-sort the pens collection after a thickness change."""
    pens = context.scene.mastro_cad_pens
    idx = next((i for i in range(len(pens)) if pens[i].pen_id == self.pen_id), -1)
    if idx < 0:
        return
    while idx > 0 and pens[idx - 1].thickness > pens[idx].thickness:
        pens.move(idx, idx - 1)
        idx -= 1
    while idx < len(pens) - 1 and pens[idx + 1].thickness < pens[idx].thickness:
        pens.move(idx, idx + 1)
        idx += 1


def _sync_layers_to_pen(pen, context):
    """Push pen colour to all layers that track this pen."""
    global _syncing
    _syncing = True
    for layer in context.scene.mastro_cad_layers:
        if layer.use_pen_color and layer.pen_id == pen.pen_id:
            layer.color = pen.color
    _syncing = False
    from ...Utils.mastro_cad.update_drawing_attributes import update_pen
    update_pen(pen, context)


def _on_pen_thickness_changed(pen, context):
    _resort_pen(pen, context)
    from ...Utils.mastro_cad.update_drawing_attributes import update_pen
    update_pen(pen, context)


class mastro_CL_cad_pen(PropertyGroup):
    """A single pen entry — either a standard (locked) or custom pen."""
    pen_id:    IntProperty(name="Id", default=-1)
    thickness: FloatProperty(name="Thickness (mm)", min=0.01, max=10.0,
                             update=_on_pen_thickness_changed)
    color:     FloatVectorProperty(name="Colour", subtype='COLOR', size=4,
                                   min=0.0, max=1.0, default=(0.5, 0.5, 0.5, 1.0),
                                   update=_sync_layers_to_pen)
    enabled:   BoolProperty(name="Active", default=True)
    locked:    BoolProperty(name="Locked", default=False)
    fixed_colour: BoolProperty(name="Fixed Colour",
                               description="Keep this pen's colour; if disabled the pen renders in black",
                               default=False)


def _next_pen_id(pens):
    if not pens:
        return 0
    return max(p.pen_id for p in pens) + 1


def _insert_pen_sorted(collection, thickness, color, enabled, locked=False, pen_id=None):
    for p in collection:
        if round(p.thickness, 4) == round(thickness, 4):
            return None
    if pen_id is None:
        pen_id = _next_pen_id(collection)
    item = collection.add()
    item.pen_id    = pen_id
    item.thickness = thickness
    item.color     = color
    item.enabled   = enabled
    item.locked    = locked
    idx = len(collection) - 1
    while idx > 0 and collection[idx - 1].thickness > collection[idx].thickness:
        collection.move(idx, idx - 1)
        idx -= 1
    return item


def ensure_standard_pens(scene):
    pens = scene.mastro_cad_pens
    existing_widths = {round(p.thickness, 4) for p in pens if p.locked}
    for std_id, data in enumerate(STANDARD_PENS):
        w = round(data["thickness"], 4)
        if w not in existing_widths:
            _insert_pen_sorted(pens, data["thickness"], data["color"], data["default"],
                               locked=True, pen_id=std_id)


# =============================================================================
# Dash Patterns / Line Types
# =============================================================================
DEFAULT_PATTERNS = [
    {"name": "Continuous", "locked": True, "slots": [1.0, 0.0, 0.0, 0.0, 0.0, 0.0]},
    {"name": "Dash",       "locked": True, "slots": [2.0, 1.0, 0.0, 0.0, 0.0, 0.0]},
    {"name": "Dash Dot",   "locked": True, "slots": [2.0, 1.0, 0.5, 1.0, 0.0, 0.0]},
    {"name": "Dot",        "locked": True, "slots": [0.5, 1.0, 0.0, 0.0, 0.0, 0.0]},
]


def _invalidate(self, context):
    from ...Icons import invalidate_icon
    invalidate_icon(self.pattern_id)
    from ...Utils.mastro_cad.update_drawing_attributes import update_pattern
    update_pattern(self, context)
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            area.tag_redraw()


def _on_custom_pattern_toggled(self, context):
    from ...Nodes.operators.NODE_OT_MaStro_Drawing_GN import set_custom_pattern_nodes
    set_custom_pattern_nodes(context.scene, self.pattern_id, self.use_custom_pattern)


class mastro_CL_cad_dash_pattern(PropertyGroup):
    """A line type: name and up to 6 alternating line/gap values in mm.
    Slots alternate l/g: [l1, g1, l2, g2, l3, g3]. Zero means slot unused."""
    pattern_id: IntProperty(name="Id", default=-1)
    name:       StringProperty(name="Name", default="Pattern")
    locked:     BoolProperty(default=False)

    l1: FloatProperty(name="Line",  description="Line length (mm)",  min=0.1, soft_max=20.0, default=1.0, precision=1, step=50, update=_invalidate)
    g1: FloatProperty(name="Space", description="Space length (mm)", min=0.0, soft_max=20.0, default=0.0, precision=1, step=50, update=_invalidate)
    l2: FloatProperty(name="Line",  description="Line length (mm)",  min=0.0, soft_max=20.0, default=0.0, precision=1, step=50, update=_invalidate)
    g2: FloatProperty(name="Space", description="Space length (mm)", min=0.0, soft_max=20.0, default=0.0, precision=1, step=50, update=_invalidate)
    l3: FloatProperty(name="Line",  description="Line length (mm)",  min=0.0, soft_max=20.0, default=0.0, precision=1, step=50, update=_invalidate)
    g3: FloatProperty(name="Space", description="Space length (mm)", min=0.0, soft_max=20.0, default=0.0, precision=1, step=50, update=_invalidate)

    use_custom_pattern: BoolProperty(
        name="Custom Pattern",
        description="Add a Combine Bundle node in the GN modifier to supply custom geometry for this line type",
        default=False,
        update=_on_custom_pattern_toggled,
    )

    def to_sequence(self):
        """Return active values as a list, trimming trailing zeros.
        If all slots are zero, returns [1.0] (solid line fallback)."""
        slots = [self.l1, self.g1, self.l2, self.g2, self.l3, self.g3]
        last = -1
        for i, v in enumerate(slots):
            if v > 0.0:
                last = i
        return slots[:last + 1] if last >= 0 else [1.0]


def _next_pattern_id(patterns):
    if not patterns:
        return 0
    return max(p.pattern_id for p in patterns) + 1


def ensure_default_patterns(patterns):
    """Populate defaults if empty; assign missing pattern_ids to existing items."""
    if len(patterns) == 0:
        for i, data in enumerate(DEFAULT_PATTERNS):
            p = patterns.add()
            p.pattern_id = i
            p.name   = data["name"]
            p.locked = data["locked"]
            p.l1, p.g1, p.l2, p.g2, p.l3, p.g3 = data["slots"]
        return
    # Migrate: assign stable ids to items that were created before pattern_id existed
    used_ids = {p.pattern_id for p in patterns if p.pattern_id >= 0}
    next_id  = (max(used_ids) + 1) if used_ids else 0
    for p in patterns:
        if p.pattern_id < 0:
            p.pattern_id = next_id
            next_id += 1
    # Clean up orphaned cache files from before migration
    from ...Icons import invalidate_icon
    invalidate_icon(-1)


# =============================================================================
# Layers
# =============================================================================
_syncing = False  # guard against recursive color updates
_enum_cache = {}  # keeps enum item lists alive so Blender's C pointers stay valid
_icon_enum_cache = []  # 4-tuple cache for template_icon_view (index-based get/set)

DEFAULT_LAYERS = [
    # ISO 128 line types — pen_id: 4=0.25mm thin, 6=0.35mm medium, 8=0.50mm thick
    # pattern_id: 0=Continuous, 1=Dash, 2=Dash Dot, 3=Dot
    {"layer_id": 0, "name": "Thin",          "pen_id": 4, "pattern_id": 0,
     "use_pen_color": True, "black": True, "visible": True, "locked": True,
     "description": "Dimension lines, extension lines, notes, boundaries of sections"},
    {"layer_id": 1, "name": "Medium",         "pen_id": 6, "pattern_id": 0,
     "use_pen_color": True, "black": True, "visible": True, "locked": True,
     "description": "Visible edges and visible outlines of components"},
    {"layer_id": 2, "name": "Thick",          "pen_id": 8, "pattern_id": 0,
     "use_pen_color": True, "black": True, "visible": True, "locked": True,
     "description": "Boundary of intersecting areas"},
    {"layer_id": 3, "name": "Dashed",         "pen_id": 4, "pattern_id": 1,
     "use_pen_color": True, "black": True, "visible": True, "locked": True,
     "description": "Hidden edges and hidden outlines of components"},
    {"layer_id": 4, "name": "Thin dash-dot",  "pen_id": 4, "pattern_id": 2,
     "use_pen_color": True, "black": True, "visible": True, "locked": True,
     "description": "Axes"},
    {"layer_id": 5, "name": "Thick dash-dot", "pen_id": 8, "pattern_id": 2,
     "use_pen_color": True, "black": True, "visible": True, "locked": True,
     "description": "Position of cutting plane"},
    {"layer_id": 6, "name": "Dotted",         "pen_id": 4, "pattern_id": 3,
     "use_pen_color": True, "black": True, "visible": True, "locked": True,
     "description": "Components in front or above the cutting plane"},
]


def _pen_enum_items(self, context):
    if not context:
        return _enum_cache.get('pens', [])
    items = [
        (f"id_{p.pen_id}", f"{p.thickness:.2f} mm", f"Id. {p.pen_id} - {p.thickness:.2f} mm", 'NONE', p.pen_id)
        for p in context.scene.mastro_cad_pens
        if p.enabled
    ]
    _enum_cache['pens'] = items
    return items


def _get_pen_enum(self):
    return self.pen_id


def _set_pen_enum(self, value):
    self.pen_id = value
    ctx = bpy.context
    if self.use_pen_color:
        _sync_pen_color(self, ctx)
    _on_layer_prop_changed(self, ctx)


def _pattern_enum_items(self, context):
    if not context:
        return _enum_cache.get('patterns', [])
    from ...Icons import get_wide_icon_id
    items = [
        (f"id_{p.pattern_id}", p.name, f"Id. {p.pattern_id} - {p.name}", get_wide_icon_id(p), p.pattern_id)
        for p in context.scene.mastro_cad_dash_patterns
    ]
    _enum_cache['patterns'] = items
    return items


def _get_pattern_enum(self):
    return self.pattern_id


def _set_pattern_enum(self, value):
    self.pattern_id = value
    _on_layer_prop_changed(self, bpy.context)


# --- 4-tuple icon enum for template_icon_view (get/set by index) ---

def _pattern_icon_enum_items(self, context):
    global _icon_enum_cache
    if not context:
        return _icon_enum_cache
    from ...Icons import get_wide_icon_id
    items = [
        (f"id_{p.pattern_id}", p.name, "", get_wide_icon_id(p))
        for p in context.scene.mastro_cad_dash_patterns
    ]
    _icon_enum_cache = items
    return items


def _get_pattern_icon_enum(self):
    for i, item in enumerate(_icon_enum_cache):
        if item[0] == f"id_{self.pattern_id}":
            return i
    return 0


def _set_pattern_icon_enum(self, value):
    if 0 <= value < len(_icon_enum_cache):
        self.pattern_id = int(_icon_enum_cache[value][0][3:])  # strip "id_"
        _on_layer_prop_changed(self, bpy.context)


def _on_name_changed(layer, context):
    from ...Utils.mastro_cad.sync_layer_groups import maybe_sync
    maybe_sync(context)


def _on_layer_prop_changed(layer, context):
    from ...Utils.mastro_cad.update_drawing_attributes import update_layer
    update_layer(layer, context)


def _on_color_changed(layer, context):
    """Manual colour edit breaks the pen link."""
    global _syncing
    if _syncing:
        return
    layer.use_pen_color = False
    _on_layer_prop_changed(layer, context)


def _sync_pen_color(layer, context):
    """When use_pen_color is turned on, copy the pen colour into layer.color."""
    if not layer.use_pen_color:
        return
    pen = next((p for p in context.scene.mastro_cad_pens if p.pen_id == layer.pen_id), None)
    if pen:
        global _syncing
        _syncing = True
        layer.color = pen.color
        _syncing = False
    _on_layer_prop_changed(layer, context)


class mastro_CL_cad_layer(PropertyGroup):
    layer_id:      IntProperty(name="Id", default=-1)
    name:          StringProperty(name="Name", default="Layer",
                       description="Layer name",
                       update=_on_name_changed)
    description:   StringProperty(name="Description", default="",
                       description="Layer use description")
    pen_id:        IntProperty(name="Pen Id", default=0,
                       description="Id of the pen used by this layer")
    pattern_id:    IntProperty(name="Line Type Id", default=0,
                       description="Id of the dash pattern used by this layer")
    pen_enum:      EnumProperty(name="Pen", items=_pen_enum_items,
                       get=_get_pen_enum, set=_set_pen_enum)
    pattern_enum:  EnumProperty(name="Line Type", items=_pattern_enum_items,
                       get=_get_pattern_enum, set=_set_pattern_enum)
    pattern_icon_enum: EnumProperty(name="Line Type", items=_pattern_icon_enum_items,
                       get=_get_pattern_icon_enum, set=_set_pattern_icon_enum)
    use_pen_color: BoolProperty(name="Use Pen Colour", default=True,
                       description="When enabled the layer colour follows the pen; disable to override",
                       update=_sync_pen_color)
    color:         FloatVectorProperty(name="Colour", subtype='COLOR', size=4,
                       min=0.0, max=1.0, default=(1.0, 1.0, 1.0, 1.0),
                       description="Layer colour — tracks the pen when Use Pen Colour is on",
                       update=_on_color_changed)
    black:         BoolProperty(name="Print in Black", default=True,
                       description="Force all strokes on this layer to be printed in black",
                       update=_on_layer_prop_changed)
    visible:       BoolProperty(name="Visible", default=True,
                       description="Toggle layer visibility",
                       update=_on_layer_prop_changed)
    locked:        BoolProperty(name="Locked", default=False,
                       description="Default layer — cannot be removed")


def _next_layer_id(layers):
    if not layers:
        return 0
    return max(l.layer_id for l in layers) + 1


def ensure_default_layers(layers):
    if len(layers) > 0:
        return
    for data in DEFAULT_LAYERS:
        l = layers.add()
        l.layer_id      = data["layer_id"]
        l.name          = data["name"]
        l.pen_id        = data["pen_id"]
        l.pattern_id    = data["pattern_id"]
        l.use_pen_color = data["use_pen_color"]
        l.black         = data["black"]
        l.visible       = data["visible"]
        l.locked        = data.get("locked", False)
        l.description   = data.get("description", "")
