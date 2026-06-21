import bpy

from ..Operators.mastro_album.sync_children_display import sync_children_display

_owner = object()


def _sync_active_album():
    """Deferred to a timer — bpy.context inside a msgbus callback is not
    guaranteed to be fully valid, so we just flag a pending sync here and
    do the actual work on the next main-loop tick."""
    view_layer = bpy.context.view_layer
    obj = view_layer.objects.active if view_layer else None
    if obj is not None and obj.get("MaStro album"):
        sync_children_display(obj)
    return None  # one-shot


def _on_active_object_changed():
    bpy.app.timers.register(_sync_active_album, first_interval=0.0)


def register():
    bpy.msgbus.subscribe_rna(
        key=(bpy.types.LayerObjects, "active"),
        owner=_owner,
        args=(),
        notify=_on_active_object_changed,
    )


def unregister():
    bpy.msgbus.clear_by_owner(_owner)
