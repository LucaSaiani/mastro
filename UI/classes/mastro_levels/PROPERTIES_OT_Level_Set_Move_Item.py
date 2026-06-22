from bpy.types import Operator
from bpy.props import EnumProperty


class PROPERTIES_OT_Level_Set_Move_Item(Operator):
    """Move the selected level set up or down in the list"""
    bl_idname = "mastro_level_set_list.move_item"
    bl_label = "Move level set"
    bl_options = {'REGISTER', 'UNDO'}

    direction: EnumProperty(items=(('UP', "Up", ""), ('DOWN', "Down", "")))

    def execute(self, context):
        scene = context.scene
        collection = scene.mastro_level_set_list
        index = scene.mastro_level_set_list_index

        neighbor = index + (-1 if self.direction == 'UP' else 1)
        if 0 <= neighbor < len(collection):
            collection.move(index, neighbor)
            scene.mastro_level_set_list_index = neighbor

        for area in context.screen.areas:
            area.tag_redraw()
        return {'FINISHED'}
