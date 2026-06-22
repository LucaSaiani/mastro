import bpy
from bpy.types import Operator
from bpy.props import StringProperty

from .sync_children_display import sync_children_display


class OBJECT_OT_Mastro_Album_Remove_Child(Operator):
    """Remove a single child listed under a MaStro album, from its row in
    the UIList. Deletes the linked-data copy, same as Unparent from Album."""
    bl_idname = "object.mastro_album_remove_child"
    bl_label = "Remove from Album"
    bl_options = {'REGISTER', 'UNDO'}

    object_name: StringProperty()

    def execute(self, context):
        child = bpy.data.objects.get(self.object_name)
        if child is None or child.parent is None:
            return {'CANCELLED'}

        album = child.parent
        # Clear children_display before removing the object — its
        # PointerProperty holds a strong reference, so removing the
        # object first leaves a zombie datablock do_unlink can't release.
        album.mastro_album_settings.children_display.clear()
        bpy.data.objects.remove(child, do_unlink=True)
        sync_children_display(album)

        return {'FINISHED'}
