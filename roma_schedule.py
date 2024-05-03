import bpy 
import gpu

from bpy.types import NodeTree, Node, NodeSocket, NodeTreeInterfaceSocket, Operator
from gpu_extras.batch import batch_for_shader

# Derived from the NodeTree base type, similar to Menu, Operator, Panel, etc.
class RoMa_Schedule_Tree(NodeTree):
    # Description string
    '''A custom node tree type that will show up in the editor type list'''
    # Optional identifier string. If not explicitly defined, the python class name is used.
    bl_idname = 'RoMaScheduleTree'
    # Label for nice name display
    bl_label = "RoMa Schedule"
    # Icon identifier
    bl_icon = 'NODETREE'

class RoMa_Schedule_Panel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "RoMa"
    bl_idname = "NODE_PT_RoMa_Schedule"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "RoMa"
    # bl_context = "scene"
    
    @classmethod
    def poll(cls, context):
        tree_type = context.space_data.tree_type
   
        return (tree_type == "RoMaScheduleTree")
   

    def draw(self, context):
        
        layout = self.layout

        scene = context.scene

        # Create a simple row.
        layout.label(text=" Simple Row:")
        col = layout.column(align=True)
        # col.operator(operators.NWDetachOutputs.bl_idname, icon='UNLINKED')

        # row = layout.row()
        # row.prop(scene, "frame_start")
        # row.prop(scene, "frame_end")

        # # Create an row where the buttons are aligned to each other.
        # layout.label(text=" Aligned Row:")

        # row = layout.row(align=True)
        # row.prop(scene, "frame_start")
        # row.prop(scene, "frame_end")

        # # Create two columns, by using a split layout.
        # split = layout.split()

        # # First column
        # col = split.column()
        # col.label(text="Column One:")
        #col.prop(scene, "frame_end")
        col.operator("node.box")
        # col.prop(scene, "frame_start")

        # # Second column, aligned
        # col = split.column(align=True)
        # col.label(text="Column Two:")
        # col.prop(scene, "frame_start")
        # col.prop(scene, "frame_end")

        # # Big render button
        # layout.label(text="Big Button:")
        # row = layout.row()
        # row.scale_y = 3.0
        # row.operator("render.render")

        # # Different sizes in a row
        # layout.label(text="Different button sizes:")
        # row = layout.row(align=True)
        # row.operator("render.render")

        # sub = row.row()
        # sub.scale_x = 2.0
        # sub.operator("render.render")

        # row.operator("render.render")
        
class Roma_Draw_Schedule(Operator):
    """Tooltip"""
    bl_idname = "node.box"
    bl_label = "Simple Object Operator"

    def execute(self, context):
        print("ciao")
        vertices = (
            (100, 100), (300, 100),
            (100, 200), (300, 200))

        indices = (
            (0, 1, 2), (2, 1, 3))

        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'TRIS', {"pos": vertices}, indices=indices)


        def draw():
            shader.uniform_float("color", (0, 0.5, 0.5, 1.0))
            batch.draw(shader)


        bpy.types.SpaceNodeEditor.draw_handler_add(draw, (), 'WINDOW', 'POST_PIXEL')
        
        return {'FINISHED'}
    



    