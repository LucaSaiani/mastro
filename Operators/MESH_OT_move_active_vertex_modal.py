import bpy
import bmesh
# from mathutils import Vector

# --- Modal operator to move active vertex along the line to another vertex ---
class MESH_OT_move_active_vertex_modal(bpy.types.Operator):
    """Move the active vertex along the line to the other selected vertex using numeric input"""
    bl_idname = "mesh.move_active_vertex_modal"
    bl_label = "Move Active Vertex (Modal)"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        obj = context.edit_object
        me = obj.data
        bm = bmesh.from_edit_mesh(me)

        # Get selected vertices
        sel_verts = [v for v in bm.verts if v.select]
        if len(sel_verts) != 2:
            self.report({'ERROR'}, "Exactly two vertices must be selected")
            return {'CANCELLED'}

        active_vert = bm.select_history.active
        if active_vert is None or not active_vert.select:
            self.report({'ERROR'}, "You must have an active vertex selected")
            return {'CANCELLED'}

        # Identify the other vertex
        other_vert = [v for v in sel_verts if v != active_vert][0]

        # Store indices instead of direct references to BMVerts
        self.active_index = active_vert.index
        self.other_index = other_vert.index
        self.mesh = me

        # Compute initial direction
        self.original_direction = (active_vert.co - other_vert.co).normalized()
        self.original_co = active_vert.co.copy()
        self.input_str = ""
        self.distance = 0.0

        # Start modal operator
        context.window_manager.modal_handler_add(self)
        self.report({'INFO'}, "Type a distance and press Enter (Esc to cancel)")
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        # Cancel operation
        if event.type in {'ESC'}:
            bm = bmesh.from_edit_mesh(self.mesh)
            bm.verts[self.active_index].co = self.original_co
            bmesh.update_edit_mesh(self.mesh)
            context.area.header_text_set(None)
            self.report({'INFO'}, "Operation cancelled")
            return {'CANCELLED'}

        # Confirm operation
        elif event.type in {'RET', 'NUMPAD_ENTER'}:
            context.area.header_text_set(None)
            self.report({'INFO'}, f"Distance set to {self.distance}")
            return {'FINISHED'}

        # Handle backspace
        elif event.type == 'BACK_SPACE':
            self.input_str = self.input_str[:-1]

        # Handle numeric input
        elif event.unicode.isdigit() or event.unicode in {'.', '-'}:
            self.input_str += event.unicode

        # Update vertex position in real-time
        if self.input_str not in {"", "-", "."}:
            try:
                dist = float(self.input_str)
                self.distance = dist
                bm = bmesh.from_edit_mesh(self.mesh)
                v_active = bm.verts[self.active_index]
                v_other = bm.verts[self.other_index]
                v_active.co = v_other.co + self.original_direction.normalized() * dist
                bmesh.update_edit_mesh(self.mesh, loop_triangles=False)
            except Exception:
                pass

        context.area.header_text_set(f"Distance: {self.input_str}")
        return {'RUNNING_MODAL'}