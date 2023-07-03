import bpy
import blf
from bpy.app.handlers import persistent
from mathutils import Vector
from bpy_extras import view3d_utils
# import numpy as np
import bmesh
from datetime import datetime

# refresh_roma_invoked = False
# running_refresh_modal = False
# running_refresh_modal_event = None

# _event = None
# from bpy.props import IntProperty, FloatProperty


# https://blender.stackexchange.com/questions/107617/how-to-align-modal-draw-to-the-middle-of-the-3d-viewport
# https://blender.stackexchange.com/questions/237428/get-pixel-coords-for-vertex-in-viewport
# class VIEW3D_OT_show_Roma_attributes(bpy.types.Operator):
#     """Overlay RoMa attributes on the screen"""
#     bl_idname = "view3d.show_roma_attributes"
#     bl_label = "Overlay RoMa attributes on the screen"

#     font_info = {
#         "font_id": 0,
#         "handler": None,
#                 }
    
#     def draw_callback_px(self, context, event):
#         obj = bpy.context.active_object
#         if "RoMa object" in obj.data:
            
#             obj.update_from_editmode()
            
#             mesh = obj.data
#             # mesh_attributes = mesh.attributes["roma_block_id"].data.items()
#             matrix = obj.matrix_world
            
#             if obj.mode == 'EDIT':
#                 bm = bmesh.from_edit_mesh(mesh)
#             else:
#                 bm = bmesh.new()
#                 bm.from_mesh(mesh)

#             bm.faces.ensure_lookup_table()      
#             bMesh_plot = bm.faces.layers.int["roma_plot_id"]
#             bMesh_block = bm.faces.layers.int["roma_block_id"]
#             bMesh_use = bm.faces.layers.int["roma_use_id"]
#             bMesh_storey = bm.faces.layers.int["roma_number_of_storeys"]

#             for a in bpy.context.screen.areas:
#                 if a.type == 'VIEW_3D':
#                     space = a.spaces.active
#                     r3d = space.region_3d
#                     # plane_no = r3d.view_rotation @ Vector((0, 0, -1))
#                     region = a.regions[-1]
#                     break
#             else:
#                 assert False, "Requires a 3D view"
        
#             font_id = self.font_info["font_id"]
#             r, g, b, a = [c for c in bpy.context.preferences.addons['roma'].preferences.fontColor]
#             blf.color(font_id, r, g, b, a)
#             font_size =  bpy.context.preferences.addons['roma'].preferences.fontSize
#             blf.size(font_id, font_size)
            
#             # multi line text
#             # https://blender.stackexchange.com/questions/31780/multi-line-text-in-blf-with-multi-colour-option
#             line_height = (blf.dimensions(font_id, "M")[1] * 1.45)
#             cr = "Carriage Return"
            
#             for bmFace in bm.faces:
#                 center_local = bmFace.calc_center_median()
                
#                 center = matrix @ center_local # convert the coordinates from local to world
#                 idPlot = bmFace[bMesh_plot]
#                 idBlock = bmFace[bMesh_block]
#                 idUse = bmFace[bMesh_use]
#                 storey = bmFace[bMesh_storey]
                
#                 text = []
#                 text_plot = ""
#                 text_block = ""
#                 text_use = ""
#                 text_storey = ""
                
#                 if bpy.context.window_manager.toggle_plot_name:   
#                     for n in bpy.context.scene.roma_plot_name_list:
#                         if n.id == idPlot:
#                             text_plot = (("Plot: " + n.name), 0)
#                             text.append(text_plot)
#                             text.append(cr)
#                             break
#                 if bpy.context.window_manager.toggle_block_name:   
#                     for n in bpy.context.scene.roma_block_name_list:
#                         if n.id == idBlock:
#                             text_block = (("Block: " + n.name), 0)
#                             text.append(text_block)
#                             text.append(cr)
#                             break
#                 if bpy.context.window_manager.toggle_use_name:   
#                     for n in bpy.context.scene.roma_use_name_list:
#                         if n.id == idUse:
#                             text_use = (("Use: " + n.name), 0)
#                             text.append(text_use)
#                             text.append(cr)           
#                             break
#                 if bpy.context.window_manager.toggle_storey_number:  
#                    # print(storey) 
#                     text_storey = (("N° of storeys: " + str(storey)), 0)
#                     text.append(text_storey)
                   
                
                
#                 coord = view3d_utils.location_3d_to_region_2d(region, r3d, center)
#                 x_offset = 0
#                 y_offset = 0
#                 for pstr in text:
#                     if len(pstr) == 2:
#                         string = pstr[0]
#                         text_width, text_height = blf.dimensions(font_id, string)
#                         blf.position(font_id, (coord.x + x_offset), (coord.y + y_offset), 0)
#                         blf.draw(font_id, string)
#                         x_offset += text_width
#                     else:
#                         x_offset = 0
#                         y_offset -= line_height       
#             bm.free()

  
#     def modal(self, context, event):
#         # If overridden outside of the 3D view
#         try:
#             context.area.tag_redraw()
#         except AttributeError:
#             print("Refresh cancelled due ", AttributeError)
#             bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
#             return {'CANCELLED'}
        
#         # If there is no active 3D view
#         #if bpy.context.area.type !="VIEW_3D":
#         # areas = bpy.context.screen.areas.items()
#         # views_3d = []
#         # for area in areas:
#         #     if area[1].type == 'VIEW_3D':
#         #         views_3d.append(area)
                
#         # if len(views_3d) == 0:
#         #     self.report({'WARNING'}, "View3D not found, cannot run operator")
#         #     bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
#         #     return {'CANCELLED'}

#         # if event.type in {'RIGHTMOUSE', 'ESC'}:
#         #     bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
#         #     return {'CANCELLED'}
        
#         # if not context.window_manager.toggle_plot_name and not context.window_manager.toggle_block_name and not context.window_manager.toggle_use_name and not context.window_manager.toggle_storey_number:
#         #     print("rimuovo")
#         #     bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
#         #     return {'FINISHED'}

#         #　All other operations are permitted.
#         return {'PASS_THROUGH'}

#     def invoke(self, context, event):
#         areas = bpy.context.screen.areas.items()
#         views_3d = []
#         for area in areas:
#             if area[1].type == 'VIEW_3D':
#                 views_3d.append(area)
                
#         if len(views_3d) > 0:
#             # if context.area.type == 'VIEW_3D':
#             # the arguments we pass the the callback
#             args = (self, context)
#             # Add the region OpenGL drawing callback
#             # draw in view space with 'POST_VIEW' and 'PRE_VIEW'
#             self._handle = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_px, args, 'WINDOW', 'POST_PIXEL')
#             # context.window_manager.modal_handler_add(self)
#             return {'RUNNING_MODAL'}
#         else:
#             self.report({'WARNING'}, "View3D not found, cannot run operator")
#             return {'CANCELLED'}
        
class show_Roma_attributes():
    font_info = {
            "font_id": 0,
            "handler": None,
        }
   
    def __init__(self):
        self.font_info["font_id"] = 0

        # set the font drawing routine to run every frame
        if self.font_info["handler"] == None:
            self.font_info["handler"] = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_px, (None, None), 'WINDOW', 'POST_PIXEL')  
        # return(self.font_info["handler"]) 
        
    def end(self):
        try:
            bpy.types.SpaceView3D.draw_handler_remove(show_Roma_attributes.font_info["handler"], 'WINDOW')
            show_Roma_attributes.font_info["handler"] = None
        except:
            pass
        
    def draw_callback_px(self, context, event):
        obj = bpy.context.active_object
        if hasattr(obj, "data") and "RoMa object" in obj.data:
            
            obj.update_from_editmode()
            
            mesh = obj.data
            matrix = obj.matrix_world
            
            if obj.mode == 'EDIT':
                bm = bmesh.from_edit_mesh(mesh)
            else:
                bm = bmesh.new()
                bm.from_mesh(mesh)

            bm.verts.ensure_lookup_table()
            bm.edges.ensure_lookup_table()    
            bMesh_facade = bm.edges.layers.int["roma_facade_id"]
            bMesh_normal = bm.edges.layers.int["roma_inverted_normal"]
            
            bm.faces.ensure_lookup_table()      
            bMesh_plot = bm.faces.layers.int["roma_plot_id"]
            bMesh_block = bm.faces.layers.int["roma_block_id"]
            bMesh_use = bm.faces.layers.int["roma_use_id"]
            bMesh_storey = bm.faces.layers.int["roma_number_of_storeys"]
            bMesh_floor = bm.faces.layers.int["roma_floor_id"]

            for a in bpy.context.screen.areas:
                if a.type == 'VIEW_3D':
                    space = a.spaces.active
                    r3d = space.region_3d
                    # plane_no = r3d.view_rotation @ Vector((0, 0, -1))
                    region = a.regions[-1]
                    break
            else:
                assert False, "Requires a 3D view"
        
            font_id = self.font_info["font_id"]
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
                
                idFacade = bmEdge[bMesh_facade]
                normal = bmEdge[bMesh_normal]
                
                text = []
                text_edge = ""
                text_normal = ""
                
                if bpy.context.window_manager.toggle_facade_name:   
                    for n in bpy.context.scene.roma_facade_name_list:
                        if n.id == idFacade:
                            text_edge = (n.name, 0)
                            line_width = blf.dimensions(font_id, n.name)[0]
                            vert_offset = -1 * half_line_height
                            text.append(text_edge)
                            text.append(cr)
                            break
                if bpy.context.window_manager.toggle_facade_normal:
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
                        text.append(text_normal)
                        
                
                        
                coord = view3d_utils.location_3d_to_region_2d(region, r3d, center)
                x_offset = (-1 * line_width) / 2
                y_offset = -1 * vert_offset
                for pstr in text:
                    if len(pstr) == 2:
                        string = pstr[0]
                        text_width, text_height = blf.dimensions(font_id, string)
                        blf.position(font_id, (coord.x + x_offset), (coord.y + y_offset), 0)
                        blf.draw(font_id, string)
                        x_offset += text_width
                    else:
                        x_offset = (-1 * line_width) / 2
                        y_offset -= line_height
                        
                
                
            
            for bmFace in bm.faces:
                center_local = bmFace.calc_center_median()
                
                center = matrix @ center_local # convert the coordinates from local to world
                idPlot = bmFace[bMesh_plot]
                idBlock = bmFace[bMesh_block]
                idUse = bmFace[bMesh_use]
                idFloor = bmFace[bMesh_floor]
                storey = bmFace[bMesh_storey]
                
                line_width = 0
                vert_offset = 0
                
                text = []
                text_plot = ""
                text_block = ""
                text_use = ""
                text_storey = ""
                text_floor = ""
                
                if bpy.context.window_manager.toggle_plot_name:   
                    for n in bpy.context.scene.roma_plot_name_list:
                        if n.id == idPlot:
                            text_plot = (("Plot: " + n.name), 0)
                            line_width = blf.dimensions(font_id, text_plot[0])[0]
                            vert_offset = half_line_height
                            text.append(text_plot)
                            text.append(cr)
                            break
                if bpy.context.window_manager.toggle_block_name:   
                    for n in bpy.context.scene.roma_block_name_list:
                        if n.id == idBlock:
                            text_block = (("Block: " + n.name), 0)
                            if blf.dimensions(font_id, text_block[0])[0] > line_width:
                                line_width = blf.dimensions(font_id, text_block[0])[0]
                            vert_offset += half_line_height
                            text.append(text_block)
                            text.append(cr)
                            break
                if bpy.context.window_manager.toggle_use_name:   
                    for n in bpy.context.scene.roma_use_name_list:
                        if n.id == idUse:
                            text_use = (("Use: " + n.name), 0)
                            if blf.dimensions(font_id, text_use[0])[0] > line_width:
                                line_width = blf.dimensions(font_id, text_use[0])[0]
                            vert_offset += half_line_height
                            text.append(text_use)
                            text.append(cr)           
                            break
                if bpy.context.window_manager.toggle_floor_name:   
                    for n in bpy.context.scene.roma_floor_name_list:
                        if n.id == idFloor:
                            text_floor = (("Floor: " + n.name), 0)
                            if blf.dimensions(font_id, text_floor[0])[0] > line_width:
                                line_width = blf.dimensions(font_id, text_floor[0])[0]
                            vert_offset += half_line_height
                            text.append(text_floor)
                            text.append(cr)           
                            break
                if bpy.context.window_manager.toggle_storey_number:  
                    text_storey = (("N° of storeys: " + str(storey)), 0)
                    if blf.dimensions(font_id, text_storey[0])[0] > line_width:
                                line_width = blf.dimensions(font_id, text_storey[0])[0]
                    vert_offset += half_line_height
                    text.append(text_storey)
                
                
                coord = view3d_utils.location_3d_to_region_2d(region, r3d, center)
                x_offset = (-1 * line_width) / 2
                y_offset = vert_offset - half_line_height
                for pstr in text:
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
    
        
def update_show_attributes(self, context):
    if (self.toggle_show_data):
        show_Roma_attributes()
    else:
        show_Roma_attributes.end(self)
    
       

        
class VIEW3D_OT_update_Roma_mesh_attributes(bpy.types.Operator):
    """Update RoMa attributes of the active mesh in the mass panel"""
    bl_idname = "object.update_roma_mesh_attributes"
    bl_label = "Update RoMa attributes of the active mesh in the mass panel"
 
#     def __init__(self):
#         pass
#         # global refresh_roma_invoked
#         # print("Start", refresh_roma_invoked)

#     def __del__(self):
#         global refresh_roma_invoked
#         refresh_roma_invoked = False
#         # print("Finito il ciclo naturalmente", refresh_roma_invoked)
        
#     def execute(self, context):
#         # global plotName
#         # global blockName
#         # global useName
        
#         obj = bpy.context.active_object
#         # if tuple(bpy.context.scene.tool_settings.mesh_select_mode)[2] == True: #we are selecting faces
#         #print("controllo dati")
        
#         obj.update_from_editmode()
#         mesh = obj.data

#         # activeFace = mesh.polygons[mesh.polygons.active]
#         selected_edges = [e for e in mesh.edges if e.select]
#         selected_faces = [p for p in mesh.polygons if p.select]
            
#         if len(selected_edges) > 0 or len(selected_faces) > 0:
#             selected_edge_indices = []
#             selected_face_indices = []
            
#             if len(selected_edges) > 0:
#                 for f in selected_edges:
#                     selected_edge_indices.append(f.index)
                    
#             if len(selected_faces) > 0:    
#                 for f in selected_faces:
#                     selected_face_indices.append(f.index)
                
#             scene = bpy.context.scene
            
#             bm = bmesh.from_edit_mesh(mesh)
#             print("AGGIUNGO BMESH")
#             bm.edges.ensure_lookup_table()

#             bMesh_facade = bm.edges.layers.int["roma_facade_id"]
#             bMesh_normal = bm.edges.layers.int["roma_inverted_normal"]
            
#             bm.faces.ensure_lookup_table()
#             bMesh_plot = bm.faces.layers.int["roma_plot_id"]
#             bMesh_block = bm.faces.layers.int["roma_block_id"]
#             bMesh_use = bm.faces.layers.int["roma_use_id"]
#             bMesh_storeys = bm.faces.layers.int["roma_number_of_storeys"]
#             bMesh_floor = bm.faces.layers.int["roma_floor_id"]

#             selected_bmEdges = [edge for edge in bm.edges if edge.select]
#             selected_bmFaces = [face for face in bm.faces if face.select]
            
#             # active_vert = isinstance(bm.select_history.active, bmesh.types.BMVert)
#             active_edge = isinstance(bm.select_history.active, bmesh.types.BMEdge)
#             active_face = isinstance(bm.select_history.active, bmesh.types.BMFace)
            
#             # if bm.faces.active is not None:
#                 # print("NONE FACES !!!!!!!!!!!!!")
#             # else:
#             if active_edge:
#                 bMesh_active_index = bm.select_history.active.index
                
#                 for edge in selected_edges:
#                     bm.edges.ensure_lookup_table()
#                     bm.edges[edge.index].select = False
                    
#                 for bmEdge in selected_bmEdges:
#                     bm.faces.ensure_lookup_table()
#                     facade_type = bmEdge[bMesh_facade]
#                     facade_normal = bmEdge[bMesh_normal]
                    
#                     if bmEdge.index ==  bMesh_active_index:
#                         ############# FACADE TYPE ####################
#                         if scene.attribute_facade_id != facade_type:
#                             scene.attribute_facade_id = facade_type
#                         if scene.roma_facade_name_current[0].id != facade_type:
#                             scene.roma_facade_name_current[0].id = facade_type
#                             for n in scene.roma_facade_name_list:
#                                 if n.id == scene.roma_facade_name_current[0].id:
#                                     scene.roma_facade_name_current[0].name = " " + n.name 
#                                     break
#                         ############# FACADE NORMAL ####################
#                         print(scene.attribute_facade_normal*1, facade_normal)
#                         # if (scene.attribute_facade_normal*1) != facade_normal:
#                         if facade_normal == -1:
#                             print("true")
#                             scene.attribute_facade_normal = True
#                         else:
#                             print("false")
#                             scene.attribute_facade_normal = False
                        
                        
#             elif active_face:
#                 bMesh_active_index = bm.select_history.active.index
                
#                 for face in selected_faces:
#                     bm.faces[face.index].select = False
                    
#                 for bmFace in selected_bmFaces:
#                     plot = bmFace[bMesh_plot]
#                     block = bmFace[bMesh_block]
#                     use = bmFace[bMesh_use] 
#                     storey = bmFace[bMesh_storeys]
#                     floor = bmFace[bMesh_floor]
#                     # if bm.faces.active is not None and bmFace.index ==  bMesh_active_index:
#                     if bmFace.index ==  bMesh_active_index:
#                         ############# PLOT ####################
#                         if scene.attribute_mass_plot_id != plot:
#                             scene.attribute_mass_plot_id = plot
#                         if scene.roma_plot_name_current[0].id != plot:
#                             scene.roma_plot_name_current[0].id = plot
#                             # if plotName["id"] == 0:
#                             #     plotName["name"] = None
#                             # else:
#                             for n in scene.roma_plot_name_list:
#                                 if n.id == scene.roma_plot_name_current[0].id:
#                                     scene.roma_plot_name_current[0].name = " " + n.name 
#                                     break
                                
#                         ############# BLOCK ####################
#                         if scene.attribute_mass_block_id != block:
#                             scene.attribute_mass_block_id = block
#                         if scene.roma_block_name_current[0].id != block:
#                             scene.roma_block_name_current[0].id = block
#                             for n in scene.roma_block_name_list:
#                                 if n.id == scene.roma_block_name_current[0].id:
#                                     scene.roma_block_name_current[0].name = " " + n.name 
#                                     break
                                
#                         ############# USE ####################
#                         if scene.attribute_mass_use_id != use:
#                             scene.attribute_mass_use_id = use
#                         if scene.roma_use_name_current[0].id != use:
#                             scene.roma_use_name_current[0].id = use
#                             for n in scene.roma_use_name_list:
#                                 if n.id == scene.roma_use_name_current[0].id:
#                                     scene.roma_use_name_current[0].name = " " + n.name 
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
#             bmesh.update_edit_mesh(mesh)
#             bm.free()
                

#             bm = bmesh.from_edit_mesh(mesh)
#             bm.edges.ensure_lookup_table()
#             for index in selected_edge_indices:
#                 bm.edges[index].select = True
                
#             bm.faces.ensure_lookup_table()
#             for index in selected_face_indices:
#                 bm.faces[index].select = True
                    
#             bmesh.update_edit_mesh(mesh)
#             bm.free() 
#             print("RIMUOVO BMESH")
#     # checkingFace = False
            
            
#         return {'FINISHED'}
                
    
    # def modal(self, context, event):
    #     # self.mouseEventType = event.type
    #     # global refresh_roma_invoked
    #     if event.type in {'LEFTMOUSE', 'RIGHTMOUSE'}:
    #         self.execute(context)
    #         # print("runno")
    #     else:
    #         # print("CANCELLATO")
    #         return {'CANCELLED'}
        
    #     return {"RUNNING_MODAL"}
    
    # def invoke(self, context, event):
    #     # if event.type in {'LEFTMOUSE', 'RIGHTMOUSE'}:
    #     #     print("MOUSE",event.type)
    #     #     self.execute(context)
    #     #     context.window_manager.modal_handler_add(self)
    #     #     return {'RUNNING_MODAL'}
    #     # else:
    #     #     print("CANCELLATO")
    #     #     return{'CANCELLED'}
    #     self.execute(context)
    #     context.window_manager.modal_handler_add(self)
    #     return {"RUNNING_MODAL"}
        
        

# @persistent
# def refresh_roma_mesh_attributes(dummy):
#     global refresh_roma_invoked
#     if refresh_roma_invoked == False:
#         obj = bpy.context.active_object
#         if hasattr(obj, "type") and obj.type == 'MESH':
#             if "RoMa object" in obj.data and obj.mode == 'EDIT':
#                 refresh_roma_invoked = True
#                 bpy.ops.object.update_roma_mesh_attributes('INVOKE_DEFAULT')
  
    
# @persistent
# def refresh_roma_mesh_attributes(scene, context):
#     global running_refresh_modal
#     global running_refresh_modal_event
#     if running_refresh_modal == False:
#         running_refresh_modal = True
#         prev_event = running_refresh_modal_event
#         running_refresh_modal_event = get_event('INVOKE_REGION_WIN')
#         if prev_event != running_refresh_modal_event:
#             prev_event = running_refresh_modal_event
#             print(running_refresh_modal_event)
#         running_refresh_modal = False
  
# class VIEW_OT_get_event(bpy.types.Operator):
#     bl_idname  = "wm.get_event"
#     bl_label   = ""
    
#     def invoke(self, context, event):
#         global _event
#         _event = str(event.type)
#         return {'FINISHED'}
    
# def get_event(exec_context='INVOKE_DEFAULT'):
#     global _event
#     bpy.ops.wm.get_event(exec_context)
#     return _event


class VIEW_3D_OT_update_mesh_attributes(bpy.types.Operator):
    """Update RoMa attributes of the active mesh in the RoMa panel"""
    bl_idname = "wm.update_mesh_attributes_modal_operator"
    bl_label = "Update RoMa attributes of the active mesh in the RoMa panel"
    
    oldTime = 0
    newTime = 0
    
    def __init__(self):
        pass
    
    def __del__(self):
        pass
    
    def execute(self, context):
    # global plotName
        # global blockName
        # global useName
        
        obj = bpy.context.active_object
        # if tuple(bpy.context.scene.tool_settings.mesh_select_mode)[2] == True: #we are selecting faces
        #print("controllo dati")
        
        obj.update_from_editmode()
        mesh = obj.data

        # activeFace = mesh.polygons[mesh.polygons.active]
        selected_edges = [e for e in mesh.edges if e.select]
        selected_faces = [p for p in mesh.polygons if p.select]
            
        if len(selected_edges) > 0 or len(selected_faces) > 0:
            selected_edge_indices = []
            selected_face_indices = []
            
            if len(selected_edges) > 0:
                for f in selected_edges:
                    selected_edge_indices.append(f.index)
                    
            if len(selected_faces) > 0:    
                for f in selected_faces:
                    selected_face_indices.append(f.index)
                
            scene = bpy.context.scene
            
            bm = bmesh.from_edit_mesh(mesh)
            # print("AGGIUNGO BMESH")
            bm.edges.ensure_lookup_table()

            bMesh_facade = bm.edges.layers.int["roma_facade_id"]
            bMesh_normal = bm.edges.layers.int["roma_inverted_normal"]
            
            bm.faces.ensure_lookup_table()
            bMesh_plot = bm.faces.layers.int["roma_plot_id"]
            bMesh_block = bm.faces.layers.int["roma_block_id"]
            bMesh_use = bm.faces.layers.int["roma_use_id"]
            bMesh_storeys = bm.faces.layers.int["roma_number_of_storeys"]
            bMesh_floor = bm.faces.layers.int["roma_floor_id"]

            selected_bmEdges = [edge for edge in bm.edges if edge.select]
            selected_bmFaces = [face for face in bm.faces if face.select]
            
            # active_vert = isinstance(bm.select_history.active, bmesh.types.BMVert)
            active_edge = isinstance(bm.select_history.active, bmesh.types.BMEdge)
            active_face = isinstance(bm.select_history.active, bmesh.types.BMFace)
            
            # if bm.faces.active is not None:
                # print("NONE FACES !!!!!!!!!!!!!")
            # else:
            if active_edge:
                bMesh_active_index = bm.select_history.active.index
                
                for edge in selected_edges:
                    bm.edges.ensure_lookup_table()
                    bm.edges[edge.index].select = False
                    
                for bmEdge in selected_bmEdges:
                    bm.faces.ensure_lookup_table()
                    facade_type = bmEdge[bMesh_facade]
                    facade_normal = bmEdge[bMesh_normal]
                    
                    if bmEdge.index ==  bMesh_active_index:
                        ############# FACADE TYPE ####################
                        if scene.attribute_facade_id != facade_type:
                            scene.attribute_facade_id = facade_type
                        if scene.roma_facade_name_current[0].id != facade_type:
                            scene.roma_facade_name_current[0].id = facade_type
                            for n in scene.roma_facade_name_list:
                                if n.id == scene.roma_facade_name_current[0].id:
                                    scene.roma_facade_name_current[0].name = " " + n.name 
                                    break
                        ############# FACADE NORMAL ####################
                        print(scene.attribute_facade_normal*1, facade_normal)
                        # if (scene.attribute_facade_normal*1) != facade_normal:
                        if facade_normal == -1:
                            # print("true")
                            scene.attribute_facade_normal = True
                        else:
                            # print("false")
                            scene.attribute_facade_normal = False
                        
                        
            elif active_face:
                bMesh_active_index = bm.select_history.active.index
                
                for face in selected_faces:
                    bm.faces[face.index].select = False
                    
                for bmFace in selected_bmFaces:
                    plot = bmFace[bMesh_plot]
                    block = bmFace[bMesh_block]
                    use = bmFace[bMesh_use] 
                    storey = bmFace[bMesh_storeys]
                    floor = bmFace[bMesh_floor]
                    # if bm.faces.active is not None and bmFace.index ==  bMesh_active_index:
                    if bmFace.index ==  bMesh_active_index:
                        ############# PLOT ####################
                        if scene.attribute_mass_plot_id != plot:
                            scene.attribute_mass_plot_id = plot
                        if scene.roma_plot_name_current[0].id != plot:
                            scene.roma_plot_name_current[0].id = plot
                            # if plotName["id"] == 0:
                            #     plotName["name"] = None
                            # else:
                            for n in scene.roma_plot_name_list:
                                if n.id == scene.roma_plot_name_current[0].id:
                                    scene.roma_plot_name_current[0].name = " " + n.name 
                                    break
                                
                        ############# BLOCK ####################
                        if scene.attribute_mass_block_id != block:
                            scene.attribute_mass_block_id = block
                        if scene.roma_block_name_current[0].id != block:
                            scene.roma_block_name_current[0].id = block
                            for n in scene.roma_block_name_list:
                                if n.id == scene.roma_block_name_current[0].id:
                                    scene.roma_block_name_current[0].name = " " + n.name 
                                    break
                                
                        ############# USE ####################
                        if scene.attribute_mass_use_id != use:
                            scene.attribute_mass_use_id = use
                        if scene.roma_use_name_current[0].id != use:
                            scene.roma_use_name_current[0].id = use
                            for n in scene.roma_use_name_list:
                                if n.id == scene.roma_use_name_current[0].id:
                                    scene.roma_use_name_current[0].name = " " + n.name 
                                    break
                                
                        ############# STOREYS ####################
                        if scene.attribute_mass_storeys != storey:
                            scene.attribute_mass_storeys = storey
                            
                        ############# FLOOR ####################
                        if scene.attribute_floor_id != floor:
                            scene.attribute_floor_id = floor
                        if scene.roma_floor_name_current[0].id != floor:
                            scene.roma_floor_name_current[0].id = floor
                            for n in scene.roma_floor_name_list:
                                if n.id == scene.roma_floor_name_current[0].id:
                                    scene.roma_floor_name_current[0].name = " " + n.name 
                                    break
                    break   
            bmesh.update_edit_mesh(mesh)
            bm.free()
                

            bm = bmesh.from_edit_mesh(mesh)
            bm.edges.ensure_lookup_table()
            for index in selected_edge_indices:
                bm.edges[index].select = True
                
            bm.faces.ensure_lookup_table()
            for index in selected_face_indices:
                bm.faces[index].select = True
                    
            bmesh.update_edit_mesh(mesh)
            bm.free() 
            # print("RIMUOVO BMESH")
            
    # checkingFace = False
            
        bpy.context.scene.updating_mesh_attributes_is_active = False    
        return {'FINISHED'}

    
        
    def modal(self, context, event):
        if event.type in {'LEFTMOUSE', 'RIGHTMOUSE'}:
            obj = bpy.context.active_object
            if obj is not None and obj.type == "MESH":
                if obj.mode == "EDIT" and "RoMa object" in obj.data:
                # print("RUNNING MODAL")
                    self.execute(context)
               
            
            
            # obj = bpy.context.active_object
            # if hasattr(obj, "type") and obj.type == 'MESH':
            #     if "RoMa object" in obj.data and obj.mode == 'EDIT':
            #         now = datetime.now()
            #         self.newTime = int(now.timestamp() * 1000)
            #         if self.newTime > self.oldTime + 500:
            #             self.oldTime = self.newTime
            #             # print("Current Time =", int(now.timestamp() * 1000))
            #             self.execute(context)
        else:
            bpy.context.scene.updating_mesh_attributes_is_active = False
        return {'PASS_THROUGH'}
        
    def invoke(self, context, event):
        # now = datetime.now()
        # self.oldtime = int(now.timestamp() * 1000)
        # self.execute(context)
        # context.window_manager.modal_handler_add(self)
        # print("INVOKED")
        if event.type in {'LEFTMOUSE', 'RIGHTMOUSE'}:
            obj = bpy.context.active_object
            if obj is not None and obj.type == "MESH":
                if obj.mode == "EDIT" and "RoMa object" in obj.data:
                    # print("INVOKED")
                    self.execute(context)
        else:
            bpy.context.scene.updating_mesh_attributes_is_active = False
        return {'RUNNING_MODAL'}
       
       
    
# @persistent
# def update_mesh_attributes(scene, context):
#     bpy.ops.wm.update_mesh_attributes_modal_operator('INVOKE_DEFAULT')
    
@persistent
def update_mesh_attributes_depsgraph(scene, context):
    if bpy.context.scene.updating_mesh_attributes_is_active == False:
        bpy.context.scene.updating_mesh_attributes_is_active = True
        bpy.ops.wm.update_mesh_attributes_modal_operator('INVOKE_DEFAULT')
    # bpy.app.handlers.depsgraph_update_post.remove(update_mesh_attributes_depsgraph)
    
