from .add_attributes_drawing import add_drawing_attributes
from .drawing_materials import ensure_all_layer_materials
from .update_bmesh_drawing_attributes import update_bmesh_drawing_attributes
from ...Nodes.operators.NODE_OT_MaStro_Drawing_GN import build_drawing_gn


def convert_object_to_mastro_cad(context, obj, layer_id=None):
    """Turn obj into a MaStro CAD drawing object: markers, edge attribute
    layers, the MaStro Drawing Mesh GN modifier, and layer materials.

    Assigns layer_id (or the 3D View sidebar's active layer if None) to
    every edge and pushes its scaled values via update_bmesh_drawing_attributes
    — without this, edges keep the placeholder defaults from
    add_drawing_attributes (e.g. thickness=0.2), which are unscaled and far
    too large compared to a real layer's values.

    Returns the layer_id that was assigned.
    """
    scene = context.scene
    me = obj.data
    me["MaStro object"]       = True
    me["MaStro drawing"]      = True
    me["MaStro drawing mesh"] = True

    add_drawing_attributes(obj)

    scene_layers = scene.mastro_cad_layers
    if layer_id is None:
        # 3D View sidebar's active layer (window_manager), consistent with
        # the extrusion handler — not the Scene Properties panel's index.
        idx = context.window_manager.mastro_cad_viewport_layer_index
        layer_id = (scene_layers[idx].layer_id
                   if scene_layers and 0 <= idx < len(scene_layers) else 0)

    layer_attr = me.attributes.get("mastro_drawing_layer")
    if layer_attr is not None:
        for item in layer_attr.data:
            item.value = layer_id

    if not any(m.type == 'NODES' and m.name == "MaStro Drawing Mesh"
               for m in obj.modifiers):
        layers = [(l.layer_id, l.name) for l in scene_layers]
        mod = obj.modifiers.new("MaStro Drawing Mesh", 'NODES')
        mod.node_group = build_drawing_gn(layers, scene=scene)

    ensure_all_layer_materials(scene)
    update_bmesh_drawing_attributes(context, {layer_id})
    return layer_id
