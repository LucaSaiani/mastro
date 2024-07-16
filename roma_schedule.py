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
import blf
import bmesh

import math

from bpy.types import NodeTree, Node, NodeSocket, NodeTreeInterfaceSocket, Operator, PropertyGroup, Menu
from bpy.props import  EnumProperty, StringProperty, PointerProperty, FloatProperty, IntProperty, CollectionProperty
import mathutils
# import nodeitems_utils
from nodeitems_utils import NodeCategory, NodeItem
from gpu_extras.batch import batch_for_shader

from itertools import chain # to identify unique keys in a list of dictionaries

font_info = {
    "font_id": 0,
    "handler": None,
}



#############################################################################
########## Node Related funcions  ###########################################
#############################################################################

# Function to store in a string tree and node name
# in order to be able to identify the node
def writeNodeFingerPrint(node):
    nodeName = node.name
    treeName = node.id_data.name
    nodeIndentifier = f"{treeName}::{nodeName}"
    return(nodeIndentifier)

# Function to unravel the nodeFingerPrint
def readNodeFingerPrint(fingerPrint):
    path = fingerPrint.split("::")
    treeName = path[0]
    nodeName = path[1]
    node = bpy.data.node_groups[treeName].nodes[nodeName]
    return(node)

# function to identify unique keys in a list of dictionaries
# it is possibile to pass extra parameters as to 
# sort = True to sort the list
# and remove = ["A", "B"] to remove said values from the list
def uniqueKeys(arr, **kwargs):
    params = {
        'remove' : None,
        'sort' : None,
    }
    
    params.update(kwargs)
    
    remove = params['remove']
    sort = params['sort']
    newList = []
    
    for a in arr:
        item = a['key_value_items']
        for itemKey in item: 
            newList.append(f"{itemKey['name']}")
    result = list(set(newList))

    if remove:
        for el in remove:
            if el in result:
                result.remove(el)
    if sort:
        result.sort()
            
    return(result)

# function to identify unique values in the attribute list
# it is possibile to pass extra parameters as to 
# sort = True to sort the list
def uniqueValue(arr, **kwargs):
    params = {
        'sort' : None,
        'key' : None
    }
    
    params.update(kwargs)
    
    sort = params['sort']
    keyName = params['key']
    newList = []
    
    for a in arr:
        item = a['key_value_items']
        for itemKey in item: 
            if itemKey['name'] == keyName:
                if itemKey['value_type'] == 'FLOAT':
                    newList.append(itemKey['value_float'])
                else:
                    newList.append(itemKey['value_string'])

    result = list(set(chain.from_iterable(sub.keys() for sub in newList)))
    
    if sort:
        result.sort()
            
    return(result)

# add keys to the node to be able to run
# some tasks when key is updated
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
# when the node is deleted
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

def cleanSocket(link, socketName, inputOutput):
    if inputOutput == "both":
        inOuts = ['input', 'output']
    elif inputOutput == "input":
        inOuts = ['input']
    else:
        inOuts = ['output']
        
    for inOut in inOuts:
        if inOut == "input":
            l = link.inputs[socketName]
        else:
            l = link.outputs[socketName]
    
        if l.bl_rna.name == 'RoMa_stringCollection_SocketType':
            l.object_items.clear()
        elif l.bl_rna.name == 'RoMa_attributeCollection_SocketType':
            # l.pop('object_items', None)
            nodeFingerPrint = writeNodeFingerPrint(link)
            RoMa_attribute_removeItem(nodeFingerPrint, socketName, inOut)
            
    
def cleanInputs(self):
    for input in self.inputs:
        cleanSocket(input.node, input.name, "input")
        # if input.bl_rna.name == 'RoMa_stringCollection_SocketType':
        #     input.object_items.clear()
        # elif input.bl_rna.name == 'RoMa_attributeCollection_SocketType':
        #     input.pop('object_items', None)
                                
def cleanOutputs(self):
     for output in self.outputs:
        cleanSocket(output.node, output.name, "output") 
        # if output.bl_rna.name == 'RoMa_stringCollection_SocketType':
        #     output.object_items.clear()
        # elif output.bl_rna.name == 'RoMa_attributeCollection_SocketType':
        #     output.pop('object_items', None)
            
            
# A Function to check if the links are compatible with the input
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
            
# a function to get all the attributes of the 
# selected meshes
def getAttributes(objNames, attrType):
    for o in objNames: print(f"ottengo gli attributi per {o.name}")
    romaObjs = [obj for obj in objNames if obj is not None and bpy.data.objects[obj.name].type == "MESH" and "RoMa object" in bpy.data.objects[obj.name].data]
    if len(romaObjs) > 0:
        data = []
        for el in romaObjs:
            obj = bpy.data.objects[el.name]
            option = None
            phase = None
            if "roma_option_attribute" in obj.roma_props.keys():
                option = obj.roma_props['roma_option_attribute']
            if "roma_phase_attribute" in obj.roma_props.keys():
                phase = obj.roma_props['roma_phase_attribute']
    
            meshName = obj.name
            mesh = obj.data
            bm = bmesh.new()
            bm.from_mesh(mesh)
            # bm.faces.ensure_lookup_table()    
           
         
            bMesh_typology = bm.faces.layers.int["roma_typology_id"]
            bMesh_use_id_list_A = bm.faces.layers.int["roma_list_use_id_A"]
            bMesh_use_id_list_B = bm.faces.layers.int["roma_list_use_id_B"]
            bMesh_storeys = bm.faces.layers.int["roma_number_of_storeys"]
            bMesh_storey_list_A = bm.faces.layers.int["roma_list_storey_A"]
            bMesh_storey_list_B = bm.faces.layers.int["roma_list_storey_B"]
            bMesh_height_A = bm.faces.layers.int["roma_list_height_A"]
            bMesh_height_B = bm.faces.layers.int["roma_list_height_B"]
            bMesh_height_C = bm.faces.layers.int["roma_list_height_C"]
            bMesh_height_D = bm.faces.layers.int["roma_list_height_D"]
            bMesh_height_E = bm.faces.layers.int["roma_list_height_E"]
            bMesh_void = bm.faces.layers.int["roma_list_void"]
    
            for f in bm.faces:
                polyId = f.index
                storeys = f[bMesh_storeys]
                # get typology name
                if attrType in ("all", "typology"):
                    for n in bpy.context.scene.roma_typology_name_list:
                        if n.id == f[bMesh_typology]:
                            typologyId = n.id
                            typologyName = n.name
                            break
                floor = 0
                indexList = 1
                storeyPreviousGroup = 0
                while floor < storeys:
                    length = int(math.log10(f[bMesh_storey_list_A])) +1
                    pos = length - indexList -1
                    storey_A = int((f[bMesh_storey_list_A] / 10 ** pos) % 10)
                    storey_B = int((f[bMesh_storey_list_B] / 10 ** pos) % 10)
                    # print(f"{storey_A} {storey_B}  storey {storey_A * 10 + storey_B}")
                    if attrType in ("all", "use"):
                        use_A = int((f[bMesh_use_id_list_A] / 10 ** pos) % 10)
                        use_B = int((f[bMesh_use_id_list_B] / 10 ** pos) % 10)
                        useId = use_A * 10 + use_B
                        # get use name
                        for n in bpy.context.scene.roma_use_name_list:
                            if n.id == useId:
                                useName = n.name
                                break

                    # print(f"{use_A} {use_B} {use}")
                    if attrType in ("all", "height"):
                        height_A = int((f[bMesh_height_A] / 10 ** pos) % 10)
                        height_B = int((f[bMesh_height_B] / 10 ** pos) % 10)
                        height_C = int((f[bMesh_height_C] / 10 ** pos) % 10)
                        height_D = int((f[bMesh_height_D] / 10 ** pos) % 10)
                        height_E = int((f[bMesh_height_E] / 10 ** pos) % 10)
                        height = height_A * 10 + height_B + height_C * 0.1 + height_D * 0.01 + height_E * 0.001

                    void = int((f[bMesh_void] / 10 ** pos) % 10)
                    
                    storeyGroup = (storey_A * 10 + storey_B) + storeyPreviousGroup
                    # print(f"Storeygroup {storeyGroup}       storey {storey}")
                    if storeyGroup == floor +1:
                        storeyPreviousGroup = storeyGroup
                        indexList += 1
                    
                    if attrType in ("all", "area"):
                        area = round(f.calc_area(),2)
                        if void == 1:
                            area = 0
                    
                    id = f"{meshName}_{polyId}_{floor}"
                    if attrType == "all":
                        tmpData = {
                                    # "meshName"      : meshName,
                                    # "polyId"        : polyId,
                                    "id"            : id,
                                    "typologyId"    : typologyId,
                                    "typologyName"  : typologyName,
                                    "floor"         : floor,
                                    "area"          : area,
                                    "useId"         : useId,
                                    "useName"       : useName,
                                    "height"        : height,
                                    "void"          : void,
                                    "option"        : option,
                                    "phase"         : phase,
                        }
                    elif attrType == "area":
                        tmpData = {
                                    # "meshName"      : meshName,
                                    # "polyId"        : polyId,
                                    "id"            : id,
                                    # "floor"         : floor,
                                    "area"          : area,
                        }
                    elif attrType == "use":
                        tmpData = {
                                    # "meshName"      : meshName,
                                    # "polyId"        : polyId,
                                    "id"            : id,
                                    # "floor"         : floor,
                                    "useID"         : useId,
                                    "useName"       : useName,
                        }

                    data.append(tmpData)
                    floor += 1
        
            bm.free
        return(data)
    return
    
# a function to walk the nodes, looking for the source 
# of the attribute, the source being the RoMa objects
# def walkNodes(links):
#     items = None
#     if len(links) > 0:
#         for link in links:
#             sockets = [x for x in link.to_node.inputs]
#             for socket in sockets:
#                 if socket.is_linked:
#                     if socket.rna_type.name == 'RoMa_stringCollection_SocketType':
#                         parent_node = socket.links[0].from_node
#                         for output in parent_node.outputs:
#                             if output.name == 'RoMa Mesh':
#                                 items = output.object_items
#                                 return(items)
#                     else:
#                         next_node = socket.links[0].to_node
#                         if next_node.outputs:
#                             links = next_node.outputs[0].links
#                             if links:
#                                 items = walkNodes(links)
#                                 if items:
#                                     return(items)
#     else:
#         return None


# a function used to store the order of the children nodes
# used to run them in the proper order
def walkBackwards(parentNode, node, depth):
    depth += 1
    if node.inputs:
        inputs = node.inputs
        for input in inputs:
            if input.links:
                links = input.links
                for link in links:
                    nextNode = link.from_node
                    nodeData = { "node" : nextNode,
                                "depth": depth
                               }
                    parentNode.executionOrder.append(nodeData)
                    walkBackwards(parentNode, nextNode, depth)
    else: # if there are no inputs, it may be that the node is an attribute node
        if node.outputs[0].identifier == "Attribute":
            sourceObjects = parentNode.inputs['RoMa Mesh'].object_items
            node.objNames.clear()
            for obj in sourceObjects:
                item = node.objNames.add()
                item.name = obj.name
                print(f"Assegno {item.name}  a {parentNode.name}")
                
            # print(f"maskerina {node.name}   {node.objs}")
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
            tree.execute()
            # tree.execute(bpy.context)
            
def update_schedule_node_editor(self, context):
        nodeName = context.active_node.name
        treeName = context.active_node.id_data.name
        nodeIdentifier = f"{treeName}::{nodeName}"
        bpy.ops.node.schedule_viewer(sourceNode = nodeIdentifier)
        
# Function to add item to object_items
def RoMa_attribute_addItem(nodeFingerPrint, socketName, inputOutput):
    node = readNodeFingerPrint(nodeFingerPrint)
    if inputOutput == "both":
        sockets = ['input', 'output']
    elif inputOutput == "input":
        sockets = ['input']
    else:
        sockets = ['output']
        
    for socket in sockets:
        if socket == "input":
            collection = node.inputs[socketName].object_items
        else:
            collection = node.outputs[socketName].object_items
        item = collection.items.add()
        item.name = f"Item {len(collection.items)-1}"
        collection.active_index = len(collection.items) - 1
        
    return {'FINISHED'}

# Function to remove items from object_items
def RoMa_attribute_removeItem(nodeFingerPrint, socketName ,inputOutput):
    if inputOutput == "both":
        sockets = ['input', 'output']
    elif inputOutput == "input":
        sockets = ['input']
    else:
        sockets = ['output']
        
    node = readNodeFingerPrint(nodeFingerPrint)
    for socket in sockets:
        if socket == "input":
            collection = node.inputs[socketName].object_items
        else:
            collection = node.outputs[socketName].object_items
        
        collectionSize = len(collection.items)
        while collectionSize > 0:
            collection.items.remove(collection.active_index)
            collection.active_index = min(max(0, collection.active_index - 1), len(collection.items) - 1)
            collectionSize -= 1
        
        # if collection.active_index >= 0 and collection.active_index < len(collection.items):
        #     collection.items.remove(collection.active_index)
        #     collection.active_index = min(max(0, collection.active_index - 1), len(collection.items) - 1)
    return {'FINISHED'}

# Function to add a key-value item to an element of the collection
def RoMa_attribute_addKeyValueItem(**kwargs):
    params = {
        'node': None,
        'item_index': None,
        'key': None,
        'valueType': None,
        'stringValue': None,
        'floatValue': None,
        'inputOutput' : None,
        'socketName' : None
    }
    
    params.update(kwargs)
    
    node = readNodeFingerPrint(params['node'])
    item_index = params['item_index']
    key = params['key']
    valueType = params['valueType']
    stringValue = params['stringValue']
    floatValue = params['floatValue']
    inputOutput = params['inputOutput']
    socketName = params['socketName']
    
    if inputOutput == "both":
        sockets = ['input', 'output']
    elif inputOutput == "input":
        sockets = ['input']
    else:
        sockets = ['output']
    
    for socket in sockets:
        if socket == "input":
            collection = node.inputs[socketName].object_items
        else:
            collection = node.outputs[socketName].object_items
    
        item = collection.items[item_index]
        kv_item = item.key_value_items.add()
        kv_item.name = key
        kv_item.value_type = valueType
        
        if valueType == "FLOAT":
            kv_item.value_float = floatValue
        else:
            kv_item.value_type = "STRING"
            kv_item.value_string = stringValue
    
    return {'FINISHED'}

# Function to remove a key-value item from an element of the collection
# def RoMa_attribute_removeKeyValueItem(self, **kwargs):
#     params = {
#         'node': None,
#         'item_index': None,
#         'key_value_index': None,
#         'inputOutput' : None,
#         'socketName' : None
#     }
    
#     params.update(kwargs)
    
#     node = readNodeFingerPrint(params['node'])
#     item_index = params['item_index']
#     key_value_index = params['key_value_index']
#     inputOutput = params['inputOutput']
#     socketName = params['socketName']

#     if inputOutput == "both":
#         sockets = ['input', 'output']
#     elif inputOutput == "input":
#         sockets = ['input']
#     else:
#         sockets = ['output']
    
#     for socket in sockets:
#         if socket == "input":
#             collection = node.inputs[socketName].object_items
#         else:
#             collection = node.outputs[socketName].object_items

#         item = collection.items[item_index]
#         if key_value_index >= 0 and key_value_index < len(item.key_value_items):
#             item.key_value_items.remove(self.key_value_index)
#     return {'FINISHED'}

# a function to copy attributes between sockets
def copyAttributesToSocket(object_items, nodeFingerPrint, socketName, inputOutput):
    node = readNodeFingerPrint(nodeFingerPrint)
    if inputOutput == "both":
        sockets = ['input', 'output']
    elif inputOutput == "input":
        sockets = ['input']
    else:
        sockets = ['output']
            
    for attr in object_items:
        RoMa_attribute_addItem(nodeFingerPrint, socketName, inputOutput)
        for socket in sockets:
            if socket == "input":
                attributeIndex = node.inputs[socketName].object_items.active_index
            else:
                attributeIndex = node.outputs[socketName].object_items.active_index
        
            for key in attr['key_value_items']:
                if key['value_type'] == "FLOAT":
                    RoMa_attribute_addKeyValueItem( node=nodeFingerPrint,
                                                    item_index=attributeIndex,
                                                    key=key['name'],
                                                    valueType=key['value_type'],
                                                    floatValue=key['value_float'],
                                                    inputOutput=socket,
                                                    socketName=socketName
                                                    )
                else:
                    RoMa_attribute_addKeyValueItem(node=nodeFingerPrint,
                                                    item_index=attributeIndex,
                                                    key=key['name'],
                                                    valueType=key['value_type'],
                                                    stringValue=key['value_string'],
                                                    inputOutput=socket,
                                                    socketName=socketName
                                                    )
    
    
            
#############################################################################
########## Classes to  manage attribute collection  #########################
#############################################################################                

            
# Class to store the name of RoMa objects
# This class is used to define the list in 
# RoMa_stringCollection_Socket and in the keys
class RoMa_string_item(PropertyGroup):
    name: StringProperty(name="Name")


# Define a key-value pair used in RoMa_attribute_collectionItem
class RoMa_keyValueItem(bpy.types.PropertyGroup):
    # key: bpy.props.StringProperty(name="Key", description="Element's key")
    value_string: bpy.props.StringProperty(name="String value", description="String value", default="")
    value_float: bpy.props.FloatProperty(name="Float value", description="Float value", default=-1)
    value_type: bpy.props.StringProperty( name="Value Type", description="Type value", default='FLOAT')


# Define the elemnent of the collection RoMa_attribute_propertyGroup
# It contains name and a collection of items
class RoMa_attribute_collectionItem(bpy.types.PropertyGroup):
    # name: bpy.props.StringProperty(name="Name", description="Collection element name")
    key_value_items: bpy.props.CollectionProperty(type=RoMa_keyValueItem)

    
# # Class to store the attributes of RoMa objects
class RoMa_attribute_propertyGroup(PropertyGroup):
    items: bpy.props.CollectionProperty(type=RoMa_attribute_collectionItem)
    active_index: bpy.props.IntProperty()


#############################################################################
########## RoMa Nodetree   ##################################################
#############################################################################           

# The node tree for RoMa schedules
class RoMaTree(NodeTree):
    '''RoMa schedule'''
    bl_idname = 'RoMaTreeType'
    bl_label = "RoMa Schedule"
    bl_icon = 'NODETREE'
    
    def execute(self):
        for node in self.nodes:
            node.execute()    
    
# RoMa custom socket type
# used to collect mesh names
class RoMa_stringCollection_Socket(NodeSocket):
    """RoMa node socket string collection type"""
    bl_idname = 'RoMa_stringCollection_SocketType'
    bl_label = "RoMa Mesh Node Socket"
    
    object_items: CollectionProperty(type=RoMa_string_item)
   
    def draw(self, context, layout, node, text):
        layout.label(text=text)

    @classmethod
    def draw_color_simple(cls):
        return (0, 0.84, 0.64, 1)
    
# RoMa custom socket type
# used in the math node
class RoMa_attributesCollectionAndFloat_Socket(NodeSocket):
    """RoMa node socket attribute collection and float type"""
    bl_idname = 'RoMa_attributeCollectionAndFloat_SocketType'
    bl_label = "RoMa Mesh Node and Float values Socket"
    
    object_items: PointerProperty(type=RoMa_attribute_propertyGroup)
    default_value : FloatProperty(default=1.0) 
   
    def draw(self, context, layout, node, text):
        if self.is_output:
            layout.label(text=text)
        else:
            if self.is_linked:
                layout.label(text=text)
            else:
                layout.prop(self,"default_value",text=text)
  
    @classmethod
    def draw_color_simple(cls):
        return (0.63, 0.63, 0.63, 1)

    
# RoMa custom socket type
# used to collect attributes
class RoMa_attributesCollection_Socket(NodeSocket):
    """RoMa node socket attribute collection type"""
    bl_idname = 'RoMa_attributeCollection_SocketType'
    bl_label = "RoMa Mesh Node Socket"
    
    object_items: PointerProperty(type=RoMa_attribute_propertyGroup)
   
    def draw(self, context, layout, node, text):
        layout.label(text=text)
  
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



##########################################################################
################ Nodes ###################################################
##########################################################################

# Mix-in class for all custom nodes in this tree type.
# Defines a poll function to enable instantiation.
class RoMaTreeNode:
    @classmethod
    def poll(cls, ntree):
        return ntree.bl_idname == 'RoMaTreeType'
    
    def execute(self):
        pass

class RoMaGroupInput(RoMaTreeNode, Node):
    '''Input node containing all the RoMa meshes existing in the scene'''
    bl_idname = 'Input RoMa Mesh'
    bl_label = 'Group Input - All'

    def init(self, context):
        self.outputs.new('RoMa_stringCollection_SocketType', 'RoMa Mesh')
    
    def update_selected_objects(self):
        if self.outputs['RoMa Mesh'].is_linked:
            cleanOutputs(self)
            objs = bpy.context.scene.objects
            # attributes = getAttributes(objs)
        
            # romaObjs = []
            romaObjs = [obj for obj in objs if obj is not None and obj.type == "MESH" and "RoMa object" in obj.data]
            # romaObjs = [obj.name for obj in objs if obj is not None and obj.type == "MESH" and "RoMa object" in obj.data]
            # self.outputs['RoMa Mesh'].object_items = romaObjs
            for obj in romaObjs:
                item = self.outputs['RoMa Mesh'].object_items.add()
                item.name = obj.name
            print(f"RoMa meshes collected {len(self.outputs['RoMa Mesh'].object_items)}")

    def update(self):
        self.update_selected_objects()
        
    def execute(self):
        self.update_selected_objects()
        

    
class RoMaSelectedInput(RoMaTreeNode, Node):
    '''Input node containing the selected RoMa meshes'''
    bl_idname = 'Input RoMa Selected Mesh'
    bl_label = 'Group Input - Selected'
   
    def init(self, context):
        self.outputs.new('RoMa_stringCollection_SocketType', 'RoMa Mesh')
    
    def update_selected_objects(self):
        if self.outputs['RoMa Mesh'].is_linked:
            cleanOutputs(self)

            objs = bpy.context.selected_objects
            romaObjs = [obj for obj in objs if obj is not None and obj.type == "MESH" and "RoMa object" in obj.data]
            for obj in romaObjs:
                item = self.outputs['RoMa Mesh'].object_items.add()
                item.name = obj.name
            print(f"RoMa meshes collected {len(self.outputs['RoMa Mesh'].object_items)}")

    def update(self):
        self.update_selected_objects()  
      
    def execute(self):
        self.update_selected_objects()

    
class RoMaAllAttributes(RoMaTreeNode, Node):
    '''RoMa All Available Attributes'''
    bl_idname = 'RoMa All Attributes'
    bl_label = 'RoMa All Attributes'
    # bl_description = 'Attribute'
    
    objNames : CollectionProperty(type=RoMa_string_item)
    
    def init(self, context):
        self.outputs.new('RoMa_attributeCollection_SocketType', 'All Attributes', identifier = 'Attribute')
        self.outputs['Attributes'].display_shape = 'DIAMOND_DOT'
        
    def manualExecute(self):
        print(f"eseguo manualmente all attributes")
        cleanSocket(self, 'Attribute', 'output')

        nodeFingerPrint = writeNodeFingerPrint(self)
        attributes = getAttributes(self.objNames, "all")
        if attributes:
            for attr in attributes:
                # add a new entry to allocate parameters
                RoMa_attribute_addItem(nodeFingerPrint, "Attribute", "output")
                
                attributeIndex = self.outputs['Attribute'].object_items.active_index
                # add keys to the entry
                for key, value in attr.items():
                    try:
                        float(value)
                        RoMa_attribute_addKeyValueItem( node=nodeFingerPrint,
                                                                item_index=attributeIndex,
                                                                key=key,
                                                                valueType="FLOAT",
                                                                floatValue=value,
                                                                socketName='Attribute'
                                                                )
                    except ValueError:
                        RoMa_attribute_addKeyValueItem( node=nodeFingerPrint,
                                                                item_index=attributeIndex,
                                                                key=key,
                                                                valueType="STRING",
                                                                stringValue=value,
                                                                socketName='Attribute'
                                                                )

            print("-------------------------------")
            print(f"stampo gli attributi ottenuti nel nodo {self.name}")
            items = self.outputs['Attribute'].object_items.items
            for item in items:
                print(f"Item name {item.name} has {len(item['key_value_items'])} attributes")
                for key in item['key_value_items']:
                    if key['value_type'] == "STRING":
                        print(f"key {key['name']} has value {key['value_string']} ")
                    else:
                        print(f"key {key['name']} has value {key['value_float']}")

            
    
    def execute(self):
        pass

         
    
class RoMaAreaAttribute(RoMaTreeNode, Node):
    '''RoMa Area Attribute'''
    bl_idname = 'RoMa Area Attribute'
    bl_label = 'RoMa Area'
    # bl_description = 'Attribute'
    
    objNames : CollectionProperty(type=RoMa_string_item)
    
    def init(self, context):
        self.outputs.new('RoMa_attributeCollection_SocketType', 'Area', identifier="Attribute")
        self.outputs['Area'].display_shape = 'DIAMOND_DOT'

    def manualExecute(self):
        cleanSocket(self, 'Attribute', 'output')

        nodeFingerPrint = writeNodeFingerPrint(self)
        attributes = getAttributes(self.objNames, "area")
        if attributes:
            for attr in attributes:
                # add a new entry to allocate parameters
                RoMa_attribute_addItem(nodeFingerPrint, "Attribute", "output")
                attributeIndex = self.outputs['Attribute'].object_items.active_index
                # add keys to the entry
                for key, value in attr.items():
                    try:
                        float(value)
                        RoMa_attribute_addKeyValueItem( node=nodeFingerPrint,
                                                                item_index=attributeIndex,
                                                                key=key,
                                                                valueType="FLOAT",
                                                                floatValue=value,
                                                                socketName='Attribute'
                                                                )
                    except ValueError:
                        RoMa_attribute_addKeyValueItem( node=nodeFingerPrint,
                                                                item_index=attributeIndex,
                                                                key=key,
                                                                valueType="STRING",
                                                                stringValue=value,
                                                                socketName='Attribute'
                                                                )
    def execute(self):
        pass

            
class RoMaUseAttribute(RoMaTreeNode, Node):
    '''RoMa Use Attribute'''
    bl_idname = 'RoMa Use Attribute'
    bl_label = 'RoMa Use'
    # bl_description = 'Attribute'
    
    objNames : CollectionProperty(type=RoMa_string_item)
    
    def init(self, context):
        self.outputs.new('RoMa_attributeCollection_SocketType', 'Use', identifier="Attribute")
        self.outputs['Use'].display_shape = 'DIAMOND_DOT'

    def manualExecute(self):
        cleanSocket(self, 'Attribute', 'output')

        nodeFingerPrint = writeNodeFingerPrint(self)
        attributes = getAttributes(self.objNames, "use")
        if attributes:
            for attr in attributes:
                # add a new entry to allocate parameters
                RoMa_attribute_addItem(nodeFingerPrint, "Attribute", "output")
                attributeIndex = self.outputs['Attribute'].object_items.active_index
                # add keys to the entry
                for key, value in attr.items():
                    try:
                        float(value)
                        RoMa_attribute_addKeyValueItem( node=nodeFingerPrint,
                                                                item_index=attributeIndex,
                                                                key=key,
                                                                valueType="FLOAT",
                                                                floatValue=value,
                                                                socketName='Attribute'
                                                                )
                    except ValueError:
                        RoMa_attribute_addKeyValueItem( node=nodeFingerPrint,
                                                                item_index=attributeIndex,
                                                                key=key,
                                                                valueType="STRING",
                                                                stringValue=value,
                                                                socketName='Attribute'
                                                                )
    def execute(self):
        pass
                            
   
class RoMaCaptureAttribute(RoMaTreeNode, Node):
    '''Read RoMa attributes'''
    bl_idname = 'Capture RoMa attribute'
    bl_label = "Capture attribute"
    
    inputList = ["RoMa Mesh", "Attributes"]
    outputList = ["Attributes"]
    
    # validated = True
    executionOrder = []
    
    def init(self, context):
        self.inputs.new('RoMa_stringCollection_SocketType', 'RoMa Mesh')
        self.inputs.new('RoMa_attributeCollection_SocketType', 'Attributes')
        # self.inputs['Attributes'].display_shape = 'DIAMOND_DOT'
        self.inputs['Attributes'].hide_value = True
        
        # self.outputs.new('RoMa_stringCollection_SocketType', 'RoMa Mesh')
        self.outputs.new('RoMa_attributeCollection_SocketType', 'Attributes')
        # self.outputs['Attributes'].display_shape = 'DIAMOND_DOT'
                                                                       
        addKeysToNode(self, inputs=self.inputList, outputs=self.inputList)
        
    def copy(self, node):
        addKeysToNode(self, inputs=self.inputList, outputs=self.inputList)
        cleanInputs(self)
        cleanOutputs(self)
        # self.validated = True
        
    def free(self):
        removeKeyFromNode(self, inputs=self.inputList, outputs=self.outputList)
        
                
    # def update(self):
    #     self.validated = checkLink(self)
    #     clearInputs(self)
    def update(self):
        print("capture attribute eseguo dopo update")
        if checkLink(self):
            if self.inputs['RoMa Mesh'].is_linked:
                self.readWrite_RoMa_mesh()
                if self.inputs['Attributes'].is_linked and self.outputs['Attributes'].is_linked:
                    self.readWrite_Attribute()
            else:
                cleanSocket(self, 'RoMa Mesh', 'input')
            
            if self.inputs['Attributes'].is_linked == False:
                cleanSocket(self, 'Attributes' , 'both')
                

    def readWrite_RoMa_mesh(self):
        cleanSocket(self, 'RoMa Mesh', 'input')
        object_items = self.inputs['RoMa Mesh'].links[0].from_socket.object_items
        for obj in object_items:
            itemIn = self.inputs['RoMa Mesh'].object_items.add()
            # itemOut = self.outputs['RoMa Mesh'].object_items.add()
            itemIn.name = obj.name
            # itemOut.name = obj.name
            
        ob = self.inputs['RoMa Mesh'].object_items
        print(f"oggetti linkati : {len(ob)}")
        for o in ob: print(f"{o.name}")
        
    def readWrite_Attribute(self):
        cleanSocket(self, 'Attributes', 'both')
        child = self.inputs['Attributes'].links[0].from_node
        nodeData = {    "node" : child,
                        "depth": 0
                    }
        self.executionOrder = [nodeData]
        # all the children nodes are searched and found, sorted 
        # from the deepest, and the run in that order
        print(f"inizio a camminare al contrario")
        walkBackwards(self, child, depth = 0)
        sortedOrder = sorted(self.executionOrder, key=lambda x: x['depth'], reverse=True)
        for el in sortedOrder:
            if hasattr(el['node'], "manualExecute"):
                print(f"Capture attribute esegue: {el}")
                el['node'].manualExecute()
        print(f"copio gli attributi in output di capture attribute")                
        object_items = self.inputs['Attributes'].links[0].from_socket.object_items.items
        
        nodeFingerPrint = writeNodeFingerPrint(self)
        copyAttributesToSocket(object_items, nodeFingerPrint, "Attributes", "output")
        # for attr in object_items:
        #     RoMa_attribute_addItem(nodeFingerPrint, "both")
        #     attributeIndex = self.outputs['Attributes'].object_items.active_index
            
        #     for key in attr['key_value_items']:
        #         if key['value_type'] == "FLOAT":
        #             RoMa_attribute_addKeyValueItem( node=nodeFingerPrint,
        #                                             item_index=attributeIndex,
        #                                             key=key['name'],
        #                                             valueType=key['value_type'],
        #                                             floatValue=key['value_float'],
        #                                             inputOutput="both"
        #                                             )
        #         else:
        #             RoMa_attribute_addKeyValueItem( node=nodeFingerPrint,
        #                                             item_index=attributeIndex,
        #                                             key=key['name'],
        #                                             valueType=key['value_type'],
        #                                             stringValue=key['value_string']
        #                                             inputOutput="both"
        #                                             )
            
            
        
        # for obj in object_items:
        #     itemIn = self.inputs['Attributes'].object_items.add()
        #     itemOut = self.outputs['Attributes'].object_items.add()
        #     itemIn.name = obj.name
        #     itemOut.name = obj.name
            
            
            
        print(f"gli attributi copiati in capture attribute sono:-------------------------------------")
        items = self.outputs['Attributes'].object_items.items
        for item in items:
            print()
            print(f"Item name {item.name} has {len(item['key_value_items'])} attributes")
            for key in item['key_value_items']:
                if key['value_type'] == "STRING":
                    print(f"key {key['name']} has value {key['value_string']} ")
                else:
                    print(f"key {key['name']} has value {key['value_float']}")
             
        
        
        
    def execute(self):
        print(f"capture attribute eseguo automatico")
        if checkLink(self):
            if self.inputs['RoMa Mesh'].is_linked:
                self.readWrite_RoMa_mesh()
                if self.inputs['Attributes'].is_linked and self.outputs['Attributes'].is_linked:
                    self.readWrite_Attribute()
                    
                    
                    
                   

                
                
                            
                        

# class RoMaMathMenu(Menu):
#     bl_label = "Math"
#     bl_idname = "ROMA_NODE_MT_menu_math"
    
#     # print("miao", props.dropdown_box_math)
    
#     def draw(self, context):
#         node = context.node
#         props = node.RoMa_math_node_entries
#         enumItems = props.bl_rna.properties["dropdown_box_math"].enum_items
        
#         set1 = enumItems[:10]        
#         set2 = enumItems[10:15]   
#         set3 = enumItems[15:]   
#         layout = self.layout
#         col = layout.column()
#         col.prop_tabs_enum(props, "dropdown_box_math")

#         row = layout.row()
#         col = row.column()
#         col.label(text="Functions")
#         for item in set1:
#             col.prop_enum(props, "dropdown_box_math",item.name, icon='BLANK1')
#         col = row.column()
#         col.label(text="Comparison")
#         for item in set2:
#             col.prop_enum(props, "dropdown_box_math",item.name, icon="CUBE")
#         col = row.column()
#         col.label(text="Rounding")
#         for item in set3:
#             col.prop_enum(props, "dropdown_box_math",item.name, icon='BLANK1')
        
        
class RoMaMathNode(RoMaTreeNode, Node):
    '''Read RoMa attributes'''
    bl_idname = 'RoMa Math Node'
    bl_label = "Math Node"
    
    # EnumProperty for dropdown box math
    dropdown_box_math: EnumProperty(
        items=(
            ("Add", "Add", "A + B."),
            ("Subtract", "Subtract", "A - B."),
            ("Multiply", "Multiply", "A * B."),
            ("Divide", "Divide", "A / B."),
            ("Power", "Power", "A power B."),
            ("Logarithm", "Logarithm", "Logarithm A base B."),
            ("Square Root", "Square Root", "Square root of A."),
            ("Inverse Square Root", "Inverse Square Root", "1 / Square root of A."),
            ("Absolute", "Absolute", "Magnitude of A."),
            ("Exponent", "Exponent", "exp(A)."),
            ("Minimum", "Minimum", "The minimum from A and B."),
            ("Maximum", "Maximum", "The maximum from A and B."),
            ("Less Than", "Less Than", "1 if A < 0 else 0."),
            ("Greater Than", "Greater Than", "1 if A > B else 0."),
            ("Compare", "Compare", "1 if (A == B)."),
            ("Round", "Round", "Round A to the nearest integer. Round upward if the fraction part is 0.5."),
            ("Floor", "Floor", "The largest integer smaller than or equal A."),
            ("Ceil", "Ceil", "The smallest integer greater than or equal A."),
            ("Truncate", "Truncate", "The integer part of A, removing fractional digits."),
        ),
        name="Mathematical functions",
        default="Add",
        update=lambda self, context: self.update_socket_visibility()
    )

    
    dropdown_A : EnumProperty(
        items=lambda self, context : self.getAvailableAttributes("A"),
        description="Attribute to use in field A"
    )
    
    dropdown_B : EnumProperty(
        items=lambda self, context: self.getAvailableAttributes("B"),
        description="Attribute to use in field B"
    )
    
   
    # RoMa_math_node_entries: PointerProperty(type=dropdown_box_maths)
    # A_list : CollectionProperty(type=RoMa_attribute_item)
    # A_value : FloatProperty(
    #             name='A',
    #             precision=3,)
    
    # B_list : CollectionProperty(type=RoMa_attribute_item) 
    # B_value : FloatProperty(
    #             name='B',
    #             precision=3,)
    # output_list : CollectionProperty(type=RoMa_attribute_item)
    # output : FloatProperty(
    #             name='output',
    #             precision=3,)
   
    
    
    
    inputList = ["A","B"]
    AB_List = ['Add', 'Subtract', 'Multiply', 'Divide']
    AB_Power = ['Power']
    AB_Log = ["Logarithm"]
    AB_Square = ["Square Root", "Inverse Square Root", "Absolute", "Exponent"]
    AB_Types_Values = ["int", "float"]
    
    def init(self, context):
        # self.inputs.new('NodeSocketFloat', 'A Value', identifier='A')
        self.inputs.new('RoMa_attributeCollectionAndFloat_SocketType', 'Attribute', identifier='A')
        # self.inputs['A_list'].display_shape = 'DIAMOND_DOT'
        self.inputs['A'].display_shape = 'DIAMOND_DOT'
        
        # self.inputs.new('NodeSocketFloat', 'B Value', identifier='B')
        self.inputs.new('RoMa_attributeCollectionAndFloat_SocketType', 'Attribute', identifier='B')
        # self.inputs['B_list'].display_shape = 'DIAMOND_DOT'
        self.inputs['B'].display_shape = 'DIAMOND_DOT'
        
        # self.outputs.new('NodeSocketFloat', 'Value', identifier='output')
        self.outputs.new('RoMa_attributeCollectionAndFloat_SocketType', 'Attribute', identifier='output')
        # self.outputs['output_list'].display_shape = 'DIAMOND_DOT'
        self.outputs['output'].display_shape = 'DIAMOND_DOT'
        
        self.update_socket_visibility()
        
        addKeysToNode(self, inputs=self.inputList)
        
    def copy(self, node):
        addKeysToNode(self, inputs=self.inputList)
        self.update_socket_visibility()
        
    def free(self):
        removeKeyFromNode(self, inputs=self.inputList)
        
    def assignValueToInput(self, inputName):
        # node = readNodeFingerPrint(sourceNode)
        # print(f"{node}  {self}")
        if self.inputs[inputName].is_linked:
            socket = self.inputs[inputName].links[0].from_socket
            if hasattr(socket, 'object_items'):
                A = socket.object_items
            else:
                A = socket.default_value
        else:
            A = self.inputs[inputName].default_value
        return(A)

    def manualExecute(self):
        selection = self.dropdown_box_math
        # nodeFingerPrint = writeNodeFingerPrint(self)
        if (selection in self.AB_List + self.AB_Power + self.AB_Log):
            A = self.assignValueToInput("A")
            print(f"assegnato A {A}")
            if self.inputs['B'].is_linked:
                socket = self.inputs['B'].links[0].from_socket
                if hasattr(socket, 'object_items'):
                    B = socket.object_items
                else:
                    B = socket.default_value
            else:
                B = self.inputs['B'].default_value

        elif selection in self.AB_Square:
            if self.inputs['A'].is_linked:
                socket = self.inputs['A'].links[0].from_socket
                if hasattr(socket, 'object_items'):
                    A = socket.object_items
                else:
                    A = socket.default_value
            else:
                A = self.inputs['A'].default_value
        
        if checkLink(self):
            
            output = {"type" : None, "value" : 0}
            if selection == "Add":
                if type(A).__name__ in self.AB_Types_Values and type(B).__name__ in  self.AB_Types_Values:
                    output["type"] = "value"
                    output["value"] = A + B
                elif type(A).__name__ == "bpy_prop_collection_idprop" and type(B).__name__ in  self.AB_Types_Values:
                    output["type"] = "list"
                    for el in A:
                        print(f"input {el.area}")
            
            elif selection == "Subtract":
                output = A - B
            elif selection == "Multiply":
                output = A * B
            elif selection == "Divide":
                output = A / B
            elif selection == "Power":
                output = A ** B
            elif selection == "Logarithm":
                output = math.log(A, B)
            elif selection == "Square Root":
                output = math.sqrt(A)
            elif selection == "Inverse Square Root":
                output = 1/math.sqrt(A)
            elif selection == "Absolute":
                output = abs(A)
            elif selection == "Exponent":
                output = math.exp(A)
                
            print(f"pireooooooooooooo {output}")
            self.outputs.move(0 ,1)
        
            # if output["type"] == "value":
            #     self.outputs['output'].default_value = output["value"]
            #     print(f"Output {self.outputs['output'].default_value}")
            # else:
            #     # cleanOutputs(self)
            #     for attr in results:
            #         item = self.outputs['output_list'].object_items.add()
            #         for key, value in attr[0].items():
            #             setattr(item, key, value)
                        
            #     for i in self.outputs['output_list'].object_items:
            #         print(f"Outputs {i.area}")
        
        
    def execute(self):
        self.manualExecute()
            
        
    # def update(self):
    #     if self.inputs["A"].is_linked:
    #         sockectName = self.inputs['A'].links[0].from_socket.rna_type.name
    #         if sockectName == "RoMa_attributeCollection_SocketType":
    #             self.inputs.move(0,1)
            
    def draw_buttons(self, context, layout):
        cleanInputs(self)
        layout.prop(self, "dropdown_box_math", text="")
        if self.inputs[0].is_linked and self.inputs[0].links:
            if self.inputs[0].links[0].from_node.outputs:
                linked_output = self.inputs[0].links[0].from_socket
                if linked_output.rna_type.name == 'RoMa_attributeCollection_SocketType':
                    layout.prop(self, "dropdown_A", text="A")
        if self.inputs[1].is_linked and self.inputs[1].links:
            if self.inputs[1].links[0].from_node.outputs:
                linked_output = self.inputs[1].links[0].from_socket
                if linked_output.rna_type.name == 'RoMa_attributeCollection_SocketType':
                    layout.prop(self, "dropdown_B", text="B")
        

   
        
    def getAvailableAttributes(self, field):
        attributes=[]
        # objects = []
        # items = []
        # get the list of available attributes
        # from the linked node
        # print(f"field {self} {field}")
        if field == "A":
            if self.inputs[0].is_linked and self.inputs[0].links:
                if self.inputs[0].links[0].from_node.outputs:
                    linked_output = self.inputs[0].links[0].from_socket
                    if linked_output.rna_type.name == 'RoMa_attributeCollection_SocketType':
                        items = linked_output.object_items.items
                        # get the unique key, sort them alphabetically and remove "id"
                        keys = uniqueKeys(items, sort=True, remove = ["id"])
                        for key in keys:
                            newProp = (key, key, key)
                            attributes.append(newProp)
                        return(attributes)
        elif field == "B":
            if self.inputs[1].is_linked and self.inputs[1].links:
                if self.inputs[1].links[0].from_node.outputs:
                    linked_output = self.inputs[1].links[0].from_socket
                    if linked_output.rna_type.name == 'RoMa_attributeCollection_SocketType':
                        items = linked_output.object_items.items
                        keys = uniqueKeys(items, sort=True, remove = ["id"])
                        for key in keys:
                            newProp = (key, key, key)
                            attributes.append(newProp)
                        return(attributes)
        else: 
            return()
        
    
    def update_socket_visibility(self):
        selection = self.dropdown_box_math
        # self.inputs['A_list'].hide = True
        # self.inputs['B_list'].hide = True
        # self.outputs['output_list'].hide = True
        
        self.inputs['A'].hide = False
        self.inputs['B'].hide = False
        if selection in self.AB_List:
            self.inputs['A'].name = "A Value"
            self.inputs['B'].name = "B Value"
        elif selection in self.AB_Power:
            self.inputs['A'].name = "Base"
            self.inputs['B'].name = "Exponent"
        elif selection in self.AB_Log:
            self.inputs['A'].name = "Value"
            self.inputs['B'].name = "Base"
        elif selection in self.AB_Square:
            self.inputs['A'].name = "Value"
            self.inputs['B'].hide = True
            
        else:
            self.inputs['A'].hide = True
            self.inputs['B'].hide = True
        
        self.update()
        
        
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
    
    def update(self):
        self.execute()

    def draw_buttons(self, context, layout):
        layout.prop(self, 'float')

    def execute(self):
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
        
    def update(self):
        self.execute()

    def draw_buttons(self, context, layout):
        layout.prop(self, 'integer')
        
    def execute(self):
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
        self.execute()
    
    def execute(self):
        if self.validated:
            cleanInputs(self)
            cleanOutputs(self)
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
    
    toggle : bpy.props.BoolProperty(
            name = "Show Schedule",
            default = False,
            update = update_schedule_node_editor)

    validated = True
    
    def init(self, context):
        # self.outputs.new('RoMa_stringCollection_SocketType', 'RoMa Mesh')
        # self.inputs.new('RoMa_stringCollection_SocketType', 'RoMa Mesh')
        self.inputs.new('RoMa_attributeCollection_SocketType', 'Attribute')
        self.inputs['Attribute'].hide_value = True
        self.inputs['Attribute'].display_shape = 'DIAMOND_DOT'
    
    def update(self):
        self.execute()
        
    def execute(self):
        if self.validated:
            # cleanInputs(self)
            if self.inputs['Attribute'].is_linked:
                # print(f"Data: {bpy.data.node_groups['RoMa Schedule'].nodes['Capture attribute'].inputs['Attribute'].links[0].from_socket.object_items}")
                object_items = self.inputs['Attribute'].links[0].from_socket.object_items
                # print("----------------------------------")
                # print(f"{len(object_items)}")
                # print("Reader Node - Oggetti Selezionati:")
                # for a in object_items:
                #      print(a.meshName, a.polyId, a.id, a.area, len(object_items))
            
    def draw_buttons(self, context, layout):
        # nodeName = self.name
        # treeName = self.id_data.name
        # nodeIndentifier = f"{treeName}::{nodeName}"
        nodeIndentifier = writeNodeFingerPrint(self)
        col = layout.column(align=True)
        col.operator("object.roma_add_column").sourceNode = nodeIndentifier
        col.prop(self, "toggle", text="Show Schedule")

    
#############################################################################
################ Add menu ###################################################
#############################################################################

class RoMaNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == "RoMaTreeType"
    
# all categories in a list
node_categories = [
    RoMaNodeCategory('INPUT', "Input", items=[
        NodeItem("Input RoMa Mesh", label="All RoMa Meshes"),
        NodeItem("Input RoMa Selected Mesh", label="Selected RoMa Meshes"),
    ]),
    RoMaNodeCategory('ATTRIBUTE', "Attribute", items=[
        NodeItem("Capture RoMa attribute", label="Capture Attribute"),
        NodeItem("RoMa All Attributes", label="All Attributes"),
        NodeItem("RoMa Area Attribute", label="Area"),
        NodeItem("RoMa Use Attribute", label="Use"),
    ]),
    RoMaNodeCategory('MATHEMATIC', "Mathematic", items=[
        NodeItem("RoMa Math Node", label="Math"),
        NodeItem("RoMa Integer", label="Integer"),
        NodeItem("RoMa Value", label="Value"),
    ]),
    RoMaNodeCategory('SCHEDULE', "Schedule", items= [
       NodeItem("RoMa Column from Data", label="Column"),
    ]),
    RoMaNodeCategory('OUTPUT', "Output", items=[
        NodeItem("RoMa Viewer", label="Viewer"),
    ]),
]


    
        
############################################################################################
############### Schedule in node editor ####################################################
############################################################################################


class NODE_EDITOR_Roma_Draw_Schedule(Operator):
    """Tooltip"""
    bl_idname = "node.schedule_viewer"
    bl_label = "Show a schedule in the schedule editor"
    
    _handle = None
    
    sourceNode : bpy.props.StringProperty(name="Source Node")
    
    @staticmethod
    def handle_add(self, context):
        if NODE_EDITOR_Roma_Draw_Schedule._handle is None:
            NODE_EDITOR_Roma_Draw_Schedule._handle = bpy.types.SpaceNodeEditor.draw_handler_add(draw_callback_schedule_overlay,
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

def draw_callback_schedule_overlay(self, context, sourceNode):
    if context.area.ui_type == "RoMaTreeType":
        # path = sourceNode.split("::")
        # treeName = path[0]
        # nodeName = path[1]
        # node = bpy.data.node_groups[treeName].nodes[nodeName]
        node = readNodeFingerPrint(sourceNode)
        
        nodeX, nodeY = node.location
        nodeWidth = node.width
        nodeHeight = node.height
        
        system = bpy.context.preferences.system
        ui_scale = system.ui_scale
        
        nodePosX = nodeX + nodeWidth
        nodePosY = nodeY - nodeHeight
        
        cellX = 200
        cellY = 50
        orientation = "column"
        verts, edges, faces, data = dataForGraphic(sourceNode, 
                                                    posX = nodePosX, 
                                                    posY = nodePosY, 
                                                    cellWidth= cellX, 
                                                    cellHeight=cellY, 
                                                    orientation=orientation, 
                                                    scale = ui_scale,
                                                    direction = "up")
        
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        
        batch = batch_for_shader(shader, 'LINES', {"pos": verts}, indices=edges)
        shader.uniform_float("color", (0.0 ,1.0, 0.0, 1.0))
            
        gpu.state.line_width_set(1)
        gpu.state.blend_set("ALPHA")
        batch.draw(shader)
        
        font_id = font_info["font_id"]
        blf.size(font_id, 50.0)

        for i, el in enumerate(data):
            index = (len(data)-1) - i
            blf.size(font_id, 50)
            if orientation == "column":
                x = (nodePosX + 10) * ui_scale
                y = (nodePosY + 10 + (index * cellY)) * ui_scale
            else:
                x = ((nodePosX + 10) + (index * cellX)) * ui_scale
                y = (nodePosY + 10) * ui_scale
                
            blf.position(font_id, x, y, 0)
            # blf.draw(font_id, f"{round(el.area,2)}")
            blf.draw(font_id, f"{(el.useName)}")
    else:
        return

    
###################################################################################
############### 3D schedule #######################################################
###################################################################################
class RoMaAddColumn(Operator):
    '''Add a column to the schedule'''
    bl_idname="object.roma_add_column"
    bl_label="RoMa Column"
    bl_options = {'REGISTER'}
    
    sourceNode : bpy.props.StringProperty(name="Source Node")
    
    # width: FloatProperty(
    #     name="Width",
    #     description="Cell Width",
    #     min=0.01, max=100.0,
    #     default=3.0,
    # )
    
    # height: FloatProperty(
    #     name="Height",
    #     description="Cell Height",
    #     min=0.01, max=100.0,
    #     default=2.0,
    # )
    
    # data : bpy.props.StringProperty(name="Filter type name")
    
    def execute(self, context):
        # retrieve data from node
        # path = self.sourceNode.split("::")
        # treeName = path[0]
        # nodeName = path[1]
        # node = bpy.data.node_groups[treeName].nodes[nodeName]
        # data = node.inputs['Attribute'].links[0].from_socket.object_items
        
        # create a column with its cells
        mesh = bpy.data.meshes.new("RoMa Column")
        bm = bmesh.new()
        verts, edges, faces, data = dataForGraphic(self.sourceNode, 
                                                   posX = 0, 
                                                   posY = 0, 
                                                   cellWidth= 3, 
                                                   cellHeight=2, 
                                                   orientation="column", 
                                                   scale=1,
                                                   direction = "down")
        for vert in verts:
            bm.verts.new(vert)
        bm.verts.ensure_lookup_table()
        
        for e in edges:
            bm.edges.new([bm.verts[i] for i in e])
        
        bm.to_mesh(mesh)
        mesh.update()

        column = bpy.data.objects.new(name="Column", object_data=mesh)
        bpy.context.scene.collection.objects.link(column)
        
        # index = 0
        # while index < len(data):
        for index, el in enumerate(data):
            font_curve = bpy.data.curves.new(type="FONT", name="Font Curve")
            # font_curve.body = f"{round(el.area)}"
            font_curve.body = f"{el.use}"
            font_obj = bpy.data.objects.new(name="Font Object", object_data=font_curve)
            bpy.context.scene.collection.objects.link(font_obj)
            newPos = mathutils.Vector((0.3, -1.3 - (2 * index), 0.0))
            font_obj.location = font_obj.location + newPos
            # index += 1
            # parenting
            font_obj.parent = bpy.data.objects[column.name]
        return {'FINISHED'}
    
################################################################################################################
############### Function to retrieve data for schedules  #######################################################
################################################################################################################
    
# collect the data from the source node and return all
# the elements necessary to draw the column or the row
def dataForGraphic(sourceNode, posX = 0, posY = 0, cellWidth = 3, cellHeight = 2, orientation="column", scale=1, direction="up"):
    # retrieve data from node
    # path = sourceNode.split("::")
    # treeName = path[0]
    # nodeName = path[1]
    # node = bpy.data.node_groups[treeName].nodes[nodeName]
    node = readNodeFingerPrint(sourceNode)
    data = node.inputs['Attribute'].links[0].from_socket.object_items
   
    verts = []
    edges = []
    faces = []
    dir = 1
    if direction == "down":
        dir = -1
    for index in range(len(data) + 1):
        if orientation == "column":
            verticalIncrement = dir * cellHeight * index
            tmpVert = ((+0.0 + posX) * scale, (verticalIncrement + posY) * scale, 0) 
            verts.append(tmpVert)
            tmpVert = tmpVert = ((cellWidth + posX) * scale, (verticalIncrement + posY) * scale, 0)  
            verts.append(tmpVert)
        elif orientation == "row":
            horizontalIncrement = 1 * cellWidth * index
            tmpVert = ((horizontalIncrement + posX) * scale, (0 + posY) * scale, 0)   
            verts.append(tmpVert)
            tmpVert = ((horizontalIncrement + posX) * scale, (cellHeight + posY) * scale, 0)   
            verts.append(tmpVert)
        else:
            return
            
        if index < len(data):
            tmpEdge = (index * 2, (index * 2) +1)    
            edges.append(tmpEdge)
            tmpEdge = (index * 2, (index * 2) +2)   
            edges.append(tmpEdge)
            tmpEdge = ((index * 2) +1, (index * 2) +3)   
            edges.append(tmpEdge)
        
    tmpEdge = (len(data) * 2, len(data) * 2 +1)    
    edges.append(tmpEdge)
    
    faces = []
    return verts, edges, faces, data
    