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
    # importlib.reload(preferences),
    # importlib.reload(mastro_project_data),
    # importlib.reload(mastro_menu),
    # importlib.reload(mastro_keymaps),
    # importlib.reload(Icons),
    # importlib.reload(mastro_xy_constraint_operators),
    # importlib.reload(mastro_wall),
    # importlib.reload(mastro_street),
    # importlib.reload(mastro_massing),
    importlib.reload(mastro_schedule)
    # importlib.reload(mastro_modal_operator)
    importlib.reload(mastro_geometryNodes)
else:
    
    
    
    
    # from .UI.classes import preferences
    # from . import mastro_project_data
    # from . import mastro_menu
    # from . import mastro_keymaps
    # from . import Icons
    # from . import mastro_xy_constraint_operators
    # from . import mastro_wall
    # from . import mastro_street
    # from . import mastro_massing
    from . import mastro_schedule
    # from . import mastro_modal_operator
    from . import mastro_geometryNodes
    

import nodeitems_utils



#### IMPORT DA TENERE ASSOLUTAMENTE ####
import bpy
from bpy.utils import register_class, unregister_class

# to set up __package__ when the extension starts from vs code
IS_VSCODE_DEV = __package__ is not None and __package__.startswith("bl_ext.vscode_development.")
if IS_VSCODE_DEV:
    PREFS_KEY = "bl_ext.vscode_development.mastro"
else:
    PREFS_KEY = __package__

from .UI.properties.properties import register as register_properties, unregister as unregister_properties
from .UI.utils.xy_constraint import register as register_ui_buttons, unregister as unregister_ui_buttons
from .UI.classes import register as register_ui_dynamic_classes, unregister as unregister_ui_dynamic_classes
from .Icons import register as register_icons, unregister as unregister_icons
from .Utils import modules
from .Utils.init_lists import init_lists
from .Utils.init_nodes import init_nodes
from .Handlers.utils.check_new_scenes import known_scenes as knownScenes
from .Keymaps.keymap import register as register_keymaps, unregister as unregister_keymaps
from .Nodes.ui import register as register_gn_ui, unregister as unregister_gn_ui
  
########################################
# from . import Utils
# from . import UI

# from .Nodes.GNodes.mastro_GN_separate_by_wall_type import mastro_GN_separate_by_wall_type
# from bpy.types import(Scene)
from bpy.app.handlers import persistent
import math

# store keymaps here to access after registration
# addon_keymaps = []


classes = (
    # preferences.mastro_addon_preferences,
    
    mastro_geometryNodes.VIEW_PT_MaStro_Node_Panel,
    mastro_geometryNodes.VIEW_PT_MaStro_GN_Panel,
    mastro_geometryNodes.separate_geometry_by_factor_OT,
    mastro_geometryNodes.NODE_OT_sticky_note,
    mastro_geometryNodes.StickyNoteProperties,
        
    

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
    
    
    
)

#
@persistent
def onFileLoaded(scene):
    init_lists()
    init_nodes()
    # bpy.context.scene.updating_mesh_attributes_is_active = False
    # bpy.context.scene.show_selection_overlay_is_active = False
    # bpy.context.scene.mastro_previous_selection_object_name = ""
    # bpy.context.scene.mastro_previous_selection_face_id = -1
    
    
    knownScenes.clear()
    knownScenes.update(bpy.data.scenes.keys())
    
  
   
@persistent
def onFileDefault(scene):
    init_lists()
    init_nodes()
    # bpy.context.scene.show_selection_overlay_is_active = False
    # bpy.context.scene.mastro_previous_selection_object_name = ""
    # bpy.context.scene.mastro_previous_selection_face_id = -1
    
    
    knownScenes.clear()
    knownScenes.update(bpy.data.scenes.keys())
    
    


def get_addon_classes(revert=False):
    from .UI.classes import classes as preference_classes
    from .UI.properties import classes as property_classes
    from .Handlers.classes import classes as handler_classes
    from .Nodes.GNodes import classes as nodes_classes
    from .Nodes.ui import classes as ui_classes
    from .Operators import classes as operator_classes
    from .Keymaps import classes as keymap_classes
    
    classes = preference_classes + property_classes + handler_classes + nodes_classes + ui_classes + operator_classes + keymap_classes

    if (revert):
        return reversed(classes)

    return classes

    
def register():
    ############################################################
    ### register icons ###
    register_icons()
        
    ### register classes ###
    for cls in get_addon_classes():
        register_class(cls)
        
    for cls in classes:
        register_class(cls)
        
    register_ui_dynamic_classes()
        
    ### register properties ###
    register_properties()
        
    ### register modules ###
    for mod in modules:
        if hasattr(mod, "register"):
            mod.register()
    
    ### register nodes UI ###
    register_gn_ui()
    
    ### register UI  buttons
    register_ui_buttons()
        
    ### register shortcuts ###
    register_keymaps()
    
    ############################################################
            
    # from .GNodes.customnodes import load_properties
    # load_properties()

        
    # from .Handlers.classes.showAttributes import update_show_attributes as updateShowAttibutes
    from .Handlers.utils.updates import updates as handlerUpdates

    # from . import mastro_modal_operator

        
    bpy.app.handlers.load_post.append(onFileLoaded)
    bpy.app.handlers.load_factory_startup_post.append(onFileDefault)
    
      
    nodeitems_utils.register_node_categories('MASTRO_NODES', mastro_schedule.node_categories) 
    
    # Add toggle to both tool header
    # bpy.types.VIEW3D_HT_tool_header.append(mastro_menu.constraint_xy_button)
    # Aggiungi la funzione al pannello nativo
    
    

    
   
  
    
    bpy.app.timers.register(init_lists, first_interval=.1)
    bpy.app.timers.register(init_nodes, first_interval=.1)
    
    
    # bpy.app.timers.register(mastro_modal_operator.update_mesh_attributes_depsgraph, first_interval=.1)
    bpy.app.handlers.depsgraph_update_post.append(handlerUpdates)
   
    
    

def unregister():
    bpy.app.handlers.load_post.remove(onFileLoaded)
    bpy.app.handlers.load_factory_startup_post.remove(onFileDefault)
    
    from .Handlers.utils.updates import updates as handlerUpdates

    bpy.app.handlers.depsgraph_update_post.remove(handlerUpdates)
    
       
    nodeitems_utils.unregister_node_categories('MASTRO_NODES')

     
    
    
  

    ############################################################
    
    ### unregister shortcuts ###
    unregister_keymaps()
    
    ### unregister UI  buttons
    unregister_ui_buttons()
   
    ### unregister nodes UI ###
    unregister_gn_ui()
    
    ### unregister modules ###            
    for mod in reversed(modules):
        if hasattr(mod, "register"):
            mod.unregister()
            
    ### unregister properties ###
    unregister_properties()
    
    ### unregister classes ###            
    unregister_ui_dynamic_classes()
    
    for cls in reversed(classes):
        unregister_class(cls)
        
    for cls in reversed(get_addon_classes()):
        unregister_class(cls)
        
    ### unregister icons ###
    unregister_icons()
    
   
        
    ############################################################
    
    
    
        
   
    
    
if __name__ == "__main__":
    register()   
    
    
   
    
