from bpy.types import Operator
from bpy.props import IntProperty


class PROPERTIES_OT_Level_Set_Toggle_Level(Operator):
    """Add or remove a level from the active level set"""
    bl_idname = "mastro_level_set_list.toggle_level"
    bl_label = "Toggle level in set"
    bl_options = {'REGISTER', 'UNDO'}

    level_id: IntProperty()

    @classmethod
    def poll(cls, context):
        # The "All Levels" set (id 0) always contains every level and
        # cannot be edited; see PROPERTIES_UL_Level_Set_Members.
        scene = context.scene
        collection = scene.mastro_level_set_list
        index = scene.mastro_level_set_list_index
        return collection and 0 <= index < len(collection) and collection[index].id != 0

    def execute(self, context):
        scene = context.scene
        level_set = scene.mastro_level_set_list[scene.mastro_level_set_list_index]

        for i, item in enumerate(level_set.levels):
            if item.level_id == self.level_id:
                level_set.levels.remove(i)
                return {'FINISHED'}

        level_set.levels.add().level_id = self.level_id
        return {'FINISHED'}
