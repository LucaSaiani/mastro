import bpy 
from ... import Icons as icons

contexts = ['OBJECT', "EDIT_MESH"]

# define the constraint to xy axis button
def xy_constraint_button(self, context):
    """Draws the xy constraint toggle"""
    if context.mode not in contexts:
        return
    constaint_xy_settings = context.scene.mastro_constraint_xy_setting
    layout = self.layout
    row = layout.row(align=True)
    icon_value = icons.icon_id('xy_on') if constaint_xy_settings.constraint_xy_on else icons.icon_id('xy_off')
    row.prop(constaint_xy_settings, "constraint_xy_on", text="", icon_value=icon_value)
    
def register():
    bpy.types.VIEW3D_HT_tool_header.append(xy_constraint_button)

def unregister():
    bpy.types.VIEW3D_HT_tool_header.remove(xy_constraint_button)