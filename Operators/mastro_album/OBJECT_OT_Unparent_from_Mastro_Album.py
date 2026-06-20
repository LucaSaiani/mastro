import bpy
from bpy.types import Operator


class OBJECT_OT_Unparent_from_Mastro_Album(Operator):
    """Unparent the selected objects from their MaStro album, resetting
    their scale back to 1 — the album's scale is the only deformation a
    child picks up, so removing the parent should also remove it."""
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

        for child in children:
            child.select_set(True)
        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

        for child in children:
            child.scale = (1.0, 1.0, 1.0)

        return {'FINISHED'}
