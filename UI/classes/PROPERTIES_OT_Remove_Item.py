import bpy
from bpy.types import Operator


class PROPERTIES_OT_Remove_Item(Operator):
    """Generic operator to remove the selected item from a list."""
    bl_idname = "properties.remove_item"
    bl_label  = "Remove Item"
    bl_options = {'REGISTER', 'UNDO'}

    list_name:  str
    index_name: str

    def execute(self, context):
        scene      = context.scene
        collection = getattr(scene, self.list_name)
        index      = getattr(scene, self.index_name)

        if not collection or index < 0 or index >= len(collection):
            return {'CANCELLED'}

        collection.remove(index)
        setattr(scene, self.index_name, max(0, index - 1))

        for area in context.screen.areas:
            area.tag_redraw()
        return {'FINISHED'}
