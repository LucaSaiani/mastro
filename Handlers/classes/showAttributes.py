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
import bpy
import blf
import bmesh
import gpu

from gpu_extras.batch import batch_for_shader
from bpy_extras import view3d_utils
from bpy.types import Operator
from mathutils import Vector

from ...__init__ import get_prefs


# show the overlayed attributes (type, number of storeys, etc...)
class VIEW_3D_OT_show_mastro_attributes(Operator):
    bl_idname = "wm.show_mastro_attributes"
    bl_label = "Show MaStro attributes"
    
    _handle_2D = None  # keep function handler
    _handle_3D = None
    
    @staticmethod
    def handle_add_2D(self, context):
        if VIEW_3D_OT_show_mastro_attributes._handle_2D is None:
            VIEW_3D_OT_show_mastro_attributes._handle_2D = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px_show_attributes_2D, (self, context),
                                                                        'WINDOW',
                                                                        'POST_PIXEL')
    @staticmethod
    def handle_add_3D(self, context):
        if VIEW_3D_OT_show_mastro_attributes._handle_3D is None:
            VIEW_3D_OT_show_mastro_attributes._handle_3D = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px_show_attributes_3D, (self, context),
                                                                        'WINDOW',
                                                                        'POST_VIEW')

    @staticmethod
    def handle_remove_2D(self, context):
        if VIEW_3D_OT_show_mastro_attributes._handle_2D is not None:
            bpy.types.SpaceView3D.draw_handler_remove(VIEW_3D_OT_show_mastro_attributes._handle_2D, 'WINDOW')
        VIEW_3D_OT_show_mastro_attributes._handle_2D = None
    
    @staticmethod
    def handle_remove_3D(self, context):
        if VIEW_3D_OT_show_mastro_attributes._handle_3D is not None:
            bpy.types.SpaceView3D.draw_handler_remove(VIEW_3D_OT_show_mastro_attributes._handle_3D, 'WINDOW')
        VIEW_3D_OT_show_mastro_attributes._handle_3D = None

    
    def execute(self, context):
        if VIEW_3D_OT_show_mastro_attributes._handle_2D is None:
            self.handle_add_2D(self, context)
            context.area.tag_redraw()
        else:
            self.handle_remove_2D(self, context)
            context.area.tag_redraw()
            
        if VIEW_3D_OT_show_mastro_attributes._handle_3D is None:
            self.handle_add_3D(self, context)
            context.area.tag_redraw()
        else:
            self.handle_remove_3D(self, context)
            context.area.tag_redraw()
        return {'FINISHED'}
    
def draw_selection_overlay(context):
    obj = bpy.context.active_object
    if hasattr(obj, "data") and obj.data is not None and "MaStro object" in obj.data:
        prefs = get_prefs()
        mesh = obj.data
        if mesh.is_editmode:
            if "MaStro mass" in obj.data:
                coords = []
                edgeIndices = []
                shader = gpu.shader.from_builtin('UNIFORM_COLOR')
                
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
                    
                    r, g, b, a = [c for c in prefs.massEdgeColor]
                    shader.uniform_float("color", (r, g, b, a))
                
                    gpu.state.line_width_set(prefs.massEdgeSize)
                    gpu.state.blend_set("ALPHA")
                    batch.draw(shader)
                    
                    # draw the selected faces
                    if bpy.context.scene.tool_settings.mesh_select_mode[2]:
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
                        r, g, b, a = [c for c in prefs.massFaceColor]
                        shader.uniform_float("color", (r, g, b, a))       
                        # gpu.state.blend_set("NONE")
                        batch.draw(shader)
                        
                        dbm.free()
                        bm.free()
            
                    if bpy.context.scene.tool_settings.mesh_select_mode[1]:
                        show_wall_overlay(obj)

            elif "MaStro block" in obj.data:
                show_block_overlay(obj)
            elif "MaStro street" in obj.data:
                show_street_overlay(obj)

def show_block_overlay(obj):
    theme = bpy.context.preferences.themes[0].view_3d
    color_editmesh_active = theme.editmesh_active
    color_edge_mode_select = theme.edge_mode_select
    
    prefs = get_prefs()

    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    mesh = obj.data
    
    if mesh.is_editmode:
        bm = bmesh.from_edit_mesh(mesh)
        
        # active edge
        active_edge = None
        for e in bm.edges:
            if e.select and e.is_valid and e == bm.select_history.active:
                active_edge = e
                break
    else:
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()    
        # bm.faces.ensure_lookup_table()  
        
    bMesh_block_id_layer = bm.edges.layers.int["mastro_typology_id_EDGE"]
    projectTypologies = bpy.context.scene.mastro_typology_name_list
    
    # matrix = bpy.context.region_data.perspective_matrix
    for edge in bm.edges:
        v1 = obj.matrix_world @ edge.verts[0].co
        v2 = obj.matrix_world @ edge.verts[1].co
        coords = [v1, v2]
        indices = [(0, 1)]
        
        typology_id = edge[bMesh_block_id_layer]
        index = next((i for i, elem in enumerate(projectTypologies) if elem.id == typology_id), None)
        if 0 <= typology_id < len(bpy.context.scene.mastro_typology_name_list):
            if mesh.is_editmode:
                if edge is active_edge:
                    r, g, b, a = color_editmesh_active
                elif edge.select:
                    r, g, b, a = (*color_edge_mode_select[:], 1.0)
                else:
                    r, g, b = [c for c in bpy.context.scene.mastro_typology_name_list[index].typologyEdgeColor]
                    a = 1.0
            else:
                r, g, b = [c for c in bpy.context.scene.mastro_typology_name_list[index].typologyEdgeColor]
                a = 1.0
            
            rgba = (r, g, b, a)   
            shader.uniform_float("color", rgba)    
                
            gpu.state.line_width_set(prefs.blockEdgeSize)
            gpu.state.blend_set("ALPHA")
            batch = batch_for_shader(shader, 'LINES', {"pos": coords}, indices=indices)
            batch.draw(shader)

    bm.free()
    
    
# a function to show wall overlays
def show_wall_overlay(obj):
    theme = bpy.context.preferences.themes[0].view_3d
    color_editmesh_active = theme.editmesh_active
    color_edge_mode_select = theme.edge_mode_select
    
    prefs = get_prefs()

    coords = []
    # edgeIndices = []  
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    mesh = obj.data
    
    if mesh.is_editmode:
        bm = bmesh.from_edit_mesh(mesh)
        
        # active edge
        active_edge = None
        for e in bm.edges:
            if e.select and e.is_valid and e == bm.select_history.active:
                active_edge = e
                break
    else:
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()    
        active_edge = None
        
    bMesh_wall_id_layer = bm.edges.layers.int["mastro_wall_id"]
    projectWalls = bpy.context.scene.mastro_wall_name_list
    
    # matrix = bpy.context.region_data.perspective_matrix
    for edge in bm.edges:
        v1 = obj.matrix_world @ edge.verts[0].co
        v2 = obj.matrix_world @ edge.verts[1].co
        coords = [v1, v2]
        indices = [(0, 1)]
        
        wall_id = edge[bMesh_wall_id_layer]
        index = next((i for i, elem in enumerate(projectWalls) if elem.id == wall_id), None)
        if 0 <= wall_id < len(bpy.context.scene.mastro_wall_name_list):
            if edge is active_edge:
                rgba = color_editmesh_active
            elif edge.select:
                rgba = (*color_edge_mode_select[:], 1.0)
            else:
                r, g, b = [c for c in bpy.context.scene.mastro_wall_name_list[index].wallEdgeColor]
                rgba = (r, g, b, 1.0)   
            shader.uniform_float("color", rgba)    
                
            gpu.state.line_width_set(prefs.wallEdgeSize)
            gpu.state.blend_set("ALPHA")
            batch = batch_for_shader(shader, 'LINES', {"pos": coords}, indices=indices)
            batch.draw(shader)

    bm.free()


# a function to show the street overlays
def show_street_overlay(obj):
    theme = bpy.context.preferences.themes[0].view_3d
    color_editmesh_active = theme.editmesh_active
    color_edge_mode_select = theme.edge_mode_select
    
    prefs = get_prefs()
 
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    mesh = obj.data
    
    
    if mesh.is_editmode:
        bm = bmesh.from_edit_mesh(mesh)
        
        # active edge
        active_edge = None
        for e in bm.edges:
            if e.select and e.is_valid and e == bm.select_history.active:
                active_edge = e
                break
    else:
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()    
        
    bMesh_street_id_layer = bm.edges.layers.int["mastro_street_id"]
    projectStreets = bpy.context.scene.mastro_street_name_list

    for edge in bm.edges:
        v1 = obj.matrix_world @ edge.verts[0].co
        v2 = obj.matrix_world @ edge.verts[1].co
        coords = [v1, v2]
        indices = [(0, 1)]
        
        street_id = edge[bMesh_street_id_layer]
        index = next((i for i, elem in enumerate(projectStreets) if elem.id == street_id), None)
        if 0 <= street_id < len(bpy.context.scene.mastro_street_name_list):
            if mesh.is_editmode:
                if edge is active_edge:
                    r, g, b, a = color_editmesh_active
                elif edge.select:
                    r, g, b, a = (*color_edge_mode_select[:], 1.0)
                else:
                    r, g, b = [c for c in bpy.context.scene.mastro_street_name_list[index].streetEdgeColor]
                    a = 1.0
            else:
                r, g, b = [c for c in bpy.context.scene.mastro_street_name_list[index].streetEdgeColor]
                a = 1.0
            rgba = (r, g, b, a)   
            shader.uniform_float("color", rgba) 
            
            batch = batch_for_shader(
                shader, 'LINES',
                {"pos": coords},
                indices = indices
            )
                
            gpu.state.line_width_set(prefs.streetEdgeSize)
            gpu.state.blend_set("ALPHA")
            
            batch.draw(shader)
  
    bm.free()

def draw_main_show_attributes_2D(context):
    obj = bpy.context.active_object
    if hasattr(obj, "data") and "MaStro object" in obj.data and ("MaStro mass" in obj.data or "MaStro block" in obj.data):
        # obj.update_from_editmode()
        prefs = get_prefs()
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
        
        if "MaStro mass" in obj.data:
            # bMesh_wall = bm.edges.layers.int["mastro_wall_id"]
            bMesh_normal = bm.edges.layers.bool["mastro_inverted_normal"]
        
            # bMesh_block = bm.faces.layers.int["mastro_block_id"]
            # bMesh_building = bm.faces.layers.int["mastro_building_id"]
            bMesh_typology = bm.faces.layers.int["mastro_typology_id"]
            bMesh_storey = bm.faces.layers.int["mastro_number_of_storeys"]
            bMesh_floor = bm.faces.layers.int["mastro_floor_id"]
        elif "MaStro block" in obj.data:
            bMesh_normal = bm.edges.layers.bool["mastro_inverted_normal_EDGE"]
            bMesh_typology = bm.edges.layers.int["mastro_typology_id_EDGE"]
            bMesh_storey = bm.edges.layers.int["mastro_number_of_storeys_EDGE"]
            
    
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
        r, g, b, a = [c for c in prefs.fontColor]
        blf.color(font_id, r, g, b, a)
        font_size =  prefs.fontSize
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
            
            # idWall = bmEdge[bMesh_wall]
            normal = bmEdge[bMesh_normal]
            
            text_edge = []
            text_typology = ""
            text_normal = ""
            text_storey = ""
            
            if "MaStro block" in obj.data:
                idUse = bmEdge[bMesh_typology]
                storey = bmEdge[bMesh_storey]
                if bpy.context.window_manager.toggle_typology_name:   
                    for n in scene.mastro_typology_name_list:
                        if n.id == idUse:
                            if n.name != "":
                                text_typology = (("Typology: " + n.name), 0)
                                if blf.dimensions(font_id, text_typology[0])[0] > line_width:
                                    line_width = blf.dimensions(font_id, text_typology[0])[0]
                                vert_offset += half_line_height
                                text_edge.append(text_typology)
                                text_edge.append(cr)           
                                break
                if bpy.context.window_manager.toggle_storey_number:  
                    text_storey = (("N° of storeys: " + str(storey)), 0)
                    if blf.dimensions(font_id, text_storey[0])[0] > line_width:
                                line_width = blf.dimensions(font_id, text_storey[0])[0]
                    vert_offset += half_line_height
                    text_edge.append(text_storey)
                    text_edge.append(cr)  
                if bpy.context.window_manager.toggle_block_normal: 
                    if normal == True:   
                        symbol = "⥌"
                        text_normal = (symbol, 0)
                        line_width = blf.dimensions(font_id, symbol)[0] 
                        vert_offset += (blf.dimensions(font_id, symbol)[1] * 1.45)/2
                        text_edge.append(text_normal)
                            
                            
            # if bpy.context.window_manager.toggle_wall_name:   
            #     for n in bpy.context.scene.mastro_wall_name_list:
            #         if n.id == idWall:
            #             text_edge = (n.name, 0)
            #             line_width = blf.dimensions(font_id, n.name)[0]
            #             vert_offset = -1 * half_line_height
            #             text_edge.append(text_edge)
            #             text_edge.append(cr)
            #             break
            if "MaStro mass" in obj.data:
                if bpy.context.window_manager.toggle_wall_normal:
                    if normal == True:   
                        symbol = "⥌"
                        text_normal = (symbol, 0)
                        line_width = blf.dimensions(font_id, symbol)[0]
                        vert_offset += (blf.dimensions(font_id, symbol)[1] * 1.45)/2
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
        
        if "MaStro mass" in obj.data:
            for bmFace in bm.faces:
                center_local = bmFace.calc_center_median()
                
                center = matrix @ center_local # convert the coordinates from local to world
                # idBlock = bmFace[bMesh_block]
                # idBuilding = bmFace[bMesh_building]
                idUse = bmFace[bMesh_typology]
                idFloor = bmFace[bMesh_floor]
                storey = bmFace[bMesh_storey]
                
                line_width = 0
                vert_offset = 0
                
                text_face = []
                text_block = ""
                text_building = ""
                text_typology = ""
                text_storey = ""
                text_floor = ""
                
                # blockId
                if bpy.context.window_manager.toggle_block_name:   
                    blockId = obj.mastro_props['mastro_block_attribute']
                    for n in scene.mastro_block_name_list:
                        if n.id == blockId:
                            if n.name != "":
                                text_block = (("Block: " + n.name), 0)
                                line_width = blf.dimensions(font_id, text_block[0])[0]
                                vert_offset = half_line_height
                                text_face.append(text_block)
                                text_face.append(cr)
                            break
                    
                # buildingId
                if bpy.context.window_manager.toggle_building_name:   
                    buildingId = obj.mastro_props['mastro_building_attribute']
                    for n in scene.mastro_building_name_list:
                        if n.id == buildingId:
                            if n.name != "":
                                text_building = (("Building: " + n.name), 0)
                                if blf.dimensions(font_id, text_building[0])[0] > line_width:
                                    line_width = blf.dimensions(font_id, text_building[0])[0]
                                    vert_offset += half_line_height
                                text_face.append(text_building)
                                text_face.append(cr)
                            break
                    
                # if bpy.context.window_manager.toggle_block_name:   
                #     for n in bpy.context.scene.mastro_block_name_list:
                #         if n.id == idBlock:
                #             text_block = (("Block: " + n.name), 0)
                #             line_width = blf.dimensions(font_id, text_block[0])[0]
                #             vert_offset = half_line_height
                #             text.append(text_block)
                #             text.append(cr)
                #             break
                # if bpy.context.window_manager.toggle_building_name:   
                #     for n in bpy.context.scene.mastro_building_name_list:
                #         if n.id == idBuilding:
                #             text_building = (("Building: " + n.name), 0)
                #             if blf.dimensions(font_id, text_building[0])[0] > line_width:
                #                 line_width = blf.dimensions(font_id, text_building[0])[0]
                #             vert_offset += half_line_height
                #             text.append(text_building)
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

def draw_main_show_attributes_3D(context):
    obj = bpy.context.active_object
    if hasattr(obj, "data") and "MaStro object" in obj.data:
        mesh = obj.data
        if mesh.is_editmode == True and bpy.context.window_manager.toggle_show_data_edit_mode:
            draw_selection_overlay(obj)
        elif mesh.is_editmode == False:
            if "MaStro street" in obj.data and bpy.context.window_manager.toggle_street_color:
                show_street_overlay(obj)
            if "MaStro mass" in obj.data and bpy.context.window_manager.toggle_wall_type:
                show_wall_overlay(obj)
            if "MaStro block" in obj.data and bpy.context.window_manager.toggle_block_typology_color:
                show_block_overlay(obj)
    
def draw_callback_px_show_attributes_2D(self, context):
    draw_main_show_attributes_2D(context)
    

def draw_callback_px_show_attributes_3D(self, context):
    draw_main_show_attributes_3D(context)
        

def update_show_attributes(self, context):
    bpy.ops.wm.show_mastro_attributes()