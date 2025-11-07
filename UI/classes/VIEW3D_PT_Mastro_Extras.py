import bpy 
from bpy.types import Panel 


class VIEW3D_PT_Mastro_Extras(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MaStro"
    bl_label = "Extras"
    bl_order = 2
    bl_options = {'DEFAULT_CLOSED'} 
    
    @classmethod
    def poll(cls, context):
        return (context.object is not None and 
                context.object.type == "MESH" and 
                context.object.mode == "EDIT" and
                "MaStro object" in context.object.data)
    
    def draw(self, context):
        obj = context.active_object 
        if obj is not None and obj.type == "MESH":
            mode = obj.mode
            if mode == "EDIT":
                scene = context.scene
                layout = self.layout
                layout.use_property_split = True    
                layout.use_property_decorate = False  # No animation.
                
                ################ Point ######################
                row = layout.row()
                row = layout.row(align=True)    
                
                if tuple(bpy.context.scene.tool_settings.mesh_select_mode)[0] == True: #we are selecting points
                    row.enabled = True
                else:
                    row.enabled = False
                row.prop(context.scene, "mastro_attribute_extra_vertex", text="Vertex") 
                
                ################ Edge ######################
                row = layout.row()
                row = layout.row(align=True)
                
                if tuple(bpy.context.scene.tool_settings.mesh_select_mode)[1] == True: #we are selecting edges
                    row.enabled = True
                else:
                    row.enabled = False
                row.prop(context.scene, "mastro_attribute_extra_edge", text="Edge") 
                
                ################ Face ######################
                row = layout.row()
                row = layout.row(align=True)
                
                if tuple(bpy.context.scene.tool_settings.mesh_select_mode)[2] == True: #we are selecting edges
                    row.enabled = True
                else:
                    row.enabled = False
                row.prop(context.scene, "mastro_attribute_extra_face", text="Face") 