import bpy 
from bpy.types import Panel

class VIEW3D_PT_Mastro_Panel(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MaStro"
    bl_label = "MaStro"
    
    @classmethod
    def poll(cls, context):
        return  (context.object is None or
                #  context.selected_objects == [] or
                    (context.object.type != "MESH" if context.object else True) or
                    ("MaStro object" not in context.object.data if context.object and context.object.type == "MESH" else False)
        )
    
    def draw(self, context):
        scene = context.scene
        layout = self.layout
        # layout.operator(MaStro_MenuOperator_add_MaStro_mass.bl_idname)
        layout.operator("object.mastro_convert_to_mastro_mass")
        # layout.operator(OBJECT_OT_Add_Mastro_Street.bl_idname)
        layout.operator("object.mastro_convert_to_mastro_street")