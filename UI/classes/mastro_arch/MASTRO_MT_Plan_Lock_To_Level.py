from bpy.types import Menu


class MASTRO_MT_Plan_Lock_To_Level(Menu):
    """Dropdown listing every project level, to lock the active plan to a
    level other than whichever is currently active in the Clip Range."""
    bl_label = "Lock to Level"

    def draw(self, context):
        layout = self.layout
        for lvl in context.scene.mastro_level_list:
            layout.operator("object.mastro_plan_lock_to_level",
                             text=lvl.name).level_id = lvl.id
