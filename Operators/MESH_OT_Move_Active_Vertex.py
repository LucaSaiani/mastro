import bpy
import bmesh
import ast
import operator as op

# Supported operators
operators = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.USub: op.neg
}

def safe_eval(expr):
    """
    Safely evaluate an arithmetic expression using AST.
    Supports +, -, *, / and numbers only.
    Ignores any other invalid input.
    """
    try:
        node = ast.parse(expr, mode='eval').body
        return eval_node(node)
    except:
        return None

def eval_node(node):
    """Recursively evaluate an AST node"""
    if isinstance(node, ast.Num):  # Number
        return node.n
    elif isinstance(node, ast.BinOp):  # Binary operations
        if type(node.op) in operators:
            return operators[type(node.op)](eval_node(node.left), eval_node(node.right))
    elif isinstance(node, ast.UnaryOp):  # Unary operations like negation
        if type(node.op) in operators:
            return operators[type(node.op)](eval_node(node.operand))
    raise ValueError("Unsupported expression")

class MESH_OT_Move_Active_Vertex(bpy.types.Operator):
    """Move the active vertex along the line to the penultimate selected vertex using numeric input"""
    bl_idname = "mesh.move_active_vertex_modal"
    bl_label = "Move Active Vertex (Modal)"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        obj = context.edit_object
        me = obj.data
        bm = bmesh.from_edit_mesh(me)

        # Get selected vertices
        sel_verts = [v for v in bm.verts if v.select]
        if len(sel_verts) < 2:
            self.report({'ERROR'}, "At least two vertices must be selected")
            return {'CANCELLED'}

        # Active vertex is the last selected
        active_vert = bm.select_history.active
        if active_vert is None or not active_vert.select:
            self.report({'ERROR'}, "You must have an active vertex selected")
            return {'CANCELLED'}

        # Reference vertex is the penultimate selected
        sel_history = [v for v in bm.select_history if v.select]
        if len(sel_history) < 2:
            self.report({'ERROR'}, "Selection history must have at least two vertices")
            return {'CANCELLED'}
        other_vert = sel_history[-2]

        # Store relevant data
        self.active_index = active_vert.index
        self.other_index = other_vert.index
        self.mesh = me
        self.original_direction = (active_vert.co - other_vert.co).normalized()
        self.original_co = active_vert.co.copy()
        self.input_str = ""
        self.distance = 0.0
        self.preview_co = active_vert.co.copy()  # Current preview position

        context.window_manager.modal_handler_add(self)
        self.report({'INFO'}, "Type a distance (preview) and press Enter to confirm, Esc to cancel")
        return {'RUNNING_MODAL'}

    def parse_input(self, input_str):
        """Safely evaluate input string; handles trailing '-' as negative"""
        if not input_str or input_str in {'.', '-'}:
            return None
        expr = input_str
        if expr.endswith('-'):  # If ends with '-', invert the result
            expr = expr[:-1]
            val = safe_eval(expr)
            if val is not None:
                return -float(val)
            else:
                return None
        return safe_eval(expr)

    def modal(self, context, event):
        bm = bmesh.from_edit_mesh(self.mesh)
        v_active = bm.verts[self.active_index]
        v_other = bm.verts[self.other_index]

        # Cancel operation
        if event.type in {'ESC'}:
            v_active.co = self.original_co
            bmesh.update_edit_mesh(self.mesh)
            context.area.header_text_set(None)
            self.report({'INFO'}, "Operation cancelled")
            return {'CANCELLED'}

        # Confirm operation
        elif event.type in {'RET', 'NUMPAD_ENTER'}:
            v_active.co = self.preview_co
            bmesh.update_edit_mesh(self.mesh)
            context.area.header_text_set(None)
            self.report({'INFO'}, f"Distance confirmed: {self.distance}")
            return {'FINISHED'}

        # Handle backspace
        elif event.type == 'BACK_SPACE':
            self.input_str = self.input_str[:-1]

        # Handle numeric input and basic arithmetic operators
        elif event.unicode.isdigit() or event.unicode in {'.', '-', '+', '*', '/'}:
            self.input_str += event.unicode

        # Update preview in real time
        parsed = self.parse_input(self.input_str)
        if parsed is not None:
            self.distance = parsed
            self.preview_co = v_other.co + self.original_direction * parsed
            v_active.co = self.preview_co
            bmesh.update_edit_mesh(self.mesh, loop_triangles=False)

        # Display current input in header
        context.area.header_text_set(f"Distance (preview): {self.input_str}")
        return {'RUNNING_MODAL'}

def register():
    bpy.utils.register_class(MESH_OT_Move_Active_Vertex)

def unregister():
    bpy.utils.unregister_class(MESH_OT_Move_Active_Vertex)

if __name__ == "__main__":
    register()
