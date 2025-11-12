import bpy 
from bpy.types import Panel

class VIEW3D_PT_Mastro_Street(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MaStro"
    bl_label = "Street"
    bl_order = 0
    
    @classmethod
    def poll(cls, context):
        return (context.object is not None and
                # context.selected_objects != [] and 
                context.object.type == "MESH" and 
                "MaStro object" in context.object.data and
                "MaStro street" in context.object.data)
    
    def draw(self, context):
        obj = context.object
        if obj is not None and obj.type == "MESH":
            mode = obj.mode
            if mode == "OBJECT":
                scene = context.scene
                
                layout = self.layout
                layout.use_property_split = True    
                layout.use_property_decorate = False  # No animation.
                
                # row = layout.row()
                row = layout.row(align=True)
                
                # layout.prop(obj.mastro_props, "mastro_option_attribute", text="Option")
                # layout.prop(obj.mastro_props, "mastro_phase_attribute", text="Phase")
                    
            elif mode == "EDIT":
                scene = context.scene
                
                layout = self.layout
                layout.use_property_split = True    
                layout.use_property_decorate = False  # No animation.
                
                if tuple(bpy.context.scene.tool_settings.mesh_select_mode)[1] == True: #we are selecting edges
                    layout.enabled = True
                else:
                    layout.enabled = False
                
                row = layout.row(align=True)

                row.prop(context.scene, "mastro_street_names", icon="NODE_TEXTURE", icon_only=True, text="Street Type")
                if len(scene.mastro_street_name_list) >0:
                    row.label(text = scene.mastro_street_name_current[0].name)
                    # streetId = scene.mastro_street_name_current[0].id
                else:
                    row.label(text = "")