import bpy 
import bmesh

# -------------------------------
# Safe wrapper operator
# -------------------------------
class MESH_OT_safe_move_active_vertex(bpy.types.Operator):
    bl_idname = "mesh.safe_move_active_vertex"
    bl_label = "Move Active Vertex"

    @classmethod
    def poll(cls, context):
        """
        Poll function to check if the operator can run.
        This ensures the operator only appears in the UI when:
        - There is an active object
        - The object is a mesh
        - The object is in Edit Mode
        - At least one vertex is selected
        This prevents Blender from raising 'Invalid operator call'
        when the context menu is opened in a place where the original
        operator cannot run.
        """
        obj = context.active_object
        if obj and obj.type == 'MESH' and obj.mode == 'EDIT':
            bm = bmesh.from_edit_mesh(obj.data)
            return any(v.select for v in bm.verts) 
        return False

    def execute(self, context):
        """
        Call the original modal operator in 'INVOKE_DEFAULT' mode.
        Using 'INVOKE_DEFAULT' ensures the operator runs properly
        within the current 3D View context.
        """
        return bpy.ops.mesh.move_active_vertex_modal('INVOKE_DEFAULT')
    
# -------------------------------
# Add operator to menus
# -------------------------------
def add_vertex_menu(self, context):
    """
    Add the safe wrapper operator to mesh menus.
    We cannot directly add the original modal operator because
    it can fail if called from a context where no vertex is active.
    Wrapping it in a safe operator ensures that it only appears
    when it is valid to call.
    """
    self.layout.operator(
        MESH_OT_safe_move_active_vertex.bl_idname,
        text="Move Active Vertex",
        icon='ARROW_LEFTRIGHT'
    )
    
# -------------------------------
# Register / Unregister
# -------------------------------
def register():
    # Register the safe wrapper operator
    bpy.utils.register_class(MESH_OT_safe_move_active_vertex)

    # Append to vertex menu and context menu
    # This ensures the operator is available in multiple UI locations
    bpy.types.VIEW3D_MT_edit_mesh_vertices.append(add_vertex_menu)
    bpy.types.VIEW3D_MT_edit_mesh_context_menu.append(add_vertex_menu)
    
def unregister():
    # Remove operator from menus
    bpy.types.VIEW3D_MT_edit_mesh_vertices.remove(add_vertex_menu)
    bpy.types.VIEW3D_MT_edit_mesh_context_menu.remove(add_vertex_menu)

    # Unregister the operator
    bpy.utils.unregister_class(MESH_OT_safe_move_active_vertex)
