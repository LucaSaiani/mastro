import bpy 
from bpy.types import Panel

# Replace the existing Transform Orientations panel in the UI, adding "orientation from edge"
class VIEW3D_PT_set_orientation(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Transform Orientations"
    bl_ui_units_x = 8

    def draw(self, context):
        
        obj = context.object
        
        # constaint_xy_settings = context.scene.constraint_xy_setting
        # if obj is None or obj.type != 'MESH':
        #     self.report({'ERROR'}, "Select a mesh object")
        #     return {'CANCELLED'}
        
        layout = self.layout
        layout.label(text="Transform Orientations")
        
        scene = context.scene
        orient_slot = scene.transform_orientation_slots[0]
        orientation = orient_slot.custom_orientation
      

        row = layout.row()
        col = row.column(align=True)
        
        col = row.column(align=True)
        col.prop(orient_slot, "type", expand=True)
         
        col_operators = row.column(align=True)
        # icon_value = icons.icon_id('AC_ON') if constaint_xy_settings.constraint_xy_on else icons.icon_id('AC_OFF')
        # col_operators.prop(constaint_xy_settings, 'constraint_xy_on', text='', icon_value=icon_value)
       
        col_operators.operator("transform.create_orientation", text="", icon='ADD', emboss=False)
        # this creates a new orientation from the selected edge
        if obj.mode == 'EDIT' and obj is not None and obj.type == 'MESH':
            col_operators.operator("transform.set_orientation_from_selection", text="", icon="EDGESEL", emboss=False)
        
        if orientation:
            row = layout.row(align=False)
            row.prop(orientation, "name", text="", icon='OBJECT_ORIGIN')
            row.operator("transform.delete_orientation", text="", icon='X', emboss=False)