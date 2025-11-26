import bpy 
from bpy.types import Panel

class PROPERTIES_PT_Mastro_Typology(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_label = "Typology"
    bl_parent_id = "PROPERTIES_PT_Mastro_Mass"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 2
    
    def draw(self, context):
        scene = context.scene
        
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.
        
        row = layout.row()
        rows = 3
        row.template_list("PROPERTIES_UL_Typology", "typology_list", scene,
                        "mastro_typology_name_list", scene, "mastro_typology_name_list_index", rows = rows)
        
        
        col = row.column(align=True)
        col.operator("mastro_typology_name_list.new_item", icon='ADD', text="")
        col.operator("mastro_typology_name_list.duplicate_item", icon='COPYDOWN', text="")
        col.separator()
        col.operator("mastro_typology_name_list.move_item", icon='TRIA_UP', text="").direction = 'UP'
        col.operator("mastro_typology_name_list.move_item", icon='TRIA_DOWN', text="").direction = 'DOWN'
            
        ########## typology uses ###############
        row = layout.row()
        row.label(text="Uses:")
        row = layout.row()
        rows = 3
        row = layout.row()
        row.template_list("PROPERTIES_UL_Typology_Uses", "typology_uses_list", scene,
                        "mastro_typology_uses_name_list", scene, "mastro_typology_uses_name_list_index", rows = rows)
        
        
        col = row.column(align=True)
        col.operator("mastro_typology_uses_name_list.new_item", icon='ADD', text="")
        sub = col.row()
        sub.operator("mastro_typology_uses_name_list.delete_item", icon='REMOVE', text="")
        if len(scene.mastro_typology_uses_name_list) < 2:
            sub.enabled = False
        else:
            sub.enabled = True
            
        
        col.separator()
        col.operator("mastro_typology_uses_name_list.move_item", icon='TRIA_UP', text="").direction = 'UP'
        
        col.operator("mastro_typology_uses_name_list.move_item", icon='TRIA_DOWN', text="").direction = 'DOWN'

        # use editor        
        row = layout.row(align=True)
        subIndex = context.scene.mastro_typology_uses_name_list_index
        subName = context.scene.mastro_typology_uses_name_list[subIndex].name
        index = context.scene.mastro_use_name_list.find(subName)
        col = layout.column(align=True)
        
        row = col.row(align=True)
       
        row.prop(context.scene, "mastro_typology_uses_name", icon="COMMUNITY", icon_only=True, text="")
        row.prop(context.scene.mastro_use_name_list[index],"name", text="")
        row.operator("mastro_use_name_list.new_item", icon='ADD', text="")
        
        layout.prop(context.scene.mastro_use_name_list[index],"floorToFloor", text="Floor to floor height")
        row = layout.row(align=True)
        sub = row.row()
        sub.prop(context.scene.mastro_use_name_list[index],"storeys", text="Number of storeys")
        layout.prop(context.scene.mastro_use_name_list[index],"liquid", text="Variable number of storeys")
        if context.scene.mastro_use_name_list[index].liquid:
            sub.enabled = False
        else:
            sub.enabled = True
        # layout.prop(context.scene.mastro_use_name_list[index],"void", text="Void")
        # sub = layout.row()
        # sub.active = not(context.window_manager.mastro_toggle_auto_update_mass_data)
        # sub.prop(context.scene.mastro_use_name_list[index],"void", text="Update")
        # sub.operator("object.update_mastro_mesh_attributes").attribute_to_update="all"
        row = layout.row(align=True)
        
        row.operator("object.update_mastro_mesh_attributes")
        row.prop(context.window_manager, "mastro_toggle_auto_update_mass_data", text="", icon="FILE_REFRESH")
 