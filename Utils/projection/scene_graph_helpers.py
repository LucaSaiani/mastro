import bpy

# =============================================================================
#  Scene-graph helpers
# =============================================================================

PROJECTION_COLLECTION = "2D Projection and Shadows"


def get_projection_collection(scene):
    """Return (creating if needed) the dedicated output collection."""
    col = bpy.data.collections.get(PROJECTION_COLLECTION)
    if col is None:
        col = bpy.data.collections.new(PROJECTION_COLLECTION)
        scene.collection.children.link(col)
    elif PROJECTION_COLLECTION not in scene.collection.children:
        scene.collection.children.link(col)
    return col


def link_to_projection_collection(obj, scene):
    """Link obj to the projection collection (unlink from scene root if needed)."""
    col = get_projection_collection(scene)
    if obj.name not in col.objects:
        col.objects.link(obj)
    if obj.name in scene.collection.objects:
        scene.collection.objects.unlink(obj)

def _delete_hierarchy(obj):
    for child in list(obj.children):
        _delete_hierarchy(child)
    if obj.data is not None:
        bpy.data.meshes.remove(obj.data, do_unlink=True)
    else:
        bpy.data.objects.remove(obj, do_unlink=True)


_PROJECTOR_EMPTY_TAG   = "projector_empty"
_PROJECTOR_OUTPUTS_KEY = "projector_outputs"


def register_projection_output(empty, obj_name):
    """Record obj_name as a projector-generated output on the empty."""
    if empty is None:
        return
    existing = list(empty.get(_PROJECTOR_OUTPUTS_KEY, []))
    if obj_name not in existing:
        existing.append(obj_name)
    empty[_PROJECTOR_OUTPUTS_KEY] = existing


def clear_projection_outputs(empty):
    """Clear the output registry at the start of a new run."""
    if empty is not None:
        empty[_PROJECTOR_OUTPUTS_KEY] = []


def delete_projection_outputs(empty):
    """Delete all registered projection output objects and clear the registry."""
    if empty is None:
        return
    known = list(empty.get(_PROJECTOR_OUTPUTS_KEY, []))
    for name in known:
        obj = bpy.data.objects.get(name)
        if obj is not None and obj.parent == empty:
            me = obj.data if obj.type == 'MESH' else None
            bpy.data.objects.remove(obj, do_unlink=True)
            if me and me.users == 0:
                bpy.data.meshes.remove(me)
    empty[_PROJECTOR_OUTPUTS_KEY] = []


def _get_or_create_empty(name, scene, parent=None):
    """
    Return a new empty object with the given name.
    If an object with that name already exists it is deleted first.
    """
    if name in bpy.data.objects:
        _delete_hierarchy(bpy.data.objects[name])
    empty = bpy.data.objects.new(name, None)
    empty.empty_display_type = 'PLAIN_AXES'
    empty[_PROJECTOR_EMPTY_TAG] = True
    link_to_projection_collection(empty, scene)
    if parent is not None:
        empty.parent = parent
    return empty


def _detach_user_edits(empty, projection_suffix=None):
    """
    Detach and return children of empty that are NOT projector-generated outputs.
    Uses the explicit output registry stored on the empty.  Children whose names
    are not in that registry are treated as user edits and detached so they
    survive the empty recreation.
    """
    known_outputs = set(empty.get(_PROJECTOR_OUTPUTS_KEY, []))
    survivors = []
    for child in list(empty.children):
        if child.name not in known_outputs:
            child.parent = None
            survivors.append(child)
    return survivors


def _get_or_create_empty_keep(name, scene, parent=None):
    """
    Return the existing empty with the given name, or create a new one.
    Used in incremental mode to preserve previously projected wire meshes.
    """
    if name in bpy.data.objects:
        existing = bpy.data.objects[name]
        existing[_PROJECTOR_EMPTY_TAG] = True
        return existing
    empty = bpy.data.objects.new(name, None)
    empty.empty_display_type = 'PLAIN_AXES'
    empty[_PROJECTOR_EMPTY_TAG] = True
    link_to_projection_collection(empty, scene)
    if parent is not None:
        empty.parent = parent
    return empty