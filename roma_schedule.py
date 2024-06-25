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

import bmesh

import math

from bpy.types import NodeTree, Node, NodeSocket, NodeTreeInterfaceSocket, Operator, PropertyGroup, Menu
from bpy.props import  EnumProperty, StringProperty, PointerProperty, FloatProperty, IntProperty, CollectionProperty
import mathutils
# from bpy_extras.object_utils import AddObjectHelper
# from bpy_extras import object_utils
import nodeitems_utils
from nodeitems_utils import NodeCategory, NodeItem
from gpu_extras.batch import batch_for_shader

# The node tree for RoMa schedules
class RoMaTree(NodeTree):
    '''RoMa schedule'''
    bl_idname = 'RoMaTreeType'
    bl_label = "RoMa Schedule"
    bl_icon = 'NODETREE'
    
    def execute(self, context):
        for node in self.nodes:
            node.execute(context)
            
# Class to store the name of RoMa objects
# This class is used to define the list in 
# RoMa_stringCollection_Socket
class RoMa_string_item(PropertyGroup):
    name: StringProperty(name="Name")

# Class to store the attributes of RoMa objects
# This class is used to define the list in 
# RoMa_attributesCollection_Socket   
class RoMa_attribute_item(PropertyGroup):
    meshName : StringProperty(
            name="meshName",
            description="Name of the source mesh",
            default="")
    
    polyId : IntProperty(
            name="polyId",
            description="Index of the source polygon",
            default=0)
    
    id : StringProperty(
            name="Id",
            description="Unique identifier of the floor. Format: meshName_polyId_floor",
            default="")
    
    area : FloatProperty(
            name="Area",
            description="Floor area",
            default=0)
    
    
# RoMa custom socket type
# used to collect mesh names
class RoMa_stringCollection_Socket(NodeSocket):
    """RoMa node socket string collection type"""
    bl_idname = 'RoMa_stringCollection_SocketType'
    bl_label = "RoMa Mesh Node Socket"
    
    object_items: CollectionProperty(type=RoMa_string_item)
   
    # Optional function for drawing the socket input value
    def draw(self, context, layout, node, text):
        layout.label(text=text)

    # Socket color
    @classmethod
    def draw_color_simple(cls):
        return (0, 0.84, 0.64, 1)
    
# RoMa custom socket type
# used to collect attributes names
class RoMa_attributesCollection_Socket(NodeSocket):
    """RoMa node socket attribute collection type"""
    bl_idname = 'RoMa_attributeCollection_SocketType'
    bl_label = "RoMa Mesh Node Socket"
    
    object_items: CollectionProperty(type=RoMa_attribute_item)
   
    # Optional function for drawing the socket input value
    def draw(self, context, layout, node, text):
        layout.label(text=text)

    # Socket color
    @classmethod
    def draw_color_simple(cls):
        return (0.63, 0.63, 0.63, 1)
    
    
# Customizable interface properties to generate a socket from.
class RoMaInterfaceSocket(NodeTreeInterfaceSocket):
    # The type of socket that is generated.
    bl_socket_idname = 'RoMaSocketType'

    default_value: FloatProperty(default=1.0, description="Default input value for new sockets",)

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
        # self.outputs.new('RoMa_stringCollection_SocketType', 'RoMa Mesh')
        self.outputs.new('RoMa_stringCollection_SocketType', 'RoMa Mesh')

    # def draw_buttons(self, context, layout):
    #     layout.prop(self, 'text')
    
    def update_selected_objects(self):
        self.outputs['RoMa Mesh'].object_items.clear()
        objs = bpy.context.scene.objects
        romaObjs = [obj for obj in objs if obj is not None and obj.type == "MESH" and "RoMa object" in obj.data]
        for obj in romaObjs:
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
    
class RoMaAreaAttribute(RoMaTreeNode, Node):
    '''RoMa Area Attribute'''
    bl_idname = 'RoMa Area Attribute'
    bl_label = "RoMa Area"
    
    def init(self, context):
        self.outputs.new('RoMa_attributeCollection_SocketType', 'Area')
        self.outputs['Area'].display_shape = 'DIAMOND_DOT'
        
    def update(self):
        #  self.browseTree()
        pass
        
    def execute(self, context):
        self.browseTree()
                
    def browseTree(self):
        links = self.outputs['Area'].links
        # if the node is linked at least once
        if len(links) > 0:
            for link in links:
                # look for the meshes from which get the data
                # return the meshe name
                source = getAttributeSource(link)
                if len(source) > 0:
                    self.outputs['Area'].object_items.clear()
                    for romaMesh in source:
                        obj = bpy.data.objects[romaMesh.name]
                        polygons = obj.data.polygons
                        for poly in polygons:
                            item = self.outputs['Area'].object_items.add()
                            item.meshName = romaMesh.name
                            item.polyId = poly.index
                            item.id = romaMesh.name + "_" + str(poly.index)
                            item.area = poly.area
                            
   
class RoMaCaptureAttribute(RoMaTreeNode, Node):
    '''Read RoMa attributes'''
    bl_idname = 'Capture RoMa attribute'
    bl_label = "Capture attribute"
    
    inputList = ["RoMa Mesh", "Attribute"]
    outputList = ["RoMa Mesh", "Attribute"]
    
    validated = True
    
    def init(self, context):
        self.inputs.new('RoMa_stringCollection_SocketType', 'RoMa Mesh')
        self.inputs.new('RoMa_attributeCollection_SocketType', 'Attribute')
        self.inputs['Attribute'].display_shape = 'DIAMOND_DOT'
        self.inputs['Attribute'].hide_value = True
        
        self.outputs.new('RoMa_stringCollection_SocketType', 'RoMa Mesh')
        self.outputs.new('RoMa_attributeCollection_SocketType', 'Attribute')
        self.outputs['Attribute'].display_shape = 'DIAMOND_DOT'
        
        # self.internal_links.new(self.inputs['RoMa Mesh'], self.outputs['RoMa Mesh'])
        # self.internal_links.new(self.inputs['Attribute'], self.outputs['Attribute'])
                                                                       
        addKeysToNode(self, inputs=self.inputList, outputs=self.inputList)
        
    def copy(self, node):
        addKeysToNode(self, inputs=self.inputList, outputs=self.inputList)
        self.validated = True
        
    def free(self):
        removeKeyFromNode(self, inputs=self.inputList, outputs=self.inputList)
                
    def update(self):
        self.validated = checkLink(self)
        clearInputs(self)
        
        # if self.inputs['RoMa Mesh'].is_linked:
        #     pass        
        # else:
        #     self.outputs['RoMa Mesh'].object_items.clear()
        
        # if self.inputs['Attribute'].is_linked:
        #     pass        
        # else:
        #     self.outputs['Attribute'].object_items.clear()
        
        
    def execute(self, context):
        self.update()
        self.outputs['RoMa Mesh'].object_items.clear()
        self.outputs['Attribute'].object_items.clear()
        if self.validated:
            if self.inputs['RoMa Mesh'].is_linked:
                input_socket = self.inputs['RoMa Mesh'].links[0].from_socket
                object_items = input_socket.object_items
                for obj in object_items:
                    item = self.outputs['RoMa Mesh'].object_items.add()
                    item.name = obj.name
                if self.inputs['Attribute'].is_linked:
                    input_socket = self.inputs['Attribute'].links[0].from_socket
                    object_items = input_socket.object_items
                    for obj in object_items:
                        item = self.outputs['Attribute'].object_items.add()
                        # duplicate attributes
                        for prop_name in obj.__annotations__.keys():
                            setattr(item, prop_name, getattr(obj, prop_name))
                        

class RoMaMathMenu(Menu):
    bl_label = "Math"
    bl_idname = "ROMA_NODE_MT_menu_math"
    
    # print("miao", props.dropdown_box_math)
    
    def draw(self, context):
        node = context.node
        props = node.RoMa_math_node_entries
        enumItems = props.bl_rna.properties["dropdown_box_math"].enum_items
        
        set1 = enumItems[:10]        
        set2 = enumItems[10:15]   
        set3 = enumItems[15:]   
        layout = self.layout
        col = layout.column()
        col.prop_tabs_enum(props, "dropdown_box_math")

        row = layout.row()
        col = row.column()
        col.label(text="Functions")
        for item in set1:
            col.prop_enum(props, "dropdown_box_math",item.name, icon='BLANK1')
        col = row.column()
        col.label(text="Comparison")
        for item in set2:
            col.prop_enum(props, "dropdown_box_math",item.name, icon="CUBE")
        col = row.column()
        col.label(text="Rounding")
        for item in set3:
            col.prop_enum(props, "dropdown_box_math",item.name, icon='BLANK1')
        
            
class RomaMathSubMenuEntries(PropertyGroup):
    dropdown_box_math: EnumProperty(
        items=(
            ("Add", "Add", "A + B."),
            ("Subtract", "Subtract", "A - B."),
            ("Multiply", "Multiply", "A * B."),
            ("Divide", "Divide", "A / B."),
            # ("","",""),
            ("Power", "Power", "A power B."),
            ("Logarithm", "Logarithm", "Logarithm A base B."),
            ("Square Root", "Square Root", "Square root of A."),
            ("Inverse Square Root", "Inverse Square Root", "1 / Square root of A."),
            ("Absolute", "Absolute", "Magnitude of A."),
            ("Exponent", "Exponent", "exp(A)."),
            # (" ","",""),
            ("Minimum", "Minimum", "The minumum from A and B."),
            ("Maximum", "Maximum", "The maximum from A and B."),
            ("Less Than", "Less Than", "1 if A < 0 else 0."),
            ("Greater Than", "Greater Than", "1 if A > B else 0."),
            ("Compare", "Compare", "1 if (A == B)."),
            # ("","",""),
            ("Round", "Round", "Round A to the nearest integer. Round upward if the fraction part is 0.5."),
            ("Floor", "Floor", "The largest integer smaller than or equal A."),
            ("Ceil", "Ceil", "The smallest integer greater than or equal A."),
            ("Truncate", "Truncate", "The integer part of A, removing fractional digits."),
        ),
        name="Mathematical functions",
        default="Add",
        update=lambda self, context: context.node.update_socket_visibility()
        # description="Tooltip for the Dropdown box",
    )
  

    
class RoMaMathNode(RoMaTreeNode, Node):
    '''Read RoMa attributes'''
    bl_idname = 'RoMa Math Node'
    bl_label = "Math Node"
    
    RoMa_math_node_entries: PointerProperty(type=RomaMathSubMenuEntries)
    
    output : FloatProperty(
                name='',
                precision=3,)
    
    A : FloatProperty(
                name='',
                precision=3,)
     
    B : FloatProperty(
                name='',
                precision=3,)
    
    inputList = ["A","B"]
    AB_List = ['Add', 'Subtract', 'Multiply', 'Divide']
    AB_Power = ['Power']
    AB_Log = ["Logarithm"]
    AB_Square = ["Square Root", "Inverse Square Root", "Absolute", "Exponent"]
    
    def init(self, context):
        # self.inputs.new('NodeSocketString', 'Attribute')
        # self.inputs['Attribute'].hide_value = True
        # self.inputs['Attribute'].hide = True
        
        self.inputs.new('NodeSocketFloat', 'Value', identifier='A')
        self.inputs['A'].display_shape = 'DIAMOND_DOT'
        
        self.inputs.new('NodeSocketFloat', 'Value', identifier='B')
        self.inputs['B'].display_shape = 'DIAMOND_DOT'
          
        self.outputs.new('NodeSocketFloat', 'Value')
        self.outputs['Value'].hide_value = True
        self.outputs['Value'].display_shape = 'DIAMOND_DOT'
        
        addKeysToNode(self, inputs=self.inputList)
        
    def copy(self, node):
        addKeysToNode(self, inputs=self.inputList)
        
    def free(self):
        removeKeyFromNode(self, inputs=self.inputList)

    
    def execute(self, context):
        props = self.RoMa_math_node_entries
        selection = props.dropdown_box_math


        if (selection in self.AB_List or 
            selection in self.AB_Power or
            selection in self.AB_Log
            ):
            if self.inputs['A'].is_linked:
                self.A = self.inputs['A'].links[0].from_socket.default_value
            else:
                self.A = self.inputs['A'].default_value
            
            if self.inputs['B'].is_linked:
                self.B = self.inputs['B'].links[0].from_socket.default_value
            else:
                self.B = self.inputs['B'].default_value
        elif selection in self.AB_Square:
            if self.inputs['A'].is_linked:
                self.A = self.inputs['A'].links[0].from_socket.default_value
            else:
                self.A = self.inputs['A'].default_value
            
        if selection == "Add":
            self.output = self.A + self.B
        elif selection == "Subtract":
            self.output = self.A - self.B
        elif selection == "Multiply":
            self.output = self.A * self.B
        elif selection == "Divide":
            self.output = self.A / self.B
        elif selection == "Power":
            self.output = self.A ** self.B
        elif selection == "Logarithm":
            self.output = math.log(self.A, self.B)
        elif selection == "Square Root":
            self.output = math.sqrt(self.A)
        elif selection == "Inverse Square Root":
            self.output = 1/math.sqrt(self.A)
        elif selection == "Absolute":
            self.output = abs(self.A)
        elif selection == "Exponent":
            self.output = math.exp(self.A)
            
        self.outputs['Value'].default_value = self.output
        
        # if self.inputs['Attribute'].is_linked:
        #     input_socket = self.inputs['Attribute'].links[0].from_socket.default_value
        #     output = "ciccio" + input_socket
        #     self.outputs['Value'].default_value = output
        
    # def update(self):
    #     props = self.RoMa_math_node_entries
    #     selection = props.dropdown_box_math
    #     if selection in self.AB_List:
    #         if self.inputs['A'].is_linked:
    #             self.A = self.inputs['A'].links[0].from_socket.default_value
    #         else:
    #             self.A = self.inputs['A'].default_value
    #         if self.inputs['B'].is_linked:
    #             self.B = self.inputs['B'].links[0].from_socket.default_value
    #         else:
    #             self.B = self.inputs['B'].default_value
            
    def update(self):
        execute_active_node_tree()
        
            
    def draw_buttons(self, context, layout):
        props = self.RoMa_math_node_entries
        
        selection = props.dropdown_box_math
        layout.menu(RoMaMathMenu.bl_idname, text=selection)

    def update_socket_visibility(self):
        selection = self.RoMa_math_node_entries.dropdown_box_math
        if selection in self.AB_List:
            self.inputs['A'].hide = False
            self.inputs['A'].name = "Value"
            self.inputs['B'].hide = False
            self.inputs['B'].name = "Value"
        elif selection in self.AB_Power:
            self.inputs['A'].hide = False
            self.inputs['A'].name = "Base"
            self.inputs['B'].hide = False
            self.inputs['B'].name = "Exponent"
        elif selection in self.AB_Log:
            self.inputs['A'].hide = False
            self.inputs['A'].name = "Value"
            self.inputs['B'].hide = False
            self.inputs['B'].name = "Base"
        elif selection in self.AB_Square:
            self.inputs['A'].hide = False
            self.inputs['A'].name = "Value"
            self.inputs['B'].hide = True
            
        else:
            self.inputs['A'].hide = True
            self.inputs['B'].hide = True
        execute_active_node_tree()
        
        
class RoMaFloatNode(RoMaTreeNode, Node):
    bl_label = 'Value'
    bl_idname = 'RoMa Value'

    float : FloatProperty(
                name='',
                precision=3,)

    def init(self, context):
        self.outputs.new('NodeSocketFloat', 'Value')
        addKeysToNode(self, key="")
    
    def copy(self, node):
        addKeysToNode(self, key="")
        
    def free(self):
        removeKeyFromNode(self, key="")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'float')

    def execute(self, context):
        self.outputs['Value'].default_value = self.float
        
        
class RoMaIntegerNode(RoMaTreeNode, Node):
    bl_label = 'Integer'
    bl_idname = 'RoMa Integer'

    integer : IntProperty(
                name='',)

    def init(self, context):
        self.outputs.new('NodeSocketInt', 'Integer')
        addKeysToNode(self, key="")
        
    def copy(self, node):
        addKeysToNode(self, key="")
        
    def free(self):
        removeKeyFromNode(self, key="")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'integer')
        
    def execute(self, context):
        self.outputs['Integer'].default_value = self.integer
       

class RoMaAttributeToColumn(RoMaTreeNode, Node):
    '''Create a column with the attribute data'''
    bl_idname = 'RoMa Column from Data'
    bl_label = "Column from Data"
    
    validated = True
    
    def init(self, context):
        self.inputs.new('RoMa_attributeCollection_SocketType', 'Attribute')
        self.inputs['Attribute'].display_shape = 'DIAMOND_DOT'
        
        self.outputs.new('RoMa_attributeCollection_SocketType', 'Attribute')
        self.outputs['Attribute'].display_shape = 'DIAMOND_DOT'
        
    def update(self):
        self.validated = checkLink(self)
        clearInputs(self)
    
    def execute(self, context):
        self.validated = checkLink(self)
        self.outputs['Attribute'].object_items.clear()
        if self.validated:
            if self.inputs['Attribute'].is_linked:
                    object_items = self.inputs['Attribute'].links[0].from_socket.object_items
                    for obj in object_items:
                        item = self.outputs['Attribute'].object_items.add()
                        # duplicate attributes
                        for prop_name in obj.__annotations__.keys():
                            setattr(item, prop_name, getattr(obj, prop_name))
    
    
class RoMaViewer(RoMaTreeNode, Node):
    '''Add a viewer node'''
    bl_idname = 'RoMa Viewer'
    bl_label = 'RoMa Viewer'
    
    validated = True
    
    def init(self, context):
        # self.outputs.new('RoMa_stringCollection_SocketType', 'RoMa Mesh')
        self.inputs.new('RoMa_stringCollection_SocketType', 'RoMa Mesh')
        self.inputs.new('RoMa_attributeCollection_SocketType', 'Attribute')
        self.inputs['Attribute'].hide_value = True
        self.inputs['Attribute'].display_shape = 'DIAMOND_DOT'
        
    # def update(self):
    #     if self.inputs['RoMa Mesh'].is_linked:
    #         input_socket = self.inputs['RoMa Mesh'].links[0].from_socket
    #         object_items = input_socket.object_items
    #         toPrint = ""
    #         for o in object_items:
    #             toPrint = str(o.name)
    #             layout.label(text=f'{toPrint}')
    #     if self.inputs['Value'].is_linked:
    #         value = self.inputs['Value'].links[0].from_socket.default_value
    #         value = round(float(value),3)
    #         layout.label(text=f'{value}')
            
        
    # def update(self):
    #     if self.inputs['RoMa Mesh'].is_linked:
    #         input_socket = self.inputs['RoMa Mesh'].links[0].from_socket
    #         object_items = input_socket.object_items
    #         print("Reader Node - Oggetti Selezionati:")
    #         for item in object_items:
    #             print(item.name)
    
    def update(self):
        self.validated = checkLink(self)
        if self.validated:
            if self.inputs['RoMa Mesh'].is_linked:
                # obj = self.inputs['RoMa Mesh'].links[0].from_socket.object_items
                # for o in obj:
                #     print(o.name)
                if self.inputs['Attribute'].is_linked:
                    object_items = self.inputs['Attribute'].links[0].from_socket.object_items
                    # print("----------------------------------")
                    # print("Reader Node - Oggetti Selezionati:")
                    # for a in object_items:
                    #      print(a.meshName, a.polyId, a.id, a.area)
                            
        
    # def execute(self, context):
    #     self.update()
    #     if self.validated:

            
    def draw_buttons(self, context, layout):
        # nodeName = self.name
        # treeName = self.id_data.name
        # nodeIndentifier = f"{treeName}::{nodeName}"
        col = layout.column(align=True)
        # col.operator("object.roma_add_column").sourceNode = nodeIndentifier
        # col.operator("node.schedule_viewer").sourceNode = nodeIndentifier
        col.prop(context.window_manager, "toggle_schedule_in_editor", text="Show Schedule")
                
    # def draw_buttons(self, context, layout):
    #     if self.validated:
    #         if self.inputs['RoMa Mesh'].is_linked:
    #             input_socket = self.inputs['RoMa Mesh'].links[0].from_socket
    #             object_items = input_socket.object_items
    #             toPrint = ""
    #             for o in object_items:
    #                 toPrint = str(o.name)
    #                 layout.label(text=f'{toPrint}')
    #         if self.inputs['Value'].is_linked:
    #             value = self.inputs['Value'].links[0].from_socket.default_value
    #             value = round(float(value),3)
    #             layout.label(text=f'{value}')
            
    
            
            
    
# class CustomNodeText(RoMaTreeNode, Node):
#     bl_label = 'Text'

#     text : StringProperty(name="OOO")

#     def init(self, context):
#         self.outputs.new('NodeSocketString', 'Text')

#     # def draw_buttons(self, context, layout):
#     #     layout.prop(self, 'text')

#     def execute(self, context):
#         self.outputs['Text'].default_value = "OOOa"
        


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
    RoMaNodeCategory('ATTRIBUTE', "Attribute", items=[
        NodeItem("Capture RoMa attribute", label="Capture RoMa attribute"),
        NodeItem("RoMa Area Attribute", label="Area"),
        NodeItem("RoMa Math Node", label="Math"),
    ]),
    RoMaNodeCategory('INPUT', "Input", items=[
        NodeItem("Input RoMa Mesh", label="RoMa Mesh"),
        NodeItem("RoMa Integer", label="Integer"),
        NodeItem("RoMa Value", label="Value"),
    ]),
    RoMaNodeCategory('OUTPUT', "Output", items=[
        NodeItem("RoMa Viewer", label="Viewer"),
    ]),
    RoMaNodeCategory('SCHEDULE', "Schedule", items= [
       NodeItem("RoMa Column from Data", label="Column"),
    ]),
    
]

#############################################################################
########## Node Related funcions  ###########################################
#############################################################################

# add keys to the node
def addKeysToNode(self,  **kwargs):
    for item_name, list in kwargs.items():
        if item_name == "inputs":
            for input in list:
                key = self.path_resolve('inputs[\"'+input+'\"]')
                bpy.msgbus.subscribe_rna(
                        key=key,
                        owner=None,
                        args=(),
                        notify=execute_active_node_tree,
                        options={"PERSISTENT"}
                    )
                #add the key to the keyDictionary
                bpy.context.scene.keyDictionary.add()
                last = len(bpy.context.scene.keyDictionary)-1
                bpy.context.scene.keyDictionary[last].name = str(key)
                # print("KEY", key)
        elif item_name == "outputs":
            for output in list:
                key = self.path_resolve('outputs[\"'+output+'\"]')
                bpy.msgbus.subscribe_rna(
                        key=key,
                        owner=None,
                        args=(),
                        notify=execute_active_node_tree,
                        options={"PERSISTENT"}
                    )
                #add the key to the keyDictionary
                bpy.context.scene.keyDictionary.add()
                last = len(bpy.context.scene.keyDictionary)-1
                bpy.context.scene.keyDictionary[last].name = str(key)
                # print("KEY", key)
        elif item_name == "key":
            key = self
            bpy.msgbus.subscribe_rna(
                    key=key,
                    owner=None,
                    args=(),
                    notify=execute_active_node_tree,
                    options={"PERSISTENT"}
                )
            #add the key to the keyDictionary
            bpy.context.scene.keyDictionary.add()
            last = len(bpy.context.scene.keyDictionary)-1
            bpy.context.scene.keyDictionary[last].name = str(key)
            # print("KEY", key)
        
# remove all the keys from the node
def removeKeyFromNode(self, **kwargs):
    for item_name, list in kwargs.items():
        if item_name == "inputs":
            for input in list:
                key = self.path_resolve('inputs[\"'+input+'\"]')
                for i, el in enumerate(bpy.context.scene.keyDictionary):
                    if el.name == str(key):
                        bpy.context.scene.keyDictionary.remove(i)
                        break
        elif item_name == "outputs":
            for output in list:
                key = self.path_resolve('outputs[\"'+output+'\"]')
                for i, el in enumerate(bpy.context.scene.keyDictionary):
                    if el.name == str(key):
                        bpy.context.scene.keyDictionary.remove(i)
                        break
        elif item_name == "key":
            key = self
            for i, el in enumerate(bpy.context.scene.keyDictionary):
                    if el.name == str(key):
                        bpy.context.scene.keyDictionary.remove(i)
                        break
                    
def clearInputs(self):
    for input in self.inputs:
        if input.is_linked == False:
            name = input.name
            self.outputs[name].object_items.clear()
            
            
# A Function to check if the links are compatible
def checkLink(self):
    inputs = self.inputs
    self.use_custom_color = False
    validated = True
    for input in inputs:
        if input.is_linked:
            inputType = input.rna_type.name
            outputType = input.links[0].from_socket.rna_type.name
            if inputType != outputType:
                self.color = (0.51, 0.19, 0.29)
                self.use_custom_color = True
                validated = False
    return(validated)
            
               
            
    
# get the source (RoMa mesh) from which get the attribute
def getAttributeSource(link):
    # name = link.to_socket.name
    # idName = link.to_socket.bl_idname
    sockets = [x for x in link.to_node.inputs if x.rna_type.name == 'RoMa_stringCollection_SocketType']
    if sockets:
        socket = sockets[0]
        if socket.is_linked:
            # print("linked", socket.name)
            parent_node = socket.links[0].from_node
            if parent_node.bl_idname == "Input RoMa Mesh":
                items = parent_node.outputs['RoMa Mesh'].object_items
                return(items)
    return()

    

# execute the active node tree
def execute_active_node_tree():
    # node_editor = next((a for a in bpy.context.screen.areas if a.type == 'NODE_EDITOR'), None)
    # if (node_editor == None): return
    # for space in node_editor.spaces:
    #     node_tree = getattr(space, 'node_tree')
    #     if (node_tree):
    #         node_tree.execute(bpy.context)
    #         break
    trees = [x for x in bpy.data.node_groups if x.bl_idname == "RoMaTreeType"]
    if trees:
        for tree in trees:
            tree.execute(bpy.context)
            
            
            # tree.execute(bpy.context)
            
    
        
###################################################################################
############### Schedule panel ####################################################
###################################################################################
# class RoMa_Schedule_Panel(bpy.types.Panel):
#     """Creates a Panel in the scene context of the properties editor"""
#     bl_label = "RoMa"
#     bl_idname = "NODE_PT_RoMa_Schedule"
#     bl_space_type = 'NODE_EDITOR'
#     bl_region_type = 'UI'
#     bl_category = "RoMa"
#     # bl_context = "scene"
    
    
    
#     @classmethod
#     def poll(cls, context):
#         tree_type = context.space_data.tree_type
   
#         return (tree_type == "RoMaTreeType")
   

#     def draw(self, context):
        
#         layout = self.layout

#         scene = context.scene

#         # Create a simple row.
#         layout.label(text=" Simple Row:")
#         col = layout.column(align=True)
        
#         # nodeName = "Column from Data"
#         # treeName = "RoMa Schedule"
#         # nodeIndentifier = f"{treeName}::{nodeName}"

#         # col.operator("object.roma_add_column").sourceNode = nodeIndentifier
        
#         col.operator("node.schedule_viewer")

        
class NODE_EDITOR_Roma_Draw_Schedule(Operator):
    """Tooltip"""
    bl_idname = "node.schedule_viewer"
    bl_label = "Show a schedule in the schedule editor"
    
    _handle = None
    
    sourceNode : bpy.props.StringProperty(name="Source Node")
    
    @staticmethod
    def handle_add(self, context):
        if NODE_EDITOR_Roma_Draw_Schedule._handle is None:
            NODE_EDITOR_Roma_Draw_Schedule._handle =bpy.types.SpaceNodeEditor.draw_handler_add(draw_callback_schedule_overlay,
                                                                                                (self, context, self.sourceNode),
                                                                                                'WINDOW',
                                                                                                'POST_VIEW')
    @staticmethod
    def handle_remove(self, context):
        bpy.types.SpaceNodeEditor.draw_handler_remove(NODE_EDITOR_Roma_Draw_Schedule._handle, 'WINDOW')
        NODE_EDITOR_Roma_Draw_Schedule._handle = None
    
    def execute(self, context):
        if NODE_EDITOR_Roma_Draw_Schedule._handle is None:
            self.handle_add(self, context)
            context.area.tag_redraw()
        else:
            self.handle_remove(self, context)
            context.area.tag_redraw()
        return {'FINISHED'}
    
    def invoke(self, context, event):
        self.execute(context)
        return {'RUNNING_MODAL'}

def draw_schedule_overlay(self, context, sourceNode):
    path = sourceNode.split("::")
    treeName = path[0]
    nodeName = path[1]
    
    # for area in bpy.context.screen.areas:
    #     if area.ui_type == 'RoMaTreeType':
    #         for space in area.spaces:
    #             if space.type == 'NODE_EDITOR' and space.node_tree and space.node_tree.name == treeName:
    node = bpy.data.node_groups[treeName].nodes[nodeName]


    # verts = [
    #     (+0.0, +0.0,  +0.0),
    #     (+400.0, +0.0,  +0.0),
    #     (+400.0, -100.0,  +0.0),
    #     (+0.0, -100.0,  +0.0),
    #     ]


    edges = [
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 0),
    ]
    
    # coords = []
    
    

    
    #get the node area
    # areaName = None
    # found = False
    # for area in bpy.context.screen.areas:
    #     if area.type == 'NODE_EDITOR':
    #         for space in area.spaces:
    #             if space.type == 'NODE_EDITOR' and space.node_tree and space.node_tree.name == treeName:
    #                 # areaName = area
    #                 found = True
    #                 break
    #     if found:
    #         break
                    
    # if found:
    # region = areaName.regions[-1]
    # view2d = region.view2d
    
    # node location
    nodeLocation = node.location
    node_width = node.width
    node_height = node.height
    
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        
    scale = context.preferences.view.ui_scale/0.8
        
    verts = [
        (nodeLocation.x * scale, nodeLocation.y * scale),
        ((nodeLocation.x + node_width) * scale, nodeLocation.y * scale),
        ((nodeLocation.x + node_width) * scale, (nodeLocation.y + node_height) * scale),
        (nodeLocation.x * scale, (nodeLocation.y + node_height) * scale),
    ]    
    
    batch = batch_for_shader(shader, 'LINES', {"pos": verts}, indices=edges)
    # r, g, b, a = [c for c in bpy.context.preferences.addons['roma'].preferences.edgeColor]
    shader.uniform_float("color", (0.0 ,1.0, 0.0, 1.0))
        
    gpu.state.line_width_set(10)
    gpu.state.blend_set("ALPHA")
    batch.draw(shader)
            
   
        
    

def draw_callback_schedule_overlay(self, context, sourceNode):
    draw_schedule_overlay(self, context, sourceNode)
    
def update_schedule_node_editor(self, context):
    nodeName = context.active_node.name
    treeName = context.active_node.id_data.name
    nodeIdentifier = f"{treeName}::{nodeName}"
    bpy.ops.node.schedule_viewer(sourceNode = nodeIdentifier)

    
###################################################################################
############### 3D schedule #######################################################
###################################################################################
    

def add_cell(width, height, index):
    """
    This function takes inputs and returns vertex and face arrays.
    no actual mesh data creation is done here.
    """

    vertical_shift = -1 * index
    vert_increment = index * 4
    verts = [
        (+0.0, +0.0 + vertical_shift,  +0.0),
        (+1.0, +0.0 + vertical_shift,  +0.0),
        (+1.0, -1.0 + vertical_shift,  +0.0),
        (+0.0, -1.0 + vertical_shift,  +0.0),
        ]

    edges = [
        (0 + vert_increment, 1 + vert_increment),
        (1 + vert_increment, 2 + vert_increment),
        (2 + vert_increment, 3 + vert_increment),
        (3 + vert_increment, 0 + vert_increment),
    ]
    faces = [
        (0 + vert_increment, 1 + vert_increment, 2 + vert_increment, 3 + vert_increment),
    ]

    # apply size
    for i, v in enumerate(verts):
        verts[i] = v[0] * width, v[1] * height, v[2]

    return verts, edges, faces

class RoMaAddColumn(Operator):
    '''Add a column to the schedule'''
    bl_idname="object.roma_add_column"
    bl_label="RoMa Column"
    bl_options = {'REGISTER'}
    
    sourceNode : bpy.props.StringProperty(name="Source Node")
    
    width: FloatProperty(
        name="Width",
        description="Cell Width",
        min=0.01, max=100.0,
        default=3.0,
    )
    
    height: FloatProperty(
        name="Height",
        description="Cell Height",
        min=0.01, max=100.0,
        default=2.0,
    )
    
    # data : bpy.props.StringProperty(name="Filter type name")
    
    def execute(self, context):
        # retrieve data from node
        path = self.sourceNode.split("::")
        treeName = path[0]
        nodeName = path[1]
        node = bpy.data.node_groups[treeName].nodes[nodeName]
        data = node.inputs['Attribute'].links[0].from_socket.object_items
        
        # create a column with its cells
        mesh = bpy.data.meshes.new("RoMa Column")
        bm = bmesh.new()
        # index = 0
        for index, el in enumerate(data):
        # while index < len(data):
            verts_loc, edges, faces = add_cell(
                self.width,
                self.height,
                index,
            )
            for v_co in verts_loc:
                bm.verts.new(v_co)

            bm.verts.ensure_lookup_table()
            for e_idx in edges:
                bm.edges.new([bm.verts[i] for i in e_idx])
            # for f_idx in faces:
            #     bm.faces.new([bm.verts[i] for i in f_idx])
            # index += 1

        # remove duplicated vertices
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.1)
        
        bm.to_mesh(mesh)
        mesh.update()

        column = bpy.data.objects.new(name="Column", object_data=mesh)
        bpy.context.scene.collection.objects.link(column)
        
        # index = 0
        # while index < len(data):
        for index, el in enumerate(data):
            font_curve = bpy.data.curves.new(type="FONT", name="Font Curve")
            font_curve.body = f"{round(el.area)}"
            font_obj = bpy.data.objects.new(name="Font Object", object_data=font_curve)
            bpy.context.scene.collection.objects.link(font_obj)
            newPos = mathutils.Vector((0.3, -1.3 - (self.height * index), 0.0))
            font_obj.location = font_obj.location + newPos
            # index += 1
            # parenting
            font_obj.parent = bpy.data.objects[column.name]
        return {'FINISHED'}

    