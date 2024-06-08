# Copyright (C) 2022-2024 Luca Saiani

# luca.saiani@gmail.com

# Created by Luca Saiani
# This is part of RoMa addon for Blender

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import bpy 
import gpu

from bpy.types import NodeTree, Node, NodeSocket, NodeTreeInterfaceSocket, Operator, PropertyGroup
from bpy.props import *
import nodeitems_utils
from nodeitems_utils import NodeCategory, NodeItem
from gpu_extras.batch import batch_for_shader

# The node tree for RoMa schedules
class RoMaTree(NodeTree):
    '''RoMa schedule'''
    bl_idname = 'RoMaTreeType'
    bl_label = "RoMa schedule"
    bl_icon = 'NODETREE'
    
    def execute(self, context):
        for node in self.nodes:
            node.execute(context)
            
# Class to store the name of RoMa objects
# This class is used to define the list in 
# RoMa_romaMeshList_Socket
class RoMa_romaObjectName_item(PropertyGroup):
    name: StringProperty(name="Name")
    
# RoMa custom socket type
class RoMa_romaMeshList_Socket(NodeSocket):
    """RoMa node socket type"""
    bl_idname = 'RoMa_romaMesh_SocketType'
    bl_label = "RoMa Mesh Node Socket"
    
    
    # input_value: bpy.props.FloatProperty(
    #     name="Value",
    #     description="Value when the socket is not connected",
    # )
    
    # default_value: bpy.props.FloatProperty(
    #     name="Value",
    #     default = 200,
    #     description="Value when the socket is not connected",
    # ) 
    
    
    object_items: bpy.props.CollectionProperty(type=RoMa_romaObjectName_item)
   
    # Set properties of newly created sockets
    # def init_socket(self, node, socket, data_path):
    #     socket.input_value = self.default_value
      

    # Optional function for drawing the socket input value
    def draw(self, context, layout, node, text):
        layout.label(text=text)
        # layout.label(text=self.name)
        # for item in self.object_items:
            # layout.label(text=item.name)
        # if self.is_output or self.is_linked:
        #     layout.label(text=text)
        # else:
        #     layout.prop(self, "input_value", text=text)

    # Socket color
    @classmethod
    def draw_color_simple(cls):
        return (0, 0.84, 0.64, 1)
    
    
# Customizable interface properties to generate a socket from.
class RoMaInterfaceSocket(NodeTreeInterfaceSocket):
    # The type of socket that is generated.
    bl_socket_idname = 'RoMaSocketType'

    default_value: bpy.props.FloatProperty(default=1.0, description="Default input value for new sockets",)

    def draw(self, context, layout):
        # Display properties of the interface.
        layout.prop(self, "default_value")

    # Set properties of newly created sockets
    def init_socket(self, node, socket, data_path):
        socket.input_value = self.default_value

    # Use an existing socket to initialize the group interface
    def from_socket(self, node, socket):
        # Current value of the socket becomes the default
        self.default_value = socket.input_value

# Mix-in class for all custom nodes in this tree type.
# Defines a poll function to enable instantiation.
class RoMaTreeNode:
    @classmethod
    def poll(cls, ntree):
        return ntree.bl_idname == 'RoMaTreeType'
    
    def execute(self, context):
        pass

##########################################################################
################ Nodes ###################################################
##########################################################################

class RoMaGroupInput(RoMaTreeNode, Node):
    '''Input node containing all the RoMa meshes existing in the scene'''
    bl_idname = 'Input RoMa Mesh'
    bl_label = 'Group Input'
    # bl_icon = 'NODE'

    # text : StringProperty(name='',)
    
    

    def init(self, context):
        # self.outputs.new('RoMa_romaMesh_SocketType', 'RoMa Mesh')
        self.outputs.new('RoMa_romaMesh_SocketType', 'RoMa Mesh')
        

    # def draw_buttons(self, context, layout):
    #     layout.prop(self, 'text')
    
    def update_selected_objects(self):
        self.outputs['RoMa Mesh'].object_items.clear()
        for obj in bpy.context.selected_objects:
            item = self.outputs['RoMa Mesh'].object_items.add()
            item.name = obj.name
        

    # def execute(self, context):
    #     self.outputs['RoMa Mesh'].object_items.clear()
    #     for obj in bpy.context.selected_objects:
    #         item = self.outputs['RoMa Mesh'].object_items.add()
    #         item.name = obj.name
            
        # self.outputs['RoMa Mesh'].default_value = bpy.context.selected_objects
        
    # Copy function to initialize a copied node from an existing one.
    def copy(self, node):
        pass
        # print("Copying from node ", node)

    # Free function to clean up on removal.
    def free(self):
        pass
        # print("Removing node ", self, ", Goodbye!")
        
    # def draw_color_simple(self):
    #     return (29, 29, 29, 1)
    
class RoMaViewer(RoMaTreeNode, Node):
    '''Add a viewer node'''
    bl_idname = 'RoMa Viewer'
    bl_label = 'RoMa Viewer'
    # bl_icon = 'NODE'
    
    
    def init(self, context):
        # self.outputs.new('RoMa_romaMesh_SocketType', 'RoMa Mesh')
        self.inputs.new('RoMa_romaMesh_SocketType', 'RoMa Mesh')
        
    def update(self):
        if self.inputs['RoMa Mesh'].is_linked:
            input_socket = self.inputs['RoMa Mesh'].links[0].from_socket
            object_items = input_socket.object_items
            print("Reader Node - Oggetti Selezionati:")
            for item in object_items:
                print(item.name)
                
    def draw_buttons(self, context, layout):
        if self.inputs['RoMa Mesh'].is_linked:
            input_socket = self.inputs['RoMa Mesh'].links[0].from_socket
            object_items = input_socket.object_items
            toPrint = ""
            for o in object_items:
                toPrint = toPrint + "\n" + str(o.name)
            layout.label(text=f'{toPrint}')

    
# class CustomNodeText(RoMaTreeNode, Node):
#     bl_label = 'Text'

#     text : StringProperty(name='',)

#     def init(self, context):
#         self.outputs.new('NodeSocketString', 'Text')

#     def draw_buttons(self, context, layout):
#         layout.prop(self, 'text')

#     def execute(self, context):
#         self.outputs['Text'].default_value = self.text
        
# class CustomNodeFloat(RoMaTreeNode, Node):
#     bl_label = 'Float'

#     float : FloatProperty(name='',)

#     def init(self, context):
#         self.outputs.new('NodeSocketFloat', 'Float')

#     def draw_buttons(self, context, layout):
#         layout.prop(self, 'float')

#     def execute(self, context):
#         self.outputs['Float'].default_value = self.float

# class CustomNodeJoin(RoMaTreeNode, Node):
#     bl_label = 'Join'

#     def init(self, context):
#         self.inputs.new('NodeSocketString', 'Value1')
#         self.inputs.new('NodeSocketString', 'Value2')

#         self.outputs.new('NodeSocketString', 'Value')

#     def draw_buttons(self, context, layout):
#         pass

#     def update(self):
#         if self.inputs['Value1'].is_linked and self.inputs['Value2'].is_linked:
#             text = self.inputs['Value1'].links[0].from_socket.default_value + self.inputs['Value2'].links[0].from_socket.default_value
#         elif self.inputs['Value1'].is_linked and not self.inputs['Value2'].is_linked:
#             text = self.inputs['Value1'].links[0].from_socket.default_value + self.inputs['Value2'].default_value
#         elif self.inputs['Value2'].is_linked and not self.inputs['Value1'].is_linked:
#             text = self.inputs['Value1'].default_value + self.inputs['Value2'].links[0].from_socket.default_value
#         else:
#             text = self.inputs['Value1'].default_value + self.inputs['Value2'].default_value

#         self.outputs['Value'].default_value = text


    
# class CustomNodePrint(RoMaTreeNode, Node):
#     bl_label = 'Print'

#     def init(self, context):
#         # self.inputs.new('NodeSocketCollection', 'Geometry')
#         self.inputs.new('NodeSocketString', 'Print')

#     def draw_buttons(self, context, layout):
#         if self.inputs['Print'].is_linked:
#             data = self.inputs['Print'].links[0].from_socket
#             print_value = (data)
#             layout.label(text=f'{print_value}')
#         # if self.inputs['Print'].is_linked:
#         #     print_value = self.inputs['Print'].links[0].from_socket.default_value
#         #     layout.label(text=f'{print_value}')
    
#############################################################################
################ Add menu ###################################################
#############################################################################

class RoMaNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == "RoMaTreeType"
    
# all categories in a list
node_categories = [
    # identifier, label, items list
    RoMaNodeCategory('INPUT', "Input", items=[
        NodeItem("Input RoMa Mesh", label="RoMa Mesh"),
    ]),
    RoMaNodeCategory('OUTPUT', "Output", items=[
        NodeItem("RoMa Viewer", label="Viewer")
        # the node item can have additional settings,
        # which are applied to new nodes
        # NOTE: settings values are stored as string expressions,
        # for this reason they should be converted to strings using repr()
        # NodeItem("CustomNodeType", label="Node A", settings={
        #     "my_string_prop": repr("Lorem ipsum dolor sit amet"),
        #     "my_float_prop": repr(1.0),
        # }),
        # NodeItem("CustomNodeType", label="Node B", settings={
        #     "my_string_prop": repr("consectetur adipisicing elit"),
        #     "my_float_prop": repr(2.0),
        # }),
       
        
        # NodeItem('CustomNodeText'),
        # NodeItem('CustomNodeFloat'),
        # NodeItem('CustomNodeJoin'),
        # NodeItem('CustomNodePrint'),
    ]),
]

def execute_active_node_tree():
    node_editor = next((a for a in bpy.context.screen.areas if a.type == 'NODE_EDITOR'), None)
    if (node_editor == None): return
    for space in node_editor.spaces:
        node_tree = getattr(space, 'node_tree')
        if (node_tree):
            node_tree.execute(bpy.context)
            break
        
###################################################################################
############### Schedule panel ####################################################
###################################################################################
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
        # print("ciao")
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
    



    