from bpy.types import Panel


class MASTRO_PT_Schedule_Tools(Panel):
    """Sidebar panel for the MaStro Schedule node editor, hosting tree-wide
    actions (e.g. force refresh) that don't belong to a specific node"""
    bl_idname = "MASTRO_PT_schedule_tools"
    bl_label = "MaStro Schedule"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "MaStro"

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.tree_type == 'MaStroScheduleTreeType' and space.edit_tree is not None

    def draw(self, context):
        self.layout.operator("mastro_schedule.force_refresh", icon='FILE_REFRESH')
