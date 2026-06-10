import bpy 
from bpy.types import Panel 


class VIEW3D_PT_Mastro_Architecture(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MaStro"
    bl_label = "Architecture"
    bl_order = 1
    
    @classmethod
    def poll(cls, context):
        return (context.object is not None and 
                context.object.type == "MESH" and 
                context.object.mode == "EDIT" and
                "MaStro object" in context.object.data and
                "MaStro mass" in context.object.data)
    
    def draw(self, context):
        obj = context.active_object 
        if obj is not None and obj.type == "MESH":
            mode = obj.mode
            if mode == "EDIT":
                scene = context.scene
                layout = self.layout
                layout.use_property_split = True    
                layout.use_property_decorate = False  # No animation.
                
                ################ WALL ######################
                row = layout.row()
                row = layout.row(align=True)
                
                if tuple(bpy.context.scene.tool_settings.mesh_select_mode)[1] == True: #we are selecting edges
                    row.enabled = True
                else:
                    row.enabled = False
                # row.prop(context.scene, "mastro_wall_names", icon="NODE_TEXTURE", icon_only=True, text="Wall Type")
                row.prop(context.scene, "mastro_wall_names", text="Wall Type")
                # if len(scene.mastro_wall_name_list) >0:
                #     row.label(text = scene.mastro_wall_name_current[0].name)
                #     wallId = scene.mastro_wall_name_current[0].id
                #     # thickness = round(scene.mastro_wall_name_list[wallId].wallThickness,3)
                #     thickness = "%.3f" % scene.mastro_wall_name_list[wallId].wallThickness
                #     # layout.label(text = str(thickness))
                #     # scene.mastro_attribute_wall_thickness = thickness
                #     # layout.prop(context.scene, 'mastro_attribute_wall_thickness', text="Thickness")
                #     # layout.prop(context.scene, 'mastro_attribute_wall_offset', text="Offset")
                # else:
                #     row.label(text = "")
                
                row = layout.row(align=True)
                row.prop(context.scene, 'mastro_attribute_wall_normal', text="Flip Normal")
                
                ################ FLOOR ######################
                row = layout.row()
                row = layout.row(align=True)
                
                if tuple(bpy.context.scene.tool_settings.mesh_select_mode)[2] == True: #we are selecting edges
                    row.enabled = True
                else:
                    row.enabled = False
                
                row.prop(context.scene, "mastro_floor_names", text="Floor Type")
                # row.prop(context.scene, "mastro_floor_names", icon="VIEW_PERSPECTIVE", icon_only=True, text="Floor Type")
                # if len(scene.mastro_floor_name_list) >0:
                #     row.label(text = scene.mastro_floor_name_current[0].name)
                # else:
                #     row.label(text = "")