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

if "bpy" in locals():
    import importlib
    importlib.reload(roma_preferences),
    importlib.reload(roma_modal_operator)
    importlib.reload(roma_project_data),
    importlib.reload(roma_menu),
    # importlib.reload(roma_vertex),
    importlib.reload(roma_wall),
    importlib.reload(roma_massing),
    importlib.reload(roma_schedule)
else:
    from . import roma_preferences
    from . import roma_modal_operator
    from . import roma_project_data
    from . import roma_menu
    # from . import roma_vertex
    from . import roma_wall
    from . import roma_massing
    from . import roma_schedule
    
import bpy

from bpy.types import(
                        Scene
                        )
from bpy.app.handlers import persistent

classes = (
    roma_preferences.roma_addon_preferences,
    roma_modal_operator.VIEW_3D_OT_show_roma_selection,
    roma_modal_operator.VIEW_3D_OT_show_roma_attributes,
    roma_modal_operator.VIEW_3D_OT_update_mesh_attributes,
    roma_modal_operator.VIEW_3D_OT_update_all_mesh_attributes,
    
    roma_project_data.update_GN_Filter_OT,
    roma_project_data.update_Shader_Filter_OT,
    
    roma_project_data.VIEW3D_PT_RoMa_project_data,
    roma_project_data.VIEW3D_PT_RoMa_show_data,
    roma_project_data.VIEW3D_PT_RoMa_mass_data,
    roma_project_data.VIEW3D_PT_RoMa_mass_plot_data,
    roma_project_data.VIEW3D_PT_RoMa_mass_block_data,
    # roma_project_data.VIEW3D_PT_RoMa_mass_use_data,
    roma_project_data.VIEW3D_PT_RoMa_mass_typology_data,
    roma_project_data.VIEW3D_PT_RoMa_building_data,
    roma_project_data.VIEW3D_PT_RoMa_building_wall_data,
    roma_project_data.VIEW3D_PT_RoMa_building_floor_data,
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
    
    # roma_project_data.OBJECT_UL_Use,
    roma_project_data.use_name_list,
    roma_project_data.USE_LIST_OT_NewItem,
    # roma_project_data.USE_LIST_OT_MoveItem,
    
    roma_project_data.OBJECT_UL_Typology,
    roma_project_data.typology_name_list,
    roma_project_data.TYPOLOGY_LIST_OT_NewItem,
    roma_project_data.TYPOLOGY_LIST_OT_MoveItem,
    
    roma_project_data.OBJECT_UL_Typology_Uses,
    roma_project_data.typology_uses_name_list,
    roma_project_data.TYPOLOGY_USES_LIST_OT_NewItem,
    roma_project_data.TYPOLOGY_USES_LIST_OT_DeleteItem,
    roma_project_data.TYPOLOGY_USES_LIST_OT_MoveItem,
    # roma_project_data.update_typology_uses_OT,
    
    roma_project_data.OBJECT_UL_Wall,
    roma_project_data.wall_name_list,
    roma_project_data.WALL_LIST_OT_NewItem,
    roma_project_data.WALL_LIST_OT_MoveItem,
    
    roma_project_data.OBJECT_UL_Floor,
    roma_project_data.floor_name_list,
    roma_project_data.FLOOR_LIST_OT_NewItem,
    roma_project_data.FLOOR_LIST_OT_MoveItem,
    
    roma_menu.RoMa_MenuOperator_add_RoMa_mass,
    roma_menu.RoMa_MenuOperator_convert_to_RoMa_mass,
    roma_menu.RoMa_MenuOperator_PrintData,
    roma_menu.RoMa_MenuOperator_ExportCSV,
    roma_menu.RoMa_Operator_transformation_orientation,
    roma_menu.RoMa_Menu,
    roma_menu.romaAddonProperties,
    
    roma_schedule.RoMa_Schedule_Tree,
    roma_schedule.RoMa_Schedule_Panel,
    roma_schedule.Roma_Draw_Schedule,
    
    # roma_vertex.OBJECT_OT_SetVertexAttribute,
    # roma_vertex.VIEW3D_PT_RoMa_vertex,
    
    roma_massing.OBJECT_OT_SetTypologyId,
    roma_massing.OBJECT_UL_OBJ_Typology_Uses,
    roma_massing.OBJECT_OT_SetMassStoreys,
    roma_massing.obj_typology_uses_name_list,
    roma_massing.VIEW3D_PT_RoMa_Mass,


    roma_wall.OBJECT_OT_SetWallId,
    roma_wall.OBJECT_OT_SetWallNormal,
    roma_wall.OBJECT_OT_SetFloorId,
    roma_wall.VIEW3D_PT_RoMa_Wall,
)

def initNodes():
    bpy.ops.node.update_gn_filter()
    bpy.ops.node.update_shader_filter(filter_name="plot")
    bpy.ops.node.update_shader_filter(filter_name="block")
    bpy.ops.node.update_shader_filter(filter_name="use")
    bpy.ops.node.update_shader_filter(filter_name="typology")
    pass
    

def initLists():
    if len(bpy.context.scene.roma_plot_name_list) == 0:
        bpy.context.scene.roma_plot_name_list.add()
        bpy.context.scene.roma_plot_name_list[0].id = 0
        bpy.context.scene.roma_plot_name_list[0].name = "Plot name..."
        
    if len(bpy.context.scene.roma_block_name_list) == 0:
        bpy.context.scene.roma_block_name_list.add()
        bpy.context.scene.roma_block_name_list[0].id = 0
        bpy.context.scene.roma_block_name_list[0].name = "Block name..."
        
    if len(bpy.context.scene.roma_use_name_list) == 0:
        bpy.context.scene.roma_use_name_list.add()
        bpy.context.scene.roma_use_name_list[0].id = 0
        bpy.context.scene.roma_use_name_list[0].name = "Use name..."
        bpy.context.scene.roma_use_name_list[0].storeys = 3
        bpy.context.scene.roma_use_name_list[0].liquid = True
    
    if len(bpy.context.scene.roma_typology_name_list) == 0:
        bpy.context.scene.roma_typology_name_list.add()
        bpy.context.scene.roma_typology_name_list[0].id = 0
        bpy.context.scene.roma_typology_name_list[0].name = "Typology name... "
        bpy.context.scene.roma_typology_name_list[0].useList = "0"
    
    if len(bpy.context.scene.roma_typology_uses_name_list) == 0:
        bpy.context.scene.roma_typology_uses_name_list.add()
        bpy.context.scene.roma_typology_uses_name_list[0].id = 0
        bpy.context.scene.roma_typology_uses_name_list[0].name = bpy.context.scene.roma_use_name_list[0].name
        
    if len(bpy.context.scene.roma_obj_typology_uses_name_list) == 0:
        bpy.context.scene.roma_obj_typology_uses_name_list.add()
        bpy.context.scene.roma_obj_typology_uses_name_list[0].id = 0
        bpy.context.scene.roma_obj_typology_uses_name_list[0].name =  bpy.context.scene.roma_use_name_list[0].name
    
    if len(bpy.context.scene.roma_wall_name_list) == 0:
        bpy.context.scene.roma_wall_name_list.add()
        bpy.context.scene.roma_wall_name_list[0].id = 0
        bpy.context.scene.roma_wall_name_list[0].name = "Wall type... "
        bpy.context.scene.roma_wall_name_list[0].normal = 0
    
    if len(bpy.context.scene.roma_floor_name_list) == 0:
        bpy.context.scene.roma_floor_name_list.add()
        bpy.context.scene.roma_floor_name_list[0].id = 0
        bpy.context.scene.roma_floor_name_list[0].name = "Floor type..."
        
    if len(bpy.context.scene.roma_plot_name_current) == 0:
        bpy.context.scene.roma_plot_name_current.add()
        bpy.context.scene.roma_plot_name_current[0].id = 0
        bpy.context.scene.roma_plot_name_current[0].name = bpy.context.scene.roma_plot_name_list[0].name
    
    if len(bpy.context.scene.roma_block_name_current) == 0:
        bpy.context.scene.roma_block_name_current.add()
        bpy.context.scene.roma_block_name_current[0].id = 0
        bpy.context.scene.roma_block_name_current[0].name = bpy.context.scene.roma_block_name_list[0].name
        
    if len(bpy.context.scene.roma_typology_name_current) == 0:
        bpy.context.scene.roma_typology_name_current.add()
        bpy.context.scene.roma_typology_name_current[0].id = 0
        bpy.context.scene.roma_typology_name_current[0].name = bpy.context.scene.roma_typology_name_list[0].name
        
    if len(bpy.context.scene.roma_wall_name_current) == 0:
        bpy.context.scene.roma_wall_name_current.add()
        bpy.context.scene.roma_wall_name_current[0].id = 0
        bpy.context.scene.roma_wall_name_current[0].name = bpy.context.scene.roma_wall_name_list[0].name
        
    if len(bpy.context.scene.roma_floor_name_current) == 0:
        bpy.context.scene.roma_floor_name_current.add()
        bpy.context.scene.roma_floor_name_current[0].id = 0
        bpy.context.scene.roma_floor_name_current[0].name = bpy.context.scene.roma_floor_name_list[0].name


def get_plot_names_from_list(scene, context):
    items = []
    
    for el in scene.roma_plot_name_list:
        newProp = (el.name, el.name, "")
        items.append(newProp)
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

def get_typology_names_from_list(scene, context):
    items = []
    for el in scene.roma_typology_name_list:
        newProp = (el.name, el.name, "")
        items.append(newProp)
    return items

def get_wall_names_from_list(scene, context):
    items = []
    for el in scene.roma_wall_name_list:
        newProp = (el.name, el.name, "")
        items.append(newProp)
    return items

def get_floor_names_from_list(scene, context):
    items = []
    for el in scene.roma_floor_name_list:
        newProp = (el.name, el.name, "")
        items.append(newProp)
    return items

@persistent
def onFileLoaded(scene):
    initLists()
    initNodes()
    bpy.context.scene.updating_mesh_attributes_is_active = False
    bpy.context.scene.show_selection_overlay_is_active = False
    try:
        bpy.app.handlers.depsgraph_update_pre.remove(onFileLoaded)
    except:
        pass
    
@persistent
def onRegister(scene):
    initLists()
    initNodes()
    try:
        bpy.app.handlers.depsgraph_update_post.remove(onRegister)
    except:
        pass
    
def register():
    bpy.app.handlers.load_post.append(onFileLoaded)
    bpy.app.handlers.depsgraph_update_post.append(onRegister)
    bpy.app.handlers.depsgraph_update_post.append(roma_project_data.update_typology_uses_function)
    bpy.app.handlers.depsgraph_update_post.append(roma_modal_operator.update_mesh_attributes_depsgraph)
    bpy.app.handlers.depsgraph_update_post.append(roma_modal_operator.update_show_overlay)
    
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
     
    bpy.types.VIEW3D_MT_editor_menus.append(roma_menu.roma_menu)
    bpy.types.VIEW3D_MT_mesh_add.append(roma_menu.roma_add_menu_func)
    bpy.types.WindowManager.toggle_show_data = bpy.props.BoolProperty(
                                            default = False,
                                            update = roma_modal_operator.update_show_attributes)
    bpy.types.WindowManager.toggle_plot_name = bpy.props.BoolProperty(
                                            name = "Plot",
                                            default = False)
    bpy.types.WindowManager.toggle_block_name = bpy.props.BoolProperty(
                                            name = "Block",
                                            default = False)
    bpy.types.WindowManager.toggle_typology_name = bpy.props.BoolProperty(
                                            name = "Typology",
                                            default = False)
    bpy.types.WindowManager.toggle_wall_name = bpy.props.BoolProperty(
                                            name = "Type",
                                            default = False)
    bpy.types.WindowManager.toggle_wall_normal = bpy.props.BoolProperty(
                                            name = "Inverted Normals",
                                            default = False)
    bpy.types.WindowManager.toggle_floor_name = bpy.props.BoolProperty(
                                            name = "Type",
                                            default = False)
    bpy.types.WindowManager.toggle_storey_number = bpy.props.BoolProperty(
                                            name = "Number of Storeys",
                                            default = False)
    bpy.types.Object.roma_props = bpy.props.PointerProperty(type=roma_menu.romaAddonProperties)

    Scene.updating_mesh_attributes_is_active = bpy.props.BoolProperty(
                                        name = "update attributes via depsgraph",
                                        default = False
                                        )
    Scene.show_selection_overlay_is_active = bpy.props.BoolProperty(
                                        name = "show selection overlay",
                                        default = False
                                        )
    Scene.attribute_mass_plot_id = bpy.props.IntProperty(
                                        name="Plot Id",
                                        default=0)
    Scene.attribute_mass_block_id = bpy.props.IntProperty(
                                        name="Block Id",
                                        default=0)
    Scene.attribute_mass_typology_id = bpy.props.IntProperty(
                                        name="Typology Id",
                                        default=0,
                                        update = roma_massing.update_attribute_mass_typology_id)
    Scene.attribute_wall_id = bpy.props.IntProperty(
                                        name="Wall Id",
                                        default=0,
                                        update = roma_wall.update_attribute_wall_id)
    Scene.attribute_wall_thickness = bpy.props.FloatProperty(
                                        name = "Wall thickness",
                                        default=0.300,
                                        precision=3
                                        )
    Scene.attribute_wall_offset = bpy.props.FloatProperty(
                                        name = "Wall offset",
                                        default=0,
                                        precision=3
                                        )
    Scene.attribute_wall_normal = bpy.props.BoolProperty(
                                            default = False,
                                            update = roma_wall.update_wall_normal)
    Scene.attribute_floor_id = bpy.props.IntProperty(
                                        name="Floor Id",
                                        default=0,
                                        update = roma_wall.update_attribute_floor_id)
    Scene.attribute_mass_storeys = bpy.props.IntProperty(
                                        name="Number of Storeys",
                                        min=1, 
                                        default=3,
                                        update = roma_massing.update_attribute_mass_storeys)
    # Scene.attribute_obj_option = bpy.props.IntProperty(
    #                                     name="Building option",
    #                                     min=1, 
    #                                     default=1,
    # Scene.attribute_obj_phase = bpy.props.IntProperty(
    #                                     name="Building phase",
    #                                     min=1, 
    #                                     default=1,
    Scene.roma_plot_name_list = bpy.props.CollectionProperty(type = roma_project_data.plot_name_list)
    Scene.roma_plot_name_current = bpy.props.CollectionProperty(type =roma_project_data.name_with_id)
    Scene.roma_plot_name_list_index = bpy.props.IntProperty(name = "Plot Name",
                                             default = 0)
    Scene.roma_plot_names = bpy.props.EnumProperty(
                                        name="Plot names",
                                        description="Current plot name",
                                        items=get_plot_names_from_list,
                                        update=roma_massing.update_plot_name_id)
    
    Scene.roma_block_name_list = bpy.props.CollectionProperty(type = roma_project_data.block_name_list)
    Scene.roma_block_name_current = bpy.props.CollectionProperty(type =roma_project_data.name_with_id)
    Scene.roma_block_name_list_index = bpy.props.IntProperty(name = "Block Name",
                                             default = 0)
    Scene.roma_block_names = bpy.props.EnumProperty(
                                        name="Block names",
                                        description="Current block name ",
                                        items=get_block_names_from_list,
                                        update=roma_massing.update_block_name_id)
    
    Scene.roma_use_name_list = bpy.props.CollectionProperty(type = roma_project_data.use_name_list)

    Scene.roma_typology_name_list = bpy.props.CollectionProperty(type = roma_project_data.typology_name_list)
    Scene.roma_typology_name_current = bpy.props.CollectionProperty(type =roma_project_data.name_with_id)
    Scene.roma_typology_name_list_index = bpy.props.IntProperty(name = "Typology Name",
                                             default = 0)
    Scene.roma_typology_names = bpy.props.EnumProperty(
                                        name="Typology List",
                                        description="",
                                        items=get_typology_names_from_list,
                                        update=roma_massing.update_typology_name_label)
    Scene.roma_typology_uses_name_list = bpy.props.CollectionProperty(type = roma_project_data.typology_uses_name_list)
    Scene.roma_typology_uses_name_list_index = bpy.props.IntProperty(name = "Typology Use Name",
                                             default = 0)
    Scene.roma_previous_selected_typology = bpy.props.IntProperty(
                                        name="Previous Typology Id",
                                        default = -1)
    Scene.roma_typology_uses_name = bpy.props.EnumProperty(
                                        name="",
                                        description="Typology use",
                                        items=get_use_names_from_list,
                                        update=roma_project_data.update_typology_uses_name_label)
    Scene.roma_obj_typology_uses_name_list = bpy.props.CollectionProperty(type = roma_massing.obj_typology_uses_name_list)
    Scene.roma_obj_typology_uses_name_list_index = bpy.props.IntProperty(name = "Typology Use Name of the selected object",
                                             default = 0)
    Scene.roma_wall_name_list = bpy.props.CollectionProperty(type = roma_project_data.wall_name_list)
    Scene.roma_wall_name_current = bpy.props.CollectionProperty(type =roma_project_data.name_with_id)
    Scene.roma_wall_name_list_index = bpy.props.IntProperty(name = "Wall Name",
                                             default = 0)
    Scene.roma_wall_names = bpy.props.EnumProperty(
                                        name="Wall List",
                                        description="",
                                        items=get_wall_names_from_list,
                                        update=roma_wall.update_wall_name_label)
    Scene.roma_floor_name_list = bpy.props.CollectionProperty(type = roma_project_data.floor_name_list)
    Scene.roma_floor_name_current = bpy.props.CollectionProperty(type =roma_project_data.name_with_id)
    Scene.roma_floor_name_list_index = bpy.props.IntProperty(name = "Floor Name",
                                             default = 0)
    Scene.roma_floor_names = bpy.props.EnumProperty(
                                        name="Floor List",
                                        description="",
                                        items=get_floor_names_from_list,
                                        update=roma_wall.update_floor_name_label)

def unregister():
    # bpy.app.handlers.load_post.remove(onFileLoaded)
    bpy.app.handlers.depsgraph_update_post.remove(roma_project_data.update_typology_uses_function)
    bpy.app.handlers.depsgraph_update_post.remove(roma_modal_operator.update_mesh_attributes_depsgraph)
    bpy.app.handlers.depsgraph_update_post.remove(roma_modal_operator.update_show_overlay)
    
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

    bpy.types.VIEW3D_MT_editor_menus.remove(roma_menu.roma_menu)
    bpy.types.VIEW3D_MT_mesh_add.remove(roma_menu.roma_add_menu_func)
    
    del bpy.types.WindowManager.toggle_show_data
    del bpy.types.WindowManager.toggle_plot_name
    del bpy.types.WindowManager.toggle_block_name
    del bpy.types.WindowManager.toggle_typology_name
    del bpy.types.WindowManager.toggle_storey_number
    del bpy.types.WindowManager.toggle_wall_name
    del bpy.types.WindowManager.toggle_wall_normal
    del bpy.types.WindowManager.toggle_floor_name
    del bpy.types.Object.roma_props
    
    del Scene.updating_mesh_attributes_is_active
    del Scene.attribute_mass_plot_id
    del Scene.attribute_mass_block_id
    del Scene.attribute_mass_typology_id
    del Scene.attribute_wall_id
    del Scene.attribute_wall_thickness
    del Scene.attribute_wall_normal
    del Scene.attribute_wall_offset
    del Scene.attribute_floor_id
    del Scene.attribute_mass_storeys

    del Scene.roma_plot_name_list
    del Scene.roma_block_name_list
    del Scene.roma_use_name_list
    del Scene.roma_typology_name_list
    del Scene.roma_obj_typology_uses_name_list
    del Scene.roma_wall_name_list
    del Scene.roma_floor_name_list
    
    del Scene.roma_plot_name_current
    del Scene.roma_block_name_current
    del Scene.roma_typology_name_current
    del Scene.roma_wall_name_current
    del Scene.roma_floor_name_current
    
    del Scene.roma_plot_name_list_index
    del Scene.roma_block_name_list_index
    del Scene.roma_typology_name_list_index
    del Scene.roma_obj_typology_uses_name_list_index
    del Scene.roma_wall_name_list_index
    del Scene.roma_floor_name_list_index
    
    del Scene.roma_plot_names
    del Scene.roma_block_names
    del Scene.roma_typology_uses_name
    del Scene.roma_typology_names
    del Scene.roma_wall_names
    del Scene.roma_floor_names
    
    del Scene.roma_previous_selected_typology
    
    
if __name__ == "__main__":
    register()   
    
    
   
    
