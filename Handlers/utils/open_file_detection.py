import atexit
import bpy
import json
import os
import socket
import sys
import datetime

from bpy.app.handlers import persistent


def _prefs():
    from ... import PREFS_KEY
    return bpy.context.preferences.addons.get(PREFS_KEY)


def _detection_enabled():
    p = _prefs()
    return p and p.preferences.open_file_detection


_STALE_TIMEOUT_MINUTES = 5
_REFRESH_INTERVAL_SECONDS = 120


def _marker_path(blend_path):
    directory = os.path.dirname(blend_path)
    stem = os.path.basename(blend_path)
    if stem.endswith(".blend"):
        stem = stem[:-6]
    # Not a ".blend" file, so it isn't picked up by file browsers/import
    # dialogs or accidentally treated as project data.
    return os.path.join(directory, f"~${stem}.in_use.lock")


def _write_marker(blend_path):
    data = {
        "user":            os.environ.get("USER") or os.environ.get("USERNAME") or "unknown",
        "hostname":        socket.gethostname(),
        "pid":             os.getpid(),
        "timestamp":       datetime.datetime.now().isoformat(),
        "blender_version": bpy.app.version_string,
    }
    try:
        with open(_marker_path(blend_path), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except OSError:
        pass


def _read_marker(blend_path):
    path = _marker_path(blend_path)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def _pid_is_alive(pid):
    if sys.platform == "win32":
        # os.kill(pid, 0) doesn't reliably signal "no such process" on
        # Windows; use OpenProcess instead.
        import ctypes
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        handle = ctypes.windll.kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except OSError:
        # Permission denied etc. still means the PID exists.
        return True


def _marker_is_stale(data):
    try:
        ts = datetime.datetime.fromisoformat(data["timestamp"])
        age = datetime.datetime.now() - ts
        if age.total_seconds() > _STALE_TIMEOUT_MINUTES * 60:
            return True
    except (KeyError, ValueError):
        return True

    # Same machine but the process that wrote the marker is gone
    # (e.g. Blender closed without running the atexit cleanup) ->
    # the marker is left over, not an active session.
    if data.get("hostname") == socket.gethostname():
        pid = data.get("pid")
        if not isinstance(pid, int) or not _pid_is_alive(pid):
            return True

    return False


def _remove_marker(blend_path):
    path = _marker_path(blend_path)
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


def _is_our_marker(blend_path):
    data = _read_marker(blend_path)
    if data is None:
        return False
    return (
        data.get("hostname") == socket.gethostname()
        and data.get("pid") == os.getpid()
    )


def check_and_mark(blend_path):
    """Check for an existing marker and write ours if possible.

    Returns:
        "ok"      — no marker found, file is free
        "stale"   — stale marker found and overwritten
        dict      — active marker by another user
    """
    if not blend_path:
        return "ok"

    data = _read_marker(blend_path)

    if data is None:
        _write_marker(blend_path)
        return "ok"

    # Check ownership before staleness: our own marker may have gone stale
    # (e.g. the refresh timer didn't run for a while), but that's not a
    # "left open after a crash by someone else" situation.
    if (data.get("hostname") == socket.gethostname()
            and data.get("pid") == os.getpid()):
        _write_marker(blend_path)
        return "ok"

    if _marker_is_stale(data):
        _write_marker(blend_path)
        return "stale"

    return data


# ── Timer: refresh our marker timestamp every 2 minutes ───────────────────────

def _refresh_marker():
    if not _detection_enabled():
        return _REFRESH_INTERVAL_SECONDS
    blend_path = bpy.data.filepath
    if blend_path and _is_our_marker(blend_path):
        _write_marker(blend_path)
    return _REFRESH_INTERVAL_SECONDS


# ── Handlers ──────────────────────────────────────────────────────────────────

@persistent
def on_load_post(filepath):
    if not _detection_enabled():
        return
    blend_path = bpy.data.filepath
    if not blend_path:
        return

    result = check_and_mark(blend_path)

    if result == "ok":
        return

    if result == "stale":
        def _warn():
            bpy.ops.mastro.open_file_warning('INVOKE_DEFAULT',
                                              message="This file may have been left open after a crash. The previous session marker has been cleared.",
                                              other_user=False)
        bpy.app.timers.register(_warn, first_interval=0.1)
        return

    user     = result.get("user", "unknown")
    hostname = result.get("hostname", "unknown")
    ts       = result.get("timestamp", "")
    message  = (
        f"{user} on {hostname} has had this file open since "
        f"{ts[:16].replace('T', ' ')}. "
        f"Working on it at the same time may lead to one user overwriting the other's work."
    )

    def _warn():
        bpy.ops.mastro.open_file_warning('INVOKE_DEFAULT',
                                          message=message,
                                          other_user=True)
    bpy.app.timers.register(_warn, first_interval=0.1)


def _cleanup_marker_on_exit():
    if not _detection_enabled():
        return
    blend_path = bpy.data.filepath
    if blend_path and _is_our_marker(blend_path):
        _remove_marker(blend_path)


@persistent
def on_load_pre(filepath):
    if not _detection_enabled():
        return
    blend_path = bpy.data.filepath
    if blend_path and _is_our_marker(blend_path):
        _remove_marker(blend_path)


@persistent
def on_save_post(filepath):
    if not _detection_enabled():
        return
    blend_path = bpy.data.filepath
    if not blend_path:
        return

    data = _read_marker(blend_path)
    if (data is not None
            and not _marker_is_stale(data)
            and not (data.get("hostname") == socket.gethostname() and data.get("pid") == os.getpid())):
        user = data.get("user", "unknown")
        hostname = data.get("hostname", "unknown")
        message = (
            f"{user} on {hostname} also has this file open. "
            f"Saving has claimed the open-file marker; if they save too, "
            f"one of you may overwrite the other's work."
        )

        def _warn():
            bpy.ops.mastro.open_file_warning('INVOKE_DEFAULT',
                                              message=message,
                                              other_user=True)
        bpy.app.timers.register(_warn, first_interval=0.1)

    _write_marker(blend_path)


# ── Dialog operator ───────────────────────────────────────────────────────────

class MASTRO_OT_open_file_warning(bpy.types.Operator):
    bl_idname  = "mastro.open_file_warning"
    bl_label   = "Open File Detection"
    bl_options = {'INTERNAL'}

    message:    bpy.props.StringProperty()
    other_user: bpy.props.BoolProperty(default=False)

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self, width=460)

    def draw(self, context):
        col = self.layout.column(align=True)
        for sentence in self.message.split(". "):
            sentence = sentence.strip()
            if sentence:
                col.label(text=sentence if sentence.endswith(".") else sentence + ".",
                          icon='ERROR' if self.other_user else 'INFO')
        col.separator()
        col.operator("mastro.open_file_warning_confirm", text="I understand")

    def execute(self, context):
        blend_path = bpy.data.filepath
        if blend_path:
            _write_marker(blend_path)
        return {'FINISHED'}


class MASTRO_OT_open_file_warning_confirm(bpy.types.Operator):
    bl_idname  = "mastro.open_file_warning_confirm"
    bl_label   = "I understand"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        blend_path = bpy.data.filepath
        if blend_path:
            _write_marker(blend_path)
        return {'FINISHED'}


# ── Register / Unregister ─────────────────────────────────────────────────────

classes = (MASTRO_OT_open_file_warning, MASTRO_OT_open_file_warning_confirm)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.app.handlers.load_post.append(on_load_post)
    bpy.app.handlers.load_pre.append(on_load_pre)
    bpy.app.handlers.save_post.append(on_save_post)
    if not bpy.app.timers.is_registered(_refresh_marker):
        bpy.app.timers.register(_refresh_marker, first_interval=_REFRESH_INTERVAL_SECONDS, persistent=True)
    atexit.register(_cleanup_marker_on_exit)


def unregister():
    atexit.unregister(_cleanup_marker_on_exit)
    if bpy.app.timers.is_registered(_refresh_marker):
        bpy.app.timers.unregister(_refresh_marker)
    if on_save_post in bpy.app.handlers.save_post:
        bpy.app.handlers.save_post.remove(on_save_post)
    if on_load_pre in bpy.app.handlers.load_pre:
        bpy.app.handlers.load_pre.remove(on_load_pre)
    if on_load_post in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(on_load_post)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
