# Copyright (C) 2022-2024 Luca Saiani

# luca.saiani@gmail.com

# Created by Luca Saiani
# This is part of RoMa addon for Blender

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

import bpy
import blf
import bmesh
import gpu
from gpu_extras.batch import batch_for_shader

from bpy.app.handlers import persistent
from bpy_extras import view3d_utils
from bpy.types import Operator

from mathutils import Vector

from .roma_schedule import RoMaMathNode, execute_active_node_tree
# from datetime import datetime
# import math

class VIEW_3D_OT_show_roma_overlay(Operator):
    bl_idname = "wm.show_roma_overlay"
    bl_label = "Show RoMa selection"
    
    _handle = None
    
    @staticmethod
    def handle_add(self, context):
        if VIEW_3D_OT_show_roma_overlay._handle is None:
            VIEW_3D_OT_show_roma_overlay._handle =bpy.types.SpaceView3D.draw_handler_add(draw_callback_selection_overlay,
                                                                                           (self, context),
                                                                                           'WINDOW',
                                                                                           'POST_VIEW')
            
    @staticmethod
    def handle_remove(self, context):
        bpy.types.SpaceView3D.draw_handler_remove(VIEW_3D_OT_show_roma_overlay._handle, 'WINDOW')
        VIEW_3D_OT_show_roma_overlay._handle = None
    
    def execute(self, context):
        if bpy.context.preferences.addons['roma'].preferences.toggleSelectionOverlay:    
            self.handle_add(self, context)
        else:
            self.handle_remove(self, context)
        return {'FINISHED'}
    
    def invoke(self, context, event):  # attributes["storey A"][index][1].value = int(list_storey_A)
      
        
        self.execute(context)
        return {'RUNNING_MODAL'}

def draw_selection_overlay(context):
    obj = bpy.context.active_object
    if hasattr(obj, "data") and "RoMa object" in obj.data:
        coords = []
        edgeIndices = []
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        
        
        mesh = obj.data
        
        if mesh.is_editmode:
            bm = bmesh.from_edit_mesh(mesh)
        # else:
        #     bm = bmesh.new()
        #     bm.from_mesh(mesh)
            
            # draw the edges of the selected object
            for vert in bm.verts:
                # print(vert.index, vert.co, obj.matrix_world @ vert.co)
                coords.append(obj.matrix_world @ vert.co)
                
            for edge in bm.edges:
                tmpEdge = (edge.verts[0].index, edge.verts[1].index)
                edgeIndices.append(tmpEdge)
                
            
            batch = batch_for_shader(shader, 'LINES', {"pos": coords}, indices=edgeIndices)
            r, g, b, a = [c for c in bpy.context.preferences.addons['roma'].preferences.edgeColor]
            shader.uniform_float("color", (r, g, b, a))
        
            gpu.state.line_width_set(bpy.context.preferences.addons['roma'].preferences.edgeSize)
            gpu.state.blend_set("ALPHA")
            batch.draw(shader)
            
            
            # draw the selected faces
            faces = [f for f in bm.faces if f.select == True]
            
            # create a new Bmesh with only the newly created faces
            dbm = bmesh.new()
            for face in faces:
                dbm.faces.new((dbm.verts.new(obj.matrix_world @ v.co, v) for v in face.verts), face)
            dbm.verts.index_update()    

            dVertices = [v.co for v in dbm.verts]
            dFaceindices = [(loop.vert.index for loop in looptris) for looptris in dbm.calc_loop_triangles()]
            # dEdgeindices = [(v.index for v in e.verts) for e in dbm.edges]
            batch = batch_for_shader(shader, 'TRIS', {"pos": dVertices}, indices=dFaceindices)
            r, g, b, a = [c for c in bpy.context.preferences.addons['roma'].preferences.faceColor]
            shader.uniform_float("color", (r, g, b, a))       
            # gpu.state.blend_set("NONE")
            batch.draw(shader)
            
            dbm.free()
            bm.free()
    
def draw_callback_selection_overlay(self, context):
    draw_selection_overlay(context)

# def roma_selection_overlay(self, context):
#     bpy.ops.wm.show_roma_overlay()
    
# @persistent
# def update_show_overlay(scene, context):
#     if scene.show_selection_overlay_is_active != bpy.context.preferences.addons['roma'].preferences.toggleSelectionOverlay:
#         scene.show_selection_overlay_is_active = bpy.context.preferences.addons['roma'].preferences.toggleSelectionOverlay
#         bpy.ops.wm.show_roma_overlay('INVOKE_DEFAULT')
    
# @persistent
# def reportEvent():
#     bpy.ops.wm.mouse_keyboard_event('INVOKE_DEFAULT')
    
# '''An operator to report the mouse or keyboard event'''
# class EventReporter(Operator):
#     bl_idname = "wm.mouse_keyboard_event"
#     bl_label = "Return the mouse or keyboard event"
    
#     @classmethod
#     def poll(cls, context):
#         return (context.object is not None)
#     #  and "RoMa object" in context.object.data
#     # and context.object.type == 'MESH'
#     def invoke(self, context, event):
#         # obj = bpy.context.active_object
#         # if obj is not None and obj.type == "MESH" and "RoMa object" in obj.data:
#         #     # if event.mouse_
#         #     # context.scene.mouse_event = event
#         if event.type != "":
#             context.scene.mouse_keyboard_event = event.type
        
#         return {'FINISHED'}

class VIEW_3D_OT_show_roma_attributes(Operator):
    bl_idname = "wm.show_roma_attributes"
    bl_label = "Show RoMa attributes"
    
    _handle = None  # keep function handler
    
    @staticmethod
    def handle_add(self, context):
        if VIEW_3D_OT_show_roma_attributes._handle is None:
            # print("acceso")
            VIEW_3D_OT_show_roma_attributes._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px_show_attributes, (self, context),
                                                                        'WINDOW',
                                                                        'POST_PIXEL')
            # context.window_manager.roma_show_properties_run_opengl = True

    @staticmethod
    def handle_remove(self, context):
        if VIEW_3D_OT_show_roma_attributes._handle is not None:
            bpy.types.SpaceView3D.draw_handler_remove(VIEW_3D_OT_show_roma_attributes._handle, 'WINDOW')
        VIEW_3D_OT_show_roma_attributes._handle = None
        # context.window_manager.roma_show_properties_run_opengl = False
    
    # def execute(self, context):
    #     areas = [i for i, a in enumerate(bpy.context.screen.areas) if a.type.startswith('VIEW_3D')]
    #     if len(areas) > 0:
    #         for a in areas:
    #             # print("miaooo",a , bpy.context.screen.areas[a].type)
    #             if context.window_manager.roma_show_properties_run_opengl is False:
    #                 self.handle_add(self, context)
    #                 context.area.tag_redraw()
    #             else:
    #                 self.handle_remove(self, context)
    #                 context.area.tag_redraw()
    #             return {'FINISHED'}
    #     else:
    #         self.report({'WARNING'},
    #             "View3D not found, cannot run operator")
        
    #     return {'CANCELLED'}
    
    def execute(self, context):
        # areas = [i for i, a in enumerate(bpy.context.screen.areas) if a.type.startswith('VIEW_3D')]
        # if len(areas) > 0:
        #     for a in areas:
        #         # print("miaooo",a , bpy.context.screen.areas[a].type)
        # if context.window_manager.roma_show_properties_run_opengl is False:
        if VIEW_3D_OT_show_roma_attributes._handle is None:
            self.handle_add(self, context)
            context.area.tag_redraw()
        else:
            self.handle_remove(self, context)
            context.area.tag_redraw()
        return {'FINISHED'}
        # else:
        #     self.report({'WARNING'},
        #         "View3D not found, cannot run operator")
        
        # return {'CANCELLED'}
        
        
    
def draw_main_show_attributes(context):
    obj = bpy.context.active_object
    if hasattr(obj, "data") and "RoMa object" in obj.data:
        obj.update_from_editmode()
        scene = context.scene
            
        mesh = obj.data
        matrix = obj.matrix_world
        
        if mesh.is_editmode:
            bm = bmesh.from_edit_mesh(mesh)
        else:
            bm = bmesh.new()
            bm.from_mesh(mesh)

        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()    
        bMesh_wall = bm.edges.layers.int["roma_wall_id"]
        bMesh_normal = bm.edges.layers.int["roma_inverted_normal"]
        
        bm.faces.ensure_lookup_table()      
        # bMesh_plot = bm.faces.layers.int["roma_plot_id"]
        # bMesh_block = bm.faces.layers.int["roma_block_id"]
        bMesh_typology = bm.faces.layers.int["roma_typology_id"]
        bMesh_storey = bm.faces.layers.int["roma_number_of_storeys"]
        bMesh_floor = bm.faces.layers.int["roma_floor_id"]
    
        region = bpy.context.region
     
        
        # Detect if Quadview to get drawing area
        if not context.space_data.region_quadviews:
            rv3d = bpy.context.space_data.region_3d
        else:
            # verify area
            if context.area.type != 'VIEW_3D' or context.space_data.type != 'VIEW_3D':
                return
            i = -1
            for region in context.area.regions:
                if region.type == 'WINDOW':
                    i += 1
                    if context.region.id == region.id:
                        break
            else:
                return
            rv3d = context.space_data.region_quadviews[i]

        #gpu.state.blend_set('ALPHA')
        
        # center = obj.location
        # print(obj.location, "posizione",pos.x, pos.y, pos.z)
        # coord = view3d_utils.location_3d_to_region_2d(region, rv3d, center)
        
        font_info = {
            "font_id": 0,
            "handler": None,
        }
        
        font_info["font_id"] = 0
        
        font_id = font_info["font_id"]
        # blf.position(font_id, coord.x, coord.y, 0)
        r, g, b, a = [c for c in bpy.context.preferences.addons['roma'].preferences.fontColor]
        blf.color(font_id, r, g, b, a)
        font_size =  bpy.context.preferences.addons['roma'].preferences.fontSize
        blf.size(font_id, font_size)
        
        # multi line text
        # https://blender.stackexchange.com/questions/31780/multi-line-text-in-blf-with-multi-colour-option
        line_height = (blf.dimensions(font_id, "M")[1] * 1.45)
        half_line_height = line_height /2
        
        cr = "Carriage Return"
                    
        for bmEdge in bm.edges:
            vertices = bmEdge.verts
            A = bm.verts[vertices[0].index].co
            B = bm.verts[vertices[1].index].co
            edge_center = Vector()
            edge_center.x = (A.x + B.x)/2
            edge_center.y = (A.y + B.y)/2
            edge_center.z = (A.z + B.z)/2
            center = matrix @ edge_center # convert the coordinates from local to world
            
            line_width = 0
            vert_offset = 0
            
            idWall = bmEdge[bMesh_wall]
            normal = bmEdge[bMesh_normal]
            
            text_edge = []
            text_edge = ""
            text_normal = ""
            
            if bpy.context.window_manager.toggle_wall_name:   
                for n in bpy.context.scene.roma_wall_name_list:
                    if n.id == idWall:
                        text_edge = (n.name, 0)
                        line_width = blf.dimensions(font_id, n.name)[0]
                        vert_offset = -1 * half_line_height
                        text_edge.append(text_edge)
                        text_edge.append(cr)
                        break
            if bpy.context.window_manager.toggle_wall_normal:
                if normal == -1:   
                    symbol = "↔️"
                    text_normal = (symbol, 0)
                    # if blf.dimensions(font_id, symbol)[0] > line_width:
                    line_width = blf.dimensions(font_id, symbol)[0]
                    # if vert_offset == 0:
                    vert_offset += (blf.dimensions(font_id, symbol)[1] * 1.45)/2
                    # else:
                    #     vert_offset += (blf.dimensions(font_id, symbol)[1] * 1.45)* (-1.5)
                            
                        # vert_offset += half_line_height
                    text_edge.append(text_normal)
                    
            coord = view3d_utils.location_3d_to_region_2d(region, rv3d, center)
            # coord = center
            x_offset = (-1 * line_width) / 2
            y_offset = -1 * vert_offset
            
            for a in bpy.context.screen.areas:
                if a.type == 'VIEW_3D':
                    for pstr in text_edge:
                        if len(pstr) == 2:
                            string = pstr[0]
                            text_width, text_height = blf.dimensions(font_id, string)
                            blf.position(font_id, (coord.x + x_offset), (coord.y + y_offset), 0)
                            blf.draw(font_id, string)
                            x_offset += text_width
                        else:
                            x_offset = (-1 * line_width) / 2
                            y_offset -= line_height
                    break
                
        for bmFace in bm.faces:
            center_local = bmFace.calc_center_median()
            
            center = matrix @ center_local # convert the coordinates from local to world
            # idPlot = bmFace[bMesh_plot]
            # idBlock = bmFace[bMesh_block]
            idUse = bmFace[bMesh_typology]
            idFloor = bmFace[bMesh_floor]
            storey = bmFace[bMesh_storey]
            
            line_width = 0
            vert_offset = 0
            
            text_face = []
            text_plot = ""
            text_block = ""
            text_typology = ""
            text_storey = ""
            text_floor = ""
            
            # plotId
            if bpy.context.window_manager.toggle_plot_name:   
                plotId = obj.roma_props['roma_plot_attribute']
                for n in scene.roma_plot_name_list:
                    if n.id == plotId:
                        if n.name != "":
                            text_plot = (("Plot: " + n.name), 0)
                            line_width = blf.dimensions(font_id, text_plot[0])[0]
                            vert_offset = half_line_height
                            text_face.append(text_plot)
                            text_face.append(cr)
                        break
                
            # blockId
            if bpy.context.window_manager.toggle_block_name:   
                blockId = obj.roma_props['roma_block_attribute']
                for n in scene.roma_block_name_list:
                    if n.id == blockId:
                        if n.name != "":
                            text_block = (("Block: " + n.name), 0)
                            if blf.dimensions(font_id, text_block[0])[0] > line_width:
                                line_width = blf.dimensions(font_id, text_block[0])[0]
                                vert_offset += half_line_height
                            text_face.append(text_block)
                            text_face.append(cr)
                        break
                
            # if bpy.context.window_manager.toggle_plot_name:   
            #     for n in bpy.context.scene.roma_plot_name_list:
            #         if n.id == idPlot:
            #             text_plot = (("Plot: " + n.name), 0)
            #             line_width = blf.dimensions(font_id, text_plot[0])[0]
            #             vert_offset = half_line_height
            #             text.append(text_plot)
            #             text.append(cr)
            #             break
            # if bpy.context.window_manager.toggle_block_name:   
            #     for n in bpy.context.scene.roma_block_name_list:
            #         if n.id == idBlock:
            #             text_block = (("Block: " + n.name), 0)
            #             if blf.dimensions(font_id, text_block[0])[0] > line_width:
            #                 line_width = blf.dimensions(font_id, text_block[0])[0]
            #             vert_offset += half_line_height
            #             text.append(text_block)
            #             text.append(cr)
            #             break
            if bpy.context.window_manager.toggle_typology_name:   
                for n in scene.roma_typology_name_list:
                    if n.id == idUse:
                        if n.name != "":
                            text_typology = (("Typology: " + n.name), 0)
                            if blf.dimensions(font_id, text_typology[0])[0] > line_width:
                                line_width = blf.dimensions(font_id, text_typology[0])[0]
                            vert_offset += half_line_height
                            text_face.append(text_typology)
                            text_face.append(cr)           
                            break
            if bpy.context.window_manager.toggle_floor_name:   
                for n in scene.roma_floor_name_list:
                    if n.id == idFloor:
                        text_floor = (("Floor: " + n.name), 0)
                        if blf.dimensions(font_id, text_floor[0])[0] > line_width:
                            line_width = blf.dimensions(font_id, text_floor[0])[0]
                        vert_offset += half_line_height
                        text_face.append(text_floor)
                        text_face.append(cr)           
                        break
            if bpy.context.window_manager.toggle_storey_number:  
                text_storey = (("N° of storeys: " + str(storey)), 0)
                if blf.dimensions(font_id, text_storey[0])[0] > line_width:
                            line_width = blf.dimensions(font_id, text_storey[0])[0]
                vert_offset += half_line_height
                text_face.append(text_storey)
            
            
            coord = view3d_utils.location_3d_to_region_2d(region, rv3d, center)
            x_offset = (-1 * line_width) / 2
            y_offset = vert_offset - half_line_height
            # print(text_face)
            for pstr in text_face:
                if len(pstr) == 2:
                    string = pstr[0]
                    text_width, text_height = blf.dimensions(font_id, string)
                    blf.position(font_id, (coord.x + x_offset), (coord.y + y_offset), 0)
                    blf.draw(font_id, string)
                    x_offset += text_width
                else:
                    x_offset = (-1 * line_width) / 2
                    y_offset -= line_height
        bm.free()
        # del bm
        # print("BM Free")
        
        
    
def draw_callback_px_show_attributes(self, context):
    draw_main_show_attributes(context)
    
        
def update_show_attributes(self, context):
    bpy.ops.wm.show_roma_attributes()
    
# Manage all the required updates fired by depsgraph_update  
@persistent
def updates(scene):
    ###############################################################################
    # update the values in the UI accordingly with the selected faces #############
    ###############################################################################
    obj = bpy.context.active_object
    if obj:
        if scene.previous_selection_object_name != obj.name:
            scene.previous_selection_object_name = obj.name
            scene.previous_selection_face_id = -1
        else:
            if obj is not None and obj.type == "MESH" and "RoMa object" in obj.data and obj.mode == 'EDIT':
                bm = bmesh.from_edit_mesh(obj.data)
                bMesh_storeys = bm.faces.layers.int["roma_number_of_storeys"]
                bMesh_storey_list_A = bm.faces.layers.int["roma_list_storey_A"]
                bMesh_storey_list_B = bm.faces.layers.int["roma_list_storey_B"]
                bMesh_typology = bm.faces.layers.int["roma_typology_id"]
            
                # check if there is an active face
                if isinstance(bm.select_history.active, bmesh.types.BMFace):
                    active_face = bm.select_history.active.index
                    if scene.previous_selection_face_id != active_face:
                        scene.previous_selection_face_id = active_face
                else:
                    selected_faces = [face for face in bm.faces if face.select]
                    if len(selected_faces) > 0:
                        for f in selected_faces:
                            scene.previous_selection_face_id = f.index
                    else:
                        scene.previous_selection_face_id = -1
                if scene.previous_selection_face_id != -1:
                    #updating the information in UI
                    bm.faces.ensure_lookup_table()
                    storeys = bm.faces[scene.previous_selection_face_id][bMesh_storeys]
                    list_storey_A = bm.faces[scene.previous_selection_face_id][bMesh_storey_list_A]
                    list_storey_B = bm.faces[scene.previous_selection_face_id][bMesh_storey_list_B]
                    typology = bm.faces[scene.previous_selection_face_id][bMesh_typology]
                    
                    # number of storeys
                    scene["attribute_mass_storeys"] = storeys
                    
                    # typology name
                    # since it is possible to sort typologies in the ui, it can be that the index of the element
                    # in the list doesn't correspond to typology_id. Therefore it is necessary to find elements
                    # in the way below and not with use_list = bpy.context.scene.roma_typology_name_list[typology_id].useList
                    item = next(i for i in scene.roma_typology_name_list if i["id"] == typology)
                    scene.roma_typology_name_current[0].name = item.name
                    # uses related to the typology
                    usesUiList = bpy.context.scene.roma_obj_typology_uses_name_list 
                    # clean the list
                    while len(usesUiList) > 0:
                        index = scene.roma_obj_typology_uses_name_list_index
                        usesUiList.remove(index)
                        scene.roma_obj_typology_uses_name_list_index = min(max(0, index - 1), len(usesUiList) - 1)
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
                        for use in scene.roma_use_name_list:
                            if id == use.id:
                                usesUiList[enum].name = use.name
                                usesUiList[enum].nameId = use.id
                                storeys = list_storey_A[enum] + list_storey_B[enum]
                                usesUiList[enum].storeys = int(storeys)
                                break
                bm.free
    ###############################################################################
    # show graphic overlays #######################################################
    ###############################################################################

    if scene.show_selection_overlay_is_active != bpy.context.preferences.addons['roma'].preferences.toggleSelectionOverlay:
        scene.show_selection_overlay_is_active = bpy.context.preferences.addons['roma'].preferences.toggleSelectionOverlay
        bpy.ops.wm.show_roma_overlay('INVOKE_DEFAULT')
        
    ####################################################################################################
    # when a typology is selected, it is necessary to update the #######################################
    # uses in the UIList using the ones stored in scene.roma_typology_uses_name_list ###################
    ####################################################################################################
    previous = scene.roma_previous_selected_typology
    current = scene.roma_typology_name_list_index
    if previous != current:
        scene.roma_previous_selected_typology = current
        use_name_list = scene.roma_typology_uses_name_list
        while len(use_name_list) > 0:
            index = scene.roma_typology_uses_name_list_index
            use_name_list.remove(index)
            scene.roma_typology_uses_name_list_index = min(max(0, index - 1), len(use_name_list) - 1)
        # add the uses stored in the typology to the current typology use UIList        
        selected_typology_index = scene.roma_typology_name_list_index
        if len(scene.roma_typology_name_list) > 0:
            list = scene.roma_typology_name_list[selected_typology_index].useList    
            split_list = list.split(";")
            for el in split_list:
                scene.roma_typology_uses_name_list.add()
                temp_list = []    
                temp_list.append(int(el))
                last = len(scene.roma_typology_uses_name_list)-1
                # look for the correspondent use name in roma_use_name_list
                for use in scene.roma_use_name_list:
                    if int(el) == use.id:
                        scene.roma_typology_uses_name_list[last].id = use.id
                        scene.roma_typology_uses_name_list[last].name = use.name 
                        break
    
    #############################################################################################
    # is the selection has changed, some  data in the RoMa schedule need to be updated ##########
    #############################################################################################
    # list of RoMaTreeType
    trees = [x for x in bpy.data.node_groups if x.bl_idname == "RoMaTreeType"]
    if trees:
        for tree in trees:
            nodes = tree.nodes
            if nodes:
                groupInput = [x for x in nodes if x.bl_idname == "Input RoMa Mesh"]
                if groupInput:
                    for group in groupInput:
                        group.update_selected_objects()
                    # execute the node tree
                    tree.execute(bpy.context)



# class VIEW_3D_OT_update_mesh_attributes(Operator):
#     '''Update RoMa attributes, shown in the RoMa panel, related to the active mesh'''
#     bl_idname = "wm.update_mesh_attributes"
#     bl_label = "Update RoMa attributes of the active mesh in the RoMa panel"
    
#     mode_type: bpy.props.StringProperty(name="Object mode type")
    
#     # oldTime = 0
#     # newTime = 0
    
#     # def __init__(self):
#     #     pass
    
#     # def __del__(self):
#     #     pass
    
#     def execute(self, context):
#         print("ciao")
#         scene = bpy.context.scene
#         obj = bpy.context.active_object
#         if self.mode_type == 'OBJECT':
#              #plot id assigned to the current object
#             plotId = obj.roma_props['roma_plot_attribute']
#             for n in scene.roma_plot_name_list:
#                 if n.id == plotId:
#                     scene.roma_plot_name_current[0].name = n.name
#                     break
            
#             #block id assigned to the current object
#             blockId = obj.roma_props['roma_block_attribute']
#             for n in scene.roma_block_name_list:
#                 if n.id == blockId:
#                     scene.roma_block_name_current[0].name = n.name
#                     break
                
#         elif self.mode_type == 'EDIT':
#             projectUses = scene.roma_use_name_list
#             obj.update_from_editmode()
#             mesh = obj.data

#             selected_edges = [e for e in mesh.edges if e.select]
#             selected_faces = [p for p in mesh.polygons if p.select]
                
#             if len(selected_edges) > 0 or len(selected_faces) > 0:
#                 selected_edge_indices = []
#                 selected_face_indices = []
                
#                 if len(selected_edges) > 0:
#                     for f in selected_edges:
#                         selected_edge_indices.append(f.index)
                        
#                 if len(selected_faces) > 0:    
#                     for f in selected_faces:
#                         selected_face_indices.append(f.index)
                
#                 bm = bmesh.from_edit_mesh(mesh)
#                 # bm.edges.ensure_lookup_table()
#                 bMesh_wall = bm.edges.layers.int["roma_wall_id"]
#                 bMesh_normal = bm.edges.layers.int["roma_inverted_normal"]
#                 # bm.faces.ensure_lookup_table()
#                 # bMesh_plot = bm.faces.layers.int["roma_plot_id"]
#                 # bMesh_block = bm.faces.layers.int["roma_block_id"]
#                 bMesh_typology = bm.faces.layers.int["roma_typology_id"]
#                 bMesh_storeys = bm.faces.layers.int["roma_number_of_storeys"]
#                 bMesh_floor = bm.faces.layers.int["roma_floor_id"]
#                 bMesh_use_list_A = bm.faces.layers.int["roma_list_use_id_A"]
#                 bMesh_use_list_B = bm.faces.layers.int["roma_list_use_id_B"]
#                 bMesh_storey_list_A = bm.faces.layers.int["roma_list_storey_A"]
#                 bMesh_storey_list_B = bm.faces.layers.int["roma_list_storey_B"]
#                 bMesh_height_A = bm.faces.layers.int["roma_list_height_A"]
#                 bMesh_height_B = bm.faces.layers.int["roma_list_height_B"]
#                 bMesh_height_C = bm.faces.layers.int["roma_list_height_C"]
#                 bMesh_height_D = bm.faces.layers.int["roma_list_height_D"]
#                 bMesh_height_E = bm.faces.layers.int["roma_list_height_E"]
#                 bMesh_void = bm.faces.layers.int["roma_list_void"]

#                 selected_bmEdges = [edge for edge in bm.edges if edge.select]
#                 selected_bmFaces = [face for face in bm.faces if face.select]
                
#                 # active_vert = isinstance(bm.select_history.active, bmesh.types.BMVert)
#                 # active_edge = isinstance(bm.select_history.active, bmesh.types.BMEdge)
#                 # active_face = isinstance(bm.select_history.active, bmesh.types.BMFace)
#                 activElem = bm.select_history.active
#                 if (activElem != None and type(activElem).__name__ == 'BMEdge'):
#                     bMesh_active_index = activElem.index
                    
#                     for edge in selected_edges:
#                         try:
#                             bm.edges.ensure_lookup_table()
#                             bm.edges[edge.index].select = False
#                         except:
#                             pass
                        
#                     for bmEdge in selected_bmEdges:
#                         try:
#                             bm.faces.ensure_lookup_table()
#                             wall_type = bmEdge[bMesh_wall]
#                             wall_normal = bmEdge[bMesh_normal]
                            
#                             if bmEdge.index ==  bMesh_active_index:
#                                 ############# WALL TYPE ####################
#                                 if scene.attribute_wall_id != wall_type:
#                                     scene.attribute_wall_id = wall_type
#                                 if scene.roma_wall_name_current[0].id != wall_type:
#                                     scene.roma_wall_name_current[0].id = wall_type
#                                     for n in scene.roma_wall_name_list:
#                                         if n.id == scene.roma_wall_name_current[0].id:
#                                             scene.roma_wall_name_current[0].name = " " + n.name 
#                                             break
#                                 ############# WALL NORMAL ####################
#                                 # print(scene.attribute_wall_normal*1, wall_normal)
#                                 # if (scene.attribute_wall_normal*1) != wall_normal:
#                                 if wall_normal == -1:
#                                     # print("true")
#                                     scene.attribute_wall_normal = True
#                                 else:
#                                     # print("false")
#                                     scene.attribute_wall_normal = False
#                         except:
#                             pass
                            
#                 # elif active_face:
#                 elif (activElem != None and type(activElem).__name__ == 'BMFace'):
#                 # elif tuple(bpy.context.scene.tool_settings.mesh_select_mode)[2] == True: #we are selecting faces
#                     # print("active")
#                     bMesh_active_index = activElem.index
#                     for face in selected_faces:
#                         try:
#                             bm.faces.ensure_lookup_table()
#                             bm.faces[face.index].select = False
#                         except:
#                             pass
                        
#                     for bmFace in selected_bmFaces:
#                         try:
#                             typology = bmFace[bMesh_typology] 
#                             storey = bmFace[bMesh_storeys]  
#                             # print("storey", storey)
#                             floor = bmFace[bMesh_floor]
#                             if bmFace.index ==  bMesh_active_index:
#                                 ############# PLOT ####################
#                                 # if scene.attribute_mass_plot_id != plot:
#                                 #     scene.attribute_mass_plot_id = plot
#                                 # if scene.roma_plot_name_current[0].id != plot:
#                                 #     scene.roma_plot_name_current[0].id = plot
#                                 #     # if plotName["id"] == 0:
#                                 #     #     plotName["name"] = None
#                                 #     # else:
#                                 #     for n in scene.roma_plot_name_list:
#                                 #         if n.id == scene.roma_plot_name_current[0].id:
#                                 #             scene.roma_plot_name_current[0].name = " " + n.name 
#                                 #             break
                                        
#                                 ############# BLOCK ####################
#                                 # if scene.attribute_mass_block_id != block:
#                                 #     scene.attribute_mass_block_id = block
#                                 # if scene.roma_block_name_current[0].id != block:
#                                 #     scene.roma_block_name_current[0].id = block
#                                 #     for n in scene.roma_block_name_list:
#                                 #         if n.id == scene.roma_block_name_current[0].id:
#                                 #             scene.roma_block_name_current[0].name = " " + n.name 
#                                 #             break
                                        
#                                 ############# TYPOLOGY ####################
#                                 if scene.attribute_mass_typology_id != typology:
#                                     scene.attribute_mass_typology_id = typology
#                                 if scene.roma_typology_name_current[0].id != typology:
#                                     scene.roma_typology_name_current[0].id = typology
#                                     for n in scene.roma_typology_name_list:
#                                         if n.id == scene.roma_typology_name_current[0].id:
#                                             scene.roma_typology_name_current[0].name = " " + n.name 
#                                             break
                                        
#                                 ############# STOREYS ####################
#                                 if scene.attribute_mass_storeys != storey:
#                                     scene.attribute_mass_storeys = storey
                                    
#                                 ############# FLOOR ####################
#                                 if scene.attribute_floor_id != floor:
#                                     scene.attribute_floor_id = floor
#                                 if scene.roma_floor_name_current[0].id != floor:
#                                     scene.roma_floor_name_current[0].id = floor
#                                     for n in scene.roma_floor_name_list:
#                                         if n.id == scene.roma_floor_name_current[0].id:
#                                             scene.roma_floor_name_current[0].name = " " + n.name 
#                                             break
#                             break   
#                         except:
#                             pass
                
#                 # update the attributes of the selected faces
#                 if len(selected_bmFaces) > 0:
#                     try:
#                         for bmFace in selected_bmFaces:
#                             typology_id = bmFace[bMesh_typology] 
#                             numberOfStoreys = bmFace[bMesh_storeys] 
#                             # use_list = bpy.context.scene.roma_typology_name_list[typology_id].useList
#                             # since it is possible to sort typologies in the ui, it can be that the index of the element
#                             # in the list doesn't correspond to typology_id. Therefore it is necessary to find elements
#                             # in the way below and not with use_list = bpy.context.scene.roma_typology_name_list[typology_id].useList
#                             item = next(i for i in bpy.context.scene.roma_typology_name_list if i["id"] == typology_id)
#                             use_list = item.useList
#                             # uses are listed top to bottom, but they need to
#                             # be added bottom to top           
#                             # use_list = use_list [::-1]
#                             useSplit = use_list.split(";")            
#                             useSplit.reverse() 
                            
#                             use_id_list_A = "1"
#                             use_id_list_B = "1"
#                             storey_list_A = "1"
#                             storey_list_B = "1"
#                             storey_list_UI = "1" # this is needed to show the number of storeys in the UI
#                             height_A = "1"
#                             height_B = "1"
#                             height_C = "1"
#                             height_D = "1"
#                             height_E = "1"
#                             liquidPosition = [] # to count how many liquid uses they are
#                             fixedStoreys = 0 # to count how many fixed storeys they are
#                             void = "1"
                            
#                             usesUiList = bpy.context.scene.roma_obj_typology_uses_name_list
#                             # clean the list
#                             while len(usesUiList) > 0:
#                                 index = bpy.context.scene.roma_obj_typology_uses_name_list_index
#                                 usesUiList.remove(index)
#                                 bpy.context.scene.roma_obj_typology_uses_name_list_index = min(max(0, index - 1), len(usesUiList) - 1)
                            
#                             for enum, el in enumerate(useSplit):
#                                 # print("split",el)
#                                 #### list_use_id
#                                 if int(el) < 10:
#                                     tmpUse = "0" + el
#                                 else:
#                                     tmpUse = el
#                                 use_id_list_A += tmpUse[0]
#                                 use_id_list_B += tmpUse[1]
                                                                
#                                 ###setting the values for each use
#                                 for use in projectUses:
#                                     if use.id == int(el):
#                                         # number of storeys for the use
#                                         # if a use is "liquid" the number of storeys is set as 00
#                                         if use.liquid: 
#                                             storeys = "00"
#                                             liquidPosition.append(enum)
#                                         else:
#                                             fixedStoreys += use.storeys
#                                             storeys = str(use.storeys)
#                                             if use.storeys < 10:
#                                                 storeys = "0" + storeys
                                                
#                                         storey_list_A += storeys[0]
#                                         storey_list_B += storeys[1]
#                                         storey_list_UI +=storeys
                                        
#                                         void += str(int(use.void))
                                        
#                                         #### floor to floor height for each use, stored in A, B, C, ...
#                                         #### due to the fact that arrays can't be used
#                                         #### and array like (3.555, 12.664, 0.123)
#                                         #### is saved as
#                                         #### A (1010) tens
#                                         #### B (1320) units
#                                         #### C (1561) first decimal
#                                         #### D (1562) second decimal
#                                         #### E (1543) third decimal
#                                         #### each array starting with 1 since a number can't start with 0
#                                         height = str(round(use.floorToFloor,3))
#                                         if use.floorToFloor < 10:
#                                             height = "0" + height
#                                         height_A += height[0]
#                                         height_B += height[1]
#                                         # print("B", height_B)
#                                         try:
#                                             # height[3]
#                                             height_C += height[3]
#                                             try:
#                                                 height_D += height[4]
#                                                 try:
#                                                     height_E += height[5]
#                                                 except:
#                                                     height_E += "0"
#                                             except:
#                                                 height_D += "0"
#                                                 height_E += "0"
#                                         except:
#                                             height_C += "0"
#                                             height_D += "0"
#                                             height_E += "0"
#                                         break
                        
                            
                            
#                             # liquid storeys need to be converted to actual storeys
#                             storeyCheck = numberOfStoreys - fixedStoreys - len(liquidPosition)
#                             # if the typology has more storeys than the selected mass
#                             # some extra storeys are added
#                             if storeyCheck < 1: 
#                                 scene.attribute_mass_storeys = fixedStoreys + len(liquidPosition)
#                             storeyLeft = numberOfStoreys - fixedStoreys

#                             # the 1 at the start of the number is removed
#                             storey_list_UI = storey_list_UI[1:]
#                             if len(liquidPosition) > 0:
#                                 # the 1 at the start of the number is removed
#                                 storey_list_A = storey_list_A[1:]
#                                 storey_list_B = storey_list_B[1:]
                                
#                                 n = storeyLeft/len(liquidPosition)
#                                 liquidStoreyNumber = math.floor(n)

#                                 insert = str(liquidStoreyNumber)
#                                 if liquidStoreyNumber < 10:
#                                     insert = "0" + insert
                                    
#                                 index = 0
#                                 while index < len(liquidPosition):
#                                     el = liquidPosition[index]
#                                     # if the rounding of the liquid storeys is uneven,
#                                     # the last liquid floor is increased of 1 storey
#                                     if index == len(liquidPosition) -1 and  math.modf(n)[0] > 0:
#                                         insert = str(liquidStoreyNumber +1) 
#                                         if liquidStoreyNumber +1 < 10:
#                                             insert = "0" + insert
                                        
#                                     storey_list_A = storey_list_A[:el] + insert[0] + storey_list_A[el +1:]
#                                     storey_list_B = storey_list_B[:el] + insert[1] + storey_list_B[el +1:]
#                                     storey_list_UI = storey_list_UI[:el*2] + insert + storey_list_UI[el*2 +2:]
#                                     # print("el", el)
#                                     index += 1
#                                 # the 1 is readded  
#                                 storey_list_A = "1" + storey_list_A
#                                 storey_list_B = "1" + storey_list_B
                            
#                             # else there are no liquid storeys, the storey operator is off
#                             bpy.data.scenes["Scene"].attribute_mass_storeys
                                
                            
#                             # update the uses shown in the UIList in the Mass menu
#                             # in the 3D view
#                             # lists needs to be reversed again since we want to show top to bottom
#                             useSplit.reverse()
#                             reversed_storey_list = "".join(map(str.__add__, storey_list_UI[-2::-2] ,storey_list_UI[-1::-2]))
#                             # print(reversed_storey_list)
#                             for enum, el in enumerate(useSplit):
#                                 id = int(el)
#                                 usesUiList.add()
#                                 usesUiList[enum].id = enum + 1
#                                 for use in bpy.context.scene.roma_use_name_list:
#                                     if id == use.id:
#                                         usesUiList[enum].name = use.name
#                                         usesUiList[enum].nameId = use.id
#                                         s = reversed_storey_list[enum*2:(enum*2+2)]
#                                         usesUiList[enum].storeys = int(s)
#                                         break
                            
                            
#                             # storey_list_UI = "1" + storey_list_UI
#                             bmFace[bMesh_use_list_A] = int(use_id_list_A)
#                             bmFace[bMesh_use_list_B] = int(use_id_list_B)
#                             bmFace[bMesh_storey_list_A] = int(storey_list_A)
#                             bmFace[bMesh_storey_list_B] = int(storey_list_B)
#                             bmFace[bMesh_height_A] = int(height_A)
#                             bmFace[bMesh_height_B] = int(height_B)
#                             bmFace[bMesh_height_C] = int(height_C)
#                             bmFace[bMesh_height_D] = int(height_D)
#                             bmFace[bMesh_height_E] = int(height_E)
#                             bmFace[bMesh_void] = int(void)
                                
#                     except:
#                         pass
                
                
                    
#                 bmesh.update_edit_mesh(mesh)
#                 bm.free()
                    

#                 bm = bmesh.from_edit_mesh(mesh)
#                 bm.edges.ensure_lookup_table()
#                 for index in selected_edge_indices:
#                     bm.edges[index].select = True
                    
#                 bm.faces.ensure_lookup_table()
#                 for index in selected_face_indices:
#                     bm.faces[index].select = True
                        
#                 bmesh.update_edit_mesh(mesh)
            
#                 bm.free() 
#         return {'FINISHED'}
    
    # def execute_object (self, context):
    #     scene = bpy.context.scene
    #     obj = bpy.context.active_object
        
    #     #plot id assigned to the current object
    #     plotId = obj.roma_props['roma_plot_attribute']
    #     for n in scene.roma_plot_name_list:
    #         if n.id == plotId:
    #             scene.roma_plot_name_current[0].name = n.name
    #             break
            
    #     #block id assigned to the current object
    #     blockId = obj.roma_props['roma_block_attribute']
    #     for n in scene.roma_block_name_list:
    #         if n.id == blockId:
    #             scene.roma_block_name_current[0].name = n.name
    #             break
    #     bpy.context.scene.updating_mesh_attributes_is_active = False    
    #     return {'FINISHED'}
        
        
    
    # def execute_edit (self, context):
    #     # print("eseguo")
    #     scene = bpy.context.scene
    #     projectUses = scene.roma_use_name_list
        
    #     obj = bpy.context.active_object
    #     # if tuple(bpy.context.scene.tool_settings.mesh_select_mode)[2] == True: #we are selecting faces
    #     # print("controllo dati", datetime.now())
        
    #     obj.update_from_editmode()
    #     mesh = obj.data
    #     # attr = mesh.attributes["roma_typology_id"].data.items()
    #     # print("aaaa", attr)

    #     # activeFace = mesh.polygons[mesh.polygons.active]
    #     selected_edges = [e for e in mesh.edges if e.select]
    #     selected_faces = [p for p in mesh.polygons if p.select]
            
    #     if len(selected_edges) > 0 or len(selected_faces) > 0:
    #         selected_edge_indices = []
    #         selected_face_indices = []
            
    #         if len(selected_edges) > 0:
    #             for f in selected_edges:
    #                 selected_edge_indices.append(f.index)
                    
    #         if len(selected_faces) > 0:    
    #             for f in selected_faces:
    #                 selected_face_indices.append(f.index)
                
            
            
    #         bm = bmesh.from_edit_mesh(mesh)
    #         # print("AGGIUNGO BMESH")
    #         # bm.edges.ensure_lookup_table()

    #         # bMesh_wall = bm.edges.layers.int["roma_wall_id"]
    #         # bMesh_normal = bm.edges.layers.int["roma_inverted_normal"]
            
    #         # bm.faces.ensure_lookup_table()
    #         # bMesh_plot = bm.faces.layers.int["roma_plot_id"]
    #         # bMesh_block = bm.faces.layers.int["roma_block_id"]
    #         bMesh_typology = bm.faces.layers.int["roma_typology_id"]
    #         bMesh_storeys = bm.faces.layers.int["roma_number_of_storeys"]
    #         bMesh_floor = bm.faces.layers.int["roma_floor_id"]
    #         bMesh_use_list_A = bm.faces.layers.int["roma_list_use_id_A"]
    #         bMesh_use_list_B = bm.faces.layers.int["roma_list_use_id_B"]
    #         bMesh_storey_list_A = bm.faces.layers.int["roma_list_storey_A"]
    #         bMesh_storey_list_B = bm.faces.layers.int["roma_list_storey_B"]
    #         bMesh_height_A = bm.faces.layers.int["roma_list_height_A"]
    #         bMesh_height_B = bm.faces.layers.int["roma_list_height_B"]
    #         bMesh_height_C = bm.faces.layers.int["roma_list_height_C"]
    #         bMesh_height_D = bm.faces.layers.int["roma_list_height_D"]
    #         bMesh_height_E = bm.faces.layers.int["roma_list_height_E"]
    #         bMesh_void = bm.faces.layers.int["roma_list_void"]

    #         selected_bmEdges = [edge for edge in bm.edges if edge.select]
    #         selected_bmFaces = [face for face in bm.faces if face.select]
            
    #         # active_vert = isinstance(bm.select_history.active, bmesh.types.BMVert)
    #         # active_edge = isinstance(bm.select_history.active, bmesh.types.BMEdge)
    #         # active_face = isinstance(bm.select_history.active, bmesh.types.BMFace)
    #         activElem = bm.select_history.active
    #         # print("contreollo", len(selected_bmFaces), activElem)
    #         # if activElem == None:
    #         #     bpy.context.scene.updating_mesh_attributes_is_active = False    
    #         #     return {'FINISHED'}
    #             # print("ce ne è uno", activElem)
    #             # for el in activElem:
    #             #     print(el)
            
            
    #         # if bm.faces.active is not None:
    #         #     print("NONE FACES !!!!!!!!!!!!!")
    #         # else:
    #         # if active_edge:
    #         if (activElem != None and type(activElem).__name__ == 'BMEdge'):
    #             bMesh_active_index = activElem.index
                
    #             for edge in selected_edges:
    #                 try:
    #                     bm.edges.ensure_lookup_table()
    #                     bm.edges[edge.index].select = False
    #                 except:
    #                     pass
                    
    #             for bmEdge in selected_bmEdges:
    #                 try:
    #                     bm.faces.ensure_lookup_table()
    #                     wall_type = bmEdge[bMesh_wall]
    #                     wall_normal = bmEdge[bMesh_normal]
                        
    #                     if bmEdge.index ==  bMesh_active_index:
    #                         ############# WALL TYPE ####################
    #                         if scene.attribute_wall_id != wall_type:
    #                             scene.attribute_wall_id = wall_type
    #                         if scene.roma_wall_name_current[0].id != wall_type:
    #                             scene.roma_wall_name_current[0].id = wall_type
    #                             for n in scene.roma_wall_name_list:
    #                                 if n.id == scene.roma_wall_name_current[0].id:
    #                                     scene.roma_wall_name_current[0].name = " " + n.name 
    #                                     break
    #                         ############# WALL NORMAL ####################
    #                         # print(scene.attribute_wall_normal*1, wall_normal)
    #                         # if (scene.attribute_wall_normal*1) != wall_normal:
    #                         if wall_normal == -1:
    #                             # print("true")
    #                             scene.attribute_wall_normal = True
    #                         else:
    #                             # print("false")
    #                             scene.attribute_wall_normal = False
    #                 except:
    #                     pass
                    
                        
                        
    #         # elif active_face:
    #         elif (activElem != None and type(activElem).__name__ == 'BMFace'):
    #         # elif tuple(bpy.context.scene.tool_settings.mesh_select_mode)[2] == True: #we are selecting faces
    #             # print("active")
    #             bMesh_active_index = activElem.index
    #             for face in selected_faces:
    #                 try:
    #                     bm.faces.ensure_lookup_table()
    #                     bm.faces[face.index].select = False
    #                 except:
    #                     pass
                    
    #             for bmFace in selected_bmFaces:
    #                 # print("ciao")
    #                 try:
    #                     # plot = bmFace[bMesh_plot]
    #                     # block = bmFace[bMesh_block]
    #                     typology = bmFace[bMesh_typology] 
    #                     storey = bmFace[bMesh_storeys]  
    #                     floor = bmFace[bMesh_floor]
    #                     # print("list", typology, storey, floor)
    #                     # if bm.faces.active is not None and bmFace.index ==  bMesh_active_index:
    #                     # print("quack", bmFace.index, bMesh_active_index)
    #                     if bmFace.index ==  bMesh_active_index:
    #                         # print("yo")
    #                         ############# PLOT ####################
    #                         # if scene.attribute_mass_plot_id != plot:
    #                         #     scene.attribute_mass_plot_id = plot
    #                         # if scene.roma_plot_name_current[0].id != plot:
    #                         #     scene.roma_plot_name_current[0].id = plot
    #                         #     # if plotName["id"] == 0:
    #                         #     #     plotName["name"] = None
    #                         #     # else:
    #                         #     for n in scene.roma_plot_name_list:
    #                         #         if n.id == scene.roma_plot_name_current[0].id:
    #                         #             scene.roma_plot_name_current[0].name = " " + n.name 
    #                         #             break
                                    
    #                         ############# BLOCK ####################
    #                         # if scene.attribute_mass_block_id != block:
    #                         #     scene.attribute_mass_block_id = block
    #                         # if scene.roma_block_name_current[0].id != block:
    #                         #     scene.roma_block_name_current[0].id = block
    #                         #     for n in scene.roma_block_name_list:
    #                         #         if n.id == scene.roma_block_name_current[0].id:
    #                         #             scene.roma_block_name_current[0].name = " " + n.name 
    #                         #             break
                                    
    #                         ############# TYPOLOGY ####################
    #                         if scene.attribute_mass_typology_id != typology:
    #                             scene.attribute_mass_typology_id = typology
    #                         if scene.roma_typology_name_current[0].id != typology:
    #                             scene.roma_typology_name_current[0].id = typology
    #                             for n in scene.roma_typology_name_list:
    #                                 if n.id == scene.roma_typology_name_current[0].id:
    #                                     scene.roma_typology_name_current[0].name = " " + n.name 
    #                                     break
                                    
    #                         ############# STOREYS ####################
    #                         if scene.attribute_mass_storeys != storey:
    #                             scene.attribute_mass_storeys = storey
                                
    #                         ############# FLOOR ####################
    #                         if scene.attribute_floor_id != floor:
    #                             scene.attribute_floor_id = floor
    #                         if scene.roma_floor_name_current[0].id != floor:
    #                             scene.roma_floor_name_current[0].id = floor
    #                             for n in scene.roma_floor_name_list:
    #                                 if n.id == scene.roma_floor_name_current[0].id:
    #                                     scene.roma_floor_name_current[0].name = " " + n.name 
    #                                     break
                            
                            
                           
    #                     break   
    #                 except:
    #                     pass
            
    #         # update the attributes of the selected faces
    #         if len(selected_bmFaces) > 0:
    #             try:
    #                 for bmFace in selected_bmFaces:
    #                     typology_id = bmFace[bMesh_typology] 
    #                     numberOfStoreys = bmFace[bMesh_storeys] 
    #                     # use_list = bpy.context.scene.roma_typology_name_list[typology_id].useList
    #                     # since it is possible to sort typologies in the ui, it can be that the index of the element
    #                     # in the list doesn't correspond to typology_id. Therefore it is necessary to find elements
    #                     # in the way below and not with use_list = bpy.context.scene.roma_typology_name_list[typology_id].useList
    #                     item = next(i for i in bpy.context.scene.roma_typology_name_list if i["id"] == typology_id)
    #                     use_list = item.useList
    #                     # uses are listed top to bottom, but they need to
    #                     # be added bottom to top           
    #                     # use_list = use_list [::-1]
    #                     useSplit = use_list.split(";")            
    #                     useSplit.reverse() 
                        
    #                     use_id_list_A = "1"
    #                     use_id_list_B = "1"
    #                     storey_list_A = "1"
    #                     storey_list_B = "1"
    #                     storey_list_UI = "1" # this is needed to show the number of storeys in the UI
    #                     height_A = "1"
    #                     height_B = "1"
    #                     height_C = "1"
    #                     height_D = "1"
    #                     height_E = "1"
    #                     liquidPosition = [] # to count how many liquid uses they are
    #                     fixedStoreys = 0 # to count how many fixed storeys they are
    #                     void = "1"
                        
    #                     usesUiList = bpy.context.scene.roma_obj_typology_uses_name_list
    #                     # clean the list
    #                     while len(usesUiList) > 0:
    #                         index = bpy.context.scene.roma_obj_typology_uses_name_list_index
    #                         usesUiList.remove(index)
    #                         bpy.context.scene.roma_obj_typology_uses_name_list_index = min(max(0, index - 1), len(usesUiList) - 1)
                        
    #                     for enum, el in enumerate(useSplit):
    #                         # print("split",el)
    #                         #### list_use_id
    #                         if int(el) < 10:
    #                             tmpUse = "0" + el
    #                         else:
    #                             tmpUse = el
    #                         use_id_list_A += tmpUse[0]
    #                         use_id_list_B += tmpUse[1]
                                                            
    #                         ###setting the values for each use
    #                         for use in projectUses:
    #                             if use.id == int(el):
    #                                 # number of storeys for the use
    #                                 # if a use is "liquid" the number of storeys is set as 00
    #                                 if use.liquid: 
    #                                     storeys = "00"
    #                                     liquidPosition.append(enum)
    #                                 else:
    #                                     fixedStoreys += use.storeys
    #                                     storeys = str(use.storeys)
    #                                     if use.storeys < 10:
    #                                         storeys = "0" + storeys
                                            
    #                                 storey_list_A += storeys[0]
    #                                 storey_list_B += storeys[1]
    #                                 storey_list_UI +=storeys
                                    
    #                                 void += str(int(use.void))
                                    
    #                                 #### floor to floor height for each use, stored in A, B, C, ...
    #                                 #### due to the fact that arrays can't be used
    #                                 #### and array like (3.555, 12.664, 0.123)
    #                                 #### is saved as
    #                                 #### A (1010) tens
    #                                 #### B (1320) units
    #                                 #### C (1561) first decimal
    #                                 #### D (1562) second decimal
    #                                 #### E (1543) third decimal
    #                                 #### each array starting with 1 since a number can't start with 0
    #                                 height = str(round(use.floorToFloor,3))
    #                                 if use.floorToFloor < 10:
    #                                     height = "0" + height
    #                                 height_A += height[0]
    #                                 height_B += height[1]
    #                                 # print("B", height_B)
    #                                 try:
    #                                     # height[3]
    #                                     height_C += height[3]
    #                                     try:
    #                                         height_D += height[4]
    #                                         try:
    #                                             height_E += height[5]
    #                                         except:
    #                                             height_E += "0"
    #                                     except:
    #                                         height_D += "0"
    #                                         height_E += "0"
    #                                 except:
    #                                     height_C += "0"
    #                                     height_D += "0"
    #                                     height_E += "0"
    #                                 break
                      
                        
                        
    #                     # liquid storeys need to be converted to actual storeys
    #                     storeyCheck = numberOfStoreys - fixedStoreys - len(liquidPosition)
    #                     # if the typology has more storeys than the selected mass
    #                     # some extra storeys are added
    #                     if storeyCheck < 1: 
    #                         scene.attribute_mass_storeys = fixedStoreys + len(liquidPosition)
    #                     storeyLeft = numberOfStoreys - fixedStoreys

    #                      # the 1 at the start of the number is removed
    #                     storey_list_UI = storey_list_UI[1:]
    #                     if len(liquidPosition) > 0:
    #                         # the 1 at the start of the number is removed
    #                         storey_list_A = storey_list_A[1:]
    #                         storey_list_B = storey_list_B[1:]
                            
    #                         n = storeyLeft/len(liquidPosition)
    #                         liquidStoreyNumber = math.floor(n)

    #                         insert = str(liquidStoreyNumber)
    #                         if liquidStoreyNumber < 10:
    #                             insert = "0" + insert
                                
    #                         index = 0
    #                         while index < len(liquidPosition):
    #                             el = liquidPosition[index]
    #                             # if the rounding of the liquid storeys is uneven,
    #                             # the last liquid floor is increased of 1 storey
    #                             if index == len(liquidPosition) -1 and  math.modf(n)[0] > 0:
    #                                 insert = str(liquidStoreyNumber +1) 
    #                                 if liquidStoreyNumber +1 < 10:
    #                                     insert = "0" + insert
                                    
    #                             storey_list_A = storey_list_A[:el] + insert[0] + storey_list_A[el +1:]
    #                             storey_list_B = storey_list_B[:el] + insert[1] + storey_list_B[el +1:]
    #                             storey_list_UI = storey_list_UI[:el*2] + insert + storey_list_UI[el*2 +2:]
    #                             # print("el", el)
    #                             index += 1
    #                         # the 1 is readded  
    #                         storey_list_A = "1" + storey_list_A
    #                         storey_list_B = "1" + storey_list_B
                        
    #                     # else there are no liquid storeys, the storey operator is off
    #                     bpy.data.scenes["Scene"].attribute_mass_storeys
                            
                        
    #                     # update the uses shown in the UIList in the Mass menu
    #                     # in the 3D view
    #                     # lists needs to be reversed again since we want to show top to bottom
    #                     useSplit.reverse()
    #                     reversed_storey_list = "".join(map(str.__add__, storey_list_UI[-2::-2] ,storey_list_UI[-1::-2]))
    #                     # print(reversed_storey_list)
    #                     for enum, el in enumerate(useSplit):
    #                         id = int(el)
    #                         usesUiList.add()
    #                         usesUiList[enum].id = enum + 1
    #                         for use in bpy.context.scene.roma_use_name_list:
    #                             if id == use.id:
    #                                 usesUiList[enum].name = use.name
    #                                 usesUiList[enum].nameId = use.id
    #                                 s = reversed_storey_list[enum*2:(enum*2+2)]
    #                                 usesUiList[enum].storeys = int(s)
    #                                 break
                        
                        
    #                     # storey_list_UI = "1" + storey_list_UI
    #                     bmFace[bMesh_use_list_A] = int(use_id_list_A)
    #                     bmFace[bMesh_use_list_B] = int(use_id_list_B)
    #                     bmFace[bMesh_storey_list_A] = int(storey_list_A)
    #                     bmFace[bMesh_storey_list_B] = int(storey_list_B)
    #                     bmFace[bMesh_height_A] = int(height_A)
    #                     bmFace[bMesh_height_B] = int(height_B)
    #                     bmFace[bMesh_height_C] = int(height_C)
    #                     bmFace[bMesh_height_D] = int(height_D)
    #                     bmFace[bMesh_height_E] = int(height_E)
    #                     bmFace[bMesh_void] = int(void)
                            
    #             except:
    #                 pass
            
            
                
    #         bmesh.update_edit_mesh(mesh)
    #         bm.free()
                

    #         bm = bmesh.from_edit_mesh(mesh)
    #         bm.edges.ensure_lookup_table()
    #         for index in selected_edge_indices:
    #             bm.edges[index].select = True
                
    #         bm.faces.ensure_lookup_table()
    #         for index in selected_face_indices:
    #             bm.faces[index].select = True
                    
    #         bmesh.update_edit_mesh(mesh)
        
    #         bm.free() 
    #         # del bm
    #         # print("RIMUOVO BMESH")
            
    # # checkingFace = False
    #     # print("fatto")
    #     bpy.context.scene.updating_mesh_attributes_is_active = False    
    #     # return {'FINISHED'}
    #     # print("miao")
    #     return {'RUNNING_MODAL'}

    
    # def modal(self, context, event):
    #     if event.type in {'LEFTMOUSE', 'RIGHTMOUSE', 'ENT', 'NUMPAD_ENTER'}:
    #         self.obj = bpy.context.active_object
    #         if self.obj is not None and self.obj.type == "MESH":
    #             if "RoMa object" in self.obj.data:
    #                 if self.obj.mode == "OBJECT":
    #                     self.mode = self.obj.mode
    #                     self.execute(context)
    #                 elif self.obj.mode == "EDIT":
    #                     self.mode = self.obj.mode
    #                     self.execute(context)

    #     return {'PASS_THROUGH'}
        
    # def modal(self, context, event):
    #     if event.type in {'LEFTMOUSE', 'RIGHTMOUSE'}:
    #         obj = bpy.context.active_object
    #         if obj is not None and obj.type == "MESH":
    #             if obj.mode == "EDIT" and "RoMa object" in obj.data:
    #             # print("RUNNING MODAL")
    #                 self.execute_edit(context)
    #     # else:
    #     bpy.context.scene.updating_mesh_attributes_is_active = False
    #     return {'PASS_THROUGH'}
        
    # def invoke(self, context, event):
    #     # if event.type in {'LEFTMOUSE', 'RIGHTMOUSE', 'ENT', 'NUMPAD_ENTER'}:
    #     #     obj = bpy.context.active_object
    #     #     if obj is not None and obj.type == "MESH":
    #     #         if "RoMa object" in obj.data:
    #     #             if obj.mode == "OBJECT":
    #     #                 self.execute_object(context)
    #     #                 bpy.context.scene.updating_mesh_attributes_is_active = False
    #     #             elif obj.mode == "EDIT":
    #     #                 self.execute_edit(context)
    #     #                 bpy.context.scene.updating_mesh_attributes_is_active = False
    #     #     bpy.context.scene.updating_mesh_attributes_is_active = False
    #     # else:
    #     #     bpy.context.scene.updating_mesh_attributes_is_active = False
      
    #     self.obj = bpy.context.active_object
    #     self.mode = "none"
    #     self.execute(context)
    #     context.window_manager.modal_handler_add(self)
    #     print("invoke VIEW 3D OT UPDATE MESH ATTRIBUTES")
    #     return {'RUNNING_MODAL'}
    
       

    
# # @persistent
# def update_mesh_attributes_depsgraph():
# #     if context.scene.updating_mesh_attributes_is_active == False:
# #         context.scene.updating_mesh_attributes_is_active = True
# #         # print("invoco default da handler")
#     bpy.ops.wm.update_mesh_attributes_modal_operator('INVOKE_DEFAULT')
# #         # bpy.app.handlers.depsgraph_update_post.remove(update_mesh_attributes_depsgraph)
    

# class VIEW_3D_OT_update_all_meshes_attributes(Operator):
#     """Update RoMa attributes of all the RoMa masses. Updated attributes are floor to floor height,..."""
#     bl_idname = "wm.update_all_meshes_attributes_modal_operator"
#     bl_label = "Update RoMa attributes of the all RoMa masses"
    
#     # oldTime = 0
#     # newTime = 0
    
#     # def __init__(self):
#     #     pass
    
#     # def __del__(self):
#     #     pass
    
#     def execute (self, context):
#         scene = bpy.context.scene
#         projectUses = scene.roma_use_name_list
        
#         objs = bpy.data.objects
#         #get the current active object
#         activeObj = bpy.context.active_object
#         if hasattr(activeObj, "type"):
#             activeObjMode = activeObj.mode
#         for ob in objs:
#             if ob is not None and ob.type == 'MESH' and "RoMa object" in ob.data:
#                 bpy.context.view_layer.objects.active = ob
#                 objMode = ob.mode
#                 mesh = ob.data
#                 bpy.ops.object.mode_set(mode="EDIT")
#                 bm = bmesh.from_edit_mesh(mesh)
                
        #         bMesh_typology = bm.faces.layers.int["roma_typology_id"]
        #         bMesh_storeys = bm.faces.layers.int["roma_number_of_storeys"]
        #         bMesh_use_list_A = bm.faces.layers.int["roma_list_use_id_A"]
        #         bMesh_use_list_B = bm.faces.layers.int["roma_list_use_id_B"]
        #         bMesh_storey_list_A = bm.faces.layers.int["roma_list_storey_A"]
        #         bMesh_storey_list_B = bm.faces.layers.int["roma_list_storey_B"]
        #         bMesh_height_A = bm.faces.layers.int["roma_list_height_A"]
        #         bMesh_height_B = bm.faces.layers.int["roma_list_height_B"]
        #         bMesh_height_C = bm.faces.layers.int["roma_list_height_C"]
        #         bMesh_height_D = bm.faces.layers.int["roma_list_height_D"]
        #         bMesh_height_E = bm.faces.layers.int["roma_list_height_E"]
        #         bMesh_void = bm.faces.layers.int["roma_list_void"]
                
        #         for bmFace in bm.faces:
        #             typology_id = bmFace[bMesh_typology] 
        #             numberOfStoreys = bmFace[bMesh_storeys] 
                    
        #             item = next(i for i in bpy.context.scene.roma_typology_name_list if i["id"] == typology_id)
        #             use_list = item.useList
        #             # uses are listed top to bottom, but they need to
        #             # be added bottom to top                       
        #             # use_list = use_list [::-1]
                    
        #             useSplit = use_list.split(";")
        #             useSplit.reverse()

        #             use_id_list_A = "1"
        #             use_id_list_B = "1"
        #             storey_list_A = "1"
        #             storey_list_B = "1"
        #             height_A = "1"
        #             height_B = "1"
        #             height_C = "1"
        #             height_D = "1"
        #             height_E = "1"
        #             liquidPosition = [] # to count how many liquid uses they are
        #             fixedStoreys = 0 # to count how many fixed storeys they are
        #             void = "1"
                    
        #             for enum, el in enumerate(useSplit):
        #                 #### list_use_id
        #                 if int(el) < 10:
        #                     tmpUse = "0" + el
        #                 else:
        #                     tmpUse = el
        #                 use_id_list_A += tmpUse[0]
        #                 use_id_list_B += tmpUse[1]

        #                 ###setting the values for each use
        #                 for use in projectUses:
        #                     if use.id == int(el):
        #                         # number of storeys for the use
        #                         # if a use is "liquid" the number of storeys is set as 00
        #                         if use.liquid: 
        #                             storeys = "00"
        #                             liquidPosition.append(enum)
        #                         else:
        #                             fixedStoreys += use.storeys
        #                             storeys = str(use.storeys)
        #                             if use.storeys < 10:
        #                                 storeys = "0" + storeys
                                        
        #                         storey_list_A += storeys[0]
        #                         storey_list_B += storeys[1]
                                
        #                         void += str(int(use.void))
                                
        #                         #### floor to floor height for each use, stored in A, B, C, ...
        #                         #### due to the fact that arrays can't be used
        #                         #### and array like (3.555, 12.664, 0.123)
        #                         #### is saved as
        #                         #### A (1010) tens
        #                         #### B (1320) units
        #                         #### C (1561) first decimal
        #                         #### D (1562) second decimal
        #                         #### E (1543) third decimal
        #                         #### each array starting with 1 since a number can't start with 0
        #                         height = str(round(use.floorToFloor,3))
        #                         if use.floorToFloor < 10:
        #                             height = "0" + height
        #                         height_A += height[0]
        #                         height_B += height[1]
        #                         try:
        #                             # height[3]
        #                             height_C += height[3]
        #                             try:
        #                                 height_D += height[4]
        #                                 try:
        #                                     height_E += height[5]
        #                                 except:
        #                                     height_E += "0"
        #                             except:
        #                                 height_D += "0"
        #                                 height_E += "0"
        #                         except:
        #                             height_C += "0"
        #                             height_D += "0"
        #                             height_E += "0"
        #                         break
               

                   
                    
        #             storeyCheck = numberOfStoreys - fixedStoreys - len(liquidPosition)
        #             # if the typology has more storeys than the selected mass
        #             # some extra storeys are added
        #             if storeyCheck < 1: 
        #                 scene.attribute_mass_storeys = fixedStoreys + len(liquidPosition)
        #             storeyLeft = numberOfStoreys - fixedStoreys
                    
        #             if len(liquidPosition) > 0:
        #                  # the 1 at the start of the number is removed
        #                 storey_list_A = storey_list_A[1:]
        #                 storey_list_B = storey_list_B[1:]
        #                 n = storeyLeft/len(liquidPosition)
        #                 liquidStoreyNumber = math.floor(n)

        #                 insert = str(liquidStoreyNumber)
        #                 if liquidStoreyNumber < 10:
        #                     insert = "0" + insert
                            
        #                 index = 0
        #                 while index < len(liquidPosition):
        #                     el = liquidPosition[index]
        #                     # if the rounding of the liquid storeys is uneven,
        #                     # the last liquid floor is increased of 1 storey
        #                     if index == len(liquidPosition) -1 and  math.modf(n)[0] > 0:
        #                         insert = str(liquidStoreyNumber +1) 
        #                         if liquidStoreyNumber +1 < 10:
        #                             insert = "0" + insert

        #                     storey_list_A = storey_list_A[:el] + insert[0] + storey_list_A[el +1:]
        #                     storey_list_B = storey_list_B[:el] + insert[1] + storey_list_B[el +1:]
        #                     index += 1
        #                 # the 1 is readded  
        #                 storey_list_A = "1" + storey_list_A
        #                 storey_list_B = "1" + storey_list_B
                        
        #             bmFace[bMesh_use_list_A] = int(use_id_list_A)
        #             bmFace[bMesh_use_list_B] = int(use_id_list_B)
        #             bmFace[bMesh_storey_list_A] = int(storey_list_A)
        #             bmFace[bMesh_storey_list_B] = int(storey_list_B)
        #             bmFace[bMesh_height_A] = int(height_A)
        #             bmFace[bMesh_height_B] = int(height_B)
        #             bmFace[bMesh_height_C] = int(height_C)
        #             bmFace[bMesh_height_D] = int(height_D)
        #             bmFace[bMesh_height_E] = int(height_E)
        #             bmFace[bMesh_void] = int(void)
                
        #         bmesh.update_edit_mesh(mesh)
        #         bm.free()
        #         bpy.ops.object.mode_set(mode=objMode)

        # #return the focus to the current active object
        # if hasattr(activeObj, "type"):
        #     bpy.context.view_layer.objects.active = activeObj
        #     bpy.ops.object.mode_set(mode=activeObjMode)
        
        # return {'FINISHED'}
        
    
    
        
    # def invoke(self, context, event):
    #     self.execute(context)
    #     return {'RUNNING_MODAL'}
