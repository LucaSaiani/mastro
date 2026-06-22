from bpy.types import Operator


class PROPERTIES_OT_Level_List_Remove_Item(Operator):
    """Remove the selected level. The default AOD level (id 0) cannot be removed"""
    bl_idname = "mastro_level_list.remove_item"
    bl_label = "Remove level"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # Disables the "-" button in the UI (rather than just failing in
        # execute) whenever the default AOD level (id 0) is selected.
        scene = context.scene
        collection = scene.mastro_level_list
        index = scene.mastro_level_list_index
        return collection and 0 <= index < len(collection) and collection[index].id != 0

    def execute(self, context):
        scene = context.scene
        collection = scene.mastro_level_list
        index = scene.mastro_level_list_index

        if not collection or index < 0 or index >= len(collection):
            return {'CANCELLED'}

        collection.remove(index)
        scene.mastro_level_list_index = max(0, index - 1)

        for area in context.screen.areas:
            area.tag_redraw()
        return {'FINISHED'}
