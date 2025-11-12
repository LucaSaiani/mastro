import bpy 
from bpy.types import Panel

class PROPERTIES_PT_Mastro_Architecture(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    # bl_category = "MaStro"
    bl_label = "Architecture"
    bl_parent_id = "PROPERTIES_PT_Mastro_Project_Data"
    # bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 2
    
    def draw(self, context):
        pass