import bpy
import blf
from bpy.app.handlers import persistent
# from mathutils import Vector, Matrix
from bpy_extras import view3d_utils
# import numpy as np
import bmesh
# from datetime import datetime

refresh_roma_invoked = False


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
        # Default font.
        self.font_info["font_id"] = 0

        # set the font drawing routine to run every frame
        if self.font_info["handler"] == None:
            self.font_info["handler"] = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_px, (None, None), 'WINDOW', 'POST_PIXEL')  
            # print("Benvenuto ", show_Roma_attributes.font_info["handler"])
        # return(self.font_info["handler"]) 
        
    def end(self):
        bpy.types.SpaceView3D.draw_handler_remove(show_Roma_attributes.font_info["handler"], 'WINDOW')
        # print("Addio ", show_Roma_attributes.font_info["handler"])
        show_Roma_attributes.font_info["handler"] = None
        # self.font_info["hander"] = None
        
    def draw_callback_px(self, context, event):
        obj = bpy.context.active_object
        if "RoMa object" in obj.data:
            
            obj.update_from_editmode()
            
            mesh = obj.data
            # mesh_attributes = mesh.attributes["roma_block_id"].data.items()
            matrix = obj.matrix_world
            
            if obj.mode == 'EDIT':
                bm = bmesh.from_edit_mesh(mesh)
            else:
                bm = bmesh.new()
                bm.from_mesh(mesh)

            bm.faces.ensure_lookup_table()      
            bMesh_plot = bm.faces.layers.int["roma_plot_id"]
            bMesh_block = bm.faces.layers.int["roma_block_id"]
            bMesh_use = bm.faces.layers.int["roma_use_id"]
            bMesh_storey = bm.faces.layers.int["roma_number_of_storeys"]

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
            cr = "Carriage Return"
            
            for bmFace in bm.faces:
                center_local = bmFace.calc_center_median()
                
                center = matrix @ center_local # convert the coordinates from local to world
                idPlot = bmFace[bMesh_plot]
                idBlock = bmFace[bMesh_block]
                idUse = bmFace[bMesh_use]
                storey = bmFace[bMesh_storey]
                
                text = []
                text_plot = ""
                text_block = ""
                text_use = ""
                text_storey = ""
                
                if bpy.context.window_manager.toggle_plot_name:   
                    for n in bpy.context.scene.roma_plot_name_list:
                        if n.id == idPlot:
                            text_plot = (("Plot: " + n.name), 0)
                            text.append(text_plot)
                            text.append(cr)
                            break
                if bpy.context.window_manager.toggle_block_name:   
                    for n in bpy.context.scene.roma_block_name_list:
                        if n.id == idBlock:
                            text_block = (("Block: " + n.name), 0)
                            text.append(text_block)
                            text.append(cr)
                            break
                if bpy.context.window_manager.toggle_use_name:   
                    for n in bpy.context.scene.roma_use_name_list:
                        if n.id == idUse:
                            text_use = (("Use: " + n.name), 0)
                            text.append(text_use)
                            text.append(cr)           
                            break
                if bpy.context.window_manager.toggle_storey_number:  
                   # print(storey) 
                    text_storey = (("N° of storeys: " + str(storey)), 0)
                    text.append(text_storey)
                   
                
                
                coord = view3d_utils.location_3d_to_region_2d(region, r3d, center)
                x_offset = 0
                y_offset = 0
                for pstr in text:
                    if len(pstr) == 2:
                        string = pstr[0]
                        text_width, text_height = blf.dimensions(font_id, string)
                        blf.position(font_id, (coord.x + x_offset), (coord.y + y_offset), 0)
                        blf.draw(font_id, string)
                        x_offset += text_width
                    else:
                        x_offset = 0
                        y_offset -= line_height       
            bm.free()
    
        
def update_show_attributes(self, context):
    if self.toggle_plot_name or self.toggle_block_name or self.toggle_use_name or self.toggle_storey_number:
        # bpy.ops.view3d.show_roma_attributes('INVOKE_DEFAULT')
        # print("pippone")
        show_Roma_attributes()
    else:
        show_Roma_attributes.end(self)
    
       

        
class VIEW3D_OT_update_Roma_face_attributes(bpy.types.Operator):
    """Update RoMa attributes of the active face in the mass panel"""
    bl_idname = "object.update_roma_face_attributes"
    bl_label = "Update RoMa attributes of the active face in the mass panel"
 
    def __init__(self):
        pass
        # global refresh_roma_invoked
        # print("Start", refresh_roma_invoked)

    def __del__(self):
        global refresh_roma_invoked
        refresh_roma_invoked = False
        print("Finito il ciclo naturalmente", refresh_roma_invoked)
        
    def execute(self, context):
        # global plotName
        # global blockName
        # global useName
        
        obj = bpy.context.active_object
        if tuple(bpy.context.scene.tool_settings.mesh_select_mode)[2] == True: #we are selecting faces
            #print("controllo dati")
            
            obj.update_from_editmode()
            mesh = obj.data

            # activeFace = mesh.polygons[mesh.polygons.active]
            selected_faces = [p for p in mesh.polygons if p.select]
                
            if len(selected_faces) > 0:
                selected_indices = []
                for f in selected_faces:
                    selected_indices.append(f.index)
                    
                scene = bpy.context.scene
             
                bm = bmesh.from_edit_mesh(mesh)
                bm.faces.ensure_lookup_table()

                bMesh_plot = bm.faces.layers.int["roma_plot_id"]
                bMesh_block = bm.faces.layers.int["roma_block_id"]
                bMesh_use = bm.faces.layers.int["roma_use_id"]
                bMesh_storeys = bm.faces.layers.int["roma_number_of_storeys"]

                selected_bmFaces = [face for face in bm.faces if face.select]
                
                if bm.faces.active is not None:
                    # print("NONE FACES !!!!!!!!!!!!!")
                # else:
                    bMesh_active_index = bm.faces.active.index
                    
                    for face in selected_faces:
                        bm.faces[face.index].select = False
                        
                    for bmFace in selected_bmFaces:
                        plot = bmFace[bMesh_plot]
                        block = bmFace[bMesh_block]
                        use = bmFace[bMesh_use] 
                        storey = bmFace[bMesh_storeys]
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
                                
                            bmesh.update_edit_mesh(mesh)
                            bm.free()
                            break

                    bm = bmesh.from_edit_mesh(mesh)
                    bm.faces.ensure_lookup_table()
                    for index in selected_indices:
                        bm.faces[index].select = True
                            
                    bmesh.update_edit_mesh(mesh)
                bm.free() 
    # checkingFace = False
            
            
        return {'FINISHED'}
                
    
    def modal(self, context, event):
        # self.mouseEventType = event.type
        # global refresh_roma_invoked
        if event.type in {'LEFTMOUSE', 'RIGHTMOUSE'}:
            self.execute(context)
            # print("runno")
        else:
            print("CANCELLATO")
            return {'CANCELLED'}
        
        return {"RUNNING_MODAL"}
    
    def invoke(self, context, event):
        # if event.type in {'LEFTMOUSE', 'RIGHTMOUSE'}:
        #     print("MOUSE",event.type)
        #     self.execute(context)
        #     context.window_manager.modal_handler_add(self)
        #     return {'RUNNING_MODAL'}
        # else:
        #     print("CANCELLATO")
        #     return{'CANCELLED'}
        self.execute(context)
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}
        
        

@persistent
def refresh_roma_face_attributes(dummy):
    global refresh_roma_invoked
    if refresh_roma_invoked == False:
        obj = bpy.context.active_object
        if obj.type == 'MESH':
            if "RoMa object" in obj.data and obj.mode == 'EDIT':
                refresh_roma_invoked = True
                print("invoco", refresh_roma_invoked)
                bpy.ops.object.update_roma_face_attributes('INVOKE_DEFAULT')
    # return