import bpy 
import bmesh
from bpy.types import Operator 

import mathutils

class TRANSFORM_OT_Mastro_Set_Orientation(Operator):
    """Create transform orientation from the last selected edge or the last two vertices"""
    bl_idname = "transform.set_orientation_from_selection"
    bl_label = "Selection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.object
        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, "Select a mesh object")
            return {'CANCELLED'}

        # Ensure we're in Edit Mesh mode
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(obj.data)

        p1, p2 = None, None

        # Caso 1: ultimo edge selezionato
        if bm.select_history and isinstance(bm.select_history[-1], bmesh.types.BMEdge):
            last_edge = bm.select_history[-1]
            v1, v2 = last_edge.verts
            p1 = obj.matrix_world @ v1.co
            p2 = obj.matrix_world @ v2.co

        # Caso 2: ultimi due vertici selezionati
        else:
            verts_in_history = [elem for elem in bm.select_history if isinstance(elem, bmesh.types.BMVert)]
            if len(verts_in_history) >= 2:
                v1, v2 = verts_in_history[-2:]
                p1 = obj.matrix_world @ v1.co
                p2 = obj.matrix_world @ v2.co

        if not p1 or not p2:
            self.report({'ERROR'}, "Select at least one edge or two vertices")
            return {'CANCELLED'}

        # Project points onto XY plane
        p1 = p1.copy(); p1.z = 0
        p2 = p2.copy(); p2.z = 0

        # Compute tangent
        tangent = (p2 - p1).normalized()

        # Build axes
        y_axis = tangent
        x_axis = mathutils.Vector((0, 0, 1)).cross(y_axis)
        if x_axis.length == 0:
            x_axis = mathutils.Vector((1, 0, 0))
        z_axis = y_axis.cross(x_axis)

        # Normalize
        x_axis.normalize()
        y_axis.normalize()
        z_axis.normalize()

        # Matrix
        matrix = mathutils.Matrix((x_axis, y_axis, z_axis)).transposed()

        # Create transform orientation
        bpy.ops.transform.create_orientation(name="Selection", use=True, overwrite=True)
        orientation = context.scene.transform_orientation_slots[0]
        orientation.custom_orientation.matrix = matrix
        context.scene.transform_orientation_slots[0].type = 'Selection'

        # Stay in Edit Mode
        bpy.ops.object.mode_set(mode='EDIT')

        return {'FINISHED'}