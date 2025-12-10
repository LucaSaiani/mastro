import bpy 
from bpy.types import Panel 

"""View 3D panel to show the export operators"""
class VIEW3D_PT_Mastro_Export(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MaStro"
    bl_label = "Export"
    bl_order = 100
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if obj is not None and obj.type == "MESH":
            mode = obj.mode
            if mode != "OBJECT":
                return False
        return True
        
    def draw(self, context):
        layout = self.layout
        layout.operator("object.mastro_export_csv")
        layout.operator("object.mastro_print_data")