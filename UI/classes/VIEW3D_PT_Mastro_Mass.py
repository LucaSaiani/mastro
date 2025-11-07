import bpy 
from bpy.types import Panel 

"""View 3D panel to show the mass related UI"""
class VIEW3D_PT_Mastro_Mass(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MaStro"
    bl_label = "Mass"
    bl_order = 0
    #bl_idname = "MASTRO_PT_Mass"
    
    
    # global blockName
    
    # @classmethod
    # def poll(cls, context):
    #     return (context.object is not None)
    
    @classmethod
    def poll(cls, context):
        return  (context.object is not None and 
                # context.selected_objects != [] and
                context.object.type == "MESH" and 
                "MaStro object" in context.object.data and
                "MaStro mass" in context.object.data)
    
    def draw(self, context):
        # obj = context.active_object 
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
                # row = layout.row()
                # row = layout.row(align=True)
                row.prop(context.scene, "mastro_block_names", icon="MOD_BOOLEAN", icon_only=True, text="Block")
                if scene.mastro_block_name_list and len(scene.mastro_block_name_list) >0:
                    row.label(text = scene.mastro_block_name_current[0].name)
                row = layout.row(align=True)
                row.prop(context.scene, "mastro_building_names", icon="HOME", icon_only=True, text="Building")
                if scene.mastro_building_name_list and len(scene.mastro_building_name_list) >0:
                    row.label(text = scene.mastro_building_name_current[0].name)
                
                    
            elif mode == "EDIT":      
                scene = context.scene
                
                layout = self.layout
                layout.use_property_split = True    
                layout.use_property_decorate = False  # No animation.
                
                if tuple(bpy.context.scene.tool_settings.mesh_select_mode)[2] == True: #we are selecting faces
                    layout.enabled = True
                else:
                    layout.enabled = False
                # col = layout.column()
                # subcol = col.column()
                
                # layout.active = bool(context.active_object.mode=='EDIT')
                # row = layout.row()
                
         
                ################ TYPOLOGY ######################
                row = layout.row(align=True)
                
                # disable the number of storeys if there are no liquids
                # current_typology = scene.mastro_typology_name_current[0]
                
                
                # since it is possible to sort typologies in the ui, it can be that the index of the element
                # in the list doesn't correspond to typology_id. Therefore it is necessary to find elements
                # in the way below and not with use_list = bpy.context.scene.mastro_typology_name_list[typology_id].useList
                item = next(i for i in bpy.context.scene.mastro_typology_name_list if i["id"] == scene.mastro_typology_name_current[0].id)
                use_list = item.useList
                uses = use_list.split(";")
                tmp_enabled = False
                for useID in uses:
                    if context.scene.mastro_use_name_list[int(useID)].liquid == True:
                        tmp_enabled = True
                        break
                row.prop(context.scene, "attribute_mass_storeys", text="N° of storeys") 
                row.enabled = tmp_enabled
                
                row = layout.row(align=True)
                row.prop(context.scene, "mastro_typology_names", icon="ASSET_MANAGER", icon_only=True, text="Typology")
                if len(scene.mastro_typology_name_list) >0:
                    row.label(text=scene.mastro_typology_name_current[0].name)
                rows = 3
                row = layout.row()
                row.template_list("OBJECT_UL_OBJ_Typology_Uses", 
                                  "obj_typology_uses_list", 
                                  scene,
                                  "mastro_obj_typology_uses_name_list",
                                  scene,
                                  "mastro_obj_typology_uses_name_list_index",
                                  rows = rows)