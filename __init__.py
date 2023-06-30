# ----------------------------------------------
# Define Addon info
# ----------------------------------------------
bl_info = {
    "name": "RoMa",
    "author": "Luca Saiani",
    "version": (0, 0, 1),
    "blender": (3, 4, 0),
    "location": "View3D > Panel",
    "description": "RoMa",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Objects"
}

# import sys
# import os
import random
import decimal
from datetime import datetime


if "bpy" in locals():
    import importlib
    importlib.reload(roma_preferences),
    importlib.reload(roma_modal_operator)
    importlib.reload(roma_project_data),
    importlib.reload(roma_menu),
    # importlib.reload(roma_vertex),
    importlib.reload(roma_facade),
    importlib.reload(roma_mass)
else:
    from . import roma_preferences
    from . import roma_modal_operator
    from . import roma_project_data
    from . import roma_menu
    # from . import roma_vertex
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
from bpy.app.handlers import persistent

classes = (
    roma_preferences.roma_addon_preferences,
    roma_preferences.OBJECT_OT_roma_addon_prefs,
    
    #roma_modal_operator.VIEW3D_OT_show_Roma_attributes,
    roma_modal_operator.VIEW3D_OT_update_Roma_mesh_attributes,
    
    roma_project_data.VIEW3D_PT_RoMa_project_data,
    roma_project_data.VIEW3D_PT_RoMa_show_data,
    roma_project_data.VIEW3D_PT_RoMa_mass_data,
    roma_project_data.VIEW3D_PT_RoMa_facade_data,
    # roma_project_data.TEST_OT_modal_operator,
    
    roma_project_data.name_with_id,
    
    roma_project_data.OBJECT_UL_Plot,
    roma_project_data.plot_name_list,
    roma_project_data.PLOT_LIST_OT_NewItem,
    roma_project_data.PLOT_LIST_OT_MoveItem,
    
    roma_project_data.OBJECT_UL_Block,
    roma_project_data.block_name_list,
    roma_project_data.BLOCK_LIST_OT_NewItem,
    roma_project_data.BLOCK_LIST_OT_MoveItem,
    
    roma_project_data.OBJECT_UL_Use,
    roma_project_data.use_name_list,
    roma_project_data.USE_LIST_OT_NewItem,
    roma_project_data.USE_LIST_OT_MoveItem,
    
    roma_project_data.OBJECT_UL_Facade,
    roma_project_data.facade_name_list,
    roma_project_data.FACADE_LIST_OT_NewItem,
    roma_project_data.FACADE_LIST_OT_MoveItem,
    
    roma_project_data.OBJECT_UL_Floor,
    roma_project_data.floor_name_list,
    roma_project_data.FLOOR_LIST_OT_NewItem,
    roma_project_data.FLOOR_LIST_OT_MoveItem,
    
    roma_menu.roma_MenuOperator_convert_to_RoMa_mesh,
    roma_menu.RoMa_MenuOperator_PrintData,
    roma_menu.RoMa_MenuOperator_ExportCSV,
    roma_menu.RoMa_Menu,
    
    # roma_vertex.OBJECT_OT_SetVertexAttribute,
    # roma_vertex.VIEW3D_PT_RoMa_vertex,
    
    # roma_mass.OBJECT_OT_add_RoMa_Mass,
    roma_mass.OBJECT_OT_SetPlotId,
    roma_mass.OBJECT_OT_SetBlockId,
    roma_mass.OBJECT_OT_SetUseId,
    roma_mass.OBJECT_OT_SetMassStoreys,
    roma_mass.VIEW3D_PT_RoMa_Mass,

    roma_facade.OBJECT_OT_SetFacadeId,
    roma_facade.OBJECT_OT_SetFacadeNormal,
    roma_facade.OBJECT_OT_SetFloorId,
    roma_facade.VIEW3D_PT_RoMa_Facade
    
    
    
)

# buttons = (
#     roma_facade.add_RoMa_facade_button,
#     roma_mass.add_RoMa_Mass_button
# )

def get_plot_names_from_list(scene, context):
    items = []
    
    for el in scene.roma_plot_name_list:
        newProp = (el.name, el.name, "")
        items.append(newProp)
    # noneItem = ("None", "None", "")
    # items.append(noneItem)
    return items

def get_block_names_from_list(scene, context):
    items = []
    for el in scene.roma_block_name_list:
        newProp = (el.name, el.name, "")
        items.append(newProp)
    return items

def get_use_names_from_list(scene, context):
    items = []
    for el in scene.roma_use_name_list:
        newProp = (el.name, el.name, "")
        items.append(newProp)
    return items

def get_facade_names_from_list(scene, context):
    items = []
    for el in scene.roma_facade_name_list:
        newProp = (el.name, el.name, "")
        items.append(newProp)
    return items

def get_floor_names_from_list(scene, context):
    items = []
    for el in scene.roma_floor_name_list:
        newProp = (el.name, el.name, "")
        items.append(newProp)
    return items

# @persistent
# def init_data(dummy):
#     elNumber = 0
#     for el in Scene.roma_plot_name_list:
#         elNumber+=1
#     print("HELLLLL",elNumber)
#     # if len(Scene.roma_plot_name_list) == 0:
#             # bpy.ops.roma_plot_name_list.new_item()
#             # print("inizializzo")
#     # print("macche")
#     bpy.app.handlers.load_post.remove(init_data)
@persistent
def onFileLoaded(scene):
    if len(bpy.context.scene.roma_plot_name_current) == 0:
        bpy.context.scene.roma_plot_name_current.add()
        bpy.context.scene.roma_plot_name_current[0].id = 0
        bpy.context.scene.roma_plot_name_current[0].name = " "
        print("roma_plot_name_current",len(bpy.context.scene.roma_plot_name_current))
    
    if len(bpy.context.scene.roma_block_name_current) == 0:
        bpy.context.scene.roma_block_name_current.add()
        bpy.context.scene.roma_block_name_current[0].id = 0
        bpy.context.scene.roma_block_name_current[0].name = " "
        print("roma_block_name_current)", len(bpy.context.scene.roma_block_name_current))
        
    if len(bpy.context.scene.roma_use_name_current) == 0:
        bpy.context.scene.roma_use_name_current.add()
        bpy.context.scene.roma_use_name_current[0].id = 0
        bpy.context.scene.roma_use_name_current[0].name = " "
        print("roma_use_name_current",len(bpy.context.scene.roma_use_name_current))
        
    if len(bpy.context.scene.roma_facade_name_current) == 0:
        bpy.context.scene.roma_facade_name_current.add()
        bpy.context.scene.roma_facade_name_current[0].id = 0
        bpy.context.scene.roma_facade_name_current[0].name = " "
        print("roma_facade_name_current",len(bpy.context.scene.roma_facade_name_current))
        
    if len(bpy.context.scene.roma_floor_name_current) == 0:
        bpy.context.scene.roma_floor_name_current.add()
        bpy.context.scene.roma_floor_name_current[0].id = 0
        bpy.context.scene.roma_floor_name_current[0].name = " "
    
    if len(bpy.context.scene.roma_plot_name_list) == 0:
        bpy.context.scene.roma_plot_name_list.add()
        bpy.context.scene.roma_plot_name_list[0].id = 0
        bpy.context.scene.roma_plot_name_list[0].name = ""
        random.seed(datetime.now().timestamp())
        rndNumber = float(decimal.Decimal(random.randrange(0,10000000))/10000000)
        bpy.context.scene.roma_plot_name_list[0].RND = rndNumber
        
    if len(bpy.context.scene.roma_block_name_list) == 0:
        bpy.context.scene.roma_block_name_list.add()
        bpy.context.scene.roma_block_name_list[0].id = 0
        bpy.context.scene.roma_block_name_list[0].name = ""
        random.seed(datetime.now().timestamp())
        rndNumber = float(decimal.Decimal(random.randrange(0,10000000))/10000000)
        bpy.context.scene.roma_block_name_list[0].RND = rndNumber
        
    if len(bpy.context.scene.roma_use_name_list) == 0:
        bpy.context.scene.roma_use_name_list.add()
        bpy.context.scene.roma_use_name_list[0].id = 0
        bpy.context.scene.roma_use_name_list[0].name = ""
        random.seed(datetime.now().timestamp())
        rndNumber = float(decimal.Decimal(random.randrange(0,10000000))/10000000)
        bpy.context.scene.roma_use_name_list[0].RND = rndNumber
        
    if len(bpy.context.scene.roma_facade_name_list) == 0:
        bpy.context.scene.roma_facade_name_list.add()
        bpy.context.scene.roma_facade_name_list[0].id = 0
        bpy.context.scene.roma_facade_name_list[0].name = ""
        bpy.context.scene.roma_facade_name_list[0].normal = 0
      
    if len(bpy.context.scene.roma_floor_name_list) == 0:
        bpy.context.scene.roma_floor_name_list.add()
        bpy.context.scene.roma_floor_name_list[0].id = 0
        bpy.context.scene.roma_floor_name_list[0].name = ""
    
    
def register():
    bpy.app.handlers.load_post.append(onFileLoaded)
    bpy.app.handlers.depsgraph_update_post.append(roma_modal_operator.refresh_roma_mesh_attributes)
    # bpy.app.handlers.load_post.append(roma_modal_operator.refresh_roma_face_attributes)
    
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
        
    # for btn in buttons:
    #     bpy.types.VIEW3D_MT_mesh_add.append(btn)
    
    bpy.types.VIEW3D_MT_editor_menus.append(roma_menu.roma_menu)
    
    bpy.types.WindowManager.toggle_show_data = bpy.props.BoolProperty(
                                            default = False,
                                            update = roma_modal_operator.update_show_attributes)
        
    bpy.types.WindowManager.toggle_plot_name = bpy.props.BoolProperty(
                                            name = "Plot",
                                            default = False,
                                            update = roma_modal_operator.update_show_attributes)
    
    bpy.types.WindowManager.toggle_block_name = bpy.props.BoolProperty(
                                            name = "Block",
                                            default = False,
                                            update = roma_modal_operator.update_show_attributes)
    
    bpy.types.WindowManager.toggle_use_name = bpy.props.BoolProperty(
                                            name = "Use",
                                            default = False,
                                            update = roma_modal_operator.update_show_attributes)
    
    bpy.types.WindowManager.toggle_facade_name = bpy.props.BoolProperty(
                                            name = "Type",
                                            default = False,
                                            update = roma_modal_operator.update_show_attributes)
    
    bpy.types.WindowManager.toggle_facade_normal = bpy.props.BoolProperty(
                                            name = "Inverted Normals",
                                            default = True,
                                            update = roma_modal_operator.update_show_attributes)
    
    bpy.types.WindowManager.toggle_floor_name = bpy.props.BoolProperty(
                                            name = "Type",
                                            default = False,
                                            update = roma_modal_operator.update_show_attributes)
    
    bpy.types.WindowManager.toggle_storey_number = bpy.props.BoolProperty(
                                            name = "Number of Storeys",
                                            default = False,
                                            update = roma_modal_operator.update_show_attributes)
        
    
    # Scene.attribute_vertex = bpy.props.IntProperty(
    #                                     name="Vertex Custom Attribute", 
    #                                     default=1,
    #                                     update = roma_vertex.update_attribute_vertex)
    
    
    
    Scene.attribute_mass_plot_id = bpy.props.IntProperty(
                                        name="Plot Id",
                                        default=0,
                                        update = roma_mass.update_attribute_mass_plot_id)
     
    Scene.attribute_mass_block_id = bpy.props.IntProperty(
                                        name="Block Id",
                                        default=0,
                                        update = roma_mass.update_attribute_mass_block_id)
     
    Scene.attribute_mass_use_id = bpy.props.IntProperty(
                                        name="Use Id",
                                        default=0,
                                        update = roma_mass.update_attribute_mass_use_id)
    
    Scene.attribute_facade_id = bpy.props.IntProperty(
                                        name="Façade Id",
                                        default=0,
                                        update = roma_facade.update_attribute_facade_id)
    
    Scene.attribute_facade_normal = bpy.props.BoolProperty(
                                            default = False,
                                            update = roma_facade.update_facade_normal)
    
    Scene.attribute_floor_id = bpy.props.IntProperty(
                                        name="Floor Id",
                                        default=0,
                                        update = roma_facade.update_attribute_floor_id)
     
    Scene.attribute_mass_storeys = bpy.props.IntProperty(
                                        name="Number of Storeys",
                                        min=0, 
                                        default=0,
                                        update = roma_mass.update_attribute_mass_storeys)
     
    
    Scene.roma_plot_name_list = CollectionProperty(type = roma_project_data.plot_name_list)
    Scene.roma_plot_name_current = CollectionProperty(type =roma_project_data.name_with_id)
    Scene.roma_plot_name_list_index = IntProperty(name = "Plot Name",
                                             default = 0)
    Scene.roma_plot_names = bpy.props.EnumProperty(
                                        name="Plot List",
                                        description="",
                                        items=get_plot_names_from_list,
                                        update=roma_mass.update_plot_name_label)
    
    Scene.roma_block_name_list = CollectionProperty(type = roma_project_data.block_name_list)
    Scene.roma_block_name_current = CollectionProperty(type =roma_project_data.name_with_id)
    Scene.roma_block_name_list_index = IntProperty(name = "Block Name",
                                             default = 0)
    Scene.roma_block_names = bpy.props.EnumProperty(
                                        name="Block List",
                                        description="",
                                        items=get_block_names_from_list,
                                        update=roma_mass.update_block_name_label)
    
    Scene.roma_use_name_list = CollectionProperty(type = roma_project_data.use_name_list)
    Scene.roma_use_name_current = CollectionProperty(type =roma_project_data.name_with_id)
    Scene.roma_use_name_list_index = IntProperty(name = "Use Name",
                                             default = 0)
    Scene.roma_use_names = bpy.props.EnumProperty(
                                        name="Use List",
                                        description="",
                                        items=get_use_names_from_list,
                                        update=roma_mass.update_use_name_label)
    
    Scene.roma_facade_name_list = CollectionProperty(type = roma_project_data.facade_name_list)
    Scene.roma_facade_name_current = CollectionProperty(type =roma_project_data.name_with_id)
    Scene.roma_facade_name_list_index = IntProperty(name = "Façade Name",
                                             default = 0)
    Scene.roma_facade_names = bpy.props.EnumProperty(
                                        name="Façade List",
                                        description="",
                                        items=get_facade_names_from_list,
                                        update=roma_facade.update_facade_name_label)
    
    Scene.roma_floor_name_list = CollectionProperty(type = roma_project_data.floor_name_list)
    Scene.roma_floor_name_current = CollectionProperty(type =roma_project_data.name_with_id)
    Scene.roma_floor_name_list_index = IntProperty(name = "Floor Name",
                                             default = 0)
    Scene.roma_floor_names = bpy.props.EnumProperty(
                                        name="Floor List",
                                        description="",
                                        items=get_floor_names_from_list,
                                        update=roma_facade.update_floor_name_label)
    
   
    

def unregister():
    bpy.app.handlers.load_post.remove(onFileLoaded)
    # bpy.app.handlers.depsgraph_update_pre.remove(roma_mass.get_face_attribute)
    #bpy.app.handlers.depsgraph_update_pre.remove(roma_modal_operator.refresh_roma_face_attributes)
    
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
        
    # for btn in buttons:
    #     bpy.types.VIEW3D_MT_mesh_add.remove(btn)
        
    bpy.types.VIEW3D_MT_editor_menus.remove(roma_menu.roma_menu)

    del bpy.types.WindowManager.toggle_show_data
    del bpy.types.WindowManager.toggle_plot_name
    del bpy.types.WindowManager.toggle_block_name
    del bpy.types.WindowManager.toggle_use_name
    del bpy.types.WindowManager.toggle_storey_number
    del bpy.types.WindowManager.toggle_facade_name
    del bpy.types.WindowManager.toggle_facade_normal
    del bpy.types.WindowManager.toggle_floor_name
    
    
    del Scene.attribute_mass_plot_id
    del Scene.attribute_mass_block_id
    del Scene.attribute_mass_use_id
    del Scene.attribute_facade_id
    del Scene.attribute_facade_normal
    del Scene.attribute_floor_id
    del Scene.attribute_mass_storeys

    del Scene.roma_plot_name_list
    del Scene.roma_block_name_list
    del Scene.roma_use_name_list
    del Scene.roma_facade_name_list
    del Scene.roma_floor_name_list
    
    del Scene.roma_plot_name_current
    del Scene.roma_block_name_current
    del Scene.roma_use_name_current
    del Scene.roma_facade_name_current
    del Scene.roma_floor_name_current
    
    del Scene.roma_plot_name_list_index
    del Scene.roma_block_name_list_index
    del Scene.roma_use_name_list_index
    del Scene.roma_facade_name_list_index
    del Scene.roma_floor_name_list_index
    
    del Scene.roma_plot_names
    del Scene.roma_block_names
    del Scene.roma_use_names
    del Scene.roma_facade_names
    del Scene.roma_floor_names
    
    
    
    
    
   
    
