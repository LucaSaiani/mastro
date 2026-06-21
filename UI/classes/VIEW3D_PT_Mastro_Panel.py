import bpy 
from bpy.types import Panel

class VIEW3D_PT_Mastro_Panel(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MaStro"
    bl_label = "MaStro"
    bl_order = 0
    
    @classmethod
    def poll(cls, context):
        return  (context.object is None or
                #  context.selected_objects == [] or
                    (context.object.type != "MESH" if context.object else True) or
                    ("MaStro object" not in context.object.data if context.object and context.object.type == "MESH" else False)
        )
    
    def draw(self, context):
        pass
