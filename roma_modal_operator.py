import bpy
import blf
# from mathutils import Vector, Matrix
from bpy_extras import view3d_utils
# import numpy as np
import bmesh
from datetime import datetime

# https://blender.stackexchange.com/questions/107617/how-to-align-modal-draw-to-the-middle-of-the-3d-viewport
# https://blender.stackexchange.com/questions/237428/get-pixel-coords-for-vertex-in-viewport
class VIEW3D_OT_show_Roma_attributes(bpy.types.Operator):
    """Draw a line with the mouse"""
    bl_idname = "view3d.show_roma_attributes"
    bl_label = "Simple Modal View3D Operator"

    font_info = {
        "font_id": 0,
        "handler": None,
                }
    
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
                    print(storey) 
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

  
    def modal(self, context, event):
        # If overridden outside of the 3D view
        try:
            context.area.tag_redraw()
        except AttributeError:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'CANCELLED'}
        # If there is no active 3D view
        if bpy.context.area.type !="VIEW_3D":
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'CANCELLED'}

        # if event.type in {'RIGHTMOUSE', 'ESC'}:
        #     bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
        #     return {'CANCELLED'}
        
        if not context.window_manager.toggle_plot_name and not context.window_manager.toggle_block_name and not context.window_manager.toggle_use_name and not context.window_manager.toggle_storey_number:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'FINISHED'}

        #　All other operations are permitted.
        return {'PASS_THROUGH'}


    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':
            # the arguments we pass the the callback
            args = (self, context)
            # Add the region OpenGL drawing callback
            # draw in view space with 'POST_VIEW' and 'PRE_VIEW'
            self._handle = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_px, args, 'WINDOW', 'POST_PIXEL')
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}


