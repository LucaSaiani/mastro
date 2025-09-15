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
import math

from gpu_extras.batch import batch_for_shader
from bpy.app.handlers import persistent
from bpy_extras import view3d_utils
from bpy.types import Operator
from mathutils import Vector

from .mastro_schedule import MaStro_MathNode, execute_active_node_tree
from .mastro_massing import update_mesh_edge_attributes_storeys, read_mesh_attributes_uses

# from datetime import datetime
# import math

known_scenes = set()

previous_selection = {}

# show the overlays when in edit mode
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
        if bpy.context.preferences.addons[__package__].preferences.toggleSelectionOverlay:    
            self.handle_add(self, context)
        else:
            try:
                self.handle_remove(self, context)
            except Exception as e: print(e)
        return {'FINISHED'}
    
    def invoke(self, context, event):  # attributes["storey A"][index][1].value = int(list_storey_A)
        self.execute(context)
        return {'RUNNING_MODAL'}

def draw_selection_overlay(context):
    obj = bpy.context.active_object
    if hasattr(obj, "data") and obj.data is not None and "MaStro object" in obj.data:
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
                    r, g, b, a = [c for c in bpy.context.preferences.addons[__package__].preferences.massEdgeColor]
                    shader.uniform_float("color", (r, g, b, a))
                
                    gpu.state.line_width_set(bpy.context.preferences.addons[__package__].preferences.massEdgeSize)
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
                        r, g, b, a = [c for c in bpy.context.preferences.addons[__package__].preferences.massFaceColor]
                        shader.uniform_float("color", (r, g, b, a))       
                        # gpu.state.blend_set("NONE")
                        batch.draw(shader)
                        
                        dbm.free()
                        bm.free()
            
                    if bpy.context.scene.tool_settings.mesh_select_mode[1]:
                        show_wall_overlay(obj)
                
            # elif ("MaStro street" in obj.data and
            #      not (bpy.context.window_manager.toggle_show_data and bpy.context.window_manager.toggle_street_color)
            #     ):
            elif "MaStro block" in obj.data:
                show_block_overlay(obj)
            elif "MaStro street" in obj.data:
                show_street_overlay(obj)

def draw_callback_selection_overlay(self, context):
    draw_selection_overlay(context)
    
# a function to show block overlays
def show_block_overlay(obj):
    theme = bpy.context.preferences.themes[0].view_3d
    color_editmesh_active = theme.editmesh_active
    color_edge_mode_select = theme.edge_mode_select

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
                
            gpu.state.line_width_set(bpy.context.preferences.addons[__package__].preferences.blockEdgeSize)
            gpu.state.blend_set("ALPHA")
            batch = batch_for_shader(shader, 'LINES', {"pos": coords}, indices=indices)
            batch.draw(shader)

    bm.free()
# a function to show wall overlays
def show_wall_overlay(obj):
    theme = bpy.context.preferences.themes[0].view_3d
    color_editmesh_active = theme.editmesh_active
    color_edge_mode_select = theme.edge_mode_select

    coords = []
    # edgeIndices = []  
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    mesh = obj.data
    
    # if mesh.is_editmode:
    bm = bmesh.from_edit_mesh(mesh)
    
    # active edge
    active_edge = None
    for e in bm.edges:
        if e.select and e.is_valid and e == bm.select_history.active:
            active_edge = e
            break
    
    # else:
    #     bm = bmesh.new()
    #     bm.from_mesh(mesh)
    #     bm.verts.ensure_lookup_table()
    #     bm.edges.ensure_lookup_table()    
        
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
                
            gpu.state.line_width_set(bpy.context.preferences.addons[__package__].preferences.wallEdgeSize)
            gpu.state.blend_set("ALPHA")
            batch = batch_for_shader(shader, 'LINES', {"pos": coords}, indices=indices)
            batch.draw(shader)

    bm.free()


# a function to show the street overlays
def show_street_overlay(obj):
    theme = bpy.context.preferences.themes[0].view_3d
    color_editmesh_active = theme.editmesh_active
    color_edge_mode_select = theme.edge_mode_select
    
    # dash shader to draw streets
    # vert_out = gpu.types.GPUStageInterfaceInfo("my_interface")
    # vert_out.smooth('FLOAT', "v_ArcLength")

    # dash_shader = gpu.types.GPUShaderCreateInfo()
    # dash_shader.push_constant('MAT4', "u_ViewProjectionMatrix")
    # dash_shader.push_constant('FLOAT', "u_Scale")
    # dash_shader.vertex_in(0, 'VEC3', "position")
    # dash_shader.vertex_in(1, 'FLOAT', "arcLength")
    # dash_shader.vertex_out(vert_out)
    # dash_shader.fragment_out(0, 'VEC4', "FragColor")

    # dash_shader.vertex_source(
    #     "void main()"
    #     "{"
    #     "  v_ArcLength = arcLength;"
    #     "  gl_Position = u_ViewProjectionMatrix * vec4(position, 1.0f);"
    #     "}"
    # )

    # dash_shader.fragment_source(
    #     "void main()"
    #     "{"
    #     "  if (step(sin(v_ArcLength * u_Scale), 0.5) == 1) discard;"
    #     "  FragColor = vec4(1.0);"
    #     "}"
    # )

    # shader = gpu.shader.create_from_info(dash_shader)
    
    
    # coords = []
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
        # bm.faces.ensure_lookup_table()  
        
    bMesh_street_id_layer = bm.edges.layers.int["mastro_street_id"]
    projectStreets = bpy.context.scene.mastro_street_name_list
    
    # matrix = bpy.context.region_data.perspective_matrix
    # dash_scale = 20 - bpy.context.preferences.addons[__package__].preferences.streetEdgeDashSize +1

    
    # coords = []
    # indices = []
    # arc_lengths = [0]

    for edge in bm.edges:
        v1 = obj.matrix_world @ edge.verts[0].co
        v2 = obj.matrix_world @ edge.verts[1].co
        coords = [v1, v2]
        indices = [(0, 1)]
        # l = (v2 - v1).length
        # arc_length = [0.0, l]
        
        
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
            # r, g, b = [c for c in bpy.context.scene.mastro_street_name_list[index].streetEdgeColor]
            # dash_shader.fragment_source(f"""
            #     void main() {{
            #         if (step(sin(v_ArcLength * u_Scale), 0.5) == 1.0) discard;
            #         FragColor = vec4({r}, {g}, {b}, {a});
            #     }}
            # """)

            
        # arc_lengths = [0]
        # for a, b in zip(coords[:-1], coords[1:]):
        #     arc_lengths.append(arc_lengths[-1] + (a - b).length)
        
            # shader = gpu.shader.create_from_info(dash_shader)   
            rgba = (r, g, b, a)   
            shader.uniform_float("color", rgba) 
            
            batch = batch_for_shader(
                shader, 'LINES',
                {"pos": coords},
                indices = indices
            )
            # shader.uniform_float("u_ViewProjectionMatrix", matrix)
            # shader.uniform_float("u_Scale", dash_scale)
                
            gpu.state.line_width_set(bpy.context.preferences.addons[__package__].preferences.streetEdgeSize)
            gpu.state.blend_set("ALPHA")
            
            batch.draw(shader)
        
    # for edge in bm.edges:
    #     coords = []
    #     indices = []

    #     v1 = obj.matrix_world @ edge.verts[0].co
    #     v2 = obj.matrix_world @ edge.verts[1].co
    #     coords = [v1, v2]
    #     indices = [(0, 1)]
        
    # if bMesh_street_id_layer:
    #     street_id = edge[bMesh_street_id_layer]
    #     projectStreets = bpy.context.scene.mastro_street_name_list
    #     index = next((i for i, elem in enumerate(projectStreets) if elem.id == street_id), None)
    #     if 0 <= street_id < len(bpy.context.scene.mastro_street_name_list):
    #         r, g, b, a = [c for c in bpy.context.scene.mastro_street_name_list[index].streetEdgeColor]
    #         dash_shader.fragment_source(f"""
    #             void main() {{
    #                 if (step(sin(v_ArcLength * u_Scale), 0.5) == 1.0) discard;
    #                 FragColor = vec4({r}, {g}, {b}, {a});
    #             }}
    #         """)
    #         shader = gpu.shader.create_from_info(dash_shader)   
    #         # shader.uniform_float("color", (r, g, b, a))
    #         # dash_shader.fragment_out("color", (r, g, b, a))
    #         #dash shader
            
    #         shader.uniform_float("u_ViewProjectionMatrix", matrix)
    #         shader.uniform_float("u_Scale", dash_scale)
            
    #         gpu.state.line_width_set(bpy.context.preferences.addons[__package__].preferences.streetEdgeSize)
    #         gpu.state.blend_set("ALPHA")
    #         # batch = batch_for_shader(shader, 'LINES', {"pos": coords}, indices=indices)   
    #         batch.draw(shader)

    bm.free()

# def mastro_selection_overlay(self, context):
#     bpy.ops.wm.show_mastro_overlay()
    
# @persistent
# def update_show_overlay(scene, context):
#     if scene.show_selection_overlay_is_active != bpy.context.preferences.addons[__package__].preferences.toggleSelectionOverlay:
#         scene.show_selection_overlay_is_active = bpy.context.preferences.addons[__package__].preferences.toggleSelectionOverlay
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
    
    
def draw_main_show_attributes_2D(context):
    obj = bpy.context.active_object
    if hasattr(obj, "data") and "MaStro object" in obj.data and ("MaStro mass" in obj.data or "MaStro block" in obj.data):
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
        
        if "MaStro mass" in obj.data:
            # bMesh_wall = bm.edges.layers.int["mastro_wall_id"]
            bMesh_normal = bm.edges.layers.int["mastro_inverted_normal"]
        
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
        r, g, b, a = [c for c in bpy.context.preferences.addons[__package__].preferences.fontColor]
        blf.color(font_id, r, g, b, a)
        font_size =  bpy.context.preferences.addons[__package__].preferences.fontSize
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
            # if "MaStro mass" in obj.data:
            #     if bpy.context.window_manager.toggle_wall_normal:
            #         if normal == True:   
            #             symbol = "↔️"
            #             text_normal = (symbol, 0)
            #             # if blf.dimensions(font_id, symbol)[0] > line_width:
            #             line_width = blf.dimensions(font_id, symbol)[0]
            #             # if vert_offset == 0:
            #             vert_offset += (blf.dimensions(font_id, symbol)[1] * 1.45)/2
            #             # else:
            #             #     vert_offset += (blf.dimensions(font_id, symbol)[1] * 1.45)* (-1.5)
                                
            #                 # vert_offset += half_line_height
            #             text_edge.append(text_normal)
                    
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
    if hasattr(obj, "data") and  "MaStro object" in obj.data:
        if "MaStro street" in obj.data and bpy.context.window_manager.toggle_street_color:
            # if mesh is in edit mode, the street overlay is already drawn
            mesh = obj.data
            if mesh.is_editmode == False:
                show_street_overlay(obj)
        if "MaStro mass" in obj.data and bpy.context.window_manager.toggle_wall_type:
            # if mesh is in edit mode, the wall overlay is already drawn
            mesh = obj.data
            if mesh.is_editmode == False:
                show_wall_overlay(obj)
        if "MaStro block" in obj.data and bpy.context.window_manager.toggle_block_typology_color:
            # if mesh is in edit mode, the block overlay is already drawn
            mesh = obj.data 
            if mesh.is_editmode == False:
                show_block_overlay(obj)
    

def draw_callback_px_show_attributes_2D(self, context):
    draw_main_show_attributes_2D(context)
    

def draw_callback_px_show_attributes_3D(self, context):
    draw_main_show_attributes_3D(context)
        

def update_show_attributes(self, context):
    bpy.ops.wm.show_mastro_attributes()
    


###############################################################################    
########## Manage all the required updates fired by depsgraph_update  #########
###############################################################################

# when a new scene is created, it is necessary to initialize the
# variables related to the scene
def check_new_scenes():
    from . import initLists
    global known_scenes
    current_scenes = set(bpy.data.scenes.keys())
    # print("current:")
    # for s in current_scenes: print(s)
    # print()
    new_scenes = current_scenes - known_scenes
    if new_scenes:
        for sceneName in new_scenes:
            print(f"Nuova scena creata: {sceneName}")
            initLists(sceneName)
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
                        bMesh_storeys = bm.faces.layers.int["mastro_number_of_storeys"]
                        bMesh_storey_list_A = bm.faces.layers.int["mastro_list_storey_A"]
                        bMesh_storey_list_B = bm.faces.layers.int["mastro_list_storey_B"]
                        bMesh_typology = bm.faces.layers.int["mastro_typology_id"]
                        bMesh_wall_type = bm.edges.layers.int["mastro_wall_id"]

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
                                    wall_type = bm.edges[scene.previous_selection_edge_id][bMesh_wall_type]
                                    # wall type name
                                    # since it is possible to sort wall types in the ui, it can be that the index of the element
                                    # in the list doesn't correspond to wall_id. Therefore it is necessary to find elements
                                    # in the way below
                                    item = next(i for i in scene.mastro_wall_name_list if i["id"] == wall_type)
                                    scene.mastro_wall_name_current[0].name = item.name
                            
                        if bpy.context.scene.tool_settings.mesh_select_mode[2]:
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
                                # if storeys == 0: # in case a new face is created in edit mode, the number of set storeys is 1
                                #     storeys = 1
                                    # bpy.ops.object.set_mesh_face_attribute_storeys
                                selected_faces = [face for face in bm.faces if face.select]
                                if len(selected_faces) == 1:
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

                        bMesh_storeys = bm.edges.layers.int["mastro_number_of_storeys_EDGE"]
                        bMesh_storey_list_A = bm.edges.layers.int["mastro_list_storey_A_EDGE"]
                        bMesh_storey_list_B = bm.edges.layers.int["mastro_list_storey_B_EDGE"]
                        
                        bMesh_block_normal = bm.edges.layers.bool["mastro_inverted_normal_EDGE"]
                        bMesh_block_depth = bm.edges.layers.float["mastro_block_depth_EDGE"]
                        
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
                                        bm.edges.ensure_lookup_table()
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
                                            data = update_mesh_edge_attributes_storeys(bpy.context, mesh, connected_edge.index)
                                            connected_edge[bMesh_storeys] = data["numberOfStoreys"]
                                            connected_edge[bMesh_storey_list_A] = int(data["storey_list_A"])
                                            connected_edge[bMesh_storey_list_B] = int(data["storey_list_B"])
                                            
                                            # update the block depth ------------------------------------------
                                            depth = bpy.context.scene.attribute_block_depth
                                            if depth == 0:
                                                depth = 18
                                            connected_edge[bMesh_block_depth] = depth
                                            
                                            # update the uses ------------------------------------------
                                            data = read_mesh_attributes_uses(bpy.context, typologySet = typology_id)
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
                                        bm.edges.ensure_lookup_table()
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
                                                data = update_mesh_edge_attributes_storeys(bpy.context, mesh, last_edge.index)
                                                last_edge[bMesh_storeys] = data["numberOfStoreys"]
                                                last_edge[bMesh_storey_list_A] = int(data["storey_list_A"])
                                                last_edge[bMesh_storey_list_B] = int(data["storey_list_B"])
                                                
                                                # update the block depth ------------------------------------------
                                                depth = bpy.context.scene.attribute_block_depth
                                                if depth == 0:
                                                    depth = 18
                                                last_edge[bMesh_block_depth] = depth

                                                # update the uses ------------------------------------------
                                                data = read_mesh_attributes_uses(bpy.context, typologySet = typology_id)
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
                                bm.edges.ensure_lookup_table()
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
                                        data = update_mesh_edge_attributes_storeys(bpy.context, mesh, active_edge.index)
                                        active_edge[bMesh_storeys] = data["numberOfStoreys"]
                                        active_edge[bMesh_storey_list_A] = int(data["storey_list_A"])
                                        active_edge[bMesh_storey_list_B] = int(data["storey_list_B"])
                                        
                                        # update the block depth ------------------------------------------
                                        depth = bpy.context.scene.attribute_block_depth
                                        if depth == 0:
                                            depth = 18
                                        active_edge[bMesh_block_depth] = depth
                                        
                                        # update typology and related uses ------------------------------------------
                                        data = read_mesh_attributes_uses(bpy.context, typologySet = typology_id)
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
                                            
                                        if bpy.context.scene.attribute_block_normal != block_normal:
                                            bpy.context.scene.attribute_block_normal = block_normal
                                    
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

    if scene.show_selection_overlay_is_active != bpy.context.preferences.addons[__package__].preferences.toggleSelectionOverlay:
        scene.show_selection_overlay_is_active = bpy.context.preferences.addons[__package__].preferences.toggleSelectionOverlay
        bpy.ops.wm.show_mastro_overlay('INVOKE_DEFAULT')
     
        
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
                list = scene.mastro_typology_name_list[selected_typology_index].useList    
                split_list = list.split(";")
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
    
