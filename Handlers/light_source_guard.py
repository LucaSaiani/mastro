"""
Watches for deleted light sources and cleans up stale references.

When a light assigned to a camera as shadow caster is removed from the scene,
this handler clears the light_source pointer on the camera.
"""

import bpy
from bpy.app.handlers import persistent

# _CACHE_PREFIX = "_cast_shadows_"  # Silhouette cache — disabled


# def _purge_cast_shadow_cache(light_name, scene):  # Silhouette cache — disabled
#     cache_name = _CACHE_PREFIX + light_name
#     obj = bpy.data.objects.get(cache_name)
#     if obj:
#         me = obj.data
#         bpy.data.objects.remove(obj, do_unlink=True)
#         if me and me.users == 0:
#             bpy.data.meshes.remove(me)


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
        if light is None:
            continue
        if light.name not in scene.objects:
            # _purge_cast_shadow_cache(light.name, scene)  # Silhouette cache — disabled
            props.light_source = None


def register():
    bpy.app.handlers.depsgraph_update_post.append(_check_light_sources)


def unregister():
    if _check_light_sources in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(_check_light_sources)
