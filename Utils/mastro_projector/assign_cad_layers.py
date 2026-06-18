from .category_map import (VG_VISIBLE, VG_SILHOUETTE, VG_HIDDEN,
                            VG_SILHOUETTE_HIDDEN, VG_SECTION, _CATEGORY_MAP)
from ..mastro_cad.update_bmesh_drawing_attributes import update_bmesh_drawing_attributes

# Fixed layer_id values from DEFAULT_LAYERS (UI/properties/property_classes_cad.py).
# These three default layers are "locked" (can't be deleted from the UI), so
# referencing them by id here is safe — they're always present in the scene.
_LAYER_ID_THIN   = 0   # "Thin"   — ISO continuous thin line
_LAYER_ID_THICK  = 2   # "Thick"  — ISO continuous thick line
_LAYER_ID_DASHED = 3   # "Dashed" — ISO dashed line

# Drawing convention (ISO 128): visible/silhouette edges are drawn thin and
# continuous, hidden edges are dashed, and section cut boundaries are thick.
_GROUP_LAYER = {
    VG_VISIBLE:           _LAYER_ID_THIN,
    VG_SILHOUETTE:        _LAYER_ID_THIN,
    VG_HIDDEN:            _LAYER_ID_DASHED,
    VG_SILHOUETTE_HIDDEN: _LAYER_ID_DASHED,
    VG_SECTION:           _LAYER_ID_THICK,
}


def assign_cad_layers_from_categories(context, obj, category_edge_indices):
    """Assign MaStro CAD layers to obj's edges based on their exact
    per-edge projection category (visible/silhouette -> Thin, hidden/hidden
    silhouette -> Dashed, section -> Thick).

    category_edge_indices: dict { bm_key: set of mesh edge index }, as
    returned by _write_merged_object. This is resolved from the exact
    (BMVert, BMVert) pairs recorded per category during the merge — NOT by
    checking which vertex groups both of an edge's endpoints belong to.
    That vertex-group approach is unreliable here: vertices are shared
    across categories wherever they're spatially coincident (e.g. a hidden
    edge's endpoint can sit exactly on top of an unrelated visible edge's
    endpoint), so "both endpoints are in group X" can match an edge that
    does not actually belong to X. Vertex groups themselves are left
    untouched by this function — they're still created for other uses.

    obj must already be a MaStro CAD drawing object (see
    convert_object_to_mastro_cad) so it has the mastro_drawing_layer
    attribute; this only overrides that attribute's per-edge values.
    """
    mesh = obj.data
    layer_attr = mesh.attributes.get("mastro_drawing_layer")
    if layer_attr is None:
        return

    touched_layers = set()
    for bm_key, group_name in _CATEGORY_MAP:
        layer_id = _GROUP_LAYER.get(group_name)
        indices = category_edge_indices.get(bm_key)
        if layer_id is None or not indices:
            continue
        for i in indices:
            layer_attr.data[i].value = layer_id
        touched_layers.add(layer_id)

    # Push the layer's real (scaled) thickness/dash-pattern values onto the
    # edges we just touched — without this they'd keep add_drawing_attributes'
    # placeholder defaults, which are unscaled and far too large.
    if touched_layers:
        update_bmesh_drawing_attributes(context, touched_layers)
