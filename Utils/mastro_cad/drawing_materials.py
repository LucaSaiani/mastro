import bpy

BLACK_MAT_NAME = "Mastro_GP_Black"


def ensure_black_material():
    """Create (once) the solid-black GP material used by the black-mode switch."""
    mat = bpy.data.materials.get(BLACK_MAT_NAME)
    if mat is None:
        mat = bpy.data.materials.new(BLACK_MAT_NAME)
        bpy.data.materials.create_gpencil_data(mat)

    gp = mat.grease_pencil
    gp.show_stroke = True
    gp.show_fill   = False
    gp.color       = (0.0, 0.0, 0.0, 1.0)
    return mat


def ensure_layer_material(scene, layer_id):
    """Create or update the GP material Mastro_GP_{layer_id} with the layer's color."""
    name = f"Mastro_GP_{layer_id}"
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        bpy.data.materials.create_gpencil_data(mat)

    layer = next((l for l in scene.mastro_cad_layers if l.layer_id == layer_id), None)
    if layer is None:
        return mat

    gp = mat.grease_pencil
    gp.show_stroke = True
    gp.show_fill   = False
    gp.color       = tuple(layer.color)
    return mat


def ensure_all_layer_materials(scene):
    """Create/update GP materials for all layers in the scene."""
    ensure_black_material()
    for layer in scene.mastro_cad_layers:
        ensure_layer_material(scene, layer.layer_id)
