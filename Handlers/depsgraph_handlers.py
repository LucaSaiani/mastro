import bpy
from bpy.app.handlers import persistent

from .utils.guard_light_sources import guard_light_sources
from .utils.sync_camera_sets import sync_default_camera_set
from .utils.sync_pdf_frames import sync_pdf_frames


@persistent
def _on_depsgraph_update(scene, depsgraph):
    guard_light_sources(scene)
    sync_default_camera_set(scene)
    sync_pdf_frames(scene)


@persistent
def _on_load_post(filepath):
    scene = bpy.context.scene
    if scene:
        sync_default_camera_set(scene)
        sync_pdf_frames(scene)


def register():
    bpy.app.handlers.depsgraph_update_post.append(_on_depsgraph_update)
    bpy.app.handlers.load_post.append(_on_load_post)


def unregister():
    if _on_depsgraph_update in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(_on_depsgraph_update)
    if _on_load_post in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_on_load_post)
