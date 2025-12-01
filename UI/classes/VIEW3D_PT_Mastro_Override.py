import bpy 
from bpy.types import Panel 

"""Overrides for the mass"""
class VIEW3D_PT_Mastro_Mass_Override(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MaStro"
    bl_label = "Override"
    bl_parent_id = "VIEW3D_PT_Mastro_Mass"
    bl_order = 0
    bl_options = {'DEFAULT_CLOSED'} 
    
    @classmethod
    def poll(cls, context):
        if not commonPoll(context):
            return False
        if "MaStro mass" not in context.object.data:
            return False
        return True
    
    def draw(self, context):
        drawingUI(self.layout, context)
        
"""Overrides for the block"""
class VIEW3D_PT_Mastro_Block_Override(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MaStro"
    bl_label = "Override"
    bl_parent_id = "VIEW3D_PT_Mastro_Block"
    bl_order = 0        
    bl_options = {'DEFAULT_CLOSED'} 
    
    @classmethod
    def poll(cls, context):
        if not commonPoll(context):
            return False
        if "MaStro block" not in context.object.data:
            return False
        return True
    
    def draw(self, context):
        drawingUI(self.layout, context)
                
def commonPoll(context):
    if context.object is None:
        return False
    if context.object.type != "MESH":
        return False
    if context.object.mode != "EDIT":
        return False
    if "MaStro object" not in context.object.data:
        return False
    return True
    
def drawingUI(layout, context):
    # obj = context.active_object 
        obj = context.object
        mode = obj.mode
        
        scene = context.scene
                
        layout.use_property_split = True    
        layout.use_property_decorate = False  # No animation.
        
        if mode == "EDIT":
            layout.enabled = True
        else:
            layout.enabled = False
            
        row = layout.row(align=True)
        row.prop(context.scene, "mastro_attribute_mass_extend_uses", text="Top Floors") 
        
        row = layout.row(align=True)
        row.prop(context.scene, "mastro_attribute_mass_undercroft", text="Undercroft") 
                