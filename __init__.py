# Copyright (C) 2022-2025 Luca Saiani

# luca.saiani@gmail.com

# Created by Luca Saiani
# This is part of MaStro addon for Blender

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

if "bpy" in locals():
    import importlib
    importlib.reload(mastro_preferences),
    importlib.reload(mastro_project_data),
    importlib.reload(mastro_menu),
    # importlib.reload(mastro_keymaps),
    importlib.reload(icons),
    importlib.reload(mastro_xy_constraint_operators),
    importlib.reload(mastro_wall),
    importlib.reload(mastro_street),
    importlib.reload(mastro_massing),
    importlib.reload(mastro_schedule)
    importlib.reload(mastro_modal_operator)
    importlib.reload(mastro_geometryNodes)
else:
    from . import mastro_preferences
    from . import mastro_project_data
    from . import mastro_menu
    # from . import mastro_keymaps
    from . import icons
    from . import mastro_xy_constraint_operators
    from . import mastro_wall
    from . import mastro_street
    from . import mastro_massing
    from . import mastro_schedule
    from . import mastro_modal_operator
    from . import mastro_geometryNodes
    
import bpy
# import bmesh

from bpy.types import(
                        Scene
                        )
import nodeitems_utils
# from nodeitems_utils import NodeCategory, NodeItem

from bpy.app.handlers import persistent

# store keymaps here to access after registration
addon_keymaps = []


classes = (
    mastro_preferences.mastro_addon_preferences,
    
    mastro_geometryNodes.VIEW_PT_MaStro_Node_Panel,
    mastro_geometryNodes.VIEW_PT_MaStro_GN_Panel,
    mastro_geometryNodes.separate_geometry_by_factor_OT,
    mastro_geometryNodes.NODE_OT_sticky_note,
    mastro_geometryNodes.StickyNoteProperties,
        
    mastro_project_data.update_GN_Filter_OT,
    mastro_project_data.update_Shader_Filter_OT,
    # mastro_project_data.separate_geometry_by_factor_OT,
    
    mastro_project_data.VIEW3D_PT_MaStro_project_data,
    mastro_project_data.VIEW3D_PT_MaStro_show_data,
    mastro_project_data.VIEW3D_PT_MaStro_mass_data,
    mastro_project_data.VIEW3D_PT_MaStro_mass_plot_data,
    mastro_project_data.VIEW3D_PT_MaStro_mass_block_data,
    # mastro_project_data.VIEW3D_PT_MaStro_mass_use_data,
    mastro_project_data.VIEW3D_PT_MaStro_mass_typology_data,
    mastro_project_data.VIEW3D_PT_MaStro_street_data,
    
    mastro_project_data.VIEW3D_PT_MaStro_building_data,
    mastro_project_data.VIEW3D_PT_MaStro_building_wall_data,
    mastro_project_data.VIEW3D_PT_MaStro_building_floor_data,
    # mastro_project_data.TEST_OT_modal_operator,
    
    mastro_project_data.name_with_id,
    mastro_project_data.OBJECT_UL_Plot,
    mastro_project_data.plot_name_list,
    mastro_project_data.PLOT_LIST_OT_NewItem,
    mastro_project_data.PLOT_LIST_OT_MoveItem,
    
    mastro_project_data.OBJECT_UL_Block,
    mastro_project_data.block_name_list,
    mastro_project_data.BLOCK_LIST_OT_NewItem,
    mastro_project_data.BLOCK_LIST_OT_MoveItem,
    
    # mastro_project_data.OBJECT_UL_Use,
    mastro_project_data.use_name_list,
    mastro_project_data.USE_LIST_OT_NewItem,
    # mastro_project_data.USE_LIST_OT_MoveItem,
    
    mastro_project_data.OBJECT_UL_Typology,
    mastro_project_data.typology_name_list,
    mastro_project_data.TYPOLOGY_LIST_OT_NewItem,
    mastro_project_data.TYPOLOGY_LIST_OT_MoveItem,
    
    mastro_project_data.OBJECT_UL_Typology_Uses,
    mastro_project_data.typology_uses_name_list,
    mastro_project_data.TYPOLOGY_USES_LIST_OT_NewItem,
    mastro_project_data.TYPOLOGY_LIST_OT_DuplicateItem,
    mastro_project_data.TYPOLOGY_USES_LIST_OT_DeleteItem,
    mastro_project_data.TYPOLOGY_USES_LIST_OT_MoveItem,
    mastro_project_data.OBJECT_OT_update_all_MaStro_meshes_attributes,
    mastro_project_data.OBJECT_OT_update_all_MaStro_street_attributes,

    mastro_project_data.OBJECT_UL_Street,
    mastro_project_data.street_name_list,
    mastro_project_data.STREET_LIST_OT_NewItem,
    mastro_project_data.STREET_LIST_OT_MoveItem,
    
    mastro_project_data.OBJECT_UL_Wall,
    mastro_project_data.wall_name_list,
    mastro_project_data.WALL_LIST_OT_NewItem,
    mastro_project_data.WALL_LIST_OT_MoveItem,
    
    mastro_project_data.OBJECT_UL_Floor,
    mastro_project_data.floor_name_list,
    mastro_project_data.FLOOR_LIST_OT_NewItem,
    mastro_project_data.FLOOR_LIST_OT_MoveItem,
    
    mastro_menu.MaStro_MenuOperator_add_MaStro_mass,
    mastro_menu.MaStro_MenuOperator_add_MaStro_plot,
    mastro_menu.MaStro_MenuOperator_add_MaStro_street,
    mastro_menu.MaStro_MenuOperator_convert_to_MaStro_mass,
    mastro_menu.MaStro_MenuOperator_convert_to_MaStro_street,
    # mastro_menu.MaStro_MenuOperator_PrintData,
    # mastro_menu.MaStro_MenuOperator_ExportCSV,
    mastro_menu.MaStro_Operator_transform_orientation,
    mastro_menu.VIEW3D_PT_transform_orientations,
    # mastro_menu.VIEW3D_MT_orientations_pie,
    # mastro_menu.MaStro_Menu,
    mastro_menu.VIEW3D_PT_MaStro_Panel,
    mastro_menu.mastroAddonProperties,
    mastro_menu.ConstraintXYSettings,
    
    mastro_schedule.MaStroTree,
    mastro_schedule.MaStro_string_item,
    mastro_schedule.MaStro_keyValueItem,
    mastro_schedule.MaStro_attribute_collectionItem,
    mastro_schedule.MaStro_attribute_propertyGroup,
    mastro_schedule.MaStro_stringCollection_Socket,
    # mastro_schedule.MaStroTreeNode,
    # mastro_schedule.MaStroInterfaceSocket,
    # mastro_schedule.MaStro_attributesCollectionAndFloat_Socket,
    mastro_schedule.MaStro_attributesCollection_Socket,
    mastro_schedule.MaStro_data_collectionItem,
    mastro_schedule.MaStro_data_propertyGroup,
    mastro_schedule.MaStro_dataCollection_Socket,
    # mastro_schedule.MaStro_dataOperation_Socket,
    # mastro_schedule.MaStro_attribute_addItemOperator,
    # mastro_schedule.MaStro_attribute_removeItemOperator,
    # mastro_schedule.MaStro_attribute_addKeyValueItemOperator,
    # mastro_schedule.MaStro_attribute_removeKeyValueItemOperator,
    # mastro_schedule.MaStro_attribute_deleteItemOperator,
    mastro_schedule.MaStroGroupInputNode,
    mastro_schedule.MaStroSelectedInputNode,
    mastro_schedule.MaStroCaptureAttributeNode,
    mastro_schedule.MaStroAllAttributesNode,
    mastro_schedule.MaStroAreaAttributeNode,
    mastro_schedule.MaStroUseAttributeNode,
    # mastro_schedule.Mastro_MathSubMenuEntries,
    mastro_schedule.MaStroIntegerNode,
    mastro_schedule.MaStroFloatNode,
    # mastro_schedule.MaStro_MathMenu,
    # mastro_schedule.MaStro_MathSubMenuFunctions,
    # mastro_schedule.MaStro_MathSubMenuComparisons,
    mastro_schedule.MaStro_MathNode,
    mastro_schedule.MaStro_key_name_list,
    mastro_schedule.NODE_UL_key_filter,
    mastro_schedule.NODE_UL_key_filter_NewItem,
    mastro_schedule.NODE_UL_key_filter_DeleteItem,
    mastro_schedule.NODE_UL_key_MoveItem,
    mastro_schedule.MaStroTableNode,
    # mastro_schedule.MaStroTableByNode,
    # mastro_schedule.MaStroGetUniqueNode,
    mastro_schedule.MaStroDataNode,
    mastro_schedule.MastroDataMathFunction,
   
    
    # mastro_schedule.MaStroAddColumn,
    
    # mastro_schedule.MyCustomNode,
    # mastro_schedule.CustomNodeText,
    # mastro_schedule.CustomNodeFloat,
    # mastro_schedule.CustomNodeJoin,
    # mastro_schedule.CustomNodePrint,
    mastro_schedule.MaStroViewerNode,
    # mastro_schedule.MaStroAttributeToColumnNode,
    # mastro_schedule.MaStro_Schedule_Panel,
 
    mastro_schedule.NODE_EDITOR_Mastro_Draw_Schedule,
    
    
    # mastro_vertex.OBJECT_OT_SetVertexAttribute,
    # mastro_vertex.VIEW3D_PT_MaStro_vertex,
    
    # mastro_massing.OBJECT_OT_SetTypologyId,
    mastro_massing.OBJECT_UL_OBJ_Typology_Uses,
    mastro_massing.OBJECT_OT_Set_Face_Attribute_Storeys,
    mastro_massing.OBJECT_OT_Set_Edge_Attribute_Storeys,
    mastro_massing.OBJECT_OT_Set_Face_Attribute_Uses,
    mastro_massing.OBJECT_OT_Set_Edge_Attribute_Uses,
    mastro_massing.OBJECT_OT_Set_Edge_Attribute_Depth,
    mastro_massing.obj_typology_uses_name_list,
    mastro_massing.VIEW3D_PT_MaStro_Mass,
    mastro_massing.VIEW3D_PT_MaStro_Plot,
    
    mastro_modal_operator.VIEW_3D_OT_show_mastro_overlay,
    mastro_modal_operator.VIEW_3D_OT_show_mastro_attributes,
    # mastro_modal_operator.VIEW_3D_OT_update_mesh_attributes,
    # mastro_modal_operator.VIEW_3D_OT_update_all_meshes_attributes,
    # mastro_modal_operator.EventReporter,

    mastro_street.VIEW3D_PT_MaStro_Street,
    mastro_street.OBJECT_OT_SetStreetId,
    
    mastro_wall.OBJECT_OT_SetWallId,
    mastro_wall.OBJECT_OT_SetWallNormal,
    mastro_wall.OBJECT_OT_SetFloorId,
    mastro_wall.VIEW3D_PT_MaStro_Wall,
    
    mastro_xy_constraint_operators.TRANSFORM_OT_translate_xy_constraint,
    mastro_xy_constraint_operators.TRANSFORM_OT_rotate_xy_constraint
)

# MaStroGroupInputNode = mastro_schedule.MaStroGroupInputNode
# MaStroViewerNode = mastro_schedule.MaStroViewerNode
# CustomNodeText = mastro_schedule.CustomNodeText

# MaStroNodeInteger = mastro_schedule.MaStroIntegerNode
# MaStroNodeFloat = mastro_schedule.MaStroFloatNode
# MaStroNodeCaptureAttribute = mastro_schedule.MaStroCaptureAttributeNode
# MaStroNodeMath = mastro_schedule.MaStro_MathNode
# CustomNodeJoin = mastro_schedule.CustomNodeJoin


# MASTRO_NODE_CAPTURE_ATTRIBUTE_HANDLE = 0
# MASTRO_NODE_INTEGER_HANDLE = 1
# MASTRO_NODE_FLOAT_HANDLE = 2

def initNodes():
    bpy.ops.node.separate_geometry_by_factor()
    bpy.ops.node.update_gn_filter(filter_name="use")
    bpy.ops.node.update_gn_filter(filter_name="typology")
    bpy.ops.node.update_gn_filter(filter_name="wall type")
    bpy.ops.node.update_gn_filter(filter_name="street type")
    
    bpy.ops.node.update_shader_filter(filter_name="plot")
    bpy.ops.node.update_shader_filter(filter_name="block")
    bpy.ops.node.update_shader_filter(filter_name="use")
    bpy.ops.node.update_shader_filter(filter_name="typology")

def initLists(scene=None):
    if scene == None:
        s = bpy.context.scene
    else:
        s = bpy.data.scenes[scene]
    # plot name
    name_list = s.mastro_plot_name_list
    name_list_current = s.mastro_plot_name_current
    if len(name_list) == 0:
        name_list.add()
        name_list[0].id = 0
        name_list[0].name = "Plot type... "
    elif not 0 in [elem.id for elem in name_list]:
        name_list.add()
        name_list[-1].id = 0
        name_list[-1].name = "Plot type... "
    if len(name_list_current) == 0:
        name_list_current.add()
        name_list_current[0].id = 0
        name_list_current[0].name = name_list[0].name 
        
    # if len(bpy.context.scene.mastro_plot_name_list) == 0:
    #     bpy.context.scene.mastro_plot_name_list.add()
    #     bpy.context.scene.mastro_plot_name_list[0].id = 0
    #     bpy.context.scene.mastro_plot_name_list[0].name = "Plot name..."
    
    # if len(bpy.context.scene.mastro_plot_name_current) == 0:
    #     bpy.context.scene.mastro_plot_name_current.add()
    #     bpy.context.scene.mastro_plot_name_current[0].id = 0
    #     bpy.context.scene.mastro_plot_name_current[0].name = bpy.context.scene.mastro_plot_name_list[0].name
    
    # block name
    name_list = s.mastro_block_name_list
    name_list_current = s.mastro_block_name_current
    if len(name_list) == 0:
        name_list.add()
        name_list[0].id = 0
        name_list[0].name = "Block name... "
    elif not 0 in [elem.id for elem in name_list]:
        name_list.add()
        name_list[-1].id = 0
        name_list[-1].name = "Block name... "
    if len(name_list_current) == 0:
        name_list_current.add()
        name_list_current[0].id = 0
        name_list_current[0].name = name_list[0].name 
        
    # if len(bpy.context.scene.mastro_block_name_list) == 0:
    #     bpy.context.scene.mastro_block_name_list.add()
    #     bpy.context.scene.mastro_block_name_list[0].id = 0
    #     bpy.context.scene.mastro_block_name_list[0].name = "Block name..."
    
    # if len(bpy.context.scene.mastro_block_name_current) == 0:
    #     bpy.context.scene.mastro_block_name_current.add()
    #     bpy.context.scene.mastro_block_name_current[0].id = 0
    #     bpy.context.scene.mastro_block_name_current[0].name = bpy.context.scene.mastro_block_name_list[0].name
    
    # use
    name_list = s.mastro_use_name_list
    if len(name_list) == 0:
        name_list.add()
        name_list[0].id = 0
        name_list[0].name = "Use name... "
        name_list[0].storeys = 3
        name_list[0].liquid = True
    elif not 0 in [elem.id for elem in name_list]:
        name_list.add()
        name_list[-1].id = 0
        name_list[-1].name = "Use name... "
        name_list[-1].storeys = 3
        name_list[-1].liquid = True
        
    # if len(bpy.context.scene.mastro_use_name_list) == 0:
    #     bpy.context.scene.mastro_use_name_list.add()
    #     bpy.context.scene.mastro_use_name_list[0].id = 0
    #     bpy.context.scene.mastro_use_name_list[0].name = "Use name..."
    #     bpy.context.scene.mastro_use_name_list[0].storeys = 3
    #     bpy.context.scene.mastro_use_name_list[0].liquid = True
    
    # typology
    name_list = s.mastro_typology_name_list
    name_list_current = s.mastro_typology_name_current
    if len(name_list) == 0:
        name_list.add()
        name_list[0].id = 0
        name_list[0].name = "Typology name... "
        name_list[0].useList = "0"
    elif not 0 in [elem.id for elem in name_list]:
        name_list.add()
        name_list[-1].id = 0
        name_list[-1].name = "Typology name... "
        name_list[-1].useList = "0"
    if len(name_list_current) == 0:
        name_list_current.add()
        name_list_current[0].id = 0
        name_list_current[0].name = name_list[0].name 
    
    # if len(bpy.context.scene.mastro_typology_name_list) == 0:
    #     bpy.context.scene.mastro_typology_name_list.add()
    #     bpy.context.scene.mastro_typology_name_list[0].id = 0
    #     bpy.context.scene.mastro_typology_name_list[0].name = "Typology name... "
    #     bpy.context.scene.mastro_typology_name_list[0].useList = "0"
    
    # if len(bpy.context.scene.mastro_typology_name_current) == 0:
    #     bpy.context.scene.mastro_typology_name_current.add()
    #     bpy.context.scene.mastro_typology_name_current[0].id = 0
    #     bpy.context.scene.mastro_typology_name_current[0].name = bpy.context.scene.mastro_typology_name_list[0].name
        
    # typology uses name list
    name_list = s.mastro_typology_uses_name_list
    if len(name_list_current) == 0:
        name_list_current.add()
        name_list_current[0].id = 0
        name_list_current[0].name = s.mastro_use_name_list[0].name
    elif not 0 in [elem.id for elem in name_list]:
        name_list.add()
        name_list[-1].id = 0
        name_list[-1].name = s.mastro_use_name_list[0].name
    
    
    # if len(bpy.context.scene.mastro_typology_uses_name_list) == 0:
    #     bpy.context.scene.mastro_typology_uses_name_list.add()
    #     bpy.context.scene.mastro_typology_uses_name_list[0].id = 0
    #     bpy.context.scene.mastro_typology_uses_name_list[0].name = bpy.context.scene.mastro_use_name_list[0].name
        
    
    # street
    name_list = s.mastro_street_name_list
    name_list_current = s.mastro_street_name_current
    if len(name_list) == 0:
        name_list.add()
        name_list[0].id = 0
        name_list[0].name = "Street type... "
    elif not 0 in [elem.id for elem in name_list]:
        name_list.add()
        name_list[-1].id = 0
        name_list[-1].name = "Street type... "
    if len(name_list_current) == 0:
        name_list_current.add()
        name_list_current[0].id = 0
        name_list_current[0].name = name_list[0].name    
        
    # wall
    name_list = s.mastro_wall_name_list
    name_list_current = s.mastro_wall_name_current
    if len(name_list) == 0:
        name_list.add()
        name_list[0].id = 0
        name_list[0].name = "Wall type... "
        name_list[0].normal = 0
    elif not 0 in [elem.id for elem in name_list]:
        name_list.add()
        name_list[-1].id = 0
        name_list[-1].name = "Wall type... "
        name_list[-1].normal = 0
    if len(name_list_current) == 0:
        name_list_current.add()
        name_list_current[0].id = 0
        name_list_current[0].name = name_list[0].name    
        
    # floor name
    name_list = s.mastro_floor_name_list
    name_list_current = s.mastro_floor_name_current
    if len(name_list) == 0:
        name_list.add()
        name_list[0].id = 0
        name_list[0].name = "Floor type... "
    elif not 0 in [elem.id for elem in name_list]:
        name_list.add()
        name_list[-1].id = 0
        name_list[-1].name = "Floor type... "
    if len(name_list_current) == 0:
        name_list_current.add()
        name_list_current[0].id = 0
        name_list_current[0].name = name_list[0].name 
    
    # if len(bpy.context.scene.mastro_floor_name_list) == 0:
    #     bpy.context.scene.mastro_floor_name_list.add()
    #     bpy.context.scene.mastro_floor_name_list[0].id = 0
    #     bpy.context.scene.mastro_floor_name_list[0].name = "Floor type..."
    
    # if len(bpy.context.scene.mastro_floor_name_current) == 0:
    #     bpy.context.scene.mastro_floor_name_current.add()
    #     bpy.context.scene.mastro_floor_name_current[0].id = 0
    #     bpy.context.scene.mastro_floor_name_current[0].name = bpy.context.scene.mastro_floor_name_list[0].name
        
    # if len(bpy.context.scene.mastro_obj_typology_uses_name_list) == 0:
    #     bpy.context.scene.mastro_obj_typology_uses_name_list.add()
    #     bpy.context.scene.mastro_obj_typology_uses_name_list[0].id = 0
    #     bpy.context.scene.mastro_obj_typology_uses_name_list[0].name =  bpy.context.scene.mastro_use_name_list[0].name
    
    
   
        
    
    
    
        
       
   
   


def get_plot_names_from_list(scene, context):
    items = []
    
    for el in scene.mastro_plot_name_list:
        newProp = (el.name, el.name, "")
        items.append(newProp)
    return items

def get_block_names_from_list(scene, context):
    items = []
    for el in scene.mastro_block_name_list:
        newProp = (el.name, el.name, "")
        items.append(newProp)
    return items

def get_use_names_from_list(scene, context):
    items = []
    for el in scene.mastro_use_name_list:
        newProp = (el.name, el.name, "")
        items.append(newProp)
    items.sort()
    return items

def get_typology_names_from_list(scene, context):
    items = []
    for el in scene.mastro_typology_name_list:
        newProp = (el.name, el.name, "")
        items.append(newProp)
    # items.sort()
    return items

def get_street_names_from_list(scene, context):
    items = []
    for el in scene.mastro_street_name_list:
        newProp = (el.name, el.name, "")
        items.append(newProp)
    return items

def get_wall_names_from_list(scene, context):
    items = []
    for el in scene.mastro_wall_name_list:
        newProp = (el.name, el.name, "")
        items.append(newProp)
    return items

def get_floor_names_from_list(scene, context):
    items = []
    for el in scene.mastro_floor_name_list:
        newProp = (el.name, el.name, "")
        items.append(newProp)
    return items


@persistent
def onFileLoaded(scene):
    initLists()
    initNodes()
    # bpy.context.scene.updating_mesh_attributes_is_active = False
    bpy.context.scene.show_selection_overlay_is_active = False
    bpy.context.scene.previous_selection_object_name = ""
    bpy.context.scene.previous_selection_face_id = -1
    
    mastro_modal_operator.known_scenes.clear()
    mastro_modal_operator.known_scenes.update(bpy.data.scenes.keys())
    
    # bpy.msgbus.subscribe_rna(
    #     key=mastro_project_data.OBJECT_UL_Typology,
    #     owner=MASTRO_TYPOLOGY_NAME_LIST_INDEX_KEY,
    #     args = (),
    #     notify=mastro_project_data.update_uses_uiList,
    #     options={"PERSISTENT",}
    # )
        
    # bpy.msgbus.subscribe_rna(
    #     key=MaStroNodeInteger,
    #     owner=MASTRO_NODE_INTEGER_HANDLE,
    #     args = (),
    #     notify=mastro_schedule.execute_active_node_tree,
    #     options={"PERSISTENT",}
    # )
    
    # bpy.msgbus.subscribe_rna(
    #     key=MaStroNodeFloat,
    #     owner=MASTRO_NODE_FLOAT_HANDLE,
    #     args = (),
    #     notify=mastro_schedule.execute_active_node_tree,
    #     options={"PERSISTENT",}
    # )
   
@persistent
def onFileDefault(scene):
    initLists()
    initNodes()
    bpy.context.scene.show_selection_overlay_is_active = False
    bpy.context.scene.previous_selection_object_name = ""
    bpy.context.scene.previous_selection_face_id = -1
    
    mastro_modal_operator.known_scenes.clear()
    mastro_modal_operator.known_scenes.update(bpy.data.scenes.keys())
    
    # bpy.msgbus.subscribe_rna(
    #     key=mastro_project_data.OBJECT_UL_Typology,
    #     owner=MASTRO_TYPOLOGY_NAME_LIST_INDEX_KEY,
    #     args = (),
    #     notify=mastro_project_data.update_uses_uiList,
    #     options={"PERSISTENT",}
    # )
    
    # bpy.msgbus.subscribe_rna(
    #     key=MaStroNodeCaptureAttribute,
    #     owner=MASTRO_NODE_CAPTURE_ATTRIBUTE_HANDLE,
    #     args = (),
    #     notify=mastro_schedule.execute_active_node_tree,
    #     options={"PERSISTENT",}
    # )
        
    # bpy.msgbus.subscribe_rna(
    #     key=MaStroNodeInteger,
    #     owner=MASTRO_NODE_INTEGER_HANDLE,
    #     args = (),
    #     notify=mastro_schedule.execute_active_node_tree,
    #     options={"PERSISTENT",}
    # )
    
    # bpy.msgbus.subscribe_rna(
    #     key=MaStroNodeFloat,
    #     owner=MASTRO_NODE_FLOAT_HANDLE,
    #     args = (),
    #     notify=mastro_schedule.execute_active_node_tree,
    #     options={"PERSISTENT",}
    # )

# MASTRO_TYPOLOGY_NAME_LIST_INDEX_KEY = 0
    
def register():
    bpy.app.handlers.load_post.append(onFileLoaded)
    bpy.app.handlers.load_factory_startup_post.append(onFileDefault)
    
    # bpy.app.handlers.depsgraph_update_post.append(mastro_project_data.update_typology_uses_function)
    # bpy.app.handlers.depsgraph_update_post.append(mastro_modal_operator.update_mesh_attributes_depsgraph)
    # bpy.app.handlers.depsgraph_update_post.append(mastro_modal_operator.update_show_overlay)
    
    # Register constraint operators
    # mastro_xy_constraint_operators.register()
    
    icons.register()
    
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    
    # Register keymaps
    # mastro_keymaps.register()
    
    # Hack to make sure keymaps register (on restart Blender can sometimes not have access to user keymaps)
    # bpy.app.timers.register(mastro_keymaps.ensure_keymaps, first_interval=2.0)
    
    nodeitems_utils.register_node_categories('MASTRO_NODES', mastro_schedule.node_categories) 
    
    # Add toggle to both tool header
    bpy.types.VIEW3D_HT_tool_header.append(mastro_menu.constraint_xy_button)
    
    # bpy.msgbus.subscribe_rna(
    #     key=mastro_project_data.OBJECT_UL_Typology,
    #     owner=MASTRO_TYPOLOGY_NAME_LIST_INDEX_KEY,
    #     args = (),
    #     notify=mastro_project_data.update_uses_uiList,
    #     options={"PERSISTENT",}
    # )
    # bpy.msgbus.subscribe_rna(
    #     key=MaStroGroupInputNode,
    #     owner=MASTRO_NODE_GROUP_HANDLE,
    #     args = (),
    #     notify=mastro_schedule.execute_active_node_tree,
    #     options={"PERSISTENT",}
    # )
    
    # bpy.msgbus.subscribe_rna(
    #     key=MaStroViewerNode,
    #     owner=MASTRO_VIEWER_HANDLE,
    #     args = (),
    #     notify=mastro_schedule.execute_active_node_tree,
    #     options={"PERSISTENT",}
    # )
    
    
    
    # bpy.msgbus.subscribe_rna(
    #     key=CustomNodeText,
    #     owner=CUSTOM_NODE_TEXT_HANDLE,
    #     args = (),
    #     notify=mastro_schedule.execute_active_node_tree,
    #     options={"PERSISTENT",}
    # )
    
    # bpy.msgbus.subscribe_rna(
    #     key=MaStroNodeCaptureAttribute,
    #     owner=MASTRO_NODE_CAPTURE_ATTRIBUTE_HANDLE,
    #     args = (),
    #     notify=mastro_schedule.execute_active_node_tree,
    #     options={"PERSISTENT",}
    # )
        
    # bpy.msgbus.subscribe_rna(
    #     key=MaStroNodeInteger,
    #     owner=MASTRO_NODE_INTEGER_HANDLE,
    #     args = (),
    #     notify=mastro_schedule.execute_active_node_tree,
    #     options={"PERSISTENT",}
    # )
    # bpy.msgbus.subscribe_rna(
    #     key=MaStroNodeFloat,
    #     owner=MASTRO_NODE_FLOAT_HANDLE,
    #     args = (),
    #     notify=mastro_schedule.execute_active_node_tree,
    #     options={"PERSISTENT",}
    # )
    # bpy.msgbus.subscribe_rna(
    #     key=MaStroNodeMath,
    #     owner=MASTRO_NODE_MATH_HANDLE,
    #     args = (),
    #     notify=mastro_schedule.execute_active_node_tree,
    #     options={"PERSISTENT",}
    # )
    # bpy.msgbus.subscribe_rna(
    #     key=CustomNodeJoin,
    #     owner=CUSTOM_NODE_JOIN_HANDLE,
    #     args = (),
    #     notify=mastro_schedule.execute_active_node_tree,
    #     options={"PERSISTENT",}
    # )
    # bpy.types.Scene.MaStro_math_node_entries = bpy.props.PointerProperty(type=mastro_schedule.Mastro_MathSubMenuEntries)
    
    # bpy.types.VIEW3D_PT_transform_orientations.append(mastro_menu.extend_transform_operation_panel)
    # bpy.types.VIEW3D_MT_editor_menus.append(mastro_menu.mastro_menu)
    bpy.types.VIEW3D_MT_mesh_add.append(mastro_menu.mastro_add_menu_func)
    bpy.types.WindowManager.toggle_show_data = bpy.props.BoolProperty(
                                            default = False,
                                            update = mastro_modal_operator.update_show_attributes)
    bpy.types.WindowManager.toggle_plot_name = bpy.props.BoolProperty(
                                            name = "Plot",
                                            default = False)
    bpy.types.WindowManager.toggle_block_name = bpy.props.BoolProperty(
                                            name = "Block",
                                            default = False)
    bpy.types.WindowManager.toggle_typology_name = bpy.props.BoolProperty(
                                            name = "Typology",
                                            default = False)
    bpy.types.WindowManager.toggle_plot_type = bpy.props.BoolProperty(
                                            name = "Typology",
                                            default = False)
    bpy.types.WindowManager.toggle_wall_type = bpy.props.BoolProperty(
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
    bpy.types.WindowManager.toggle_street_color = bpy.props.BoolProperty(
                                            name = "Type",
                                            default = False)
    bpy.types.WindowManager.toggle_auto_update_mass_data = bpy.props.BoolProperty(
                                            name = "Auto Update Mass Data",
                                            default = True)
                                            # update = mastro_project_data.update_all_mastro_meshes_useList)
                                            
    # bpy.types.WindowManager.toggle_schedule_in_editor = bpy.props.BoolProperty(
    #                                         name = "Show Schedule",
    #                                         default = False,
    #                                         update = mastro_schedule.update_schedule_node_editor)
    
    bpy.types.Object.mastro_props = bpy.props.PointerProperty(type=mastro_menu.mastroAddonProperties)
    bpy.types.Node.sticky_note_props = bpy.props.PointerProperty(type=mastro_geometryNodes.StickyNoteProperties)
    # bpy.types.Scene.mastro_note_text_props = bpy.props.PointerProperty(type=mastro_geometryNodes.MaStroPostItText)
    # bpy.types.Scene.mastro_attribute_collection = bpy.props.PointerProperty(type=mastro_schedule.MaStro_attribute_propertyGroup)

    # Scene.updating_mesh_attributes_is_active = bpy.props.BoolProperty(
    #                                     name = "update attributes via depsgraph",
    #                                     default = False
    #                                     )
    # Scene.update_attributes = bpy.props.IntProperty(
    #                                     name = "Update attributes once faces are selected",
    #                                     default = 0
    #                                     )
    Scene.constraint_xy_setting = bpy.props.PointerProperty(type=mastro_menu.ConstraintXYSettings)
   
    Scene.mastroKeyDictionary = bpy.props.CollectionProperty(type=mastro_schedule.MaStro_string_item)
    Scene.show_selection_overlay_is_active = bpy.props.BoolProperty(
                                        name = "Show selection overlay",
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
                                        default=0)
                                        # update = mastro_massing.update_attributes_mastro_mesh)
    Scene.attribute_street_id = bpy.props.IntProperty(
                                        name="Street Id",
                                        default=0,
                                        #update = mastro_street.update_attribute_street_id
                                        )
    Scene.attribute_street_width = bpy.props.FloatProperty(
                                        name = "Street width",
                                        default=8,
                                        precision=3
                                        )
    Scene.attribute_street_radius = bpy.props.FloatProperty(
                                        name = "Street radius",
                                        default=18,
                                        precision=3
                                        )
    Scene.attribute_wall_id = bpy.props.IntProperty(
                                        name="Wall Id",
                                        default=0,
                                        update = mastro_wall.update_attribute_wall_id)
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
                                            update = mastro_wall.update_wall_normal)
    Scene.attribute_floor_id = bpy.props.IntProperty(
                                        name="Floor Id",
                                        default=0,
                                        update = mastro_wall.update_attribute_floor_id)
    Scene.attribute_mass_storeys = bpy.props.IntProperty(
                                        name="Number of Storeys",
                                        min=1, 
                                        default=3,
                                        update = mastro_massing.update_attributes_mastro_mesh_storeys)
    Scene.attribute_plot_depth = bpy.props.FloatProperty(
                                        name="The depth of the building",
                                        min=0, 
                                        default=18,
                                        update = mastro_massing.update_attributes_mastro_plot_depth)
    
    # Scene.mouse_keyboard_event = bpy.props.StringProperty(
    #                                     name="Mouse and keyboard event"
    #                             )
    # Scene.attribute_obj_option = bpy.props.IntProperty(
    #                                     name="Building option",
    #                                     min=1, 
    #                                     default=1,
    # Scene.attribute_obj_phase = bpy.props.IntProperty(
    #                                     name="Building phase",
    #                                     min=1, 
    #                                     default=1,
    
    Scene.geometryMenuSwitch  = bpy.props.EnumProperty(
                                                items = (
                                                        ("POINT", "Point", ""),
                                                        ("EDGE", "Edge", ""),
                                                        ("FACE", "Face", ""),
                                                        ),
                                                default = "EDGE",
                                                update=mastro_geometryNodes.updateGroup)
    
    Scene.mastro_group_node_number_of_split = bpy.props.IntProperty(name = "Number of split",
                                             default = 1,
                                             min = 1,
                                             update=mastro_geometryNodes.updateGroup)
    
    Scene.previous_selection_object_name = bpy.props.StringProperty(
                                    name="Previously selected object name",
                                    default = "",
                                    description="Store the name of the previous selected object"
                                    )
    Scene.previous_selection_face_id = bpy.props.IntProperty(
                                    name="Previously selected face Id",
                                    default = -1,
                                    description="Store the id of the previous selected face"
                                    )
    Scene.previous_selection_edge_id = bpy.props.IntProperty(
                                    name="Previously selected edge Id",
                                    default = -1,
                                    description="Store the id of the previous selected edge"
                                    )
    Scene.previous_selection_vert_id = bpy.props.IntProperty(
                                    name="Previously selected vert Id",
                                    default = -1,
                                    description="Store the id of the previous selected vertex"
                                    )
    Scene.previous_edge_number = bpy.props.IntProperty(
                                    name="Previously number of edges",
                                    default = -1,
                                    description="Store the number of edges of the previous selection"
                                    )                                          
    Scene.mastro_plot_name_list = bpy.props.CollectionProperty(type = mastro_project_data.plot_name_list)
    Scene.mastro_plot_name_current = bpy.props.CollectionProperty(type =mastro_project_data.name_with_id)
    Scene.mastro_plot_name_list_index = bpy.props.IntProperty(name = "Plot Name",
                                             default = 0)
    Scene.mastro_plot_names = bpy.props.EnumProperty(
                                        name="Plot names",
                                        description="Current plot name",
                                        items=get_plot_names_from_list,
                                        update=mastro_massing.update_plot_name_id)
    
    Scene.mastro_block_name_list = bpy.props.CollectionProperty(type = mastro_project_data.block_name_list)
    Scene.mastro_block_name_current = bpy.props.CollectionProperty(type =mastro_project_data.name_with_id)
    Scene.mastro_block_name_list_index = bpy.props.IntProperty(name = "Block Name",
                                             default = 0)
    Scene.mastro_block_names = bpy.props.EnumProperty(
                                        name="Block names",
                                        description="Current block name ",
                                        items=get_block_names_from_list,
                                        update=mastro_massing.update_block_name_id)
    
    Scene.mastro_use_name_list = bpy.props.CollectionProperty(type = mastro_project_data.use_name_list)

    Scene.mastro_typology_name_list = bpy.props.CollectionProperty(type = mastro_project_data.typology_name_list)
    Scene.mastro_typology_name_current = bpy.props.CollectionProperty(type =mastro_project_data.name_with_id)
    Scene.mastro_typology_name_list_index = bpy.props.IntProperty(name = "Typology Name",
                                             default = 0)
    Scene.mastro_typology_names = bpy.props.EnumProperty(
                                        name="Typology List",
                                        items=get_typology_names_from_list,
                                        update=mastro_massing.update_attributes_mastro_mesh_typology)
    Scene.mastro_typology_uses_name_list = bpy.props.CollectionProperty(type = mastro_project_data.typology_uses_name_list)
    Scene.mastro_typology_uses_name_list_index = bpy.props.IntProperty(name = "Typology Use Name",
                                             default = 0)
    Scene.mastro_previous_selected_typology = bpy.props.IntProperty(
                                        name="Previous Typology Id",
                                        default = -1)
    Scene.mastro_typology_uses_name = bpy.props.EnumProperty(
                                        name="Typology uses drop down menu",
                                        description="Typology use drop down list in the Typology Uses UI",
                                        items=get_use_names_from_list,
                                        update=mastro_project_data.update_typology_uses_name_label)
    Scene.mastro_obj_typology_uses_name_list = bpy.props.CollectionProperty(type = mastro_massing.obj_typology_uses_name_list)
    Scene.mastro_obj_typology_uses_name_list_index = bpy.props.IntProperty(name = "Typology Use Name of the selected object",
                                             default = 0)
    
    Scene.mastro_street_name_list = bpy.props.CollectionProperty(type = mastro_project_data.street_name_list)
    Scene.mastro_street_name_current = bpy.props.CollectionProperty(type =mastro_project_data.name_with_id)
    Scene.mastro_street_name_list_index = bpy.props.IntProperty(name = "Street Name",
                                             default = 0)
    Scene.mastro_street_names = bpy.props.EnumProperty(
                                        name="Street List",
                                        description="",
                                        items=get_street_names_from_list,
                                        update=mastro_street.update_attributes_street
                                        )
    
    Scene.mastro_wall_name_list = bpy.props.CollectionProperty(type = mastro_project_data.wall_name_list)
    Scene.mastro_wall_name_current = bpy.props.CollectionProperty(type =mastro_project_data.name_with_id)
    Scene.mastro_wall_name_list_index = bpy.props.IntProperty(name = "Wall Name",
                                             default = 0)
    Scene.mastro_wall_names = bpy.props.EnumProperty(
                                        name="Wall List",
                                        description="",
                                        items=get_wall_names_from_list,
                                        update=mastro_wall.update_attributes_wall
                                        )
    
    Scene.mastro_floor_name_list = bpy.props.CollectionProperty(type = mastro_project_data.floor_name_list)
    Scene.mastro_floor_name_current = bpy.props.CollectionProperty(type =mastro_project_data.name_with_id)
    Scene.mastro_floor_name_list_index = bpy.props.IntProperty(name = "Floor Name",
                                             default = 0)
    Scene.mastro_floor_names = bpy.props.EnumProperty(
                                        name="Floor List",
                                        description="",
                                        items=get_floor_names_from_list,
                                        # update=mastro_wall.update_floor_name_label
                                        )
   
  
    
    bpy.app.timers.register(initLists, first_interval=.1)
    bpy.app.timers.register(initNodes, first_interval=.1)
    # bpy.app.timers.register(mastro_modal_operator.update_mesh_attributes_depsgraph, first_interval=.1)
    bpy.app.handlers.depsgraph_update_post.append(mastro_modal_operator.updates)
    
    # handle the keymap
    wm = bpy.context.window_manager
    # Note that in background mode (no GUI available), keyconfigs are not available either,
    # so we have to check this to avoid nasty errors in background case.
    kc = wm.keyconfigs.addon
    if kc:
        km = wm.keyconfigs.addon.keymaps.new(name='Object Mode', space_type='EMPTY')
        kmi = km.keymap_items.new(mastro_xy_constraint_operators.TRANSFORM_OT_translate_xy_constraint.bl_idname, 'G', 'PRESS', ctrl=False, shift=False)
        addon_keymaps.append((km, kmi))
        
        kmi = km.keymap_items.new(mastro_xy_constraint_operators.TRANSFORM_OT_rotate_xy_constraint.bl_idname, 'R', 'PRESS', ctrl=False, shift=False)
        addon_keymaps.append((km, kmi))
        
        km = wm.keyconfigs.addon.keymaps.new(name='Mesh', space_type='EMPTY')
        kmi = km.keymap_items.new(mastro_xy_constraint_operators.TRANSFORM_OT_translate_xy_constraint.bl_idname, 'G', 'PRESS', ctrl=False, shift=False)
        addon_keymaps.append((km, kmi))
        
        kmi = km.keymap_items.new(mastro_xy_constraint_operators.TRANSFORM_OT_rotate_xy_constraint.bl_idname, 'R', 'PRESS', ctrl=False, shift=False)
        addon_keymaps.append((km, kmi))
    

def unregister():
    bpy.app.handlers.load_post.remove(onFileLoaded)
    bpy.app.handlers.load_factory_startup_post.remove(onFileDefault)
    bpy.app.handlers.depsgraph_update_post.remove(mastro_modal_operator.updates)
    
    # Unregister constraint operators
    # mastro_xy_constraint_operators.unregister()
    
    
    # bpy.app.handlers.depsgraph_update_post.remove(mastro_project_data.update_typology_uses_function)
    # bpy.app.handlers.depsgraph_update_post.remove(mastro_modal_operator.update_mesh_attributes_depsgraph)
    # bpy.app.handlers.depsgraph_update_post.remove(mastro_modal_operator.update_show_overlay)
    

    # bpy.msgbus.clear_by_owner(MASTRO_TYPOLOGY_NAME_LIST_INDEX_KEY)
    # bpy.msgbus.clear_by_owner(MASTRO_NODE_INTEGER_HANDLE)
    # bpy.msgbus.clear_by_owner(MASTRO_NODE_FLOAT_HANDLE)
    
    nodeitems_utils.unregister_node_categories('MASTRO_NODES')

    # bpy.types.VIEW3D_PT_transform_orientations.remove(mastro_menu.extend_transform_operation_panel)
    # bpy.types.VIEW3D_MT_editor_menus.remove(mastro_menu.mastro_menu)
    bpy.types.VIEW3D_MT_mesh_add.remove(mastro_menu.mastro_add_menu_func)
    
    bpy.types.VIEW3D_HT_tool_header.remove(mastro_menu.constraint_xy_button)
    
    # del bpy.types.Scene.MaStro_math_node_entries
    # del bpy.types.Scene.MaStroAttributes
    del bpy.types.WindowManager.toggle_show_data
    del bpy.types.WindowManager.toggle_plot_name
    del bpy.types.WindowManager.toggle_block_name
    del bpy.types.WindowManager.toggle_typology_name
    del bpy.types.WindowManager.toggle_storey_number
    del bpy.types.WindowManager.toggle_wall_type
    del bpy.types.WindowManager.toggle_wall_normal
    del bpy.types.WindowManager.toggle_floor_name
    del bpy.types.WindowManager.toggle_auto_update_mass_data
    # del bpy.types.WindowManager.toggle_schedule_in_editor
    del bpy.types.Object.mastro_props
    del bpy.types.Node.sticky_note_props
    
    del Scene.mastroKeyDictionary
    del Scene.constraint_xy_setting
    # del Scene.updating_mesh_attributes_is_active
    del Scene.attribute_mass_plot_id
    del Scene.attribute_mass_block_id
    del Scene.attribute_mass_typology_id
    del Scene.attribute_wall_id
    del Scene.attribute_wall_thickness
    del Scene.attribute_wall_normal
    del Scene.attribute_wall_offset
    del Scene.attribute_floor_id
    del Scene.attribute_mass_storeys
    del Scene.attribute_plot_depth
    # del Scene.mastro_attribute_collection
    # del Scene.update_attributes
    # del Scene.mouse_keyboard_event
    
    del Scene.geometryMenuSwitch

    del Scene.previous_selection_object_name
    del Scene.previous_selection_face_id
    del Scene.previous_selection_edge_id
    del Scene.previous_selection_vert_id
    del Scene.previous_edge_number
    
    del Scene.mastro_plot_name_list
    del Scene.mastro_block_name_list
    del Scene.mastro_use_name_list
    del Scene.mastro_typology_name_list
    del Scene.mastro_obj_typology_uses_name_list
    del Scene.mastro_wall_name_list
    del Scene.mastro_floor_name_list
    
    del Scene.mastro_plot_name_current
    del Scene.mastro_block_name_current
    del Scene.mastro_typology_name_current
    del Scene.mastro_wall_name_current
    del Scene.mastro_floor_name_current
    
    del Scene.mastro_plot_name_list_index
    del Scene.mastro_block_name_list_index
    del Scene.mastro_typology_name_list_index
    del Scene.mastro_obj_typology_uses_name_list_index
    del Scene.mastro_wall_name_list_index
    del Scene.mastro_floor_name_list_index
    
    del Scene.mastro_plot_names
    del Scene.mastro_block_names
    del Scene.mastro_typology_uses_name
    del Scene.mastro_typology_names
    del Scene.mastro_wall_names
    del Scene.mastro_floor_names
    
    del Scene.mastro_previous_selected_typology
    
    del Scene.mastro_group_node_number_of_split
    
    
    
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
        
    # Unregister keymaps
    # mastro_keymaps.unregister()
    
    icons.unregister()
    
        
   
    
    
if __name__ == "__main__":
    register()   
    
    
   
    
