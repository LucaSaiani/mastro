import bpy 
from bpy.types import PropertyGroup
from bpy.props import IntProperty, StringProperty

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
           default = 1)