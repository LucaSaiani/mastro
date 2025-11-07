import bpy
import blf
import bmesh
import gpu
import math

from gpu_extras.batch import batch_for_shader
from bpy.app.handlers import persistent
from bpy_extras import view3d_utils
from bpy.types import Operator
from mathutils import Vector

from ...mastro_schedule import MaStro_MathNode, execute_active_node_tree
from ...Nodes.GNodes import mastro_GN_window_info
from ...Utils.read_storey_attribute import read_storey_attribute
from ...Utils.read_use_attribute import read_use_attribute
# from datetime import datetime
# import math

known_scenes = set()

previous_selection = {}

# show the overlays when in edit mode
# class VIEW_3D_OT_show_mastro_overlay(Operator):
#     bl_idname = "wm.show_mastro_overlay"
#     bl_label = "Show MaStro selection"
    
#     _handle = None
    
#     @staticmethod
#     def handle_add(self, context):
#         if VIEW_3D_OT_show_mastro_overlay._handle is None:
#             VIEW_3D_OT_show_mastro_overlay._handle =bpy.types.SpaceView3D.draw_handler_add(draw_callback_selection_overlay,
#                                                                                            (self, context),
#                                                                                            'WINDOW',
#                                                                                            'POST_VIEW')
            
#     @staticmethod
#     def handle_remove(self, context):
#         bpy.types.SpaceView3D.draw_handler_remove(VIEW_3D_OT_show_mastro_overlay._handle, 'WINDOW')
#         VIEW_3D_OT_show_mastro_overlay._handle = None
    
#     def execute(self, context):
#         # if bpy.context.preferences.addons[__package__].preferences.toggleSelectionOverlay:    
#         if bpy.context.window_manager.toggle_show_data_edit_mode:
#             print("miao")
#             self.handle_add(self, context)
#         else:
#             try:
#                 print("bau")
#                 self.handle_remove(self, context)
#             except Exception as e: print(e)
#         return {'FINISHED'}
    
#     def invoke(self, context, event):  # attributes["storey A"][index][1].value = int(list_storey_A)
#         self.execute(context)
#         return {'RUNNING_MODAL'}



# def draw_callback_selection_overlay(self, context):
#     draw_selection_overlay(context)
    
# a function to show block overlays




    
    

 
         

        


    


###############################################################################    
########## Manage all the required updates fired by depsgraph_update  #########
###############################################################################

# when a new scene is created, it is necessary to initialize the
# variables related to the scene
def check_new_scenes():
    from ...Utils.init_lists import init_lists
    global known_scenes
    current_scenes = set(bpy.data.scenes.keys())
    # print("current:")
    # for s in current_scenes: print(s)
    # print()
    new_scenes = current_scenes - known_scenes
    if new_scenes:
        for sceneName in new_scenes:
            print(f"Nuova scena creata: {sceneName}")
            init_lists(sceneName)
        known_scenes = current_scenes
    return()
        
@persistent
def updates(scene, depsgraph):
    ###############################################################################
    # update the values in the UI accordingly with the selected edges or faces ####
    ###############################################################################
    check_new_scenes()
    
    obj = bpy.context.active_object
    if obj:
        if obj is not None and obj.type == "MESH" and "MaStro object" in obj.data:
            #######################################################################
            ############################# MaStro Mass #############################
            #######################################################################
            if "MaStro mass" in obj.data:
                if scene.previous_selection_object_name != obj.name:
                    scene.previous_selection_object_name = obj.name
                    scene.previous_selection_face_id = -1
                    # if obj is not None and obj.type == "MESH" and "MaStro object" in obj.data and "MaStro mass" in obj.data:
                    if obj.mode == "OBJECT":
                        buildingId = obj.mastro_props['mastro_building_attribute']
                        blockId = obj.mastro_props['mastro_block_attribute']
                        
                        building = scene.mastro_building_name_list[buildingId].name
                        block = scene.mastro_block_name_list[blockId].name
                        
                        scene.mastro_building_name_current[0].name = building
                        scene.mastro_block_name_current[0].name = block
                else:
                    # if obj is not None and obj.type == "MESH" and "MaStro object" in obj.data and obj.mode == 'EDIT':
                    if obj.mode == 'EDIT':
                        bm = bmesh.from_edit_mesh(obj.data)
                        bm.edges.ensure_lookup_table()    
                        bm.faces.ensure_lookup_table()     
                        bMesh_storeys = bm.faces.layers.int["mastro_number_of_storeys"]
                        bMesh_storey_list_A = bm.faces.layers.int["mastro_list_storey_A"]
                        bMesh_storey_list_B = bm.faces.layers.int["mastro_list_storey_B"]
                        bMesh_typology = bm.faces.layers.int["mastro_typology_id"]
                        bMesh_wall_type = bm.edges.layers.int["mastro_wall_id"]
                        bMesh_wall_normal = bm.edges.layers.bool["mastro_inverted_normal"]

                        ######################  Edge ########################################
                        if bpy.context.scene.tool_settings.mesh_select_mode[1]:
                            # check if there is an active edge
                            if isinstance(bm.select_history.active, bmesh.types.BMEdge):
                                # active_edge = bm.select_history.active.index
                                # if scene.previous_selection_edge_id != active_edge:
                                #     scene.previous_selection_edge_id = active_edge
                                # else:
                                #     selected_edges = [edge for edge in bm.edges if edge.select]
                                #     if len(selected_edges) > 0:
                                #         for e in selected_edges:
                                #             scene.previous_selection_edge_id = e.index
                                #     else:
                                #         scene.previous_selection_edge_id = -1
                                # if scene.previous_selection_edge_id != -1:
                                #     #updating the information in UI
                                #     bm.edges.ensure_lookup_table()
                                #     wall_type = bm.edges[scene.previous_selection_edge_id][bMesh_wall_type]
                                #     wall_normal = bm.edges[scene.previous_selection_edge_id][bMesh_wall_normal]
                                #     # wall type name
                                #     # since it is possible to sort wall types in the ui, it can be that the index of the element
                                #     # in the list doesn't correspond to wall_id. Therefore it is necessary to find elements
                                #     # in the way below
                                #     item = next(i for i in scene.mastro_wall_name_list if i["id"] == wall_type)
                                #     scene.mastro_wall_name_current[0].name = item.name
                                #     if bpy.context.scene.attribute_wall_normal != wall_normal:
                                #         bpy.context.scene.attribute_wall_normal = wall_normal
                                # bm.edges.ensure_lookup_table()
                                active_edge = bm.select_history.active
                                selected_edges = [edge for edge in bm.edges if edge.select]
                                if scene.previous_selection_edge_id != active_edge.index and scene.previous_selection_edge_id != -1:
                                    scene.previous_selection_edge_id = active_edge.index
                                    wall_type = bm.edges[scene.previous_selection_edge_id][bMesh_wall_type]
                                    wall_normal = bm.edges[scene.previous_selection_edge_id][bMesh_wall_normal]
                                    if len(selected_edges) == 1:
                                        # wall type name
                                        # since it is possible to sort wall types in the ui, it can be that the index of the element
                                        # in the list doesn't correspond to wall_id. Therefore it is necessary to find elements
                                        # in the way below
                                        item = next(i for i in scene.mastro_wall_name_list if i["id"] == wall_type)
                                        scene.mastro_wall_name_current[0].name = item.name
                                        if bpy.context.scene.attribute_wall_normal != wall_normal:
                                            bpy.context.scene.attribute_wall_normal = wall_normal
                                else:
                                    if len(selected_edges) > 0:
                                        # for e in selected_edges:
                                        scene.previous_selection_edge_id = selected_edges[-1].index
                                    else: # no selected edges
                                        scene.previous_selection_edge_id = -1
                                        
                                    
                         
                        ######################  Face  ########################################    
                        if bpy.context.scene.tool_settings.mesh_select_mode[2]:
                            # check if there is an active face
                            if isinstance(bm.select_history.active, bmesh.types.BMFace):
                                # bm.faces.ensure_lookup_table()
                                active_face = bm.select_history.active.index
                                selected_faces = [face for face in bm.faces if face.select]
                            #     if scene.previous_selection_face_id != active_face:
                            #         scene.previous_selection_face_id = active_face
                            # else:
                            #     selected_faces = [face for face in bm.faces if face.select]
                            #     if len(selected_faces) > 0:
                            #         for f in selected_faces:
                            #             scene.previous_selection_face_id = f.index
                            #     else:
                            #         scene.previous_selection_face_id = -1
                            # if scene.previous_selection_face_id != -1:
                                
                                #updating the information in UI
                                if len(selected_faces) == 1:
                                    storeys = bm.faces[active_face][bMesh_storeys]
                                    list_storey_A = bm.faces[active_face][bMesh_storey_list_A]
                                    list_storey_B = bm.faces[active_face][bMesh_storey_list_B]
                                    typology = bm.faces[active_face][bMesh_typology]
                                    
                                    # number of storeys
                                    # if storeys == 0: # in case a new face is created in edit mode, the number of set storeys is 1
                                    #     storeys = 1
                                        # bpy.ops.object.set_face_attribute_storeys
                                    # selected_faces = [face for face in bm.faces if face.select]
                                    # if len(selected_faces) == 1:
                                    if storeys == 0:
                                        storeys = 1
                                        list_storey_A = 10
                                        list_storey_B = 11
                                        typology = 0
                                    if scene.attribute_mass_storeys != storeys:
                                        scene.attribute_mass_storeys = storeys
                                    # if bpy.context.scene.attribute_mass_storeys != storeys:
                                    #     bpy.context.scene.props_mass_storeys._ui_temp_storeys = storeys
                                    # scene["attribute_mass_storeys"] = storeys
                                    
                                    
                                    # typology name
                                    # since it is possible to sort typologies in the ui, it can be that the index of the element
                                    # in the list doesn't correspond to typology_id. Therefore it is necessary to find elements
                                    # in the way below and not with use_list = bpy.context.scene.mastro_typology_name_list[typology_id].useList
                                    item = next(i for i in scene.mastro_typology_name_list if i["id"] == typology)
                                    scene.mastro_typology_name_current[0].name = item.name
                                    # uses related to the typology
                                    usesUiList = bpy.context.scene.mastro_obj_typology_uses_name_list 
                                    # clean the list
                                    while len(usesUiList) > 0:
                                        index = scene.mastro_obj_typology_uses_name_list_index
                                        usesUiList.remove(index)
                                        scene.mastro_obj_typology_uses_name_list_index = min(max(0, index - 1), len(usesUiList) - 1)
                                    # populate the list of uses
                                    use_list = item.useList
                                    list_storey_A = str(list_storey_A)[1:]
                                    list_storey_B = str(list_storey_B)[1:]
                                    list_storey_A = list_storey_A[::-1]
                                    list_storey_B = list_storey_B[::-1]
                                    
                                    useSplit = use_list.split(";") 
                                    for enum, el in enumerate(useSplit):
                                        id = int(el)
                                        usesUiList.add()
                                        usesUiList[enum].id = enum + 1
                                        for use in scene.mastro_use_name_list:
                                            if id == use.id:
                                                usesUiList[enum].name = use.name
                                                usesUiList[enum].nameId = use.id
                                                # when a new face is added in edit mode
                                                # no storeys are assigned to the newly created face
                                                # therefore the system returns an indexError
                                                try:
                                                    storeys = list_storey_A[enum] + list_storey_B[enum]
                                                except IndexError:
                                                    storeys = 1
                                                usesUiList[enum].storeys = int(storeys)     
                                                break
                           
                        bm.free
                        # bpy.data.scenes["Scene"].attribute_mass_storeys = 5 
                        
            #######################################################################
            ############################# MaStro Block #############################
            #######################################################################
                        
            elif "MaStro block" in obj.data:
                if scene.previous_selection_object_name != obj.name:
                    scene.previous_selection_object_name = obj.name
                    # scene.previous_selection_edge_id = -1
                    if obj.mode == "OBJECT":
                        # buildingId = obj.mastro_props['mastro_building_attribute']
                        blockId = obj.mastro_props['mastro_block_attribute']
                        
                        # building = scene.mastro_building_name_list[buildingId].name
                        block = scene.mastro_block_name_list[blockId].name
                        
                        # scene.mastro_building_name_current[0].name = building
                        scene.mastro_block_name_current[0].name = block
                else:
                    # if obj is not None and obj.type == "MESH" and "MaStro object" in obj.data and obj.mode == 'EDIT':
                    if obj.mode == 'EDIT':
                        bm = bmesh.from_edit_mesh(obj.data)
                        bm.verts.ensure_lookup_table()
                        mesh = obj.data  
                        
                        bm.edges.ensure_lookup_table()    
                        bm.faces.ensure_lookup_table()     

                        bMesh_storeys = bm.edges.layers.int["mastro_number_of_storeys_EDGE"]
                        bMesh_storey_list_A = bm.edges.layers.int["mastro_list_storey_A_EDGE"]
                        bMesh_storey_list_B = bm.edges.layers.int["mastro_list_storey_B_EDGE"]
                        
                        bMesh_block_normal = bm.edges.layers.bool["mastro_inverted_normal"]
                        bMesh_block_depth = bm.edges.layers.float["mastro_block_depth"]
                        
                        bMesh_typology = bm.edges.layers.int["mastro_typology_id_EDGE"]
                        bMesh_use_list_A   = bm.edges.layers.int["mastro_list_use_id_A_EDGE"]
                        bMesh_use_list_B   = bm.edges.layers.int["mastro_list_use_id_B_EDGE"]
                        bMesh_height_A     = bm.edges.layers.int["mastro_list_height_A_EDGE"]
                        bMesh_height_B     = bm.edges.layers.int["mastro_list_height_B_EDGE"]
                        bMesh_height_C     = bm.edges.layers.int["mastro_list_height_C_EDGE"]
                        bMesh_height_D     = bm.edges.layers.int["mastro_list_height_D_EDGE"]
                        bMesh_height_E     = bm.edges.layers.int["mastro_list_height_E_EDGE"]
                        bMesh_void         = bm.edges.layers.int["mastro_list_void_EDGE"]
                        
                        bMesh_angle = bm.verts.layers.float["mastro_side_angle"]
                        
                        ######################  Vert ########################################
                        if bpy.context.scene.tool_settings.mesh_select_mode[0]:
                            # check if a new vertex is added, and in case add parameters
                            if isinstance(bm.select_history.active, bmesh.types.BMVert):
                                active_vert = bm.select_history.active
                                angle = bm.verts[active_vert.index][bMesh_angle]
                                number_of_edges = len(bm.edges)
                                # check if a new vertex is selected
                                if scene.previous_selection_vert_id != active_vert.index:
                                    scene.previous_selection_vert_id = active_vert.index
                                    # get how many vertices are selected
                                    selected_verts = [v for v in bm.verts if v.select]
                                    # check if the new vertex is at the end of edge and there is
                                    # only 1 selected vertex, we are in the case of extruded 
                                    # vertex, and therefore it is necessary to add parameters
                                    
                                    if len(selected_verts) == 1 and len(active_vert.link_edges) == 1:
                                        # check it the connected edge has attributes
                                        # bm.edges.ensure_lookup_table()
                                        # bm.verts.ensure_lookup_table()
                                        # active_vert = bm.select_history.active
                                        connected_edge = active_vert.link_edges[0]
                                        storeys = bm.edges[connected_edge.index][bMesh_storeys]
                                        
                                        # if storeys are 0, it is a new edge and data is assigned
                                        if storeys == 0:
                                            # update the typology ------------------------------------------
                                            typology_id = bpy.context.scene.mastro_typology_name_current[0].id
                                            connected_edge[bMesh_typology] = typology_id
                                            
                                            # update the number of storeys ------------------------------------------
                                            data = read_storey_attribute(bpy.context, mesh, connected_edge.index, element_type="EDGE")
                                            connected_edge[bMesh_storeys] = data["numberOfStoreys"]
                                            connected_edge[bMesh_storey_list_A] = int(data["storey_list_A"])
                                            connected_edge[bMesh_storey_list_B] = int(data["storey_list_B"])
                                            
                                            # update the block depth ------------------------------------------
                                            depth = bpy.context.scene.attribute_block_depth
                                            if depth == 0:
                                                depth = 18
                                            connected_edge[bMesh_block_depth] = depth
                                            
                                            # update the uses ------------------------------------------
                                            data = read_use_attribute(bpy.context, typologySet = typology_id)
                                            connected_edge[bMesh_use_list_A] = data["use_id_list_A"]
                                            connected_edge[bMesh_use_list_B] = data["use_id_list_B"]
                                            connected_edge[bMesh_height_A] = data["height_A"]
                                            connected_edge[bMesh_height_B] = data["height_B"]
                                            connected_edge[bMesh_height_C] = data["height_C"]
                                            connected_edge[bMesh_height_D] = data["height_D"]
                                            connected_edge[bMesh_height_E] = data["height_E"]
                                            connected_edge[bMesh_void] = data["void"]
                                            
                                            # update the side angle ------------------------------------
                                            active_vert[bMesh_angle] = 0
                                            bpy.context.scene.attribute_block_side_angle = 0

                                            bmesh.update_edit_mesh(mesh)
                                            
                                # the selected vertices are the same: it mean that the user
                                # has operated something with the vertices
                                else:
                                    # get how many vertices are selected
                                    selected_verts = [v for v in bm.verts if v.select]
                                    if len(selected_verts) == 2:
                                        # bm.edges.ensure_lookup_table()
                                        if scene.previous_edge_number != len(bm.edges):
                                            # an edge has been added with "new edge" operator
                                            if scene.previous_edge_number == len(bm.edges) -1:
                                                # values are copied
                                                # get the id of the newly created edge
                                                last_edge = bm.edges[-1]
                                                # update the typology ------------------------------------------
                                                typology_id = bpy.context.scene.mastro_typology_name_current[0].id
                                                last_edge[bMesh_typology] = typology_id
                                                
                                                # update the number of storeys ------------------------------------------
                                                data = read_storey_attribute(bpy.context, mesh, last_edge.index, element_type="EDGE")
                                                last_edge[bMesh_storeys] = data["numberOfStoreys"]
                                                last_edge[bMesh_storey_list_A] = int(data["storey_list_A"])
                                                last_edge[bMesh_storey_list_B] = int(data["storey_list_B"])
                                                
                                                # update the block depth ------------------------------------------
                                                depth = bpy.context.scene.attribute_block_depth
                                                if depth == 0:
                                                    depth = 18
                                                last_edge[bMesh_block_depth] = depth

                                                # update the uses ------------------------------------------
                                                data = read_use_attribute(bpy.context, typologySet = typology_id)
                                                last_edge[bMesh_use_list_A] = data["use_id_list_A"]
                                                last_edge[bMesh_use_list_B] = data["use_id_list_B"]
                                                last_edge[bMesh_height_A] = data["height_A"]
                                                last_edge[bMesh_height_B] = data["height_B"]
                                                last_edge[bMesh_height_C] = data["height_C"]
                                                last_edge[bMesh_height_D] = data["height_D"]
                                                last_edge[bMesh_height_E] = data["height_E"]
                                                last_edge[bMesh_void] = data["void"]

                                                bmesh.update_edit_mesh(mesh)
                                                
                                scene.previous_edge_number = number_of_edges
                                
                                if len(selected_verts) == 1:
                                    if bpy.context.scene.attribute_block_side_angle != angle:
                                        bpy.context.scene.attribute_block_side_angle = angle   

                        ######################  Edge ########################################
                        if bpy.context.scene.tool_settings.mesh_select_mode[1]:
                            # check if there is an active edge
                            if isinstance(bm.select_history.active, bmesh.types.BMEdge):
                                # bm.edges.ensure_lookup_table()
                                active_edge = bm.select_history.active
                                selected_edges = [edge for edge in bm.edges if edge.select]
                                if scene.previous_selection_edge_id != active_edge.index and scene.previous_selection_edge_id != -1:
                                    scene.previous_selection_edge_id = active_edge.index
                                    #updating the information in UI
                                    storeys = bm.edges[active_edge.index][bMesh_storeys]
                                    list_storey_A = bm.edges[active_edge.index][bMesh_storey_list_A]
                                    list_storey_B = bm.edges[active_edge.index][bMesh_storey_list_B]
                                    typology = bm.edges[active_edge.index][bMesh_typology]
                                    block_depth = bm.edges[active_edge.index][bMesh_block_depth]
                                    block_normal = bm.edges[active_edge.index][bMesh_block_normal]
                                    
                                    # if storeys are 0, it is a new edge and data is assigned
                                    if storeys == 0:
                                        # update the typology ------------------------------------------
                                        typology_id = bpy.context.scene.mastro_typology_name_current[0].id
                                        active_edge[bMesh_typology] = typology_id
                                        
                                        # update the number of storeys ------------------------------------------
                                        data = read_storey_attribute(bpy.context, mesh, active_edge.index, element_type="EGDE")
                                        active_edge[bMesh_storeys] = data["numberOfStoreys"]
                                        active_edge[bMesh_storey_list_A] = int(data["storey_list_A"])
                                        active_edge[bMesh_storey_list_B] = int(data["storey_list_B"])
                                        
                                        # update the block depth ------------------------------------------
                                        depth = bpy.context.scene.attribute_block_depth
                                        if depth == 0:
                                            depth = 18
                                        active_edge[bMesh_block_depth] = depth
                                        
                                        # update typology and related uses ------------------------------------------
                                        data = read_use_attribute(bpy.context, typologySet = typology_id)
                                        active_edge[bMesh_use_list_A] = data["use_id_list_A"]
                                        active_edge[bMesh_use_list_B] = data["use_id_list_B"]
                                        active_edge[bMesh_height_A] = data["height_A"]
                                        active_edge[bMesh_height_B] = data["height_B"]
                                        active_edge[bMesh_height_C] = data["height_C"]
                                        active_edge[bMesh_height_D] = data["height_D"]
                                        active_edge[bMesh_height_E] = data["height_E"]
                                        active_edge[bMesh_void] = data["void"]
                                        
                                        bmesh.update_edit_mesh(mesh)
                                    
                                    if len(selected_edges) == 1:
                                        if bpy.context.scene.attribute_mass_storeys != storeys:
                                            bpy.context.scene.attribute_mass_storeys = storeys
                                    
                                        if bpy.context.scene.attribute_block_depth != block_depth:
                                            bpy.context.scene.attribute_block_depth = block_depth
                                            
                                        if bpy.context.scene.attribute_wall_normal != block_normal:
                                            bpy.context.scene.attribute_wall_normal = block_normal
                                    
                                    # typology name
                                    # since it is possible to sort typologies in the ui, it can be that the index of the element
                                    # in the list doesn't correspond to typology_id. Therefore it is necessary to find elements
                                    # in the way below and not with use_list = bpy.context.scene.mastro_typology_name_list[typology_id].useList
                                    item = next(i for i in scene.mastro_typology_name_list if i["id"] == typology)
                                    scene.mastro_typology_name_current[0].name = item.name
                                    # uses related to the typology
                                    usesUiList = bpy.context.scene.mastro_obj_typology_uses_name_list 
                                    # clean the list
                                    while len(usesUiList) > 0:
                                        index = scene.mastro_obj_typology_uses_name_list_index
                                        usesUiList.remove(index)
                                        scene.mastro_obj_typology_uses_name_list_index = min(max(0, index - 1), len(usesUiList) - 1)
                                    # populate the list of uses
                                    use_list = item.useList
                                    list_storey_A = str(list_storey_A)[1:]
                                    list_storey_B = str(list_storey_B)[1:]
                                    list_storey_A = list_storey_A[::-1]
                                    list_storey_B = list_storey_B[::-1]
                                    
                                    useSplit = use_list.split(";") 
                                    for enum, el in enumerate(useSplit):
                                        id = int(el)
                                        usesUiList.add()
                                        usesUiList[enum].id = enum + 1
                                        for use in scene.mastro_use_name_list:
                                            if id == use.id:
                                                usesUiList[enum].name = use.name
                                                usesUiList[enum].nameId = use.id
                                                # when a new face is added in edit mode
                                                # no storeys are assigned to the newly created face
                                                # therefore the system returns an indexError
                                                try:
                                                    storeys = list_storey_A[enum] + list_storey_B[enum]
                                                except IndexError:
                                                    storeys = 1
                                                usesUiList[enum].storeys = int(storeys)     
                                                break
                                else:
                                    if len(selected_edges) > 0:
                                        # for e in selected_edges:
                                        scene.previous_selection_edge_id = selected_edges[-1].index
                                    else: # no selected edges
                                        scene.previous_selection_edge_id = -1
                                # if scene.previous_selection_edge_id != -1:
                        bm.free
                        
            #######################################################################
            ########################### MaStro Street #############################
            #######################################################################
            elif "MaStro street" in obj.data:
                if obj.mode == 'EDIT':
                    bm = bmesh.from_edit_mesh(obj.data)
                    bMesh_street_type = bm.edges.layers.int["mastro_street_id"]
                    
                    if bpy.context.scene.tool_settings.mesh_select_mode[1]:
                        # check if there is an active edge
                        if isinstance(bm.select_history.active, bmesh.types.BMEdge):
                            active_edge = bm.select_history.active.index
                            if scene.previous_selection_edge_id != active_edge:
                                
                                scene.previous_selection_edge_id = active_edge
                            else:
                                selected_edges = [edge for edge in bm.edges if edge.select]
                                if len(selected_edges) > 0:
                                    for e in selected_edges:
                                        scene.previous_selection_edge_id = e.index
                                else:
                                    scene.previous_selection_edge_id = -1
                            if scene.previous_selection_edge_id != -1:
                                #updating the information in UI
                                bm.edges.ensure_lookup_table()
                                street_type = bm.edges[scene.previous_selection_edge_id][bMesh_street_type]
                                # street type name
                                # since it is possible to sort street types in the ui, it can be that the index of the element
                                # in the list doesn't correspond to street_id. Therefore it is necessary to find elements
                                # in the way below
                                item = next(i for i in scene.mastro_street_name_list if i["id"] == street_type)
                                scene.mastro_street_name_current[0].name = item.name
                    bm.free
                            
                    
                    
    ###############################################################################
    # show graphic overlays #######################################################
    ###############################################################################

    # if scene.show_selection_overlay_is_active != bpy.context.preferences.addons[__package__].preferences.toggleSelectionOverlay:
    #     scene.show_selection_overlay_is_active = bpy.context.preferences.addons[__package__].preferences.toggleSelectionOverlay
    #     bpy.ops.wm.show_mastro_overlay('INVOKE_DEFAULT')
    
    # if bpy.context.window_manager.toggle_show_overlays: 
    #     if scene.show_selection_overlay_is_active != bpy.context.window_manager.toggle_show_data_edit_mode:
    #         scene.show_selection_overlay_is_active = bpy.context.window_manager.toggle_show_data_edit_mode
    #         print("invoco")
    #         bpy.ops.wm.show_mastro_overlay('INVOKE_DEFAULT')
    # else:
    #     scene.show_selection_overlay_is_active = False
     
        
    ######################################################################################################
    # when a typology is selected, it is necessary to update the #########################################
    # uses in the UIList using the ones stored in scene.mastro_typology_uses_name_list ###################
    ######################################################################################################
    if hasattr(scene, "mastro_typology_name_list_index"):
        previous = scene.mastro_previous_selected_typology
        current = scene.mastro_typology_name_list_index
        if previous != current:
            scene.mastro_previous_selected_typology = current
            use_name_list = scene.mastro_typology_uses_name_list
            while len(use_name_list) > 0:
                index = scene.mastro_typology_uses_name_list_index
                use_name_list.remove(index)
                scene.mastro_typology_uses_name_list_index = min(max(0, index - 1), len(use_name_list) - 1)
            # add the uses stored in the typology to the current typology use UIList        
            selected_typology_index = scene.mastro_typology_name_list_index
            if len(scene.mastro_typology_name_list) > 0:
                name_list = scene.mastro_typology_name_list[selected_typology_index].useList    
                split_list = name_list.split(";")
                for el in split_list:
                    if el.strip() != '': # to avoid empty values which could append when the software starts
                        scene.mastro_typology_uses_name_list.add()
                        temp_list = []    
                        temp_list.append(int(el))
                        last = len(scene.mastro_typology_uses_name_list)-1
                        # look for the correspondent use name in mastro_use_name_list
                        for use in scene.mastro_use_name_list:
                            if int(el) == use.id:
                                scene.mastro_typology_uses_name_list[last].id = use.id
                                scene.mastro_typology_uses_name_list[last].name = use.name 
                                break
                            
    ################################################################################################
    # for custom geometry nodes ####################################################################
    ################################################################################################
    # for update in bpy.context.view_layer.depsgraph.updates:
    #     print("cuao")
    #     if isinstance(update.id, bpy.types.Object):
    #         # update the nodes below
    mastro_GN_window_info.update_all()
            # break
    


    ################################################################################################
    # is the selection has changed, some data in the MaStro schedule need to be updated ###########
    ################################################################################################
    # Detect selection changes or added or remove objects
    global previous_selection
    newSelection = False
    current_selection = {obj.name: obj for obj in scene.objects if obj.select_get()}
    if current_selection != previous_selection:
        for obj in current_selection: 
            mesh = bpy.data.objects[obj].data
            if mesh is not None and "MaStro object" in mesh:
                newSelection = True
                break
    previous_selection = current_selection
    
    # this for the new or deleted objects    
    # for update in depsgraph.updates:
    #     if isinstance(update.id, bpy.types.Object):
    #         # newSelection = True
    #         break
        
        
    if newSelection:          
        newSelection = False  
        
        # list of MaStroTreeType
        trees = [x for x in bpy.data.node_groups if x.bl_idname == "MaStroTreeType"]
        if trees:
            for tree in trees:
                nodes = tree.nodes
                if nodes:
                    groupInput = [x for x in nodes if x.bl_idname == "Input MaStro Mesh" or x.bl_idname == "Input MaStro Selected Mesh"]
                    if groupInput:
                        for group in groupInput:
                            group.update_selected_objects()
                        # execute the node tree
                        print(f"updating tree from modalllllllllllllllllllllllllllllllllllllllll")
                        tree.execute()
    
