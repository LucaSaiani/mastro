import bpy
from bpy.types import Operator

from .sync_children_display import sync_children_display


class OBJECT_OT_Parent_to_Mastro_Album(Operator):
    """Create a linked-data copy of each selected object and parent it to
    the active MaStro album, leaving the originals untouched in place.

    The new object's origin sits at the album's origin (no inverse), so
    it immediately picks up the album's current scale — no need to touch
    the album's Scale property again before a newly parented copy reacts
    to it."""
    bl_idname = "object.mastro_parent_to_album"
    bl_label = "Add to MaStro Album"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        album = context.object
        return (album is not None and album.get("MaStro album")
                and len(context.selected_objects) > 1)

    def execute(self, context):
        album = context.object
        sources = [obj for obj in context.selected_objects if obj is not album]

        for source in sources:
            child = bpy.data.objects.new(source.name, source.data)
            child.parent = album
            child.matrix_parent_inverse.identity()
            for collection in source.users_collection:
                collection.objects.link(child)

        sync_children_display(album)
        return {'FINISHED'}
