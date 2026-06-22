import bpy
from bpy.types import Operator

from .sync_children_display import sync_children_display


class OBJECT_OT_Parent_to_Mastro_Album(Operator):
    """Create a linked-data copy of each selected object and parent it to
    the active MaStro album, leaving the originals untouched in place.

    The copy's position relative to the album mirrors the source's
    position relative to the world origin — i.e. parenting with the
    inverse Blender would compute for a normal Ctrl+P (Object), as if the
    album's origin were the 3D cursor and its scale were applied from
    there. Any later change to the album's scale re-applies proportionally
    from the album's origin, exactly like scaling around the cursor."""
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
            child.matrix_world = source.matrix_world
            for collection in source.users_collection:
                collection.objects.link(child)

            for mod in source.modifiers:
                if mod.type == 'NODES':
                    new_mod = child.modifiers.new(mod.name, 'NODES')
                    new_mod.node_group = mod.node_group

            child.parent = album
            child.matrix_parent_inverse = album.matrix_world.inverted()

        sync_children_display(album)
        return {'FINISHED'}
