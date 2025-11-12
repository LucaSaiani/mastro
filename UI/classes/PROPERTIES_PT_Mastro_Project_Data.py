import bpy 
from bpy.types import Panel 

class PROPERTIES_PT_Mastro_Project_Data(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    # bl_category = "MaStro"
    bl_label = "MaStro"
    bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
       