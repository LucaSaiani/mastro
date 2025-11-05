import bpy 

from .. import Icons as icons

# add the entry to the add menu
def add_mesh_menu(self, context):
    self.layout.separator()
    myIcon = icons.icon_id("block")
    self.layout.operator("object.mastro_add_mastro_block", icon_value=myIcon)
    myIcon = icons.icon_id("mass")
    self.layout.operator("object.mastro_add_mastro_mass", icon_value=myIcon)
    myIcon = icons.icon_id("street")
    self.layout.operator("object.mastro_add_mastro_street", icon_value=myIcon)
    # myIcon = icons.icon_id("street")
    self.layout.operator("object.mastro_add_mastro_dimension", icon_value=myIcon)
  
  
def register():
    bpy.types.VIEW3D_MT_mesh_add.append(add_mesh_menu)
    
def unregister():
    bpy.types.VIEW3D_MT_mesh_add.remove(add_mesh_menu)