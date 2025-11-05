import bpy 
from bpy.types import Panel 

class VIEW3D_PT_MaStro_Block(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MaStro"
    bl_label = "Block"
    
    @classmethod
    def poll(cls, context):
        return  (context.object is not None and 
                context.object.type == "MESH" and 
                "MaStro object" in context.object.data and
                "MaStro block" in context.object.data)
    
    def draw(self, context):
        obj = context.object
        if obj is not None and obj.type == "MESH":
        
            mode = obj.mode
            if mode == "OBJECT":
                scene = context.scene
                
                layout = self.layout
                layout.use_property_split = True    
                layout.use_property_decorate = False  # No animation.
                
                row = layout.row(align=True)
                
                row.prop(context.scene, "mastro_block_names", icon="MOD_BOOLEAN", icon_only=True, text="Block")
                if scene.mastro_block_name_list and len(scene.mastro_block_name_list) >0:
                    row.label(text = scene.mastro_block_name_current[0].name)
                # row = layout.row(align=True)
                # row.prop(context.scene, "mastro_building_names", icon="HOME", icon_only=True, text="Building")
                # if scene.mastro_building_name_list and len(scene.mastro_building_name_list) >0:
                #     row.label(text = scene.mastro_building_name_current[0].name)
                
                    
            elif mode == "EDIT":      
                scene = context.scene
                
                layout = self.layout
                layout.use_property_split = True
                layout.use_property_decorate = False

                layout_1 = layout.column()
                layout_0 = layout.column()
               
                # layout_0 = self.layout
                # layout_0.use_property_split = True    
                # layout_0.use_property_decorate = False  # No animation. 
                # layout_1 = self.layout
                # layout_1.use_property_split = True    
                # layout_1.use_property_decorate = False  # No animation.
               
                if tuple(bpy.context.scene.tool_settings.mesh_select_mode)[0] == True: #we are selecting edges
                    layout_0.enabled = True
                else:
                    layout_0.enabled = False
                if tuple(bpy.context.scene.tool_settings.mesh_select_mode)[1] == True: #we are selecting edges
                    layout_1.enabled = True
                else:
                    layout_1.enabled = False
                
                
         
                ################ TYPOLOGY ######################
                row = layout_1.row(align=True)
                row.prop(context.scene, "attribute_mass_storeys", text="N° of storeys") 
                row = layout_1.row(align=True)
                row.prop(context.scene, "attribute_block_depth", text="Depth") 
                # disable the number of storeys if there are no liquids
                # current_typology = scene.mastro_typology_name_current[0]
                
                
                # since it is possible to sort typologies in the ui, it can be that the index of the element
                # in the list doesn't correspond to typology_id. Therefore it is necessary to find elements
                # in the way below and not with use_list = bpy.context.scene.mastro_typology_name_list[typology_id].useList
                row = layout_1.row(align=True)
                item = next(i for i in bpy.context.scene.mastro_typology_name_list if i["id"] == scene.mastro_typology_name_current[0].id)
                use_list = item.useList
                uses = use_list.split(";")
                tmp_enabled = False
                for useID in uses:
                    if context.scene.mastro_use_name_list[int(useID)].liquid == True:
                        tmp_enabled = True
                        break
                
                row.enabled = tmp_enabled
                
                row = layout_1.row(align=True)
                row.prop(context.scene, "mastro_typology_names", icon="ASSET_MANAGER", icon_only=True, text="Typology")
                if len(scene.mastro_typology_name_list) >0:
                    row.label(text=scene.mastro_typology_name_current[0].name)
                rows = 3
                row = layout_1.row()
                row.template_list("OBJECT_UL_OBJ_Typology_Uses", 
                                  "obj_typology_uses_list", 
                                  scene,
                                  "mastro_obj_typology_uses_name_list",
                                  scene,
                                  "mastro_obj_typology_uses_name_list_index",
                                  rows = rows)
                
                row = layout_1.row(align=True)
                row.prop(context.scene, "attribute_block_normal", text="Flip Normal") 
                
                row = layout_0.row(align=True)
                row.prop(context.scene, "attribute_block_side_angle", text="Side rotation") 