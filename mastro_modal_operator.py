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

import bpy
import blf
import bmesh
import gpu
from gpu_extras.batch import batch_for_shader

from bpy.app.handlers import persistent
from bpy_extras import view3d_utils
from bpy.types import Operator

from mathutils import Vector

from .mastro_schedule import MaStro_MathNode, execute_active_node_tree
# from datetime import datetime
# import math

previous_selection = {}

# show the faces of a MaStro object as overlay
class VIEW_3D_OT_show_mastro_overlay(Operator):
    bl_idname = "wm.show_mastro_overlay"
    bl_label = "Show MaStro selection"
    
    _handle = None
    
    @staticmethod
    def handle_add(self, context):
        if VIEW_3D_OT_show_mastro_overlay._handle is None:
            VIEW_3D_OT_show_mastro_overlay._handle =bpy.types.SpaceView3D.draw_handler_add(draw_callback_selection_overlay,
                                                                                           (self, context),
                                                                                           'WINDOW',
                                                                                           'POST_VIEW')
            
    @staticmethod
    def handle_remove(self, context):
        bpy.types.SpaceView3D.draw_handler_remove(VIEW_3D_OT_show_mastro_overlay._handle, 'WINDOW')
        VIEW_3D_OT_show_mastro_overlay._handle = None
    
    def execute(self, context):
        if bpy.context.preferences.addons['mastro'].preferences.toggleSelectionOverlay:    
            self.handle_add(self, context)
        else:
            self.handle_remove(self, context)
        return {'FINISHED'}
    
    def invoke(self, context, event):  # attributes["storey A"][index][1].value = int(list_storey_A)
      
        
        self.execute(context)
        return {'RUNNING_MODAL'}

def draw_selection_overlay(context):
    obj = bpy.context.active_object
    if hasattr(obj, "data") and "MaStro object" in obj.data and "MaStro mass" in obj.data:
        coords = []
        edgeIndices = []
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        mesh = obj.data
        
        if mesh.is_editmode:
            bm = bmesh.from_edit_mesh(mesh)
            
            # draw the edges of the selected object
            for vert in bm.verts:
                # print(vert.index, vert.co, obj.matrix_world @ vert.co)
                coords.append(obj.matrix_world @ vert.co)
                
            for edge in bm.edges:
                tmpEdge = (edge.verts[0].index, edge.verts[1].index)
                edgeIndices.append(tmpEdge)
                
            
            batch = batch_for_shader(shader, 'LINES', {"pos": coords}, indices=edgeIndices)
            r, g, b, a = [c for c in bpy.context.preferences.addons['mastro'].preferences.massEdgeColor]
            shader.uniform_float("color", (r, g, b, a))
        
            gpu.state.line_width_set(bpy.context.preferences.addons['mastro'].preferences.massEdgeSize)
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
            r, g, b, a = [c for c in bpy.context.preferences.addons['mastro'].preferences.massFaceColor]
            shader.uniform_float("color", (r, g, b, a))       
            # gpu.state.blend_set("NONE")
            batch.draw(shader)
            
            dbm.free()
            bm.free()
            
    elif hasattr(obj, "data") and "MaStro object" in obj.data and "MaStro street" in obj.data:
        coords = []
        edgeIndices = []
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        mesh = obj.data
        
        if mesh.is_editmode:
            bm = bmesh.from_edit_mesh(mesh)
            
            # draw the edges of the selected object
            for vert in bm.verts:
                coords.append(obj.matrix_world @ vert.co)
                
            for edge in bm.edges:
                tmpEdge = (edge.verts[0].index, edge.verts[1].index)
                edgeIndices.append(tmpEdge)
                bMesh_street_id = bm.edges.layers.int["mastro_street_id"]
                street_id = edge[bMesh_street_id]
            
                batch = batch_for_shader(shader, 'LINES', {"pos": coords}, indices=edgeIndices)
                # r, g, b, a = [c for c in bpy.context.preferences.addons['mastro'].preferences.massEdgeColor]
                r, g, b, a = [c for c in bpy.context.scene.mastro_street_name_list[street_id].streetEdgeColor]
                shader.uniform_float("color", (r, g, b, a))
                
                gpu.state.line_width_set(bpy.context.preferences.addons['mastro'].preferences.streetEdgeSize)
                gpu.state.blend_set("ALPHA")
                batch.draw(shader)
                edgeIndices = []

            bm.free()
    
def draw_callback_selection_overlay(self, context):
    draw_selection_overlay(context)

# def mastro_selection_overlay(self, context):
#     bpy.ops.wm.show_mastro_overlay()
    
# @persistent
# def update_show_overlay(scene, context):
#     if scene.show_selection_overlay_is_active != bpy.context.preferences.addons['mastro'].preferences.toggleSelectionOverlay:
#         scene.show_selection_overlay_is_active = bpy.context.preferences.addons['mastro'].preferences.toggleSelectionOverlay
#         bpy.ops.wm.show_mastro_overlay('INVOKE_DEFAULT')
    
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
#     #  and "MaStro object" in context.object.data
#     # and context.object.type == 'MESH'
#     def invoke(self, context, event):
#         # obj = bpy.context.active_object
#         # if obj is not None and obj.type == "MESH" and "MaStro object" in obj.data:
#         #     # if event.mouse_
#         #     # context.scene.mouse_event = event
#         if event.type != "":
#             context.scene.mouse_keyboard_event = event.type
        
#         return {'FINISHED'}

# show the overlayed attributes (type, number of storeys, etc...)
class VIEW_3D_OT_show_mastro_attributes(Operator):
    bl_idname = "wm.show_mastro_attributes"
    bl_label = "Show MaStro attributes"
    
    _handle = None  # keep function handler
    
    @staticmethod
    def handle_add(self, context):
        if VIEW_3D_OT_show_mastro_attributes._handle is None:
            VIEW_3D_OT_show_mastro_attributes._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px_show_attributes, (self, context),
                                                                        'WINDOW',
                                                                        'POST_PIXEL')

    @staticmethod
    def handle_remove(self, context):
        if VIEW_3D_OT_show_mastro_attributes._handle is not None:
            bpy.types.SpaceView3D.draw_handler_remove(VIEW_3D_OT_show_mastro_attributes._handle, 'WINDOW')
        VIEW_3D_OT_show_mastro_attributes._handle = None
    
    def execute(self, context):
        if VIEW_3D_OT_show_mastro_attributes._handle is None:
            self.handle_add(self, context)
            context.area.tag_redraw()
        else:
            self.handle_remove(self, context)
            context.area.tag_redraw()
        return {'FINISHED'}
    
def draw_main_show_attributes(context):
    obj = bpy.context.active_object
    if hasattr(obj, "data") and "MaStro object" in obj.data and "Mastro mass" in obj.data:
        # obj.update_from_editmode()
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
        bm.faces.ensure_lookup_table()      
        
        bMesh_wall = bm.edges.layers.int["mastro_wall_id"]
        bMesh_normal = bm.edges.layers.int["mastro_inverted_normal"]
       
        # bMesh_plot = bm.faces.layers.int["mastro_plot_id"]
        # bMesh_block = bm.faces.layers.int["mastro_block_id"]
        bMesh_typology = bm.faces.layers.int["mastro_typology_id"]
        bMesh_storey = bm.faces.layers.int["mastro_number_of_storeys"]
        bMesh_floor = bm.faces.layers.int["mastro_floor_id"]
    
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
        r, g, b, a = [c for c in bpy.context.preferences.addons['mastro'].preferences.fontColor]
        blf.color(font_id, r, g, b, a)
        font_size =  bpy.context.preferences.addons['mastro'].preferences.fontSize
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
                for n in bpy.context.scene.mastro_wall_name_list:
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
                plotId = obj.mastro_props['mastro_plot_attribute']
                for n in scene.mastro_plot_name_list:
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
                blockId = obj.mastro_props['mastro_block_attribute']
                for n in scene.mastro_block_name_list:
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
            #     for n in bpy.context.scene.mastro_plot_name_list:
            #         if n.id == idPlot:
            #             text_plot = (("Plot: " + n.name), 0)
            #             line_width = blf.dimensions(font_id, text_plot[0])[0]
            #             vert_offset = half_line_height
            #             text.append(text_plot)
            #             text.append(cr)
            #             break
            # if bpy.context.window_manager.toggle_block_name:   
            #     for n in bpy.context.scene.mastro_block_name_list:
            #         if n.id == idBlock:
            #             text_block = (("Block: " + n.name), 0)
            #             if blf.dimensions(font_id, text_block[0])[0] > line_width:
            #                 line_width = blf.dimensions(font_id, text_block[0])[0]
            #             vert_offset += half_line_height
            #             text.append(text_block)
            #             text.append(cr)
            #             break
            if bpy.context.window_manager.toggle_typology_name:   
                for n in scene.mastro_typology_name_list:
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
                for n in scene.mastro_floor_name_list:
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
    bpy.ops.wm.show_mastro_attributes()
    
# Manage all the required updates fired by depsgraph_update  
@persistent
def updates(scene, depsgraph):
    ###############################################################################
    # update the values in the UI accordingly with the selected faces #############
    ###############################################################################
    obj = bpy.context.active_object
    if obj:
        if obj is not None and obj.type == "MESH" and "MaStro object" in obj.data and "MaStro mass" in obj.data:
            if scene.previous_selection_object_name != obj.name:
                scene.previous_selection_object_name = obj.name
                scene.previous_selection_face_id = -1
                # if obj is not None and obj.type == "MESH" and "MaStro object" in obj.data and "MaStro mass" in obj.data:
                if obj.mode == "OBJECT":
                    blockId = obj.mastro_props['mastro_block_attribute']
                    plotId = obj.mastro_props['mastro_plot_attribute']
                    
                    block = scene.mastro_block_name_list[blockId].name
                    plot = scene.mastro_plot_name_list[plotId].name
                    
                    scene.mastro_block_name_current[0].name = block
                    scene.mastro_plot_name_current[0].name = plot
            else:
                # if obj is not None and obj.type == "MESH" and "MaStro object" in obj.data and obj.mode == 'EDIT':
                if obj.mode == 'EDIT':
                    bm = bmesh.from_edit_mesh(obj.data)
                    bMesh_storeys = bm.faces.layers.int["mastro_number_of_storeys"]
                    bMesh_storey_list_A = bm.faces.layers.int["mastro_list_storey_A"]
                    bMesh_storey_list_B = bm.faces.layers.int["mastro_list_storey_B"]
                    bMesh_typology = bm.faces.layers.int["mastro_typology_id"]
                
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
                        if storeys == 0: # in case a new face is created in edit mode, the number of set storeys is 1
                            storeys = 1
                            bpy.ops.object.set_mesh_attribute_storeys
                        scene["attribute_mass_storeys"] = storeys
                        
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
                    
    ###############################################################################
    # show graphic overlays #######################################################
    ###############################################################################

    if scene.show_selection_overlay_is_active != bpy.context.preferences.addons['mastro'].preferences.toggleSelectionOverlay:
        scene.show_selection_overlay_is_active = bpy.context.preferences.addons['mastro'].preferences.toggleSelectionOverlay
        bpy.ops.wm.show_mastro_overlay('INVOKE_DEFAULT')
     
        
    ####################################################################################################
    # when a typology is selected, it is necessary to update the #######################################
    # uses in the UIList using the ones stored in scene.mastro_typology_uses_name_list ###################
    ####################################################################################################
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
                list = scene.mastro_typology_name_list[selected_typology_index].useList    
                split_list = list.split(";")
                for el in split_list:
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

    #############################################################################################
    # is the selection has changed, some  data in the MaStro schedule need to be updated ##########
    #############################################################################################
    # Detect selection changes or added or remove objects
    global previous_selection
    newSelection = False
    current_selection = {obj.name: obj for obj in scene.objects if obj.select_get()}
    if current_selection != previous_selection:
        for obj in current_selection: 
            mesh = bpy.data.objects[obj].data
            if "MaStro object" in mesh:
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
    
