import bpy
from bpy.types import Operator

from .sync_children_display import sync_children_display


class OBJECT_OT_Unparent_from_Mastro_Album(Operator):
    """Remove the selected objects' linked-data copies from their MaStro
    album. These copies only exist as the album's rendering of the
    original object, which was never touched — so detaching means
    deleting the copy, not unparenting it."""
    bl_idname = "object.mastro_unparent_from_album"
    bl_label = "Unparent from MaStro Album"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return any(obj.parent and obj.parent.get("MaStro album")
                   for obj in context.selected_objects)

    def execute(self, context):
        children = [obj for obj in context.selected_objects
                    if obj.parent and obj.parent.get("MaStro album")]
        albums = {child.parent for child in children}

        # Clear children_display's PointerProperty references first — it
        # holds a strong reference to each object, so removing the object
        # before clearing this leaves a zombie datablock that do_unlink
        # can't fully release (gone from the scene, but not from bpy.data,
        # and still reporting its old obj.parent).
        for album in albums:
            album.mastro_album_settings.children_display.clear()

        for child in children:
            bpy.data.objects.remove(child, do_unlink=True)

        for album in albums:
            sync_children_display(album)

        return {'FINISHED'}
