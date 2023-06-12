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
    importlib.reload(roma_menu),
    importlib.reload(roma_vertex),
    importlib.reload(roma_facade),
    importlib.reload(roma_mass)
else:
    from . import roma_menu
    from . import roma_vertex
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
    roma_menu.roma_MenuOperator_convert_to_RoMa_mesh,
    roma_menu.RoMa_MenuOperator_PrintData,
    roma_menu.RoMa_MenuOperator_ExportCSV,
    roma_menu.RoMa_Menu,
    
    roma_vertex.OBJECT_OT_SetVertexAttribute,
    roma_vertex.VIEW3D_PT_RoMa_vertex,

    # OPERATOR_update_RoMa_facade_attribute,
    roma_facade.OBJECT_OT_add_RoMa_facade,
    roma_facade.OBJECT_OT_SetFacadeType,
    roma_facade.VIEW3D_PT_RoMa_facade,
#    roma_facade.set_facade_type,
    roma_facade.ListFacadeType,
    roma_facade.FACADE_UL_edgeslots,
    roma_facade.LIST_OT_NewItem,
    roma_facade.LIST_OT_DeleteItem,
    roma_facade.LIST_OT_MoveItem,
    
    roma_mass.OBJECT_OT_add_RoMa_Mass,
    roma_mass.OBJECT_OT_SetPlotName,
    roma_mass.OBJECT_OT_SetBlockName,
    roma_mass.OBJECT_OT_SetUseName,
    roma_mass.OBJECT_OT_SetMassStoreys,
    roma_mass.VIEW3D_PT_RoMa_Mass,
    
)

buttons = (
    roma_facade.add_RoMa_facade_button,
    roma_mass.add_RoMa_Mass_button
)


def getFacadeList(scene, context):
    items = []
    for el in scene.roma_facade_type_list:
        newProp = (el.name, el.name, "")
        items.append(newProp)
    return items

          
def register():
    bpy.app.handlers.depsgraph_update_pre.append(roma_mass.get_face_attribute)
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
        
    for btn in buttons:
        bpy.types.VIEW3D_MT_mesh_add.append(btn)
        
    bpy.types.VIEW3D_MT_editor_menus.append(roma_menu.roma_menu)
    
    Scene.attribute_vertex = bpy.props.IntProperty(
                                        name="Vertex Custom Attribute", 
                                        default=1,
                                        update = roma_vertex.update_attribute_vertex)
    
    
    Scene.attribute_facade_type = bpy.props.IntProperty(
                                        name="Type", 
                                        default=1,
                                        update = roma_facade.update_attribute_facade_type)
    
    
    Scene.attribute_mass_plot_name = bpy.props.StringProperty(
                                        name="Plot Name",
                                        default="Plot Name",
                                        update = roma_mass.update_attribute_mass_plot_name)
     
    Scene.attribute_mass_block_name = bpy.props.StringProperty(
                                        name="Block Name",
                                        default="Block Name",
                                        update = roma_mass.update_attribute_mass_block_name)
     
    Scene.attribute_mass_use_name = bpy.props.StringProperty(
                                        name="Use",
                                        default="Use",
                                        update = roma_mass.update_attribute_mass_use_name)
     
    Scene.attribute_mass_storeys = bpy.props.IntProperty(
                                        name="Number of Storeys",
                                        min=1, 
                                        default=3,
                                        update = roma_mass.update_attribute_mass_storeys)
     
    
    
    Scene.roma_facade_type_list = CollectionProperty(type = roma_facade.ListFacadeType)
    
    Scene.roma_facade_type_index = IntProperty(name = "Façade Type",
                                             default = 0)
    
    Scene.roma_facade_type_name = bpy.props.EnumProperty(
                                        name="Façade Type List",
                                        description="",
                                        items=getFacadeList)
    

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
        
    for btn in buttons:
        bpy.types.VIEW3D_MT_mesh_add.remove(btn)
        
    bpy.types.VIEW3D_MT_editor_menus.remove(roma_menu.roma_menu)

    del Scene.attribute_facade_type
    del Scene.attribute_mass_plot_name
    del Scene.attribute_mass_block_name
    del Scene.attribute_mass_use_name
    del Scene.attribute_mass_storeys
    del Scene.roma_facade_type_list
    del Scene.roma_facade_type_index
    del Scene.roma_facade_type_name
    
