import os

import bpy

from ..mastro_preferences.get_preferences import get_prefs


def _check_all_scenes():
    """Compare each LOADED entry's stored mtime against the source file's
    current mtime, flagging entries whose source changed since link/reload.
    Read-only: never touches the linked data itself, only the registry."""
    for scene in bpy.data.scenes:
        props = getattr(scene, "mastro_linked_collections_props", None)
        if props is None:
            continue
        for entry in props.entries:
            if entry.status != 'LOADED' or not entry.filepath:
                continue
            abs_path = bpy.path.abspath(entry.filepath)
            if not os.path.isfile(abs_path):
                continue
            current_mtime = os.path.getmtime(abs_path)
            if current_mtime > float(entry.source_mtime):
                entry.source_changed = True


def _tick():
    _check_all_scenes()
    try:
        prefs = get_prefs()
    except KeyError:
        return None  # addon not registered under its expected key, stop the timer
    if not prefs.linked_collections_check_for_updates:
        return None  # stop the timer
    return prefs.linked_collections_check_interval


def start_polling():
    if not bpy.app.timers.is_registered(_tick):
        bpy.app.timers.register(_tick, first_interval=1.0, persistent=True)


def stop_polling():
    if bpy.app.timers.is_registered(_tick):
        bpy.app.timers.unregister(_tick)
