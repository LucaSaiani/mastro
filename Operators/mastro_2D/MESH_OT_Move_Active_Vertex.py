import bpy
import bmesh
# import ast
import operator as op
import math

from ..mastro_cad.CAD_mixin import CadMixin, CAD_CHAR_MAP

# Supported operators
# operators = {
#     ast.Add: op.add,
#     ast.Sub: op.sub,
#     ast.Mult: op.mul,
#     ast.Div: op.truediv,
#     ast.USub: op.neg
# }

# def safe_eval(expr):
#     """
#     Safely evaluate an arithmetic expression using AST.
#     Supports +, -, *, / and numbers only.
#     Accepts both . and , as decimal separator.
#     Ignores any other invalid input.
#     """
#     try:
#         node = ast.parse(expr.replace(',', '.'), mode='eval').body
#         return eval_node(node)
#     except:
#         return None

# def eval_node(node):
#     """Recursively evaluate an AST node"""
#     if isinstance(node, ast.Num):  # Number
#         return node.n
#     elif isinstance(node, ast.BinOp):  # Binary operations
#         if type(node.op) in operators:
#             return operators[type(node.op)](eval_node(node.left), eval_node(node.right))
#     elif isinstance(node, ast.UnaryOp):  # Unary operations like negation
#         if type(node.op) in operators:
#             return operators[type(node.op)](eval_node(node.operand))
#     raise ValueError("Unsupported expression")


class MESH_OT_Move_Active_Vertex(bpy.types.Operator):
    """Move the active vertex along the line to the penultimate selected vertex using numeric input"""
    bl_idname = "mesh.move_active_vertex_modal"
    bl_label = "Move Active Vertex (Modal)"
    bl_description = ("Move the active vertex along the line to the penultimate selected vertex using numeric input")
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # Only meaningful in vertex select mode: select_history holds BMVert
        # only there, so edge/face select mode would otherwise reach invoke()
        # with non-vertex history entries and crash on .co access below.
        return (context.mode == 'EDIT_MESH'
                and context.tool_settings.mesh_select_mode[0])

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
        if (not isinstance(active_vert, bmesh.types.BMVert)
                or not active_vert.select):
            self.report({'ERROR'}, "You must have an active vertex selected")
            return {'CANCELLED'}

        # Reference vertex is the penultimate selected
        sel_history = [v for v in bm.select_history
                       if isinstance(v, bmesh.types.BMVert) and v.select]
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
        self._number_input = ""
        self.distance = 0.0
        self.preview_co = active_vert.co.copy()  # Current preview position
        self.parsed = False

        context.window_manager.modal_handler_add(self)
        self.report({'INFO'}, "Type a distance and press Enter to confirm, Esc to cancel")
        return {'RUNNING_MODAL'}

    # def parse_input(self, input_str):
    #     """Safely evaluate input string; handles trailing '-' as negative"""
    #     if not input_str or input_str in {'.', '-'}:
    #         return None
    #     expr = input_str
    #     if expr.endswith('-'):  # If ends with '-', invert the result
    #         expr = expr[:-1]
    #         val = safe_eval(expr)
    #         if val is not None:
    #             return -float(val)
    #         else:
    #             return None
    #     return safe_eval(expr)

    def modal(self, context, event):
        bm = bmesh.from_edit_mesh(self.mesh)
        v_active = bm.verts[self.active_index]
        v_other = bm.verts[self.other_index]
        old_distance = math.dist(v_active.co, v_other.co)

        # Cancel operation
        if event.type in {'ESC'}:
            v_active.co = self.original_co
            bmesh.update_edit_mesh(self.mesh)
            context.area.header_text_set(None)
            self.report({'INFO'}, "Operation cancelled")
            return {'CANCELLED'}

        # Confirm operation
        elif event.type in {'RET', 'NUMPAD_ENTER'} and event.value == 'PRESS':
            v_active.co = self.preview_co
            bmesh.update_edit_mesh(self.mesh)
            context.area.header_text_set(None)
            self.report({'INFO'}, f"Distance confirmed: {self.distance}")
            return {'FINISHED'}

        # Handle backspace
        elif event.type == 'BACK_SPACE' and event.value == 'PRESS':
            self._number_input = self._number_input[:-1]
            if self._number_input:
                from ...Utils.mastro_cad.cad.cad_utils import safe_eval
                val = safe_eval(self._number_input)
                if val is not None:
                    self.parsed = True
                    self.distance = val

        # Handle numeric input and basic arithmetic operators
        # elif event.unicode.isdigit() or event.unicode in {'.', '-', '+', '*', '/'}:
        #     self.input_str += event.unicode
        elif event.value == 'PRESS' and event.type in CAD_CHAR_MAP:
            
            self._number_input += CAD_CHAR_MAP[event.type]
            from ...Utils.mastro_cad.cad.cad_utils import safe_eval
            val = safe_eval(self._number_input)
            if val is not None:
                self.parsed = True
                self.distance = val

        # Update preview in real time
        # parsed = self.parse_input(self.input_str)
        
        # if self.parsed:
        #     # self.distance = parsed
        #     self.preview_co = v_other.co + self.original_direction * self.distance
        #     v_active.co = self.preview_co
        #     bmesh.update_edit_mesh(self.mesh, loop_triangles=False)


        # Display current input in header
        # Update preview in real time
        if self.parsed:
            context.area.header_text_set(f"Distance: {self.distance}")
            self.preview_co = v_other.co + self.original_direction * self.distance
            v_active.co = self.preview_co
            bmesh.update_edit_mesh(self.mesh, loop_triangles=False)
        else:
            context.area.header_text_set(f"Distance: {round(old_distance,3)}")
        return {'RUNNING_MODAL'}

def register():
    bpy.utils.register_class(MESH_OT_Move_Active_Vertex)

def unregister():
    bpy.utils.unregister_class(MESH_OT_Move_Active_Vertex)

if __name__ == "__main__":
    register()
