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

from bpy.types import NodeTree, Node, NodeSocket, NodeTreeInterfaceSocket, Operator, PropertyGroup, Menu, UIList
from bpy.props import  EnumProperty, StringProperty, PointerProperty, FloatProperty, IntProperty, CollectionProperty
import mathutils
# import nodeitems_utils
from nodeitems_utils import NodeCategory, NodeItem
from gpu_extras.batch import batch_for_shader

from itertools import product # to generate all the combinations from a given list of lists
from collections import defaultdict # used to count the occurences of uniques


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

# function to add object items to a list
def addItemsToList(objectList, node, socketName = ""):
    nodeFingerPrint = writeNodeFingerPrint(node)
    for object in objectList:
        RoMa_attribute_addItem(nodeFingerPrint,socketName, "output")
        attributeIndex = node.outputs[socketName].object_items.active_index
        for key, value in object.items():
            try:
                float(value)
                RoMa_attribute_addKeyValueItem( node=nodeFingerPrint,
                                                item_index=attributeIndex,
                                                key=key,
                                                valueType="FLOAT",
                                                floatValue=value,
                                                socketIdentifier=socketName
                                                )
            except ValueError:
                RoMa_attribute_addKeyValueItem( node=nodeFingerPrint,
                                                item_index=attributeIndex,
                                                key=key,
                                                valueType="STRING",
                                                stringValue=value,
                                                socketIdentifier=socketName
                                                )
        
        
    

# function to identify unique values in the attribute list
# it is possibile to pass extra parameters as to 
# sort = True to sort the list
def uniqueValues(arr, **kwargs):
    params = {
        'sort' : None,
        'key' : None,
        'count' : None,
    }
    
    params.update(kwargs)
    
    sort = params['sort']
    keyName = params['key']
    keyCount = params['count']
    newList = []
    
    for a in arr:
        item = a['key_value_items']
        for itemKey in item: 
            if itemKey['name'] == keyName:
                if itemKey['value_type'] == 'FLOAT':
                    newList.append(itemKey['value_float'])
                else:
                    newList.append(itemKey['value_string'])

    if keyCount == True: # count the instances for each unique
        count_dict = defaultdict(int)
        for value in newList:
            count_dict[value] += 1
        # a tuple with key and the number of occurencies
        # result = list(count_dict.items())
        result = [{keyName: key, 'count': value} for key, value in count_dict.items()]
        
    else: # return only the unique list
        result = [{keyName: key} for key in set(newList)]
    
    if sort:
        result.sort(key=lambda x: x[0])
            
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
                #add the key to the romaKeyDictionary
                bpy.context.scene.romaKeyDictionary.add()
                last = len(bpy.context.scene.romaKeyDictionary)-1
                bpy.context.scene.romaKeyDictionary[last].name = str(key)
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
                #add the key to the romaKeyDictionary
                bpy.context.scene.romaKeyDictionary.add()
                last = len(bpy.context.scene.romaKeyDictionary)-1
                bpy.context.scene.romaKeyDictionary[last].name = str(key)
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
            #add the key to the romaKeyDictionary
            bpy.context.scene.romaKeyDictionary.add()
            last = len(bpy.context.scene.romaKeyDictionary)-1
            bpy.context.scene.romaKeyDictionary[last].name = str(key)
            # print("KEY", key)
        
# remove all the keys from the node
# when the node is deleted
def removeKeyFromNode(self, **kwargs):
    for item_name, list in kwargs.items():
        if item_name == "inputs":
            for input in list:
                key = self.path_resolve('inputs[\"'+input+'\"]')
                for i, el in enumerate(bpy.context.scene.romaKeyDictionary):
                    if el.name == str(key):
                        bpy.context.scene.romaKeyDictionary.remove(i)
                        break
        elif item_name == "outputs":
            for output in list:
                key = self.path_resolve('outputs[\"'+output+'\"]')
                for i, el in enumerate(bpy.context.scene.romaKeyDictionary):
                    if el.name == str(key):
                        bpy.context.scene.romaKeyDictionary.remove(i)
                        break
        elif item_name == "key":
            key = self
            for i, el in enumerate(bpy.context.scene.romaKeyDictionary):
                    if el.name == str(key):
                        bpy.context.scene.romaKeyDictionary.remove(i)
                        break

def cleanSocket(link, socketIdentifier, inputOutput):
    if inputOutput == "both":
        inOuts = ['input', 'output']
    elif inputOutput == "input":
        inOuts = ['input']
    else:
        inOuts = ['output']
        
    for inOut in inOuts:
        if inOut == "input":
            l = link.inputs[socketIdentifier]
        else:
            l = link.outputs[socketIdentifier]
    
        if l.bl_rna.name == 'RoMa_stringCollection_SocketType':
            l.object_items.clear()
        elif l.bl_rna.name in ['RoMa_attributeCollection_SocketType', 'RoMa_attributeCollectionAndFloat_SocketType']:
            # l.pop('object_items', None)
            nodeFingerPrint = writeNodeFingerPrint(link)
            RoMa_attribute_removeItem(nodeFingerPrint, socketIdentifier, inOut)
   
            
    
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
            inputName = input.bl_label
            outputName =  input.links[0].from_socket.bl_label
            # print(f"check linksssssssssssssssssss{self.name}     {inputName}   {outputName}")
            if inputName != outputName:
                self.color = (0.51, 0.19, 0.29)
                self.use_custom_color = True
                validated = False
    return(validated)
            
# a function to get all the attributes of the 
# selected meshes
def getAttributes(objNames, attrType):
    # for o in objNames: print(f"ottengo gli attributi per {o.name}")
    romaObjs = [obj for obj in objNames if obj is not None and bpy.data.objects[obj.name].type == "MESH" and "RoMa object" in bpy.data.objects[obj.name].data]
    if len(romaObjs) > 0:
        data = []
        for el in romaObjs:
            obj = bpy.data.objects[el.name]
          
            option = obj.roma_props['roma_option_attribute']
            phase = obj.roma_props['roma_phase_attribute']
            plot = obj.roma_props['roma_plot_attribute']
            block = obj.roma_props['roma_block_attribute']
    
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
                level = 0
                indexList = 1
                storeyPreviousGroup = 0
                while level < storeys:
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
                    if storeyGroup == level +1:
                        storeyPreviousGroup = storeyGroup
                        indexList += 1
                    
                    if attrType in ("all", "area"):
                        area = round(f.calc_area(),2)
                        if void == 1:
                            area = 0
                    
                    id = f"{meshName}_{polyId}_{level}"
                    if attrType == "all":
                        tmpData = {
                                    "id"            : id,
                                    "typologyId"    : typologyId,
                                    "level"         : level,
                                    "area"          : area,
                                    "useId"         : useId,
                                    "height"        : height,
                                    "void"          : void,
                                    "option"        : option,
                                    "phase"         : phase,
                                    "block"         : block,
                                    "plot"          : plot
                        }
                    elif attrType == "area":
                        tmpData = {
                                    "id"            : id,
                                    "area"          : area,
                        }
                    elif attrType == "use":
                        tmpData = {
                                    "id"            : id,
                                    "useID"         : useId,
                        }

                    data.append(tmpData)
                    level += 1
        
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
def walkBackwards(parentNode, inputId, node, depth):
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
                    # try:
                    #     parentNode.executionOrder[inputId]
                    # except IndexError:
                    #     parentNode.executionOrder.append([])
                    parentNode.executionOrder[inputId].append(nodeData)
                    # print(f"aggiungo {nodeData} a {inputId}")
                    walkBackwards(parentNode, inputId, nextNode, depth)
    # else: # if there are no inputs, it may be that the node is an attribute node
    #     if node.outputs[0].name == "Attribute":
    #         sourceObjects = parentNode.inputs['RoMa Mesh'].object_items
    #         node.objNames.clear()
    #         for obj in sourceObjects:
    #             item = node.objNames.add()
    #             item.name = obj.name
    #     elif node.outputs[0].name == "Function":
    #         print(f"Trovato {node.name}")
           

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
            
def update_schedule_node_editor(node):
        bpy.ops.node.schedule_viewer(sourceNode = writeNodeFingerPrint(node))

# read attribute from the specified node
def readAttributeFromLinkedNode (node, inputId):
    nodeList = ['RoMa_attributeCollectionAndFloat_SocketType', 'RoMa_attributeCollection_SocketType']
    attributes = []
    if node.inputs[inputId].is_linked and node.inputs[inputId].links:
        if node.inputs[inputId].links[0].from_node.outputs:
            linked_output = node.inputs[inputId].links[0].from_socket
            if linked_output.rna_type.name in nodeList:
                items = linked_output.object_items.items
                keys = uniqueKeys(items, sort=True, remove = ["id"])
                for key in keys:
                    newProp = (key, key, "")
                    attributes.append(newProp)
    return(attributes)
    
    
# to get the available attributes (keys) from the linked
# attribute list
def getAvailableAttributes(node, **kwargs):
    params = {
        'nodeType': None,
        'inputId' : None,
    }
    
    params.update(kwargs)
    
    nodeType = params['nodeType']
    inputId = params['inputId']

    if nodeType == "Group by":
        inputId = 0

    if nodeType in ['Group by', 'Math']:
        attributes = readAttributeFromLinkedNode(node, inputId)
        return attributes
    elif nodeType in ['Data']:
        if node.outputs[0].is_linked and node.outputs[0].links:
            if node.outputs[0].links[0].from_node.inputs:
                linkedNode = node.outputs[0].links[0].to_node
                attributes = readAttributeFromLinkedNode(linkedNode, 0)
                return attributes
    else: 
        return

# Function to add item to object_items
def RoMa_attribute_addItem(nodeFingerPrint, socketIdentifier, inputOutput):
    node = readNodeFingerPrint(nodeFingerPrint)
    if inputOutput == "both":
        sockets = ['input', 'output']
    elif inputOutput == "input":
        sockets = ['input']
    else:
        sockets = ['output']
        
    for socket in sockets:
        if socket == "input":
            collection = node.inputs[socketIdentifier].object_items
        else:
            collection = node.outputs[socketIdentifier].object_items
        item = collection.items.add()
        item.name = f"Item {len(collection.items)-1}"
        collection.active_index = len(collection.items) - 1
        
    return {'FINISHED'}

# Function to remove items from object_items
def RoMa_attribute_removeItem(nodeFingerPrint, socketIdentifier ,inputOutput):
    if inputOutput == "both":
        sockets = ['input', 'output']
    elif inputOutput == "input":
        sockets = ['input']
    else:
        sockets = ['output']
        
    node = readNodeFingerPrint(nodeFingerPrint)
    for socket in sockets:
        if socket == "input":
            collection = node.inputs[socketIdentifier].object_items
        else:
            collection = node.outputs[socketIdentifier].object_items
        
        collectionSize = len(collection.items)
        while collectionSize > 0:
            collectionSize -= 1
            # if collection.items[collectionSize]:
            try:
                collection.items.remove(collectionSize)
            except AttributeError as e:
                print(F"Error in Roma_attribute_removeItem {e}")
                # this is to handle the sockets that have both default_value
                # and item
                pass                
                
            # collection.active_index = collectionSize    
        #     collection.items.remove(collection.active_index)
        #     collection.active_index = min(max(0, collection.active_index - 1), len(collection.items) - 1)
            
        
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
        'socketIdentifier' : None
    }
    
    params.update(kwargs)
    
    node = readNodeFingerPrint(params['node'])
    item_index = params['item_index']
    key = params['key']
    valueType = params['valueType']
    stringValue = params['stringValue']
    floatValue = params['floatValue']
    inputOutput = params['inputOutput']
    socketIdentifier = params['socketIdentifier']
    
    if inputOutput == "both":
        sockets = ['input', 'output']
    elif inputOutput == "input":
        sockets = ['input']
    else:
        sockets = ['output']
    
    for socket in sockets:
        if socket == "input":
            collection = node.inputs[socketIdentifier].object_items
        else:
            collection = node.outputs[socketIdentifier].object_items
    
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

# Function to rearrange elements in a list
def rearrangeElements(node, keyName, newPosition):
    items = node.outputs[0].object_items.items
    for item in items:
        for i, key in enumerate(item['key_value_items']):
            if key['name'] == keyName:
                startingPosition = i
                break
        if startingPosition != newPosition:
            neighbor = startingPosition + (-1 if startingPosition > newPosition else 1)
            item.key_value_items.move(neighbor, startingPosition)
            
    return {'FINISHED'}

# Function to remove a key-value item from an element of the collection
# def RoMa_attribute_removeKeyValueItem(self, **kwargs):
#     params = {
#         'node': None,
#         'item_index': None,
#         'key_value_index': None,
#         'inputOutput' : None,
#         'socketIdentifier' : None
#     }
    
#     params.update(kwargs)
    
#     node = readNodeFingerPrint(params['node'])
#     item_index = params['item_index']
#     key_value_index = params['key_value_index']
#     inputOutput = params['inputOutput']
#     socketIdentifier = params['socketIdentifier']

#     if inputOutput == "both":
#         sockets = ['input', 'output']
#     elif inputOutput == "input":
#         sockets = ['input']
#     else:
#         sockets = ['output']
    
#     for socket in sockets:
#         if socket == "input":
#             collection = node.inputs[socketIdentifier].object_items
#         else:
#             collection = node.outputs[socketIdentifier].object_items

#         item = collection.items[item_index]
#         if key_value_index >= 0 and key_value_index < len(item.key_value_items):
#             item.key_value_items.remove(self.key_value_index)
#     return {'FINISHED'}

# a function to copy attributes between sockets
def copyAttributesToSocket(object_items, nodeFingerPrint, socketIdentifier, inputOutput):
    node = readNodeFingerPrint(nodeFingerPrint)
    if inputOutput == "both":
        sockets = ['input', 'output']
    elif inputOutput == "input":
        sockets = ['input']
    else:
        sockets = ['output']
            
    for attr in object_items:
        RoMa_attribute_addItem(nodeFingerPrint, socketIdentifier, inputOutput)
        for socket in sockets:
            if socket == "input":
                attributeIndex = node.inputs[socketIdentifier].object_items.active_index
            else:
                attributeIndex = node.outputs[socketIdentifier].object_items.active_index
        
            for key in attr['key_value_items']:
                if key['value_type'] == "FLOAT":
                    RoMa_attribute_addKeyValueItem( node=nodeFingerPrint,
                                                    item_index=attributeIndex,
                                                    key=key['name'],
                                                    valueType=key['value_type'],
                                                    floatValue=key['value_float'],
                                                    inputOutput=socket,
                                                    socketIdentifier=socketIdentifier
                                                    )
                else:
                    RoMa_attribute_addKeyValueItem(node=nodeFingerPrint,
                                                    item_index=attributeIndex,
                                                    key=key['name'],
                                                    valueType=key['value_type'],
                                                    stringValue=key['value_string'],
                                                    inputOutput=socket,
                                                    socketIdentifier=socketIdentifier
                                                    )
                    
# a function to copy and merge attributes between sockets             
def copyAndMergeAttributeToSocket(object_items, nodeFingerPrint, socketIdentifier, inputOutput):
    node = readNodeFingerPrint(nodeFingerPrint)
    if inputOutput == "both":
        sockets = ['input', 'output']
    elif inputOutput == "input":
        sockets = ['input']
    else:
        sockets = ['output']
            
    node = readNodeFingerPrint(nodeFingerPrint)
    
    for attr in object_items:
        # RoMa_attribute_addItem(nodeFingerPrint, socketIdentifier, inputOutput)
        for socket in sockets:
            if socket == "input":
                attributeIndex = node.inputs[socketIdentifier].object_items.active_index
                if len(node.inputs[socketIdentifier].object_items.items) == 0:
                    newData = True
                else:
                    newData = False
            else:
                attributeIndex = node.outputs[socketIdentifier].object_items.active_index
                if len(node.outputs[socketIdentifier].object_items.items) == 0:
                    newData = True
                else:
                    newData = False
            
            # In case the socket is empty, the first batch of data is copied
            # else data is merged
            if newData:
                copyAttributesToSocket(object_items, nodeFingerPrint, socketIdentifier, inputOutput)
                return()
            else:
                object_items = node.outputs[0].object_items.items
                for keys in attr['key_value_items']:
                    if keys['name'] == 'id':
                        id = keys['value_string']
                    else:
                        keyName = keys['name']
                        valueType = keys['value_type']
                        if valueType == "FLOAT":
                            value = keys['value_float']
                        else:
                            value = keys['value_string']
                        
                for attributeIndex, attr in enumerate(object_items):
                    for keys in attr['key_value_items']:
                        if keys['name'] == 'id' and keys['value_string'] == id:
                            if valueType == "FLOAT":
                                RoMa_attribute_addKeyValueItem(node=nodeFingerPrint,
                                                            item_index=attributeIndex,
                                                            key=keyName,
                                                            valueType="FLOAT",
                                                            floatValue=value,
                                                            socketIdentifier=socketIdentifier
                                                            )
                            else:
                                RoMa_attribute_addKeyValueItem(node=nodeFingerPrint,
                                                            item_index=attributeIndex,
                                                            key=keyName,
                                                            valueType="STRING",
                                                            stringValue=value,
                                                            socketIdentifier=socketIdentifier
                                                            )
                            break
    return()
                            
               
################################################################################################################
################# Class  to retrieve data for schedules  #######################################################
################################################################################################################

# collect the data from the source node and return all
# the elements necessary to draw the column or the row    
class dataForGraphic:
    def __init__(self, sourceNode, posX=0, posY=0, cellWidth=3, cellHeight=2, scale=1):
        self.sourceNode = sourceNode
        self.posX = posX
        self.posY = posY
        self.cellWidth = cellWidth
        self.cellHeight = cellHeight
        self.scale = scale

        self.node = readNodeFingerPrint(self.sourceNode)
        self.object_items = self.node.inputs['Schedule'].links[0].from_socket.object_items.items
    
    # Reading data from the input node and store as new list of dictionaries
    def collect_data(self):
        data = []
        item = self.object_items[0]
        tmp = {'id': 'id'}
        for key in item['key_value_items']:
            tmp[key['name']] = key['name']
        data.append(tmp)

        # Append data to the list
        for item in self.object_items:
            tmp = {'id': item.name}
            for key in item['key_value_items']:
                if key['value_type'] == "STRING":
                    tmp[key['name']] = key['value_string']
                else:
                    tmp[key['name']] = str(key['value_float'])
            data.append(tmp)
        return(data)
        
    def define_vertices(self, keyIndex, itemIndex, numberOfItems):
        tmpVerts = []
        horizontalIncrement = self.cellWidth * keyIndex
        verticalIncrement = -1 * self.cellHeight * itemIndex

        x = (horizontalIncrement + self.posX) * self.scale
        y = (verticalIncrement + self.posY) * self.scale
        z = 0
        tmpVerts.append((x, y, z))

        if itemIndex == numberOfItems - 1:
            verticalIncrement = -1 * self.cellHeight * (itemIndex + 1)
            x = (horizontalIncrement + self.posX) * self.scale
            y = (verticalIncrement + self.posY) * self.scale
            z = 0
            tmpVerts.append((x, y, z))
        return tmpVerts
            
    def generate_graphics(self, data):
        verts = []
        edges = []
        faces = []
        numberOfKeys = len(data[0])
        numberOfItems = len(data)

        for keyIndex in range(numberOfKeys):
            for itemIndex in range(numberOfItems):
                verts.extend(self.define_vertices(keyIndex, itemIndex, numberOfItems))

                if itemIndex <= numberOfItems + 1:
                    A = itemIndex + ((numberOfItems + 1) * keyIndex)
                    B = A + numberOfItems + 1
                    # C = B + 1
                    D = A + 1

                    edges.append((A, B))
                    edges.append((A, D))

            A = itemIndex + ((numberOfItems + 1) * keyIndex) + 1
            B = A + numberOfItems + 1
            edges.append((A, B))

        # extra set of vertices to be added at the end
        for itemIndex in range(numberOfItems):
            verts.extend(self.define_vertices(numberOfKeys, itemIndex, numberOfItems))

            A = itemIndex + ((numberOfItems + 1) * numberOfKeys)
            D = A + 1
            edges.append((A, D))
            
        return verts, edges, faces

    def data_for_graphic(self):
        data = self.collect_data()
        verts, edges, faces = self.generate_graphics(data)
        return data, verts, edges, faces
            
#############################################################################
########## Classes to  manage attribute collection  #########################
#############################################################################                

# Class to store the name of RoMa objects
# This class is used to define the list in 
# RoMa_stringCollection_Socket and in the keys
class RoMa_string_item(PropertyGroup):
    name: StringProperty(name="Name")


# Define a key-value pair used in RoMa_attribute_collectionItem
class RoMa_keyValueItem(PropertyGroup):
    # key: bpy.props.StringProperty(name="Key", description="Element's key")
    value_string: bpy.props.StringProperty(name="String value", description="String value", default="")
    value_float: bpy.props.FloatProperty(name="Float value", description="Float value", default=-1)
    value_type: bpy.props.StringProperty( name="Value Type", description="Type value", default='FLOAT')


# Define the element of the collection RoMa_attribute_propertyGroup
class RoMa_attribute_collectionItem(PropertyGroup):
    key_value_items: bpy.props.CollectionProperty(type=RoMa_keyValueItem)

    
# Class to store the attributes of RoMa objects
class RoMa_attribute_propertyGroup(PropertyGroup):
    items: bpy.props.CollectionProperty(type=RoMa_attribute_collectionItem)
    active_index: bpy.props.IntProperty(default=0)
    
# Define the elements of the data RoMa_attribute_propertyGroup
# It contains name and a collection of items (the row values in the schedule)
# and the operation for the footer
class RoMa_data_collectionItem(PropertyGroup):
    key_name : bpy.props.StringProperty(name="Key name")
    key_value_items: bpy.props.CollectionProperty(type=RoMa_keyValueItem)
    key_footer_operation : bpy.props.StringProperty(name="Key footer operation")

# Class to store the data of RoMa objects
# Data is used to define schedules
class RoMa_data_propertyGroup(PropertyGroup):
    items: bpy.props.CollectionProperty(type=RoMa_data_collectionItem)
    active_index: bpy.props.IntProperty(default=0)


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
    bl_label = "RoMa Mesh"
    
    
    object_items: CollectionProperty(type=RoMa_string_item)
   
    def draw(self, context, layout, node, text):
        layout.label(text=self.identifier)

    @classmethod
    def draw_color_simple(cls):
        return (0, 0.84, 0.64, 1)
    
# RoMa custom socket type
# used in the math node
class RoMa_attributesCollectionAndFloat_Socket(NodeSocket):
    """RoMa node socket attribute collection and float type"""
    bl_idname = 'RoMa_attributeCollectionAndFloat_SocketType'
    bl_label = "Attribute"
    
    object_items: PointerProperty(type=RoMa_attribute_propertyGroup)
    default_value : FloatProperty(default=1.0) 
   
    def draw(self, context, layout, node, text):
        if self.is_output:
            layout.label(text=self.identifier)
        else:
            if self.is_linked or self.hide_value:
                layout.label(text=self.identifier)
            else:
                layout.prop(self,"default_value",text=self.identifier)
  
    @classmethod
    def draw_color_simple(cls):
        return (0.63, 0.63, 0.63, 1)

    
# RoMa custom socket type
# used to collect attributes
class RoMa_attributesCollection_Socket(NodeSocket):
    """RoMa node socket attribute collection type"""
    bl_idname = 'RoMa_attributeCollection_SocketType'
    bl_label = "Attribute"
    
    object_items: PointerProperty(type=RoMa_attribute_propertyGroup)
   
    def draw(self, context, layout, node, text):
        layout.label(text=self.identifier)
  
    @classmethod
    def draw_color_simple(cls):
        return (0.63, 0.63, 0.63, 1)
    
# RoMa custom socket type
# used to manage data
class RoMa_dataCollection_Socket(NodeSocket):
    """RoMa node socket data collection type"""
    bl_idname = 'RoMa_dataCollection_SocketType'
    bl_label = "Data"
    
    object_items: PointerProperty(type=RoMa_data_propertyGroup)
   
    def draw(self, context, layout, node, text):
        layout.label(text=self.identifier)
  
    @classmethod
    def draw_color_simple(cls):
        return (1.0, 0.67, 0.0, 1.0)
    
# RoMa custom socket type
# used to set operation data
# class RoMa_dataOperation_Socket(NodeSocket):
#     """RoMa node socket to operate data"""
#     bl_idname = 'RoMa_dataOperation_SocketType'
#     bl_label = "Data Operation"
    
#     object_items: PointerProperty(type=RoMa_attribute_propertyGroup)
#     default_value : FloatProperty(default=1.0) 
   
#     def draw(self, context, layout, node, text):
#         layout.label(text=self.identifier)
  
#     @classmethod
#     def draw_color_simple(cls):
#         return (0.99, 0.96, 0.54, 1.0)
    
# Customizable interface properties to generate a socket from.
# class RoMaInterfaceSocket(NodeTreeInterfaceSocket):
#     # The type of socket that is generated.
#     bl_socket_idname = 'RoMaSocketType'

#     default_value: FloatProperty(default=1.0, description="Default input value for new sockets",)

#     def draw(self, context, layout):
#         # Display properties of the interface.
#         layout.prop(self, "default_value")

#     # Set properties of newly created sockets
#     def init_socket(self, node, socket, data_path):
#         socket.input_value = self.default_value

#     # Use an existing socket to initialize the group interface
#     def from_socket(self, node, socket):
#         # Current value of the socket becomes the default
#         self.default_value = socket.input_value



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

class RoMaGroupInputNode(RoMaTreeNode, Node):
    '''Input node containing all the RoMa meshes existing in the scene'''
    bl_idname = 'Input RoMa Mesh'
    bl_label = 'Group Input - All'

    def init(self, context):
        self.outputs.new('RoMa_stringCollection_SocketType', name='RoMa Mesh', identifier='RoMa Mesh')
    
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
            # print(f"RoMa meshes collected {len(self.outputs['RoMa Mesh'].object_items)}")

    def update(self):
        self.update_selected_objects()
        
    def execute(self):
        self.update_selected_objects()
        

    
class RoMaSelectedInputNode(RoMaTreeNode, Node):
    '''Input node containing the selected RoMa meshes'''
    bl_idname = 'Input RoMa Selected Mesh'
    bl_label = 'Group Input - Selected'
   
    def init(self, context):
        self.outputs.new('RoMa_stringCollection_SocketType', name='RoMa Mesh', identifier='RoMa Mesh')
    
    def update_selected_objects(self):
        if self.outputs['RoMa Mesh'].is_linked:
            cleanOutputs(self)

            objs = bpy.context.selected_objects
            romaObjs = [obj for obj in objs if obj is not None and obj.type == "MESH" and "RoMa object" in obj.data]
            for obj in romaObjs:
                item = self.outputs['RoMa Mesh'].object_items.add()
                item.name = obj.name
            # print(f"RoMa meshes collected {len(self.outputs['RoMa Mesh'].object_items)}")

    def update(self):
        self.update_selected_objects()  
      
    def execute(self):
        self.update_selected_objects()

    
class RoMaAllAttributesNode(RoMaTreeNode, Node):
    '''RoMa All Available Attributes'''
    bl_idname = 'RoMa All Attributes'
    bl_label = 'All Attributes'
    # bl_description = 'Attribute'
    
    objNames : CollectionProperty(type=RoMa_string_item)
    
    def init(self, context):
        self.outputs.new('RoMa_attributeCollection_SocketType', name='Attribute', identifier = 'All Attributes')
        self.outputs['All Attributes'].display_shape = 'DIAMOND_DOT'
        
    def manualExecute(self):
        # print(f"eseguo manualmente all attributes")
        cleanSocket(self, 'All Attributes', 'output')

        nodeFingerPrint = writeNodeFingerPrint(self)
        attributes = getAttributes(self.objNames, "all")
        if attributes:
            for attr in attributes:
                # add a new entry to allocate parameters
                RoMa_attribute_addItem(nodeFingerPrint, "All Attributes", "output")
                
                attributeIndex = self.outputs['All Attributes'].object_items.active_index
                # add keys to the entry
                for key, value in attr.items():
                    try:
                        float(value)
                        RoMa_attribute_addKeyValueItem( node=nodeFingerPrint,
                                                                item_index=attributeIndex,
                                                                key=key,
                                                                valueType="FLOAT",
                                                                floatValue=value,
                                                                socketIdentifier='All Attributes'
                                                                )
                    except ValueError:
                        RoMa_attribute_addKeyValueItem( node=nodeFingerPrint,
                                                                item_index=attributeIndex,
                                                                key=key,
                                                                valueType="STRING",
                                                                stringValue=value,
                                                                socketIdentifier='All Attributes'
                                                                )

            # print("-------------------------------")
            # print(f"stampo gli attributi ottenuti nel nodo {self.name}")
            # items = self.outputs['Attribute'].object_items.items
            # for item in items:
            #     print(f"Item name {item.name} has {len(item['key_value_items'])} attributes")
            #     for key in item['key_value_items']:
            #         if key['value_type'] == "STRING":
            #             print(f"key {key['name']} has value {key['value_string']} ")
            #         else:
            #             print(f"key {key['name']} has value {key['value_float']}")

            
    
    def execute(self):
        pass

         
    
class RoMaAreaAttributeNode(RoMaTreeNode, Node):
    '''RoMa Area Attribute'''
    bl_idname = 'RoMa Area Attribute'
    bl_label = 'Area'
    # bl_description = 'Attribute'
    
    objNames : CollectionProperty(type=RoMa_string_item)
    
    def init(self, context):
        self.outputs.new('RoMa_attributeCollection_SocketType', name='Attribute', identifier="Area")
        self.outputs['Area'].display_shape = 'DIAMOND_DOT'

    def manualExecute(self):
        cleanSocket(self, 'Area', 'output')

        nodeFingerPrint = writeNodeFingerPrint(self)
        attributes = getAttributes(self.objNames, "area")
        if attributes:
            for attr in attributes:
                # add a new entry to allocate parameters
                RoMa_attribute_addItem(nodeFingerPrint, "Area", "output")
                attributeIndex = self.outputs['Area'].object_items.active_index
                # add keys to the entry
                for key, value in attr.items():
                    try:
                        float(value)
                        RoMa_attribute_addKeyValueItem( node=nodeFingerPrint,
                                                                item_index=attributeIndex,
                                                                key=key,
                                                                valueType="FLOAT",
                                                                floatValue=value,
                                                                socketIdentifier='Area'
                                                                )
                    except ValueError:
                        RoMa_attribute_addKeyValueItem( node=nodeFingerPrint,
                                                                item_index=attributeIndex,
                                                                key=key,
                                                                valueType="STRING",
                                                                stringValue=value,
                                                                socketIdentifier='Area'
                                                                )
    def execute(self):
        pass

            
class RoMaUseAttributeNode(RoMaTreeNode, Node):
    '''RoMa Use Attribute'''
    bl_idname = 'RoMa Use Attribute'
    bl_label = 'Use'
    # bl_description = 'Attribute'
    
    objNames : CollectionProperty(type=RoMa_string_item)
    
    def init(self, context):
        self.outputs.new('RoMa_attributeCollection_SocketType', name='Attribute', identifier="Use")
        self.outputs['Use'].display_shape = 'DIAMOND_DOT'

    def manualExecute(self):
        cleanSocket(self, 'Use', 'output')

        nodeFingerPrint = writeNodeFingerPrint(self)
        attributes = getAttributes(self.objNames, "use")
        if attributes:
            for attr in attributes:
                # add a new entry to allocate parameters
                RoMa_attribute_addItem(nodeFingerPrint, "Use", "output")
                attributeIndex = self.outputs['Use'].object_items.active_index
                # add keys to the entry
                for key, value in attr.items():
                    try:
                        float(value)
                        RoMa_attribute_addKeyValueItem( node=nodeFingerPrint,
                                                                item_index=attributeIndex,
                                                                key=key,
                                                                valueType="FLOAT",
                                                                floatValue=value,
                                                                socketIdentifier='Use'
                                                                )
                    except ValueError:
                        RoMa_attribute_addKeyValueItem( node=nodeFingerPrint,
                                                                item_index=attributeIndex,
                                                                key=key,
                                                                valueType="STRING",
                                                                stringValue=value,
                                                                socketIdentifier='Use'
                                                                )
    def execute(self):
        pass
                     
class RomaDataMathFunction(RoMaTreeNode, Node):
    '''Define the operation to be done with the data, both in every data entry and with the footer'''
    bl_idname = "RoMa Table Function"
    bl_label = "Table Function"
    
     # EnumProperty for dropdown box math
    dropdown: EnumProperty(
        items=(
            ("Sum", "Sum", ""),
            ("Average", "Average", "A"),
            ("Min", "Min", ""),
            ("Max", "Max", ""),
            ("Count", "Count", ""),
            ("Compare", "Compare", ""),
        ),
        name="Table Functions",
        default="Sum",
        update=lambda self, context: self.update_socket_visibility()
    )
    
    def init(self, context):
        # self.outputs.new('RoMa_dataOperation_SocketType', name='Function', identifier='Function')
        self.outputs.new('RoMa_attributeCollection_SocketType', name='Function', identifier='Function')
        
    def draw_buttons(self, context, layout):
        layout.prop(self, "dropdown", text="")
    
    def cleanSocket(self):
        cleanSocket(self, 'Function', 'output')
        # print(f"pulisco")
        items = self.outputs[0].object_items.items
        # print(len(items))
         
        
    def manualExecute(self, combo_key, items, keyName, filterKeys):
        result = 0
        operation = self.dropdown
       
        for item in items:
            if operation == "Sum":
                result = result + item[f"{keyName}"]
        
        # set up the ID
        keys = []
        for key, value in combo_key.items():
            keys.append(key)
            if value.is_integer():
                value = int(value)
            keys.append(str(value))
        # keys = combo_key.keys()
        id = "_".join(keys)
        # id = "keys_" + id
        
        nodeFingerPrint = writeNodeFingerPrint(self)
        RoMa_attribute_addItem(nodeFingerPrint, "Function", "output")
        attributeIndex = self.outputs['Function'].object_items.active_index
        # add the id to the attributes
        RoMa_attribute_addKeyValueItem( node=nodeFingerPrint,
                                        item_index=attributeIndex,
                                        key='id',
                                        valueType="STRING",
                                        stringValue=id,
                                        socketIdentifier='Function'
                                        )
        # add the keys to the attributes
        for kName, value in combo_key.items():
            try:
                float(value)
                RoMa_attribute_addKeyValueItem( node=nodeFingerPrint,
                                        item_index=attributeIndex,
                                        key=kName,
                                        valueType="FLOAT",
                                        floatValue=value,
                                        socketIdentifier='Function'
                                        )
            except ValueError:
                RoMa_attribute_addKeyValueItem( node=nodeFingerPrint,
                                        item_index=attributeIndex,
                                        key=kName,
                                        valueType="STRING",
                                        floatValue=value,
                                        socketIdentifier='Function'
                                        )
                
            
        
        # add result to the attributes
        RoMa_attribute_addKeyValueItem( node=nodeFingerPrint,
                                        item_index=attributeIndex,
                                        key=keyName,
                                        valueType="FLOAT",
                                        floatValue=result,
                                        socketIdentifier='Function'
                                        )
        
        # Key filters need to have the same order as in the UI List
        # index 0 is id, so we need to start changing from 1
        
        node = readNodeFingerPrint(nodeFingerPrint)
        for i, keyName in enumerate(filterKeys):
            newPosition = i + 1
            rearrangeElements(node, keyName, newPosition)
            
            
            
            

        
        
            
        
        # print(f"risultato = {result}")


        # items = self.outputs[0].object_items.items
        # print("--------------------------------------##########################")
        # for item in items:
        #     # print(item.name)
        #     print(f"Item name {item.name} is {(item['key_value_items'])}")
        #     i = "miao"
        #     for key in item['key_value_items']:
        #         if key['value_type'] == "STRING":
        #             print(f"{i} key {key['name']} has value {key['value_string']} ")
        #         else:
        #             print(f"{i} key {key['name']} has value {key['value_float']}")
        
   
    
    
class RoMaDataNode(RoMaTreeNode, Node):
    '''Define the column data to be shown in the schedule'''
    bl_idname = 'RoMa Table Data'
    bl_label = "Table Data"
    
    dropdown : EnumProperty(
        items=lambda self, context : getAvailableAttributes(self, nodeType="Data"),
        description="Attribute to use as filter")
    
    def init(self, context):
        self.inputs.new('RoMa_attributeCollection_SocketType', name='Row', identifier='Row')
        self.inputs.new('RoMa_attributeCollection_SocketType', name='Footer', identifier='Footer')
        # self.inputs['Attribute'].hide_value = True
        
        self.outputs.new('RoMa_dataCollection_SocketType', name='Data', identifier='Data')
        
    def draw_buttons(self, context, layout):
        layout.prop(self, "dropdown", text="Key")
        
    
class RoMaCaptureAttributeNode(RoMaTreeNode, Node):
    '''Read RoMa attributes'''
    bl_idname = 'Capture RoMa Attribute'
    bl_label = "Capture attribute"
    
    # inputList = ["RoMa Mesh", 'Attribute']
    # outputList = ['Attribute']
    
    # validated = True
    executionOrder = []
    
    def init(self, context):
        self.inputs.new('RoMa_stringCollection_SocketType', name='RoMa Mesh', identifier='RoMa Mesh')
        self.inputs.new('RoMa_attributeCollection_SocketType', name='Attribute', identifier='Attribute')
        self.inputs['Attribute'].display_shape = 'DIAMOND_DOT'
        self.inputs['Attribute'].hide_value = True
        
        # self.outputs.new('RoMa_stringCollection_SocketType', 'RoMa Mesh')
        self.outputs.new('RoMa_attributeCollection_SocketType', name='Attribute', identifier='Attribute')
        self.outputs['Attribute'].display_shape = 'DIAMOND_DOT'
                                                                       
        # addKeysToNode(self, inputs=self.inputList, outputs=self.outputList)
        
    def copy(self, node):
        # addKeysToNode(self, inputs=self.inputList, outputs=self.outputList)
        cleanInputs(self)
        cleanOutputs(self)
        # self.validated = True
        
    def free(self):
        # removeKeyFromNode(self, inputs=self.inputList, outputs=self.outputList)
        pass
        
                
    # def update(self):
    #     self.validated = checkLink(self)
    #     clearInputs(self)
    def update(self):
        # print("capture attribute eseguo dopo update")
        if checkLink(self):
            if self.inputs['RoMa Mesh'].is_linked:
                self.readWrite_RoMa_mesh()
                if self.inputs['Attribute'].is_linked and self.outputs['Attribute'].is_linked:
                    self.readWrite_Attribute()
            else:
                cleanSocket(self, 'RoMa Mesh', 'input')
            
            if self.inputs['Attribute'] and self.inputs['Attribute'].is_linked == False:
                cleanSocket(self, 'Attribute' , 'both')
                

    def readWrite_RoMa_mesh(self):
        cleanSocket(self, 'RoMa Mesh', 'input')
        object_items = self.inputs['RoMa Mesh'].links[0].from_socket.object_items
        for obj in object_items:
            itemIn = self.inputs['RoMa Mesh'].object_items.add()
            # itemOut = self.outputs['RoMa Mesh'].object_items.add()
            itemIn.name = obj.name
            # itemOut.name = obj.name
            
        # ob = self.inputs['RoMa Mesh'].object_items
        # # print(f"oggetti linkati : {len(ob)}")
        # for o in ob: print(f"{o.name}")
        
    def readWrite_Attribute(self):
        cleanSocket(self, 'Attribute', 'both')
        child = self.inputs['Attribute'].links[0].from_node
        nodeData = {    "node" : child,
                        "depth": 0
                    }
        try:
            self.executionOrder[0]
        except IndexError:
            self.executionOrder.append([])
        self.executionOrder[0] = [nodeData]
        # all the children nodes are searched and found, sorted 
        # from the deepest, and the run in that order
        # print(f"inizio a camminare al contrario")
        walkBackwards(self, 0, child, depth = 0)
        sortedOrder = sorted(self.executionOrder[0], key=lambda x: x['depth'], reverse=True)
        for el in sortedOrder:
            if hasattr(el['node'], "manualExecute"):
                # print(f"Capture attribute esegue: {el}")
                el['node'].manualExecute()
        # print(f"copio gli attributi in output di capture attribute")                
        object_items = self.inputs['Attribute'].links[0].from_socket.object_items.items
        
        nodeFingerPrint = writeNodeFingerPrint(self)
        copyAttributesToSocket(object_items, nodeFingerPrint, 'Attribute', "output")
            
        # print(f"gli attributi copiati in capture attribute sono:-------------------------------------")
        # items = self.outputs['Attribute'].object_items.items
        # for item in items:
        #     print()
        #     print(f"Item name {item.name} has {len(item['key_value_items'])} attributes")
        #     for key in item['key_value_items']:
        #         if key['value_type'] == "STRING":
        #             print(f"key {key['name']} has value {key['value_string']} ")
        #         else:
        #             print(f"key {key['name']} has value {key['value_float']}")
             
        
        
        
    def execute(self):
        # print(f"capture attribute eseguo automatico")
        if checkLink(self):
            if self.inputs['RoMa Mesh'].is_linked:
                self.readWrite_RoMa_mesh()
                if self.inputs['Attribute'].is_linked and self.outputs['Attribute'].is_linked:
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



class RoMa_key_name_list(PropertyGroup):
    id: IntProperty(
           name="Id",
           default = 0)
    
    name: StringProperty(
           name="Name",
           default="")
        #    update=update_roma_filter_by_typology)
        
class RoMaGetUniqueNode(RoMaTreeNode, Node):
    '''Get the list of unique values of a given key '''
    bl_idname = 'RoMa Unique Values'
    bl_label = "Unique values"     
  
    
    dropdown : EnumProperty(
        items=lambda self, context : getAvailableAttributes(self, nodeType="Group by"),
        description="Attribute to use as filter"
    )
    
    # key_list : CollectionProperty(type=RoMa_key_name_list)
        
    # key_list_index : IntProperty(name = "Key list index",
    #                             default = 0)
    # executionOrder = []
    
    def init(self, context):
        self.inputs.new('RoMa_attributeCollectionAndFloat_SocketType', name = 'Attribute', identifier='Attribute')
        # self.inputs.new('RoMa_dataCollection_SocketType', name='Data', identifier='Data', use_multi_input=True)
        self.inputs['Attribute'].display_shape = 'DIAMOND_DOT'
        self.inputs['Attribute'].hide_value = True
        
        self.outputs.new('RoMa_attributeCollectionAndFloat_SocketType', name = 'Attribute', identifier='Attribute')
        self.outputs['Attribute'].display_shape = 'DIAMOND_DOT'
        
    def copy(self, node):
        # addKeysToNode(self, inputs=self.inputList, outputs=self.outputList)
        cleanInputs(self)
        cleanOutputs(self)
        # self.validated = True
        
    def free(self):
        # removeKeyFromNode(self, inputs=self.inputList, outputs=self.outputList)
        pass
        
    def draw_buttons(self, context, layout):
        layout.prop(self, "dropdown", text="Key")
        
    def manualExecute(self):
        cleanSocket(self, 'Attribute', 'output')
        object_items = self.inputs['Attribute'].links[0].from_socket.object_items.items
        uniqueList = uniqueValues(object_items, key=self.dropdown )
        addItemsToList(uniqueList, self, 'Attribute')
        # nodeFingerPrint = writeNodeFingerPrint(self)
        # for unique in uniqueList:
        #     RoMa_attribute_addItem(nodeFingerPrint,"Attribute", "output")
        #     attributeIndex = self.outputs['Attribute'].object_items.active_index
        #     for key, value in unique.items():
        #         try:
        #             float(value)
        #             RoMa_attribute_addKeyValueItem( node=nodeFingerPrint,
        #                                             item_index=attributeIndex,
        #                                             key=key,
        #                                             valueType="FLOAT",
        #                                             floatValue=value,
        #                                             socketIdentifier='Attribute'
        #                                             )
        #         except ValueError:
        #             RoMa_attribute_addKeyValueItem( node=nodeFingerPrint,
        #                                             item_index=attributeIndex,
        #                                             key=key,
        #                                             valueType="STRING",
        #                                             stringValue=value,
        #                                             socketIdentifier='Attribute'
        #                                             )
        
    
    def update(self):
        self.manualExecute()
        
    def execute(self):
        self.manualExecute()
        
        


    
    
class RoMaTableNode(RoMaTreeNode, Node):
    '''Group attributes in a table following on a selected criterion '''
    bl_idname = 'Table by RoMa Attribute'
    bl_label = "Table Group By"     
  
    
    dropdown : EnumProperty(
        items=lambda self, context : getAvailableAttributes(self, nodeType="Group by"),
        description="Attribute to use as filter",
        update=lambda self, context: self.updateKeyName()
    )
    
    key_list : CollectionProperty(type=RoMa_key_name_list)
        
    key_list_index : IntProperty(name = "Key list index",
                                default = 0)
    executionOrder = []
    
    def init(self, context):
        self.inputs.new('RoMa_attributeCollection_SocketType', name = 'Attribute', identifier='Attribute')
        self.inputs.new('RoMa_dataCollection_SocketType', name='Data', identifier='Data', use_multi_input=True)
        self.inputs['Attribute'].display_shape = 'DIAMOND_DOT'
        self.inputs['Attribute'].hide_value = True
        
        self.outputs.new('RoMa_attributeCollection_SocketType', name = 'Attribute', identifier='Table')
        # self.outputs['Value'].display_shape = 'DIAMOND_DOT'
        
    def copy(self, node):
        # addKeysToNode(self, inputs=self.inputList, outputs=self.outputList)
        cleanInputs(self)
        cleanOutputs(self)
        # self.validated = True
        
    def free(self):
        # removeKeyFromNode(self, inputs=self.inputList, outputs=self.outputList)
        pass
        
    def draw_buttons(self, context, layout):
        # scene = context.scene
        row = layout.row()
        row.label(text="Group by:")
        row = layout.row()
        rows = 3
        
        node_id = writeNodeFingerPrint(self)
        row.template_list("NODE_UL_key_filter", node_id, self,
                        "key_list", self, "key_list_index", rows = rows)
        
        
        col = row.column(align=True)
        col.operator("roma_key.new_item", icon='ADD', text="").nodeFingerprint = writeNodeFingerPrint(self)
        sub = col.row()
        sub.operator("roma_key.delete_item", icon='REMOVE', text="").nodeFingerprint = writeNodeFingerPrint(self)
        if len(self.key_list) < 2:
            sub.enabled = False
        else:
            sub.enabled = True
        col.separator()
        op = col.operator("roma_key.move_item", icon='TRIA_UP', text="")
        op.direction = 'UP'
        op.nodeFingerprint = writeNodeFingerPrint(self)
        
        op=col.operator("roma_key.move_item", icon='TRIA_DOWN', text="")
        op.direction = 'DOWN'
        op.nodeFingerprint = writeNodeFingerPrint(self)
        
        layout.prop(self, "dropdown", text="Key")
        
    def update(self):
        pass
    
        # if self.inputs[0].is_linked and self.inputs[1].is_linked:
        #     dataLinks = self.inputs[1].links
        #     print(f"Links {len(dataLinks)}")
        #     dataColumn = []

        #     for linkId, link in enumerate(dataLinks):
        #         child = link.from_node
        #         nodeData = {    "node" : child,
        #             "depth": 0
        #         }
        #         self.executionOrder = [nodeData]
        #         walkBackwards(self, linkId, child, depth = 0)
                # sortedOrder = sorted(self.executionOrder, key=lambda x: x['depth'], reverse=True)
                # for el in sortedOrder:
                #     if hasattr(el['node'], "manualExecute"):
                #     # print(f"Capture attribute esegue: {el}")
                #     el['node'].manualExecute()

    # update the key name and id in the key list
    def updateKeyName(self):
        currentId = self.key_list_index
        selectedName = self.dropdown
        self.key_list[currentId].name = selectedName
        nodeFingerPrint = writeNodeFingerPrint(self)
        updateGroupByCombination(nodeFingerPrint)

                
# Update the combination used in the node Group by to determine
# the data in the created table
def updateGroupByCombination(nodeFingerPrint):
    node = readNodeFingerPrint(nodeFingerPrint)
    object_items = node.inputs['Attribute'].links[0].from_socket.object_items.items
    
    
    # get the keys selected in the linked table data nodes
    # and store the sort order of the linked nodes
    dataLinks = node.inputs['Data'].links
    keys_to_keep = []
    # executionOrder = [] 
    if len(dataLinks)>0:
        for linkId, link in enumerate(dataLinks):
            child = link.from_node
            # get the linked keys
            keyName = child.dropdown
            keys_to_keep.append(keyName)
            
            # walk backwards to store the execution order
            nodeData = {"node" : child,
                        "depth": 0
            }
            try:
                node.executionOrder[linkId]
            except IndexError:
                node.executionOrder.append([])
            node.executionOrder[linkId] = [nodeData]
            print(f"aggiunto {nodeData} a {linkId}")
            walkBackwards(node, linkId, child, depth = 0)
            sortedExecutionOrder = [sorted(sublist, key=lambda x: x['depth'], reverse=True) for sublist in node.executionOrder]

 
        
        
    
    # Get the unique values based on the keys added to the UIList
    # and after that calculte all the possible combinations
    listOfList = []
    for key in node.key_list: 
        tmpList = uniqueValues(object_items, key=key.name)
        listOfList.append(tmpList)
        keys_to_keep.append(key.name) # Add the key listed in the UIList to the list to keys to keep
    combinations = list(product(*listOfList))
    
    # Remove duplicates by converting to a set and then back to a list
    keys_to_keep = list(set(keys_to_keep))
    
    itemList = []
    for item in object_items:
        tmpItem = {}
        for key in item['key_value_items']:
            if key['value_type'] == "STRING":
                tmpItem[f"{key['name']}"] = key['value_string']
            else:
                tmpItem[f"{key['name']}"] = key['value_float']
        itemList.append(tmpItem)
   
    # Keep only specified keys in each dictionary in the list.
    
    # :param item_list: List of dictionaries to process.
    # :param keys_to_keep: List of keys to keep in each dictionary.
    # :return: Modified list of dictionaries with only specified keys.
    
    for item in itemList:
        # Create a new dictionary with only the keys specified in keys_to_keep
        filtered_item = {key: item[key] for key in keys_to_keep if key in item}
        # Update the item in the list with the filtered dictionary
        item.clear()  # Clear the original dictionary
        item.update(filtered_item)  # Update with the filtered dictionary

    # Instantiate the ItemGrouper class and use it
    # grouper = ItemGrouper(itemList, combinations)
    # grouper.group_by_combination()
    
    grouped_dict = defaultdict(list)
    
    #  Groups items by the combinations of keys specified.
    for item in itemList:
        for combo in combinations:
            # Merge the two dictionaries in the combination tuple
            combo_dicts = [dict(part) for part in combo]
            
            # Merges a list of dictionaries into a single dictionary.
            # :param dict_list: List of dictionaries to be merged.
            # :result: A single dictionary containing all key-value pairs from the input dictionaries.
            result = {}
            for d in combo_dicts:
                result.update(d)
            combo_dict = result
            
            # Create a hashable key for the combination dictionary
            combo_key = {}
            # Creates a hashable key from a dictionary by converting it to a frozenset.
            # :combo_dict: Dictionary to be converted to a hashable key.
            # :return: frozenset representing the hashable key.
            combo_key = frozenset(combo_dict.items())
            
            # Create a key for the item based on the combination
            # Creates a key from an item based on the given combination dictionary.
            # :param item: Dictionary representing an item.
            # :param combo_dict: Dictionary representing the combination to match.
            # :return: frozenset representing the key for the item based on the combination.
            item_key = frozenset((key, item[key]) for key in combo_dict if key in item)
            
            # Check if the item matches the combination and group it
            if item_key == frozenset(combo_dict.items()):
                grouped_dict[combo_key].append(item)
                break
    
    # dataToTable = []
    # for combo_key, items in grouped_dict.items():
    #     print()
    #     print(f"Combo = {dict(combo_key)}")
    #     keys = dict(combo_dict)
    #     for item in items:
    #         tmp = keys.copy()
    #         tmp.update(item)            
    #         print(f"        item {tmp}")
    #         dataToTable.append(tmp)
            
    # for d in dataToTable: print(d)
            
    # print("-------------")
    # for linkedNodes in sortedExecutionOrder:
    #     print(f"{linkedNodes}")
    
    # print("----------------------------------------")
    # print(node.key_list)
    filterKeys = []
    for k in node.key_list:
        filterKeys.append(k.name)
    cleanSocket(node, 'Table', 'output')
    
    for linkedNodes in sortedExecutionOrder:
        tableDataNode = linkedNodes[len(linkedNodes)-1]['node']
       
        key = tableDataNode.dropdown
        # all the child nodes are executed        
        for linkedNode in linkedNodes:
            node = linkedNode['node']
            if linkedNode['depth'] > 0:
                node.cleanSocket()
                for combo_key, items in grouped_dict.items():
                    node.manualExecute(dict(combo_key), items, key, filterKeys)
            # When depth = 0 it means a table data is passed 
            # In this case the data from the child of table data is copied in the 
            # node output socket
            else:
                if node.inputs[0].is_linked:
                    object_items = node.inputs[0].links[0].from_socket.object_items.items
                    copyAndMergeAttributeToSocket(object_items, nodeFingerPrint, 'Table', 'output')
                if node.inputs[1].is_linked:
                    object_items = node.inputs[1].links[0].from_socket.object_items.items
                    copyAndMergeAttributeToSocket(object_items, nodeFingerPrint, 'Table', 'output')
                    


    # print("--------------------------------------##########################")
    # node = readNodeFingerPrint(nodeFingerPrint)
    # items = node.outputs[0].object_items.items
    # for item in items:
    #     # print(item.name)
    #     print(f"Item name {item.name} is {(item['key_value_items'])}")
    #     for i, key in enumerate(item['key_value_items']):
    #         if key['value_type'] == "STRING":
    #             print(f"{i} key {key['name']} has value {key['value_string']} ")
    #         else:
    #             print(f"{i} key {key['name']} has value {key['value_float']}")

            
class NODE_UL_key_filter(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text= f"{item.name}") 

    def filter_items(self, context, data, propname):
        filtered = []
        ordered = []
        items = getattr(data, propname)
        filtered = [self.bitflag_filter_item] * len(items)
        return filtered, ordered

    def draw_filter(self, context, layout):
        pass
    
class NODE_UL_key_filter_NewItem(Operator):
    '''Add a new key filter'''
    bl_idname = "roma_key.new_item"
    bl_label = "Add"
    
    nodeFingerprint: StringProperty(name="Node Name")

    def execute(self, context): 
        node = readNodeFingerPrint(self.nodeFingerprint)
        node.key_list.add()
        temp_list = []
        for el in node.key_list:
            temp_list.append(el.id)
        last = len(node.key_list)-1
        node.key_list[last].id = max(temp_list)+1
        
        selectedName = node.dropdown
        node.key_list[last].name = selectedName
        
        updateGroupByCombination(self.nodeFingerprint)
        return{'FINISHED'}
    

class NODE_UL_key_filter_DeleteItem(Operator):
    '''Remove a key filter'''
    bl_idname = "roma_key.delete_item"
    bl_label = "Remove"
    
    nodeFingerprint: StringProperty(name="Node Name")
    
    # @classmethod
    # def poll(self, cls, context):
    #     node = readNodeFingerPrint(self.nodeFingerprint)
    #     return node.key_list
        
    def execute(self, context):
        node = readNodeFingerPrint(self.nodeFingerprint)
        my_list = node.key_list
        index =  node.key_list_index

        my_list.remove(index)
        node.key_list_index = min(max(0, index - 1), len(my_list) - 1)
        
        updateGroupByCombination(self.nodeFingerprint)
        return{'FINISHED'}
    
class NODE_UL_key_MoveItem(Operator):
    '''Move the filter. Filter on top have priority'''
    bl_idname = "roma_key.move_item"
    bl_label = "Move key"

    direction: bpy.props.EnumProperty(items=(('UP', 'Up', ""),
                                              ('DOWN', 'Down', ""),))
    
    nodeFingerprint: StringProperty(name="Node Name")

    # @classmethod
    # def poll(cls, context):
    #     return context.scene.roma_typology_uses_name_list

    def move_index(self):
        node = readNodeFingerPrint(self.nodeFingerprint)
        index = node.key_list_index
        list_length = len(node.key_list) - 1 
        new_index = index + (-1 if self.direction == 'UP' else 1)

        node.key_list_index = max(0, min(new_index, list_length))

    def execute(self, context):
        node = readNodeFingerPrint(self.nodeFingerprint)
        my_list = node.key_list
        index =  node.key_list_index

        neighbor = index + (-1 if self.direction == 'UP' else 1)
        my_list.move(neighbor, index)
        self.move_index()
        
        updateGroupByCombination(self.nodeFingerprint)
        
        return{'FINISHED'}
        
        
    
class RoMaMathNode(RoMaTreeNode, Node):
    '''Read RoMa attributes'''
    bl_idname = 'RoMa Math Node'
    bl_label = "Math"
    
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
        items=lambda self, context : getAvailableAttributes(self, nodeType="Math", inputId=0),
        description="Attribute to use in field A"
    )
    
    dropdown_B : EnumProperty(
        items=lambda self, context: getAvailableAttributes(self, nodeType="Math", inputId=1),
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
   
    
    
    
    inputList = ["A", "B"]
    AB_List = ['Add', 'Subtract', 'Multiply', 'Divide']
    AB_Power = ['Power']
    AB_Log = ["Logarithm"]
    AB_Square = ["Square Root", "Inverse Square Root", "Absolute", "Exponent"]
    AB_Types_Values = ["int", "float"]
    
    def init(self, context):
        # self.inputs.new('NodeSocketFloat', 'A Value', identifier='A')
        self.inputs.new('RoMa_attributeCollectionAndFloat_SocketType', name = 'Attribute', identifier='A')
        # self.inputs['A_list'].display_shape = 'DIAMOND_DOT'
        self.inputs['A'].display_shape = 'DIAMOND_DOT'
        
        # self.inputs.new('NodeSocketFloat', 'B Value', identifier='B')
        self.inputs.new('RoMa_attributeCollectionAndFloat_SocketType', name = 'Attribute', identifier='B')
        # self.inputs['B_list'].display_shape = 'DIAMOND_DOT'
        self.inputs['B'].display_shape = 'DIAMOND_DOT'
        
        # self.outputs.new('NodeSocketFloat', 'Value', identifier='output')
        self.outputs.new('RoMa_attributeCollectionAndFloat_SocketType', name = 'Attribute', identifier='Value')
        self.outputs['Value'].display_shape = 'DIAMOND_DOT'
        
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
        cleanSocket(self, 'A', "input")
        if self.inputs['A'].is_linked:
            object_items = self.inputs['A'].links[0].from_socket.object_items.items
            nodeFingerPrint = writeNodeFingerPrint(self)
            copyAttributesToSocket(object_items, nodeFingerPrint, 'A', "input")
        
        
        # B = self.inputs['B'].default_value 
        # print(f"gli attributi copiati in capture attribute sono:-------------------------------------")
        # items = self.inputs['A'].object_items.items
        # for item in items:
        #     print()
        #     print(f"Item name {item.name} has {len(item['key_value_items'])} attributes")
        #     for key in item['key_value_items']:
        #         if key['value_type'] == "STRING":
        #             print(f"key {key['name']} has value {key['value_string']} ")
        #         else:
        #             print(f"key {key['name']} has value {key['value_float']}")
                    
                    
                    
        # if self.inputs['A'].is_linked:
        #     A = PointerProperty(type=RoMa_attribute_propertyGroup)
        #     object_items = self.inputs['A'].links[0].from_socket.object_items.items
            
        # else:
        #     A =FloatProperty(default=self.inputs['A'].default_value) 
        #     # A = self.inputs['A'].default_value
            
        # print(f"socket A {A}")
        # # nodeFingerPrint = writeNodeFingerPrint(self)
        # if (selection in self.AB_List + self.AB_Power + self.AB_Log):
        #     A = self.assignValueToInput("A")
        #     # print(f"assegnato A {A}")
        #     if self.inputs['B'].is_linked:
        #         socket = self.inputs['B'].links[0].from_socket
        #         if hasattr(socket, 'object_items'):
        #             B = socket.object_items
        #         else:
        #             B = socket.default_value
        #     else:
        #         B = self.inputs['B'].default_value

        # elif selection in self.AB_Square:
        #     if self.inputs['A'].is_linked:
        #         socket = self.inputs['A'].links[0].from_socket
        #         if hasattr(socket, 'object_items'):
        #             A = socket.object_items
        #         else:
        #             A = socket.default_value
        #     else:
        #         A = self.inputs['A'].default_value
        
      
            
           
        #     if selection == "Add":
        #         if type(A).__name__ in self.AB_Types_Values and type(B).__name__ in  self.AB_Types_Values:
        #             output["type"] = "value"
        #             output["value"] = A + B
        #         elif type(A).__name__ == "bpy_prop_collection_idprop" and type(B).__name__ in  self.AB_Types_Values:
        #             output["type"] = "list"
        #             for el in A:
        #                 print(f"input {el.area}")
            
        #     elif selection == "Subtract":
        #         output = A - B
        #     elif selection == "Multiply":
        #         output = A * B
        #     elif selection == "Divide":
        #         output = A / B
        #     elif selection == "Power":
        #         output = A ** B
        #     elif selection == "Logarithm":
        #         output = math.log(A, B)
        #     elif selection == "Square Root":
        #         output = math.sqrt(A)
        #     elif selection == "Inverse Square Root":
        #         output = 1/math.sqrt(A)
        #     elif selection == "Absolute":
        #         output = abs(A)
        #     elif selection == "Exponent":
        #         output = math.exp(A)
                
            # print(f"pireooooooooooooo {output}")
            # self.outputs.move(0 ,1)
        
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
        if checkLink(self):
            self.manualExecute()
            
        
    def update(self):
        # if the socket is linked, it is necessary to remove the assigned key
        # to avoid recursive update
        print("valuto")
        for input in self.inputs:
            if input.is_linked:
                removeKeyFromNode(self, inputs=[input.name])
                # print("rimuovo")
            else:
                keyList = bpy.context.scene.romaKeyDictionary.items()
                madeUpKey = self.path_resolve('inputs[\"'+input.name+'\"]')
                keyToTest = [key[0] for key in keyList]
                if str(madeUpKey) not in map(str, keyToTest):
                    addKeysToNode(self, inputs=[input.name])
                    # print("aggiunto")
                        
                                
        if checkLink(self):
            self.manualExecute()
        else:
            cleanOutputs(self)
            
        # print(f"Math Node output status: {self.outputs[0].enabled}")

            
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
        
        # self.update()
        
        
class RoMaFloatNode(RoMaTreeNode, Node):
    bl_label = 'Value'
    bl_idname = 'RoMa Value'

    float : FloatProperty(
                name='',
                precision=3,)

    def init(self, context):
        self.outputs.new('NodeSocketFloat', name='Value', identifier='Value')
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
        self.outputs.new('NodeSocketInt', name='Attribute', identifier='Integer')
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
       

# class RoMaAttributeToColumnNode(RoMaTreeNode, Node):
#     '''Create a column with the attribute data'''
#     bl_idname = 'RoMa Column from Data'
#     bl_label = "Data to Column"
    
#     validated = True
    
#     def init(self, context):
#         self.inputs.new('RoMa_attributeCollectionAndFloat_SocketType', name = 'Attribute', identifier='Attribute')
#         self.inputs['Attribute'].display_shape = 'DIAMOND_DOT'
        
#         self.outputs.new('RoMa_attributeCollectionAndFloat_SocketType', name = 'Attribute', identifier='Attribute')
#         self.outputs['Attribute'].display_shape = 'DIAMOND_DOT'
        
#     def manualExecute(self):
#         pass    
        
#     def update(self):
#         self.manualExecute()
    
#     def execute(self):
#         self.manualExecute()
        # if self.validated:
        #     cleanInputs(self)
        #     cleanOutputs(self)
        #     if self.inputs['Attribute'].is_linked:
        #             object_items = self.inputs['Attribute'].links[0].from_socket.object_items
        #             for obj in object_items:
        #                 item = self.outputs['Attribute'].object_items.add()
        #                 # duplicate attributes
        #                 for prop_name in obj.__annotations__.keys():
        #                     setattr(item, prop_name, getattr(obj, prop_name))
    


        
class RoMaViewerNode(RoMaTreeNode, Node):
    '''Add a viewer node'''
    bl_idname = 'RoMa Viewer'
    bl_label = 'Viewer'
    
    def data_to_update_schedule_node_editor(self, context):
        update_schedule_node_editor(self)
    
    toggle : bpy.props.BoolProperty(
            name = "Show Table",
            default = False,
            update = data_to_update_schedule_node_editor)

    
    def init(self, context):
        # self.outputs.new('RoMa_stringCollection_SocketType', 'RoMa Mesh')
        # self.inputs.new('RoMa_stringCollection_SocketType', 'RoMa Mesh')
        self.inputs.new('RoMa_attributeCollection_SocketType', name="Table", identifier='Schedule')
        self.inputs['Schedule'].hide_value = True
        self.inputs['Schedule'].display_shape = 'DIAMOND_DOT'
        
    def copy(self, node):
        cleanInputs(self)
    
    def manualExecute(self):
        if checkLink(self):
            if self.inputs['Schedule'].is_linked:
                pass
                # cleanSocket(self, 'Schedule', 'input')
                # object_items = self.inputs['Schedule'].links[0].from_socket.object_items.items
                # nodeFingerPrint = writeNodeFingerPrint(self)
                # copyAttributesToSocket(object_items, nodeFingerPrint, 'Schedule', "input")
                
                # print(f"gli attributi copiati in viewer attribute sono:-------------------------------------")
                # # items = self.inputs['Schedule'].object_items.items
                # for item in object_items:
                #     print()
                #     print(f"Item name {item.name} has {len(item['key_value_items'])} attributes")
                #     for key in item['key_value_items']:
                #         if key['value_type'] == "STRING":
                #             print(f"key {key['name']} has value {key['value_string']} ")
                #         else:
                #             print(f"key {key['name']} has value {key['value_float']}")
                
    
    
    def update(self):
        self.manualExecute()
        
    def execute(self):
        self.manualExecute()

            
    def draw_buttons(self, context, layout):
        # nodeName = self.name
        # treeName = self.id_data.name
        # nodeIndentifier = f"{treeName}::{nodeName}"
        nodeIndentifier = writeNodeFingerPrint(self)
        col = layout.column(align=True)
        # col.operator("object.roma_add_column").sourceNode = nodeIndentifier
        col.prop(self, "toggle", text="Show Table")

    
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
        NodeItem("Capture RoMa Attribute", label="Capture Attribute"),
        NodeItem("RoMa All Attributes", label="All Attributes"),
        NodeItem("RoMa Area Attribute", label="Area"),
        NodeItem("RoMa Use Attribute", label="Use"),
    ]),
    RoMaNodeCategory('MATHEMATIC', "Mathematic", items=[
        NodeItem("RoMa Math Node", label="Math"),
        NodeItem("RoMa Integer", label="Integer"),
        NodeItem("RoMa Value", label="Value"),
    ]),
    RoMaNodeCategory('TABLE', "Table", items= [
        NodeItem("Table by RoMa Attribute", label="Table"),
        NodeItem("RoMa Table Data", label="Table Data"),
        NodeItem("RoMa Table Function", label="Table Function"),
        NodeItem("RoMa Unique Values", label="Unique Values")
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
    
    
# convert rgb to hsv    
def rgb_to_hsv(r, g, b):
    # Compute the maximum and minimum values among r, g, b
    max_rgb = max(r, g, b)
    min_rgb = min(r, g, b)
    chroma = max_rgb - min_rgb  # Difference between max and min
    
    # Calculate Hue
    if chroma == 0:
        hue = 0  # If chroma is 0, hue is undefined (set to 0)
    else:
        if max_rgb == r:
            hue = ((g - b) / chroma) % 6
        elif max_rgb == g:
            hue = ((b - r) / chroma) + 2
        else:
            hue = ((r - g) / chroma) + 4
        hue *= 60  # Convert to degrees
        if hue < 0:
            hue += 360

    # Calculate Saturation
    saturation = 0 if max_rgb == 0 else chroma / max_rgb
    
    # Calculate Value
    value = max_rgb
    
    return hue, saturation, value

# convert hsv to rgb
def hsv_to_rgb(h, s, v):
    # If saturation is zero, the color is a shade of grey
    if s == 0:
        r = g = b = v
        return r, g, b
    
    # Calculate the chroma
    chroma = v * s
    h_prime = h / 60.0  # Sector of the color wheel
    x = chroma * (1 - abs(h_prime % 2 - 1))
    
    if 0 <= h_prime < 1:
        r1, g1, b1 = chroma, x, 0
    elif 1 <= h_prime < 2:
        r1, g1, b1 = x, chroma, 0
    elif 2 <= h_prime < 3:
        r1, g1, b1 = 0, chroma, x
    elif 3 <= h_prime < 4:
        r1, g1, b1 = 0, x, chroma
    elif 4 <= h_prime < 5:
        r1, g1, b1 = x, 0, chroma
    elif 5 <= h_prime < 6:
        r1, g1, b1 = chroma, 0, x
    else:
        r1, g1, b1 = 0, 0, 0  # Should not happen
    
    # Match the value by adding the same amount to each component
    m = v - chroma
    r = r1 + m
    g = g1 + m
    b = b1 + m
    
    return r, g, b



def draw_callback_schedule_overlay(self, context, sourceNode):
    if context.area.ui_type == "RoMaTreeType":
        # path = sourceNode.split("::")
        # treeName = path[0]
        # nodeName = path[1]
        # node = bpy.data.node_groups[treeName].nodes[nodeName]
        node = readNodeFingerPrint(sourceNode)
        
        nodeX, nodeY = node.location
        nodeWidth = node.width
        # nodeHeight = node.height
        
        system = bpy.context.preferences.system
        ui_scale = system.ui_scale
        
        # text settings
        fontSize = 12
        font_id = font_info["font_id"]
        red = 1.0
        green = 1.0
        blue = 1.0
        alpha = 1.0
        blf.size(font_id, fontSize)
        blf.color(font_id, red, green, blue, alpha)
        
        
        # cell settings
        cellX = 100
        cellY = 25
        paddingX = 5
        lineWidth = 0.5
        lineColor = (red, green, blue, alpha)
        theme = bpy.context.preferences.themes.items()[0][1]
        paperColor = theme.node_editor.node_backdrop

        input_node = theme.node_editor.input_node
        hue, saturation, value = rgb_to_hsv(input_node[0], input_node[1], input_node[2])
        r, g, b = hsv_to_rgb(hue, saturation - 0.17, value - 0.49)
        headerColor = (r, g, b, 1)
        
        nodePosX = nodeX + nodeWidth + paddingX
        nodePosY = nodeY
        
        graphic_data = dataForGraphic(sourceNode, 
                                    posX = nodePosX, 
                                    posY = nodePosY, 
                                    cellWidth= cellX, 
                                    cellHeight=cellY, 
                                    scale = ui_scale)
        
        data, verts, edges, faces = graphic_data.data_for_graphic()
        
        # data, verts, edges, faces = dataForGraphic(sourceNode, 
        #                                             posX = nodePosX, 
        #                                             posY = nodePosY, 
        #                                             cellWidth= cellX, 
        #                                             cellHeight=cellY, 
        #                                             scale = ui_scale)
        
        
                    
        # drawing ###############################################
        
                    
        # drawing canvas background
        rows = len(data)
        columns = len(data[0])
        A = 1
        D = (rows +1) * (columns +1) -1
        B = D - rows +1
        C = A + rows -1
        
        vertices = (
            (verts[A]), (verts[B]),
            (verts[C]), (verts[D])
        )
        indices = (
            (0, 1, 2), (2, 3, 1)
        )
        
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'TRIS', {"pos": vertices}, indices=indices)
        shader.uniform_float("color", paperColor)
        batch.draw(shader)
        
                
        # drawing header background
        A = 0
        D = (rows +1) * (columns +1) - rows
        B = D - 1
        C = A + 1
        
        vertices = (
            (verts[A]), (verts[B]),
            (verts[C]), (verts[D])
        )
        indices = (
            (0, 1, 2), (2, 3, 1)
        )
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'TRIS', {"pos": vertices}, indices=indices)
        shader.uniform_float("color", headerColor)
        batch.draw(shader)
        
        
        
        # drawing cells
        batch = batch_for_shader(shader, 'LINES', {"pos": verts}, indices=edges)
        shader.uniform_float("color", lineColor)
            
        gpu.state.line_width_set(lineWidth)
        gpu.state.blend_set("ALPHA")
        batch.draw(shader)
        
        # drawing data #########################################
        for itemIndex, items in enumerate(data):
            for keyIndex, key in enumerate(items):
                value = items.get(key, '')
                x = ((nodePosX + 10) + (cellX * keyIndex)) * ui_scale 
                y = ((nodePosY - cellY/2 - fontSize/4) + (-1 * itemIndex * cellY)) * ui_scale

                blf.position(font_id, x, y, 0)
                try:
                    floated =round(float(value),2)
                    blf.draw(font_id, f"{floated}")
                except:
                    blf.draw(font_id, value)
        
        


        
    else:
        return

    
###################################################################################
############### 3D schedule #######################################################
###################################################################################
# class RoMaAddColumn(Operator):
#     '''Add a column to the schedule'''
#     bl_idname="object.roma_add_column"
#     bl_label="RoMa Column"
#     bl_options = {'REGISTER'}
    
#     sourceNode : bpy.props.StringProperty(name="Source Node")
    
#     # width: FloatProperty(
#     #     name="Width",
#     #     description="Cell Width",
#     #     min=0.01, max=100.0,
#     #     default=3.0,
#     # )
    
#     # height: FloatProperty(
#     #     name="Height",
#     #     description="Cell Height",
#     #     min=0.01, max=100.0,
#     #     default=2.0,
#     # )
    
#     # data : bpy.props.StringProperty(name="Filter type name")
    
#     def execute(self, context):
#         # retrieve data from node
#         # path = self.sourceNode.split("::")
#         # treeName = path[0]
#         # nodeName = path[1]
#         # node = bpy.data.node_groups[treeName].nodes[nodeName]
#         # data = node.inputs['Attribute'].links[0].from_socket.object_items
        
#         # create a column with its cells
#         mesh = bpy.data.meshes.new("RoMa Column")
#         bm = bmesh.new()
#         verts, edges, faces, data = dataForGraphic(self.sourceNode, 
#                                                    posX = 0, 
#                                                    posY = 0, 
#                                                    cellWidth= 3, 
#                                                    cellHeight=2, 
#                                                    scale=1)
#         for vert in verts:
#             bm.verts.new(vert)
#         bm.verts.ensure_lookup_table()
        
#         for e in edges:
#             bm.edges.new([bm.verts[i] for i in e])
        
#         bm.to_mesh(mesh)
#         mesh.update()

#         column = bpy.data.objects.new(name="Column", object_data=mesh)
#         bpy.context.scene.collection.objects.link(column)
        
#         # index = 0
#         # while index < len(data):
#         for index, el in enumerate(data):
#             font_curve = bpy.data.curves.new(type="FONT", name="Font Curve")
#             # font_curve.body = f"{round(el.area)}"
#             font_curve.body = f"{el.use}"
#             font_obj = bpy.data.objects.new(name="Font Object", object_data=font_curve)
#             bpy.context.scene.collection.objects.link(font_obj)
#             newPos = mathutils.Vector((0.3, -1.3 - (2 * index), 0.0))
#             font_obj.location = font_obj.location + newPos
#             # index += 1
#             # parenting
#             font_obj.parent = bpy.data.objects[column.name]
#         return {'FINISHED'}
    

 