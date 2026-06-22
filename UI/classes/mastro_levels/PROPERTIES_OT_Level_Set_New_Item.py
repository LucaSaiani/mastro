from bpy.types import Operator


class PROPERTIES_OT_Level_Set_New_Item(Operator):
    """Add a new, empty level set"""
    bl_idname = "mastro_level_set_list.new_item"
    bl_label = "Add level set"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        collection = scene.mastro_level_set_list

        item = collection.add()
        ids = [el.id for el in collection]
        item.id = max(ids) + 1 if ids else 1
        item.name = "Level Set"

        scene.mastro_level_set_list_index = len(collection) - 1

        for area in context.screen.areas:
            area.tag_redraw()
        return {'FINISHED'}
