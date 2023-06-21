import bpy
import blf
from mathutils import Vector, Matrix
from bpy_extras import view3d_utils
import numpy as np

# https://blender.stackexchange.com/questions/107617/how-to-align-modal-draw-to-the-middle-of-the-3d-viewport
# https://blender.stackexchange.com/questions/237428/get-pixel-coords-for-vertex-in-viewport
class ModalDrawOperator(bpy.types.Operator):
    """Draw a line with the mouse"""
    bl_idname = "view3d.modal_operator"
    bl_label = "Simple Modal View3D Operator"

    font_info = {
        "font_id": 0,
        "handler": None,
                }
    
    def draw_callback_px(self, context, event):
        obj = bpy.context.active_object
        if "RoMa object" in obj.data:
            
            if obj.mode == 'EDIT':
                obj.update_from_editmode()
                
            mesh = obj.data
            mesh_attributes = mesh.attributes["roma_block_id"].data.items()
            matrix = obj.matrix_world

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
            blf.color(font_id, 0, 0.292, 1, 0.7)
            blf.size(font_id, 50.0)
            for f in mesh.polygons:
                center_local = f.center
                center = matrix @ center_local # convert the coordinates from local to world
                # text = str(f.index)
                try:
                    text = str(mesh_attributes[f.index][1].value)
                except:
                    text = ""
                coords = view3d_utils.location_3d_to_region_2d(region, r3d, center)
                blf.position(font_id, coords.x, coords.y, 0)
                blf.draw(font_id, text)

  
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
        
        if not context.window_manager.test_toggle:
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


