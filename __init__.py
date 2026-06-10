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

import nodeitems_utils



# bpy must be imported here (not at the top) to ensure Blender's API is ready
import bpy
from bpy.utils import register_class, unregister_class

# to set up __package__ when the extension starts from vs code
IS_VSCODE_DEV = __package__ is not None and __package__.startswith("bl_ext.vscode_development.")
if IS_VSCODE_DEV:
    PREFS_KEY = "bl_ext.vscode_development.mastro"
else:
    PREFS_KEY = __package__

from .UI.properties.properties import register as register_properties, unregister as unregister_properties
from .Handlers import register as register_handlers, unregister as unregister_handlers
from .UI.utils.xy_constraint import register as register_ui_buttons, unregister as unregister_ui_buttons
from .UI.classes import register as register_ui_dynamic_classes, unregister as unregister_ui_dynamic_classes
from .Icons import register as register_icons, unregister as unregister_icons
from .Utils import modules
from .Utils.init_lists import init_lists, init_drawing
from .Utils.init_nodes import init_nodes
from .Handlers.utils.check_new_scenes import known_scenes as knownScenes
from .Keymaps.keymap import register as register_keymaps, unregister as unregister_keymaps
from .Nodes.ui import register as register_gn_ui, unregister as unregister_gn_ui
from .Utils.mastro_layer.sync_layer_slots import sync_layer_slots
from .Utils.add_nodes import add_nodes, add_materials
from .UI.utils.layer_manager_button import draw_layer_manager_header_button, draw_viewlayer_context_panel
from .UI.utils.console_header import draw_console_header_mastro_button
########################################
# from . import Utils
# from . import UI

# from .Nodes.GNodes.mastro_GN_separate_by_wall_type import mastro_GN_separate_by_wall_type
# from bpy.types import(Scene)
from bpy.app.handlers import persistent
import time

# store keymaps here to access after registration
# addon_keymaps = []

# --- View Layer Manager state ---
_lm_original_draw_right = None
_lm_original_viewlayer_draw = None
_lm_last_depsgraph_check = 0.0
_LM_DEPSGRAPH_INTERVAL = 0.3  # seconds between shadow-list name-set checks


@persistent
def _lm_on_depsgraph_update(scene, depsgraph):
    """Sync the active_index to the window's current view layer; throttled shadow-list sync."""
    window = bpy.context.window
    if window and window.scene == scene:
        props = scene.mastro_layer_manager_props
        active_vl_name = window.view_layer.name
        for i, slot in enumerate(props.layer_slots):
            if slot.name == active_vl_name:
                if props.active_index != i:
                    props.active_index = i
                break

    global _lm_last_depsgraph_check
    now = time.time()
    if now - _lm_last_depsgraph_check < _LM_DEPSGRAPH_INTERVAL:
        return
    _lm_last_depsgraph_check = now

    props = scene.mastro_layer_manager_props
    real_names = {vl.name for vl in scene.view_layers}
    slot_names = {s.name for s in props.layer_slots}
    if real_names != slot_names:
        sync_layer_slots(scene)


@persistent
def _lm_on_load_post(filepath):
    """Defer shadow-list sync until bpy.data is fully accessible after file load."""
    def _deferred():
        for scene in bpy.data.scenes:
            sync_layer_slots(scene)
        add_nodes()
        add_materials()
        return None  # one-shot timer
    bpy.app.timers.register(_deferred, first_interval=0.0)


# classes = (
#     # preferences.mastro_addon_preferences,
    
#     # mastro_geometryNodes.VIEW_PT_MaStro_Node_Panel,
#     # mastro_geometryNodes.VIEW_PT_MaStro_GN_Panel,
#     # mastro_geometryNodes.separate_geometry_by_factor_OT,
#     # mastro_geometryNodes.NODE_OT_sticky_note,
#     # mastro_geometryNodes.mastro_CL_Sticky_Note,
        
    

#     mastro_schedule.MaStroTree,
#     mastro_schedule.MaStro_string_item,
#     mastro_schedule.MaStro_keyValueItem,
#     mastro_schedule.MaStro_attribute_collectionItem,
#     mastro_schedule.MaStro_attribute_propertyGroup,
#     mastro_schedule.MaStro_stringCollection_Socket,
#     # mastro_schedule.MaStroTreeNode,
#     # mastro_schedule.MaStroInterfaceSocket,
#     # mastro_schedule.MaStro_attributesCollectionAndFloat_Socket,
#     mastro_schedule.MaStro_attributesCollection_Socket,
#     mastro_schedule.MaStro_data_collectionItem,
#     mastro_schedule.MaStro_data_propertyGroup,
#     mastro_schedule.MaStro_dataCollection_Socket,
#     # mastro_schedule.MaStro_dataOperation_Socket,
#     # mastro_schedule.MaStro_attribute_addItemOperator,
#     # mastro_schedule.MaStro_attribute_removeItemOperator,
#     # mastro_schedule.MaStro_attribute_addKeyValueItemOperator,
#     # mastro_schedule.MaStro_attribute_removeKeyValueItemOperator,
#     # mastro_schedule.MaStro_attribute_deleteItemOperator,
#     mastro_schedule.MaStroGroupInputNode,
#     mastro_schedule.MaStroSelectedInputNode,
#     mastro_schedule.MaStroCaptureAttributeNode,
#     mastro_schedule.MaStroAllAttributesNode,
#     mastro_schedule.MaStroAreaAttributeNode,
#     mastro_schedule.MaStroUseAttributeNode,
#     # mastro_schedule.Mastro_MathSubMenuEntries,
#     mastro_schedule.MaStroIntegerNode,
#     mastro_schedule.MaStroFloatNode,
#     # mastro_schedule.MaStro_MathMenu,
#     # mastro_schedule.MaStro_MathSubMenuFunctions,
#     # mastro_schedule.MaStro_MathSubMenuComparisons,
#     mastro_schedule.MaStro_MathNode,
#     mastro_schedule.MaStro_key_name_list,
#     mastro_schedule.NODE_UL_key_filter,
#     mastro_schedule.NODE_UL_key_filter_NewItem,
#     mastro_schedule.NODE_UL_key_filter_DeleteItem,
#     mastro_schedule.NODE_UL_key_MoveItem,
#     mastro_schedule.MaStroTableNode,
#     # mastro_schedule.MaStroTableByNode,
#     # mastro_schedule.MaStroGetUniqueNode,
#     mastro_schedule.MaStroDataNode,
#     mastro_schedule.MastroDataMathFunction,
   
    
#     # mastro_schedule.MaStroAddColumn,
    
#     # mastro_schedule.MyCustomNode,
#     # mastro_schedule.CustomNodeText,
#     # mastro_schedule.CustomNodeFloat,
#     # mastro_schedule.CustomNodeJoin,
#     # mastro_schedule.CustomNodePrint,
#     mastro_schedule.MaStroViewerNode,
#     # mastro_schedule.MaStroAttributeToColumnNode,
#     # mastro_schedule.MaStro_Schedule_Panel,
 
#     mastro_schedule.NODE_EDITOR_Mastro_Draw_Schedule,
    
    
    
# )

#
@persistent
def onFileLoaded(scene):
    init_lists()
    init_nodes()
    init_drawing(bpy.context.scene)
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
    from .Nodes.operators import classes as nodes_classes
    from .Nodes.ui import classes as ui_classes
    from .Operators import classes as operator_classes
    
    classes = preference_classes + property_classes + handler_classes + nodes_classes + ui_classes + operator_classes

    if (revert):
        return reversed(classes)

    return classes


def _mastro_import_menu(self, context):
    self.layout.operator("object.mastro_import_objects",
                         text="Mastro Objects (.blend)",
                         icon='NONE')


def register():
    ############################################################
    ### register icons ###
    register_icons()
        
    ### register classes ###
    for cls in get_addon_classes():
        register_class(cls)
        
    # for cls in classes:
    #     register_class(cls)
        
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
    bpy.types.TOPBAR_MT_file_import.append(_mastro_import_menu)
        
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
    
      
    # nodeitems_utils.register_node_categories('MASTRO_NODES', mastro_schedule.node_categories)
    
    # Add toggle to both tool header
    # bpy.types.VIEW3D_HT_tool_header.append(mastro_menu.constraint_xy_button)
    # Aggiungi la funzione al pannello nativo
    
    

    
   
  
    
    bpy.app.timers.register(init_lists, first_interval=.1)
    bpy.app.timers.register(init_nodes, first_interval=.1)

    # bpy.app.timers.register(mastro_modal_operator.update_mesh_attributes_depsgraph, first_interval=.1)
    bpy.app.handlers.depsgraph_update_post.append(handlerUpdates)

    ### register handlers (light_source_guard, etc.) ###
    register_handlers()

    # --- View Layer Manager ---
    bpy.app.handlers.depsgraph_update_post.append(_lm_on_depsgraph_update)
    bpy.app.handlers.load_post.append(_lm_on_load_post)

    global _lm_original_draw_right, _lm_original_viewlayer_draw
    _lm_original_draw_right = bpy.types.TOPBAR_HT_upper_bar.draw_right
    bpy.types.TOPBAR_HT_upper_bar.draw_right = draw_layer_manager_header_button

    _lm_original_viewlayer_draw = bpy.types.VIEWLAYER_PT_context_layer.draw
    bpy.types.VIEWLAYER_PT_context_layer.draw = draw_viewlayer_context_panel

    def _lm_initial_sync():
        for scene in bpy.data.scenes:
            sync_layer_slots(scene)
        return None  # one-shot timer
    bpy.app.timers.register(_lm_initial_sync, first_interval=0.0)
   
    # append the print data button to the console header
    bpy.types.CONSOLE_HT_header.append(draw_console_header_mastro_button)
    

def unregister():
    bpy.app.handlers.load_post.remove(onFileLoaded)
    bpy.app.handlers.load_factory_startup_post.remove(onFileDefault)

    
    
    from .Handlers.utils.updates import updates as handlerUpdates
    bpy.app.handlers.depsgraph_update_post.remove(handlerUpdates)

    # --- View Layer Manager ---
    if _lm_on_depsgraph_update in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(_lm_on_depsgraph_update)
    if _lm_on_load_post in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_lm_on_load_post)

    ### unregister handlers (light_source_guard, etc.) ###
    unregister_handlers()

    if _lm_original_draw_right is not None:
        bpy.types.TOPBAR_HT_upper_bar.draw_right = _lm_original_draw_right

    if _lm_original_viewlayer_draw is not None:
        bpy.types.VIEWLAYER_PT_context_layer.draw = _lm_original_viewlayer_draw

    # nodeitems_utils.unregister_node_categories('MASTRO_NODES')

     
    
    
  

    ############################################################
    
    ### unregister shortcuts ###
    unregister_keymaps()
    
    ### unregister UI  buttons
    bpy.types.CONSOLE_HT_header.remove(draw_console_header_mastro_button)
    bpy.types.TOPBAR_MT_file_import.remove(_mastro_import_menu)
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
    
    # for cls in reversed(classes):
    #     unregister_class(cls)
        
    for cls in reversed(get_addon_classes()):
        unregister_class(cls)
        
    ### unregister icons ###
    unregister_icons()
    
   
        
    ############################################################
    
    
    
        
   
    
    
if __name__ == "__main__":
    register()   
    
    
   
    
