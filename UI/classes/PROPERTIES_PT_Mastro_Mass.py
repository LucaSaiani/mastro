import bpy 
from bpy.types import Panel

class PROPERTIES_PT_Mastro_Mass(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    # bl_category = "MaStro"
    bl_label = ""
    bl_parent_id = "PROPERTIES_PT_Mastro_Project_Data"
    # bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 1

    
    # @classmethod
    # def poll(cls, context):
    #     return (context.object is not None)
    
    def draw_header(self, context):
        layout = self.layout
        # split = layout.split(factor=.9)
        row = layout.row()
        row.label(text="Mass")
        # row.prop(context.window_manager, "mastro_toggle_auto_update_mass_data", text="", icon="FILE_REFRESH")
        
        
    def draw(self, context):
        pass