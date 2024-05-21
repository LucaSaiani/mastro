import bpy

from bpy.props import StringProperty, IntProperty
from bpy.types import Operator, Panel, UIList, PropertyGroup



class VIEW3D_PT_RoMa_Mass(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "RoMa"
    bl_label = "Mass"
    #bl_idname = "ROMA_PT_Mass"
    
    
    # global plotName
    
    # @classmethod
    # def poll(cls, context):
    #     return (context.object is not None)
    
    @classmethod
    def poll(cls, context):
        return (context.object is not None and context.object.type == "MESH" and "RoMa object" in context.object.data)
    
    def draw(self, context):
        # obj = context.active_object 
        obj = context.object
        if obj is not None and obj.type == "MESH":
        
            mode = obj.mode
            if mode == "OBJECT" and "RoMa object" in obj.data:
                scene = context.scene
                
                layout = self.layout
                layout.use_property_split = True    
                layout.use_property_decorate = False  # No animation.
                
                # row = layout.row()
                row = layout.row(align=True)
                
                layout.prop(obj.roma_props, "roma_option_attribute", text="Option")
                layout.prop(obj.roma_props, "roma_phase_attribute", text="Phase")
                # row = layout.row()
                row = layout.row(align=True)
                row.prop(context.scene, "roma_plot_names", icon="MOD_BOOLEAN", icon_only=True, text="Plot")
                if scene.roma_plot_name_list and len(scene.roma_plot_name_list) >0:
                    row.label(text = scene.roma_plot_name_current[0].name)
                row = layout.row(align=True)
                row.prop(context.scene, "roma_block_names", icon="HOME", icon_only=True, text="Block")
                if scene.roma_block_name_list and len(scene.roma_block_name_list) >0:
                    row.label(text = scene.roma_block_name_current[0].name)
                
                    
            elif mode == "EDIT" and "RoMa object" in obj.data:
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
                current_typology = scene.roma_typology_name_current[0]
                use_list = context.scene.roma_typology_name_list[current_typology.id].useList
                uses = use_list.split(";")
                tmp_enabled = False
                for useID in uses:
                    if context.scene.roma_use_name_list[int(useID)].liquid == True:
                        tmp_enabled = True
                        break
                row.prop(context.scene, "attribute_mass_storeys", text="N° of storeys") 
                row.enabled = tmp_enabled
                   
                
                
                row = layout.row(align=True)
                row.prop(context.scene, "roma_typology_names", icon="ASSET_MANAGER", icon_only=True, text="Typology")
                if len(scene.roma_typology_name_list) >0:
                    row.label(text= current_typology.name)
                rows = 3
                row = layout.row()
                row.template_list("OBJECT_UL_OBJ_Typology_Uses", 
                                  "obj_typology_uses_list", 
                                  scene,
                                  "roma_obj_typology_uses_name_list",
                                  scene,
                                  "roma_obj_typology_uses_name_list_index",
                                  rows = rows)
                
            
                
      

class OBJECT_UL_OBJ_Typology_Uses(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):
        custom_icon = 'COMMUNITY'
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            split = layout.split(factor=0.5)
            split.label(text="Storeys: %s" % (item.storeys))
            split.label(text=item.name)
            
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon = custom_icon)

    def filter_items(self, context, data, propname):
        filtered = []
        ordered = []
        items = getattr(data, propname)
        filtered = [self.bitflag_filter_item] * len(items)
        
        # for i, item in enumerate(items):
        #     if item.id == 0:
        #         filtered[i] &= ~self.bitflag_filter_item
        return filtered, ordered

    def draw_filter(self, context, layout):
        pass
    
    
class OBJECT_OT_SetTypologyId(Operator):
    """Set Face Attribute as typology of the block"""
    bl_idname = "object.set_attribute_mass_typology_id"
    bl_label = "Set Face Attribute as Typology of the Block"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        mesh = obj.data

        # attribute_mass_typology_id = context.scene.attribute_mass_typology_id
        
        try:
            mesh.attributes["roma_typology_id"]
            # attribute_mass_typology_id = context.scene.attribute_mass_typology_id

            mode = obj.mode
            bpy.ops.object.mode_set(mode='OBJECT')
           
            selected_faces = [p for p in bpy.context.active_object.data.polygons if p.select]
            mesh_attributes = mesh.attributes["roma_typology_id"].data.items()

            
            for face in selected_faces:
                index = face.index
                for mesh_attribute in mesh_attributes:
                    if mesh_attribute[0] == index:
                        mesh_attribute[1].value = context.scene.attribute_mass_typology_id
                        break
               
           
            bpy.ops.object.mode_set(mode=mode)
                    
            # self.report({'INFO'}, "Attribute set to face, use: "+str(attribute_mass_use_id))
            return {'FINISHED'}
        except:
            return {'FINISHED'}
        

    
class OBJECT_OT_SetMassStoreys(Operator):
    """Set Face Attribute as Number of Mass Storeys"""
    bl_idname = "object.set_attribute_mass_storeys"
    bl_label = "Set Face Attribute as number of Mass Storeys"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        mesh = obj.data

        # attribute_mass_storeys = context.scene.attribute_mass_storeys
        
        # a custom attribute is assigned to the edges
       
        try:
            mesh.attributes["roma_number_of_storeys"]
            

            
            
            # we need to switch from Edit mode to Object mode so the selection gets updated
            mode = obj.mode
            bpy.ops.object.mode_set(mode='OBJECT')
            
            selected_faces = [p for p in bpy.context.active_object.data.polygons if p.select]
            mesh_attributes = mesh.attributes["roma_number_of_storeys"].data.items()
            
            for face in selected_faces:
                index = face.index
                for mesh_attribute in mesh_attributes:
                    if mesh_attribute[0] == index:
                        mesh_attribute[1].value = context.scene.attribute_mass_storeys
                        # updateArrays(index, attributes)
                        break
            # back to whatever mode we were in
            bpy.ops.object.mode_set(mode=mode)
                    
            return {'FINISHED'}
        except:
            return {'FINISHED'}
        


class obj_typology_uses_name_list(PropertyGroup):
    id: IntProperty(
           name="Id",
           description="Obj typology use name id",
           default = 0)
    
    nameId: IntProperty(
           name="nameId",
           description="The id of the name in the main uses list",
           default = 0)
    
    name: StringProperty(
           name="Obj floor use name",
           description="The use associated to that set of floors",
           default="")
    
    storeys: IntProperty(
           name="Number of storeys",
           description="The number of storeys associated to that use",
           default = 0)
    
def update_attribute_mass_typology_id(self, context):
    bpy.ops.object.set_attribute_mass_typology_id()
    
        
def update_attribute_mass_storeys(self, context):
    bpy.ops.object.set_attribute_mass_storeys()


# update the plot id attribute assigned to the selected object
def update_plot_name_id(self, context):
    scene = context.scene
    name = scene.roma_plot_names
    # scene.roma_plot_name_current[0].name = " " + name
    scene.roma_plot_name_current[0].name = name
    for n in scene.roma_plot_name_list:
        if n.name == name:
            scene.attribute_mass_plot_id = n.id
            scene.roma_plot_name_current[0].id = n.id
            
            obj = context.active_object
            obj.roma_props['roma_plot_attribute'] = n.id
            break 

def update_block_name_id(self, context):
    # global blockName
    scene = context.scene
    name = scene.roma_block_names
    scene.roma_block_name_current[0].name = name
    for n in scene.roma_block_name_list:
        if n.name == name:
            scene.attribute_mass_block_id = n.id
            scene.roma_block_name_current[0].id = n.id
            
            obj = context.active_object
            obj.roma_props['roma_block_attribute'] = n.id
            break   
        
def update_typology_name_label(self, context):
    # global useName
    scene = context.scene
    name = scene.roma_typology_names
    scene.roma_typology_name_current[0].name = name
    for n in scene.roma_typology_name_list:
        if n.name == name:
            scene.attribute_mass_typology_id = n.id
            scene.roma_typology_name_current[0].id = n.id
            break  

        
    

       