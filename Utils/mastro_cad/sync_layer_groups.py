from .add_attributes_drawing import add_drawing_attributes
from .update_bmesh_drawing_attributes import update_all_bmesh_drawing_attributes
from .drawing_materials import ensure_all_layer_materials
from ...Nodes.operators.NODE_OT_MaStro_Drawing_GN import rebuild_drawing_gn


def sync_layer_groups(context):
    """Ensure every MaStro drawing mesh has all drawing edge attributes,
    push current layer values, then rebuild the GN node group."""
    scene = context.scene
    for obj in scene.objects:
        if obj.type != 'MESH':
            continue
        if not obj.data.get("MaStro drawing mesh"):
            continue
        add_drawing_attributes(obj)

    update_all_bmesh_drawing_attributes(context)
    ensure_all_layer_materials(scene)
    rebuild_drawing_gn(scene)


def maybe_sync(context):
    if context.window_manager.mastro_cad_auto_update_layers:
        sync_layer_groups(context)
