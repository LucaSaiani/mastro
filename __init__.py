# ----------------------------------------------
# Define Addon info
# ----------------------------------------------
bl_info = {
    "name": "RoMa",
    "author": "Luca Saiani",
    "version": (1, 0, 0),
    "blender": (3, 4, 0),
    "location": "View3D > Panel",
    "description": "RoMa",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Development"
}

import sys
import os
if "bpy" in locals():
    import importlib
    importlib.reload(roma_facade)
    importlib.reload(roma_mass)
else:
    from . import roma_facade
    from . import roma_mass


import bpy
from bpy.props import (
    IntProperty, 
    CollectionProperty
    )
from bpy.types import(
    Scene
)

classes = (
    # OPERATOR_update_RoMa_facade_attribute,
    roma_facade.OBJECT_OT_add_RoMa_facade,
    roma_facade.VIEW3D_PT_RoMa_facade,
    roma_facade.SetEdgeAttributeOperator_facade_type,
    roma_facade.ListItem,
    roma_facade.MY_UL_List,
    roma_facade.LIST_OT_NewItem,
    roma_facade.LIST_OT_DeleteItem,
    roma_facade.LIST_OT_MoveItem,
    
    roma_mass.OBJECT_OT_add_RoMa_Mass,
    roma_mass.VIEW3D_PT_RoMa_Mass,
    roma_mass.SetFaceAttributeOperator_mass_storeys
)

buttons = (
    roma_facade.add_RoMa_facade_button,
    roma_mass.add_RoMa_Mass_button
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
        
    for btn in buttons:
        bpy.types.VIEW3D_MT_mesh_add.append(btn)
    
    Scene.attribute_facade_type = bpy.props.IntProperty(
                                        name="Type", 
                                        default=0,
                                        update = roma_facade.update_attribute_facade_type)
    
    Scene.attribute_mass_storeys = bpy.props.IntProperty(
                                        name="Number of Storeys",
                                        min=1, 
                                        default=1,
                                        update = roma_mass.update_attribute_mass_storeys)
    
    Scene.my_list = CollectionProperty(type = roma_facade.ListItem)
    Scene.list_index = IntProperty(name = "Index for my_list",
                                             default = 0)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
        
    for btn in buttons:
        bpy.types.VIEW3D_MT_mesh_add.remove(btn)
        
    del Scene.attribute_facade_type
    del Scene.attribute_mass_storeys
    del Scene.my_list
    del Scene.list_index

