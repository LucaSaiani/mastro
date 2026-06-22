from bpy.types import Menu


class MASTRO_MT_Level_List_Specials(Menu):
    bl_label = "Level List Specials"

    def draw(self, context):
        layout = self.layout
        layout.operator("mastro_level_list.batch_add", icon='ADD', text="Add Levels...")
