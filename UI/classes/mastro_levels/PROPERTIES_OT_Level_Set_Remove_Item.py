from bpy.types import Operator


class PROPERTIES_OT_Level_Set_Remove_Item(Operator):
    """Remove the selected level set. The default "All Levels" set (id 0) cannot be removed"""
    bl_idname = "mastro_level_set_list.remove_item"
    bl_label = "Remove level set"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # Disables the "-" button in the UI whenever the default
        # "All Levels" set (id 0) is selected.
        scene = context.scene
        collection = scene.mastro_level_set_list
        index = scene.mastro_level_set_list_index
        return collection and 0 <= index < len(collection) and collection[index].id != 0

    def execute(self, context):
        scene = context.scene
        collection = scene.mastro_level_set_list
        index = scene.mastro_level_set_list_index

        if not collection or index < 0 or index >= len(collection):
            return {'CANCELLED'}

        collection.remove(index)
        scene.mastro_level_set_list_index = max(0, index - 1)

        for area in context.screen.areas:
            area.tag_redraw()
        return {'FINISHED'}
