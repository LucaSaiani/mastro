"""Dispatch operator — Alt+G in edit mode.

Checks the active element and forwards to the correct edit operator:
  rectangle → mastrocad.edit_rectangle
  circle    → mastrocad.edit_circle
  nothing   → warning
"""

import bpy
import bmesh

from ...Utils.mastro_cad.cad.rect_utils   import check_rect
from ...Utils.mastro_cad.cad.circle_utils import check_circle
from .CAD_mixin import CadMixin


class MESH_OT_MaStroCad_EditCAD(bpy.types.Operator):
    """Edit the active MaStroCad element (rectangle or circle)."""
    bl_idname  = "mastrocad.edit"
    bl_label   = "Edit MaStroCad Element"
    bl_options = {'INTERNAL'}   # not shown in search / menus

    @classmethod
    def poll(cls, context):
        if context.mode != 'EDIT_MESH' or context.active_object is None:
            return False

        bm   = bmesh.from_edit_mesh(context.active_object.data)
        seed = CadMixin.active_seed(bm)
        if seed is None:
            return False

        ok_rect, _, _ = check_rect(bm, seed)
        if ok_rect:
            return True

        ok_circ, _, _, _ = check_circle(bm, seed)
        return ok_circ

    def invoke(self, context, event):
        obj = context.active_object
        bm  = bmesh.from_edit_mesh(obj.data)

        seed = CadMixin.active_seed(bm)
        if seed is None:
            self.report({'WARNING'}, "Select an edge or vertex first")
            return {'CANCELLED'}

        ok_rect, _, _ = check_rect(bm, seed)
        if ok_rect:
            bpy.ops.mastrocad.edit_rectangle('INVOKE_DEFAULT')
            return {'FINISHED'}

        ok_circ, _, _, _ = check_circle(bm, seed)
        if ok_circ:
            bpy.ops.mastrocad.edit_circle('INVOKE_DEFAULT')
            return {'FINISHED'}

        self.report({'WARNING'}, "Active element is not part of a valid rectangle or circle")
        return {'CANCELLED'}
