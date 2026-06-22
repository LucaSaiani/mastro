import bpy

GN_GROUP_NAME = "MaStro Drawing"
SCALE_NODE_LABEL = "Scale"


def sync_drawing_scale(scale):
    """Set the integer value of the Scale node inside the MaStro Drawing node group."""
    ng = bpy.data.node_groups.get(GN_GROUP_NAME)
    if ng is None:
        return
    for node in ng.nodes:
        if node.bl_idname == 'FunctionNodeInputInt' and node.label == SCALE_NODE_LABEL:
            node.integer = int(scale)
            break


# Camera-scoped "Scale 1:" disabled — kept commented instead of removed
# in case it's wanted back.
# def sync_drawing_scale_from_camera(scene):
#     """Mirror the active camera's mastro_cad_drawing_scale to scene.mastro_cad_drawing_scale."""
#     cam = scene.camera
#     if cam is None or cam.type != 'CAMERA':
#         return
#     scale = cam.data.get("mastro_cad_drawing_scale", 100)
#     if scene.mastro_cad_drawing_scale != scale:
#         scene.mastro_cad_drawing_scale = scale
