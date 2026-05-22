"""
Watches for deleted light sources and cleans up stale references.

When a light assigned to a camera as shadow caster is removed from the scene,
this handler clears the light_source pointer on the camera.
"""

import bpy
from bpy.app.handlers import persistent


@persistent
def _check_light_sources(scene, depsgraph):
    for cam_obj in scene.objects:
        if cam_obj.type != 'CAMERA':
            continue
        try:
            props = cam_obj.data.mastro_projector_cl
        except AttributeError:
            continue
        light = props.light_source
        if light is not None and light.name not in scene.objects:
            props.light_source = None

    _sync_default_camera_set(scene)


def _sync_default_camera_set(scene):
    """Keep Set 0 ('All') in sync with all enabled cameras."""
    ssp = scene.mastro_projector_props

    # Ensure Set 0 exists
    if not ssp.camera_sets or not ssp.camera_sets[0].is_default:
        s = ssp.camera_sets.add()
        s.name = "All"
        s.is_default = True
        ssp.camera_sets.move(len(ssp.camera_sets) - 1, 0)

    default_set = ssp.camera_sets[0]
    enabled = {
        obj.name for obj in scene.objects
        if obj.type == 'CAMERA'
        and obj.data is not None
        and obj.data.mastro_projector_cl.enabled
    }
    existing = {item.camera_name for item in default_set.cameras}

    if enabled == existing:
        return  # nothing to do — avoid unnecessary writes

    for name in enabled - existing:
        default_set.cameras.add().camera_name = name
    to_remove = [i for i, item in enumerate(default_set.cameras)
                 if item.camera_name not in enabled]
    for i in reversed(to_remove):
        default_set.cameras.remove(i)


def register():
    bpy.app.handlers.depsgraph_update_post.append(_check_light_sources)
    bpy.app.handlers.load_post.append(_on_load_post)


def unregister():
    if _check_light_sources in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(_check_light_sources)
    if _on_load_post in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_on_load_post)


@persistent
def _on_load_post(filepath):
    scene = bpy.context.scene
    if scene:
        _sync_default_camera_set(scene)
