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
# import bmesh
# import gpu
# from gpu_extras.batch import batch_for_shader

# import bmesh

from bpy.props import StringProperty, IntProperty, FloatProperty, BoolProperty
from bpy.types import PropertyGroup, UIList, Operator, Panel
from bpy.app.handlers import persistent


import random
import decimal
from datetime import datetime

# selectedTypology = None

# switch = False

# coords = [(1, 1, 1), (-2, 0, 0), (-2, -1, 3), (0, 1, 1)]
# coords = []
# indices = []
# shader = gpu.shader.from_builtin('UNIFORM_COLOR')
# # batch = batch_for_shader(shader, 'LINES', {"pos": coords})
# batch = None

# class SimpleOperator(Operator):
    
#     """Print object name in Console"""
#     bl_idname = "object.simple_operator"
#     bl_label = "Simple Object Operator"
    
    
            
#     _handle = None
    
#     def execute(self, context):
#         global switch
#         global coords
#         global indices
#         global shader
#         global batch
#         if switch == False:
#             switch = True
            
#             obj = bpy.context.view_layer.objects.active
#             # location = obj.location
#             mesh = obj.data
#             mesh.calc_loop_triangles()
            
#             for vert in mesh.vertices:
#                 coords.append(obj.matrix_world @ vert.co)
#             for tri in mesh.loop_triangles:
#                 # tmpCoords = (obj.matrix_world @ mesh.vertices[tri.vertices[0]].co,
#                 #        obj.matrix_world @ mesh.vertices[tri.vertices[1]].co,
#                 #        obj.matrix_world @ mesh.vertices[tri.vertices[2]].co)
#                 # coords.append(tmpCoords)
                
#                 tmpIndices = (tri.vertices[0],
#                               tri.vertices[1],
#                               tri.vertices[2])
#                 indices.append(tmpIndices)
                
                
                
            
            
            
#             # bm = bmesh.new()
            
#             # bm.from_mesh(mesh)
            
#             # for c in bm.verts:
#             #     # from local to global coordinates
#             #     globalCoord = obj.matrix_world @ c.co
                
#             #     vert = (globalCoord.x, globalCoord.y, globalCoord.z)
#             #     coords.append(vert)
                
#             # for e in bm.edges:
#             #     tmp = (e.verts[0].index, e.verts[1].index)
#             #     indices.append(tmp)
                

#             # print(coords)
#             # print(indices)
#             # batch = batch_for_shader(shader, 'LINES', {"pos": coords}, indices=indices)
#             batch = batch_for_shader(shader, 'TRIS', {"pos": coords}, indices=indices)
#             # bm.free()
            
#             SimpleOperator._handle = bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_VIEW')
#             print("acceso")
#         else:
#             switch = False
            
#             coords = []
#             indices = []
#             batch = None
            
#             bpy.types.SpaceView3D.draw_handler_remove(SimpleOperator._handle, 'WINDOW')
#             SimpleOperator._handle = None
            
#             print("spento")
            
#         return {'FINISHED'}
    
# def draw():
#     shader.uniform_float("color", (1, 1, 0, 0.01))
#     batch.draw(shader)


# def initRomaLists(listName):
#     if listName == "romaTypologyName":
#         bpy.context.scene.roma_typology_name_list.add()
#         bpy.context.scene.roma_typology_name_list[0].id = 0
#         bpy.context.scene.roma_typology_name_list[0].name = "Typology name... "
#         bpy.context.scene.roma_typology_name_list[0].useList = "0"
#     elif listName == "romaTypologyUsesName":
#         bpy.context.scene.oma_typology_uses_name_list.add()
#         bpy.context.scene.roma_typology_uses_name_list[0].id = 0
#         bpy.context.scene.roma_typology_uses_name_list[0].name = bpy.context.scene.roma_use_name_list[0].name
       

class update_GN_Filter_OT(Operator):
    """Update the GN node Filter by Use"""
    bl_idname = "node.update_gn_filter"
    bl_label = "Update the GN filter by Use"
    
    # filter_name: bpy.props.StringProperty(name="Filter type name")
        
    #     return node_obj, node_x_location
    def newGroup (self, groupName, type):
        attributeName = "roma_use"
        # if self.filter_name == "use": attributeName = "RoMa_Use"
        # elif self.filter_name == "typology": attributeName = "roma_typology_id"
        
         # geometry nodes group
        # if type == "GN":
        group = bpy.data.node_groups.new(groupName,'GeometryNodeTree')
        
        #Add Group Output
        group_output = group.nodes.new('NodeGroupOutput')
        # Add named attribute
        named_attribute_node = group.nodes.new(type="GeometryNodeInputNamedAttribute")
        named_attribute_node.data_type = 'INT'
        named_attribute_node.inputs[0].default_value = attributeName
        # else: # shader group
        #     group = bpy.data.node_groups.new(groupName,'ShaderNodeTree')
        #     #Add Group Output
        #     group_output = group.nodes.new('NodeGroupOutput')
        #     # Add named attribute
        #     named_attribute_node = group.nodes.new(type="ShaderNodeAttribute")
        #     named_attribute_node.attribute_type = 'GEOMETRY'
        #     named_attribute_node.attribute_name = attributeName
        #     named_attribute_node.name = "Named Attribute" # this to keep more generic the following code
        #     named_attribute_node.label = "Named Attribute"
            
        group_output.location = (600, 0)
        named_attribute_node.location = (0,-100)
        return(group)
        
        
    def execute(self, context):
        # groupTypes = ["GN", "Shader"]
        
        #Create NodeGroup
        # for type in groupTypes:
        name = "RoMa Geometry Filter by Use"
            # if type == "GN": name = "RoMa Geometry Filter by " + self.filter_name
            # else: name = "RoMa Shader Filter by " + self.filter_name
            
        if name not in bpy.data.node_groups:
            filterBy_Group = self.newGroup(name, "GN")
            #     if type == "GN": filterBy_Group = self.newGroup(name, "GN")
            #     elif type == "Shader": filterBy_Group = self.newGroup(name, "Shader")
        else:
            filterBy_Group = bpy.data.node_groups[name]
                
        nodes = filterBy_Group.nodes
        
        group_output = nodes["Group Output"]
        named_attribute_node = nodes["Named Attribute"]
                    
        filterNodeIds = []
        filterNodeDescriptions = []
        for node in nodes:
            if node.type == "COMPARE":
                tmpId = node.inputs[3].default_value
                filterNodeIds.append(tmpId)
                filterNodeDescriptions.append(filterBy_Group.interface.items_tree[tmpId].description)
            # elif node.type == "MATH":
            #         tmpId = int(node.inputs[1].default_value)
            #         filterNodeIds.append(tmpId)
            #         filterNodeDescriptions.append(filterBy_Group.interface.items_tree[tmpId].description)
                    
            
        if len(filterNodeIds) == 0:
            lastId = -1           
        else:
            lastId = max(filterNodeIds)
            # print(lastId, len(nodes))
                
            # if self.filter_name == "use": listToLoop = bpy.context.scene.roma_use_name_list
            # elif self.filter_name == "typology": listToLoop = bpy.context.scene.roma_typology_name_list
        listToLoop = bpy.context.scene.roma_use_name_list
        for el in listToLoop:
            if hasattr(el, "id"):
                #a new name has been added
                if el.id not in filterNodeIds:
                    if lastId >= 0:
                        node_y_location = nodes["Compare " + str(lastId)].location[1] -25
                    else:
                        node_y_location = 0
                    
                    # if type == "GN":
                    compare_node = filterBy_Group.nodes.new(type="FunctionNodeCompare")
                    compare_node.data_type = 'INT'
                    compare_node.operation = 'EQUAL'
                    compare_node.inputs[3].default_value = el.id
                    # else:
                    #     compare_node = filterBy_Group.nodes.new(type="ShaderNodeMath")
                    #     compare_node.operation = "COMPARE"
                    #     compare_node.inputs[1].default_value = el.id
                    #     compare_node.inputs[2].default_value = 0.001
                        
                    compare_node.location = (300, node_y_location-35)
                    compare_node.hide = True
                    compare_node.label="="+str(el.id)
                    compare_node.name="Compare "+str(el.id)
                    lastId = el.id
                    
                    #Add the Output Sockets and change their Default Value
                    if el.name == "":
                        elName = "Use name..."
                    else:
                        elName = el.name
                    descr = "id: " + str(el.id) + " - " + elName
                    filterBy_Group.interface.new_socket(name=elName,description=descr,in_out ="OUTPUT", socket_type="NodeSocketBool")
            
                    #Add Links
                    index = len(group_output.inputs) -2
                    filterBy_Group.links.new(named_attribute_node.outputs[0], compare_node.inputs[2])
                    # if type == "GN":
                    #     filterBy_Group.links.new(named_attribute_node.outputs[0], compare_node.inputs[2])
                    # else:
                    #     filterBy_Group.links.new(named_attribute_node.outputs[2], compare_node.inputs[0])
                    filterBy_Group.links.new(compare_node.outputs[0], group_output.inputs[index])

                # a name has been renamed
                elif ("id: " + str(el.id) + " - " + str(el.name)) not in filterNodeDescriptions:
                    for i, desc in enumerate(filterNodeDescriptions):
                        if i == int(el.id):
                            filterBy_Group.interface.items_tree[i].name = str(el.name)
                            filterBy_Group.interface.items_tree[i].description = "id: " + str(el.id) + " - " + str(el.name)
                            
                            
                            
                        

        return {'FINISHED'}
    
class update_Shader_Filter_OT(Operator):
    """Update the shader node Filter by... based on the passed type value"""
    bl_idname = "node.update_shader_filter"
    bl_label = "Update the Shader filter by..."
    
    filter_name: bpy.props.StringProperty(name="Filter type name")
        
    #     return node_obj, node_x_location
    def newGroup (self, groupName, type):
        if self.filter_name == "plot": attributeName = "roma_plot_id"
        elif self.filter_name == "block": attributeName = "roma_block_id"
        elif self.filter_name == "use": attributeName = "roma_use"
        elif self.filter_name == "typology": attributeName = "roma_typology_id"
        
         # geometry nodes group
        # if type == "GN":
        #     group = bpy.data.node_groups.new(groupName,'GeometryNodeTree')
        #     #Add Group Output
        #     group_output = group.nodes.new('NodeGroupOutput')
        #     # Add named attribute
        #     named_attribute_node = group.nodes.new(type="GeometryNodeInputNamedAttribute")
        #     named_attribute_node.data_type = 'INT'
        #     named_attribute_node.inputs[0].default_value = attributeName
        
        # shader group
        group = bpy.data.node_groups.new(groupName,'ShaderNodeTree')
        #Add Group Output
        group_output = group.nodes.new('NodeGroupOutput')
        # Add named attribute
        named_attribute_node = group.nodes.new(type="ShaderNodeAttribute")
        named_attribute_node.attribute_type = 'GEOMETRY'
        named_attribute_node.attribute_name = attributeName
        named_attribute_node.name = "Named Attribute" # this to keep more generic the following code
        named_attribute_node.label = "Named Attribute"
        #Add value attribute
        # value_attribute_node = group.nodes.new(type="ShaderNodeValue")
        # value_attribute_node.label = self.filter_name + " number"
        # value_attribute_node.outputs[0].default_value = 0

            
        group_output.location = (600, 0)
        named_attribute_node.location = (0,-100)
        # value_attribute_node.location = (0,100)
        
        return(group)
        
        
    def execute(self, context):
        # groupTypes = ["GN", "Shader"]
        
        #Create NodeGroup
        # for type in groupTypes:
        #     if type == "GN": name = "RoMa Geometry Filter by " + self.filter_name
        #     else: name = "RoMa Shader Filter by " + self.filter_name
        name = "RoMa Shader Filter by " + self.filter_name
        
        if name not in bpy.data.node_groups:
            # if type == "GN": filterBy_Group = self.newGroup(name, "GN")
            # elif type == "Shader": filterBy_Group = self.newGroup(name, "Shader")
            filterBy_Group = self.newGroup(name, "Shader")
        else:
            filterBy_Group = bpy.data.node_groups[name]
            
        nodes = filterBy_Group.nodes
        
        group_output = nodes["Group Output"]
        named_attribute_node = nodes["Named Attribute"]
        # nodeName = self.filter_name + " number"
        # value_attribute_node = nodes[nodeName]
                    
        filterNodeIds = []
        filterNodeDescriptions = []
        for node in nodes:
            # if node.type == "COMPARE":
            #     tmpId = node.inputs[3].default_value
            #     filterNodeIds.append(tmpId)
            #     filterNodeDescriptions.append(filterBy_Group.interface.items_tree[tmpId].description)
            if node.type == "MATH":
                tmpId = int(node.inputs[1].default_value)
                filterNodeIds.append(tmpId)
                filterNodeDescriptions.append(filterBy_Group.interface.items_tree[tmpId].description)
                
        
        if len(filterNodeIds) == 0:
            lastId = -1           
        else:
            lastId = max(filterNodeIds)
            # print(lastId, len(nodes))
            
        if self.filter_name == "plot": listToLoop = bpy.context.scene.roma_plot_name_list
        elif self.filter_name == "block": listToLoop = bpy.context.scene.roma_block_name_list
        elif self.filter_name == "use": listToLoop = bpy.context.scene.roma_use_name_list
        elif self.filter_name == "typology": listToLoop = bpy.context.scene.roma_typology_name_list
        
        # filterBy_Group.links.new(named_attribute_node.outputs[2], group_output.inputs[0])
        # filterBy_Group.links.new(value_attribute_node.outputs[0], group_output.inputs[1])
        
            
        for el in listToLoop:
            if hasattr(el, "id"):
                #a new name has been added
                if el.id not in filterNodeIds:
                    if lastId >= 0:
                        node_y_location = nodes["Compare " + str(lastId)].location[1] -25
                    else:
                        node_y_location = 0
                    
                    # if type == "GN":
                    #     compare_node = filterBy_Group.nodes.new(type="FunctionNodeCompare")
                    #     compare_node.data_type = 'INT'
                    #     compare_node.operation = 'EQUAL'
                    #     compare_node.inputs[3].default_value = el.id
                    # else:
                    compare_node = filterBy_Group.nodes.new(type="ShaderNodeMath")
                    compare_node.operation = "COMPARE"
                    compare_node.inputs[1].default_value = el.id
                    compare_node.inputs[2].default_value = 0.001
                        
                    compare_node.location = (300, node_y_location-35)
                    compare_node.hide = True
                    compare_node.label="="+str(el.id)
                    compare_node.name="Compare "+str(el.id)
                    lastId = el.id
                    
                    #Add the Output Sockets and change their Default Value
                    if el.name == "":
                        elName = self.filter_name + " name..."
                    else:
                        elName = el.name
                    descr = "id: " + str(el.id) + " - " + elName
                    filterBy_Group.interface.new_socket(name=elName,description=descr,in_out ="OUTPUT", socket_type="NodeSocketBool")
            
                    #Add Links
                    index = len(group_output.inputs) -2
                    # if type == "GN":
                    #     filterBy_Group.links.new(named_attribute_node.outputs[0], compare_node.inputs[2])
                    # else:
                    filterBy_Group.links.new(named_attribute_node.outputs[2], compare_node.inputs[0])
                    filterBy_Group.links.new(compare_node.outputs[0], group_output.inputs[index])

                # a name has been renamed
                elif ("id: " + str(el.id) + " - " + str(el.name)) not in filterNodeDescriptions:
                    for i, desc in enumerate(filterNodeDescriptions):
                        if i == int(el.id):
                            filterBy_Group.interface.items_tree[i].name = str(el.name)
                            filterBy_Group.interface.items_tree[i].description = "id: " + str(el.id) + " - " + str(el.name)
        return {'FINISHED'}
    

class VIEW3D_PT_RoMa_project_data(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    # bl_category = "RoMa"
    bl_label = "RoMa Project Data"
    bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        # obj = context.object

        # col = layout.column(align=True)
        # col.prop(context.window_manager, 'toggle_selection_overlay', icon_only=False)
        # layout.separator()


class VIEW3D_PT_RoMa_show_data(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    # bl_category = "RoMa"
    bl_label = "Show Data"
    bl_parent_id = "VIEW3D_PT_RoMa_project_data"
    # bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw_header(self, context):
        self.layout.prop(context.window_manager, "toggle_show_data", text="")
        
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.
        
        layout.active = context.window_manager.toggle_show_data
        
        # flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=True)

        # col = flow.column()
        # col = flow.column(heading="Mass", align = True)
        col = layout.column(heading="Mass", align=True)
        col.prop(context.window_manager, 'toggle_plot_name', icon_only=False)
        col.prop(context.window_manager, 'toggle_block_name', icon_only=False)
        col.prop(context.window_manager, 'toggle_typology_name', icon_only=False)
        col.prop(context.window_manager, 'toggle_storey_number', icon_only=False)
        # col.separator()
        col = layout.column(heading="Wall", align = True)
        col.prop(context.window_manager, 'toggle_wall_name', icon_only=False)
        col.prop(context.window_manager, 'toggle_wall_normal', icon_only=False)
        # col.separator()
        col = layout.column(heading="Floor", align = True)
        col.prop(context.window_manager, 'toggle_floor_name', icon_only=False)
        
############################      ############################
############################ MASS ############################
############################      ############################
           
class VIEW3D_PT_RoMa_mass_data(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    # bl_category = "RoMa"
    bl_label = "Mass Data"
    bl_parent_id = "VIEW3D_PT_RoMa_project_data"
    # bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}
    
    # @classmethod
    # def poll(cls, context):
    #     return (context.object is not None)
    
    def draw(self, context):
        pass
      
############################        ############################
############################ PLOT   ############################
############################        ############################ 
            
class VIEW3D_PT_RoMa_mass_plot_data(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_label = "Plot"
    bl_parent_id = "VIEW3D_PT_RoMa_mass_data"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        scene = context.scene
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.
        
        row = layout.row()
        # row.label(text="Plot")
        
        rows = 3
        
        row = layout.row()
        row.template_list("OBJECT_UL_Plot", "plot_list", scene,
                        "roma_plot_name_list", scene, "roma_plot_name_list_index", rows = rows)
        
        
        col = row.column(align=True)
        col.operator("roma_plot_name_list.new_item", icon='ADD', text="")
        # col.operator("roma_wall_type_list.delete_item", icon='REMOVE', text="")
        col.separator()
        col.operator("roma_plot_name_list.move_item", icon='TRIA_UP', text="").direction = 'UP'
        col.operator("roma_plot_name_list.move_item", icon='TRIA_DOWN', text="").direction = 'DOWN'
        
        # row = layout.row()
        # row = layout.row(align=True)
        # row.prop(context.scene, "roma_plot_names", icon="MOD_BOOLEAN", icon_only=True, text="")
        # row.operator("scene.add_plot_name", icon="ADD", text="New")
        
        # if scene.roma_plot_name_list_index >= 0 and scene.roma_plot_name_list:
        #     item = scene.roma_plot_name_list[scene.roma_plot_name_list_index]
        #     row.prop(item, "name", icon_only=True, text="Plot Name")
            
        # row.prop(item, "index")
        
class OBJECT_UL_Plot(UIList):
   
    """Wall type UIList."""
    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):
       
        # We could write some code to decide which icon to use here...
        custom_icon = 'MOD_BOOLEAN'

        # Make sure your code supports all 3 layout types
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            
            # split.label(text="Index: %d" % (index))
            
            split = layout.split(factor=0.3)
            split.label(text="Id: %d" % (item.id)) 
            # split.label(text=item.name, icon=custom_icon) 
            split.prop(context.scene.roma_plot_name_list[index],
                       "name",
                       icon_only=True,
                       icon = custom_icon)
            
            # layout.alignment = 'LEFT'
            # layout.label(text=item.name, icon="MOD_BOOLEAN")
            
            
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon = custom_icon)

        # self.filter_zero_id(context, data, "roma_plot_name_list")


    def filter_items(self, context, data, propname):
        """Filter and order items in the list."""

        # We initialize filtered and ordered as empty lists. Notice that 
        # if all sorting and filtering is disabled, we will return
        # these empty. 

        filtered = []
        ordered = []
        items = getattr(data, propname)
        # Initialize with all items visible
        filtered = [self.bitflag_filter_item] * len(items)
        
        # for i, item in enumerate(items):
        #     if item.id == 0:
        #         filtered[i] &= ~self.bitflag_filter_item
        return filtered, ordered

    def draw_filter(self, context, layout):
        pass
    
class PLOT_LIST_OT_NewItem(Operator):
    bl_idname = "roma_plot_name_list.new_item"
    bl_label = "Add a new plot"

    def execute(self, context): 
        context.scene.roma_plot_name_list.add()
        # last = len(context.scene.roma_plot_name_list)-1
        # if last == 0:
        #     context.scene.roma_plot_name_list[0].id = 0
        #     context.scene.roma_plot_name_list[0].name = ""
        #     random.seed(datetime.now().timestamp())
        #     rndNumber = float(decimal.Decimal(random.randrange(0,10000000))/10000000)
        #     context.scene.roma_plot_name_list[0].RND = rndNumber
        #     context.scene.roma_plot_name_list.add()
        temp_list = []    
        for el in context.scene.roma_plot_name_list:
            temp_list.append(el.id)
        last = len(context.scene.roma_plot_name_list)-1
        
        context.scene.roma_plot_name_list[last].id = max(temp_list)+1
        # rndNumber = float(decimal.Decimal(random.randrange(0,1000))/1000)
        # context.scene.roma_plot_name_list[last].RND = rndNumber
        bpy.ops.node.update_shader_filter(filter_name="plot")   
        return{'FINISHED'}
    
class PLOT_LIST_OT_MoveItem(Operator):
    bl_idname = "roma_plot_name_list.move_item"
    bl_label = "Move an item in the list"

    direction: bpy.props.EnumProperty(items=(('UP', 'Up', ""),
                                              ('DOWN', 'Down', ""),))

    @classmethod
    def poll(cls, context):
        return context.scene.roma_plot_name_list

    def move_index(self):
        index = bpy.context.scene.roma_plot_name_list_index
        list_length = len(bpy.context.scene.roma_plot_name_list) - 1 
        new_index = index + (-1 if self.direction == 'UP' else 1)

        bpy.context.scene.roma_plot_name_list_index = max(0, min(new_index, list_length))

    def execute(self, context):
        roma_plot_name_list = context.scene.roma_plot_name_list
        index = context.scene.roma_plot_name_list_index

        neighbor = index + (-1 if self.direction == 'UP' else 1)
        roma_plot_name_list.move(neighbor, index)
        self.move_index()

        return{'FINISHED'}
    
# update the node "filter by plot" if a new plot is added or
# a plot name has changed
def update_roma_filter_by_plot(self, context):
    bpy.ops.node.update_shader_filter(filter_name="plot")
    return None
            
class plot_name_list(PropertyGroup):
    id: IntProperty(
           name="Id",
           description="Plot name id",
           default = 0)
    
    name: StringProperty(
           name="Plot Name",
           description="The name of the plot",
           default="Plot name...",
           update=update_roma_filter_by_plot)
    
    # RND: FloatProperty(
    #        name="Random Value per Plot",
    #        description="A random value assigned to each plot",
    #        default = 0)
        
############################        ############################
############################ BLOCK  ############################
############################        ############################

    
class VIEW3D_PT_RoMa_mass_block_data(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_label = "Block"
    bl_parent_id = "VIEW3D_PT_RoMa_mass_data"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        scene = context.scene
        
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.
        
        row = layout.row()
        
        #row.label(text="Block")
        # row.prop(context.window_manager, 'toggle_block_name', toggle=True, icon="HIDE_OFF", icon_only=True)
        
        # is_sortable = len(scene.roma_block_name_list) > 1
        rows = 3
        # if is_sortable:
        #     rows = 5
            
        row = layout.row()
        row.template_list("OBJECT_UL_Block", "block_list", scene,
                        "roma_block_name_list", scene, "roma_block_name_list_index", rows = rows)
        
        
        col = row.column(align=True)
        col.operator("roma_block_name_list.new_item", icon='ADD', text="")
        col.separator()
        col.operator("roma_block_name_list.move_item", icon='TRIA_UP', text="").direction = 'UP'
        col.operator("roma_block_name_list.move_item", icon='TRIA_DOWN', text="").direction = 'DOWN'
        
        # row = layout.row()
        # row = layout.row(align=True)
        
        # if scene.roma_block_name_list_index >= 0 and scene.roma_block_name_list:
        #     item = scene.roma_block_name_list[scene.roma_block_name_list_index]
        #     row.prop(item, "name", icon_only=True, text="Block Name")
            
            
class OBJECT_UL_Block(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):
       
        custom_icon = 'HOME'

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            split = layout.split(factor=0.5)
            split.label(text="Id: %d" % (item.id)) 
            # split.label(text=item.name, icon=custom_icon) 
            split.prop(context.scene.roma_block_name_list[index],
                       "name",
                       icon_only=True,
                       icon = custom_icon)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon = custom_icon)

    def filter_items(self, context, data, propname):
        filtered = []
        ordered = []
        items = getattr(data, propname)
        filtered = [self.bitflag_filter_item] * len(items)
        
        # for i, item in enumerate(items):
        #     if item.id == 0:
        #         filtered[i] &= ~self.bitflag_filter_item
        return filtered, ordered

    def draw_filter(self, context, layout):
        pass
    
class BLOCK_LIST_OT_NewItem(Operator):
    bl_idname = "roma_block_name_list.new_item"
    bl_label = "Add a new block"

    def execute(self, context): 
        context.scene.roma_block_name_list.add()
        # last = len(context.scene.roma_block_name_list)-1
        # if last == 0:
        #     context.scene.roma_block_name_list[0].id = 0
        #     context.scene.roma_block_name_list[0].name = ""
        #     random.seed(datetime.now().timestamp())
        #     rndNumber = float(decimal.Decimal(random.randrange(0,10000000))/10000000)
        #     context.scene.roma_block_name_list[0].RND = rndNumber
        #     context.scene.roma_block_name_list.add()
        temp_list = []    
        for el in context.scene.roma_block_name_list:
            temp_list.append(el.id)
        last = len(context.scene.roma_block_name_list)-1
        
        context.scene.roma_block_name_list[last].id = max(temp_list)+1
        # rndNumber = float(decimal.Decimal(random.randrange(0,1000))/1000)
        # context.scene.roma_block_name_list[last].RND = rndNumber
        bpy.ops.node.update_shader_filter(filter_name="block")
        return{'FINISHED'}
    
class BLOCK_LIST_OT_MoveItem(Operator):
    bl_idname = "roma_block_name_list.move_item"
    bl_label = "Move an item in the list"

    direction: bpy.props.EnumProperty(items=(('UP', 'Up', ""),
                                              ('DOWN', 'Down', ""),))

    @classmethod
    def poll(cls, context):
        return context.scene.roma_block_name_list

    def move_index(self):
        index = bpy.context.scene.roma_block_name_list_index
        list_length = len(bpy.context.scene.roma_block_name_list) - 1 
        new_index = index + (-1 if self.direction == 'UP' else 1)

        bpy.context.scene.roma_block_name_list_index = max(0, min(new_index, list_length))

    def execute(self, context):
        roma_block_name_list = context.scene.roma_block_name_list
        index = context.scene.roma_block_name_list_index

        neighbor = index + (-1 if self.direction == 'UP' else 1)
        roma_block_name_list.move(neighbor, index)
        self.move_index()

        return{'FINISHED'}
    
# update the node "filter by block" if a new block is added or
# a block name has changed
def update_roma_filter_by_block(self, context):
    bpy.ops.node.update_shader_filter(filter_name="block")
    return None
            
class block_name_list(PropertyGroup):
    id: IntProperty(
           name="Id",
           description="Block name id",
           default = 0)
    
    name: StringProperty(
           name="Block Name",
           description="The name of the block",
           default="Block name...",
           update=update_roma_filter_by_block)
    
    # RND: FloatProperty(
    #        name="Random Value per Block",
    #        description="A random value assigned to each block",
    #        default = 0)
            
############################        ############################
############################ USE    ############################
############################        ############################

# class VIEW3D_PT_RoMa_mass_use_data(Panel):
#     bl_space_type = "PROPERTIES"
#     bl_region_type = "WINDOW"
#     bl_label = "Use"
#     bl_parent_id = "VIEW3D_PT_RoMa_mass_data"
#     bl_options = {'DEFAULT_CLOSED'}
    
#     def draw(self, context):
#         scene = context.scene
        
#         layout = self.layout
#         layout.use_property_split = True
#         layout.use_property_decorate = False  # No animation.
        
#         row = layout.row()
#         #row.label(text="Use")
#         # row.prop(context.window_manager, 'toggle_use_name', toggle=True, icon="HIDE_OFF", icon_only=True)
        
#         # is_sortable = len(scene.roma_use_name_list) > 1
#         rows = 3
#         # if is_sortable:
#         #     rows = 5
            
#         row = layout.row()
#         row.template_list("OBJECT_UL_Use", "use_list", scene,
#                         "roma_use_name_list", scene, "roma_use_name_list_index", rows = rows)
        
        
#         col = row.column(align=True)
#         col.operator("roma_use_name_list.new_item", icon='ADD', text="")
#         col.separator()
#         col.operator("roma_use_name_list.move_item", icon='TRIA_UP', text="").direction = 'UP'
#         col.operator("roma_use_name_list.move_item", icon='TRIA_DOWN', text="").direction = 'DOWN'
        
#         # row = layout.row()
#         row = layout.row(align=True)
#         index = context.scene.roma_use_name_list_index
#         # layout.label(text=()"Current use:",context.scene.roma_use_name_list[index].name))
#         # layout.label(text=str(context.scene.roma_use_name_list[index].floorToFloor))
#         # layout.label(text=str(context.scene.roma_use_name_list[index].liquidHeight))
#         layout.prop(context.scene.roma_use_name_list[index],"name", text="Name")
#         layout.prop(context.scene.roma_use_name_list[index],"floorToFloor", text="Floor to floor height")
#         row = layout.row(align=True)
#         sub = row.row()
#         sub.prop(context.scene.roma_use_name_list[index],"storeys", text="Number of storeys")
#         layout.prop(context.scene.roma_use_name_list[index],"liquid", text="Variable number of storeys")
#         if context.scene.roma_use_name_list[index].liquid:
#             sub.enabled = False
#         else:
#             sub.enabled = True
#         # if scene.roma_use_name_list_index >= 0 and scene.roma_use_name_list:
#         #     item = scene.roma_use_name_list[scene.roma_use_name_list_index]
#         #     row.prop(item, "name", icon_only=True, text="Use Name")
            
            
# class OBJECT_UL_Use(UIList):
#     def draw_item(self, context, layout, data, item, icon, active_data,
#                   active_propname, index):
       
#         custom_icon = 'COMMUNITY'

#         if self.layout_type in {'DEFAULT', 'COMPACT'}:
#             split = layout.split(factor=0.3)
#             split.label(text="Id: %d" % (item.id)) 
#             split.label(text=item.name, icon=custom_icon) 
#             # split.prop(context.scene.roma_use_name_list[index],
#             #            "name",
#             #            icon_only=True,
#             #            icon = custom_icon)
#         elif self.layout_type in {'GRID'}:
#             layout.alignment = 'CENTER'
#             layout.label(text="", icon = custom_icon)

#     def filter_items(self, context, data, propname):
#         filtered = []
#         ordered = []
#         items = getattr(data, propname)
#         filtered = [self.bitflag_filter_item] * len(items)
        
#         # for i, item in enumerate(items):
#         #     if item.id == 0:
#         #         filtered[i] &= ~self.bitflag_filter_item
#         return filtered, ordered

#     def draw_filter(self, context, layout):
#         pass
    
class USE_LIST_OT_NewItem(Operator):
    bl_idname = "roma_use_name_list.new_item"
    bl_label = "Add a new use"

    def execute(self, context): 
        context.scene.roma_use_name_list.add()
        temp_list = []    
        for el in context.scene.roma_use_name_list:
            temp_list.append(el.id)
        last = len(context.scene.roma_use_name_list)-1
        
        id = max(temp_list)+1
        context.scene.roma_use_name_list[last].id = id
        
        subIndex = context.scene.roma_typology_uses_name_list_index
        context.scene.roma_typology_uses_name_list[subIndex].name = context.scene.roma_use_name_list[last].name
        context.scene.roma_typology_uses_name_list[subIndex].id = id
        update_typology_uses_list(context)
        update_roma_masses_data(self, context)
        
        bpy.ops.node.update_gn_filter()
        bpy.ops.node.update_shader_filter(filter_name="use")
        
        
        return{'FINISHED'}
    
# class USE_LIST_OT_MoveItem(Operator):
#     bl_idname = "roma_use_name_list.move_item"
#     bl_label = "Move an item in the list"

#     direction: bpy.props.EnumProperty(items=(('UP', 'Up', ""),
#                                               ('DOWN', 'Down', ""),))

#     @classmethod
#     def poll(cls, context):
#         return context.scene.roma_use_name_list

#     def move_index(self):
#         index = bpy.context.scene.roma_use_name_list_index
#         list_length = len(bpy.context.scene.roma_use_name_list) - 1 
#         new_index = index + (-1 if self.direction == 'UP' else 1)

#         bpy.context.scene.roma_use_name_list_index = max(0, min(new_index, list_length))

#     def execute(self, context):
#         roma_use_name_list = context.scene.roma_use_name_list
#         index = context.scene.roma_use_name_list_index

#         neighbor = index + (-1 if self.direction == 'UP' else 1)
#         roma_use_name_list.move(neighbor, index)
#         self.move_index()

#         return{'FINISHED'}

# once the floor to floor height is updated, it is necessary
# to update all the heights of the existing roma masses    
def update_roma_masses_data(self, context):
    bpy.ops.wm.update_all_mesh_attributes_modal_operator('INVOKE_DEFAULT')
    return None

# update the node "filter by use" if a new use is added or
# a use name has changed
# also updates the names of roma_typology_uses_name_list_index  
def update_roma_filter_by_use(self, context):
    from . import initLists
    bpy.ops.node.update_gn_filter()
    bpy.ops.node.update_shader_filter(filter_name="use")
    # updating roma_typology_uses_name_list_index
    current_list = context.scene.roma_typology_uses_name_list
    for i, el in enumerate(current_list):
        name = context.scene.roma_use_name_list[el.id].name
        context.scene.roma_typology_uses_name_list[i].name = name
    # updating the names in bpy.context.scene.roma_obj_typology_uses_name_list
    # if they are shown in the RoMa panel in the 3dView
    usesUiList = context.scene.roma_obj_typology_uses_name_list
    subIndex = context.scene.roma_typology_uses_name_list_index
    if  len(context.scene.roma_typology_uses_name_list) == 0: 
        initLists()
    subName = context.scene.roma_typology_uses_name_list[subIndex].name
    useIndex = context.scene.roma_use_name_list.find(subName)
    for use in usesUiList:
        if use.nameId == useIndex:
            use.name = subName
            break
    return None
            
# class use_name_list(PropertyGroup):
#     id: IntProperty(
#            name="Id",
#            description="Use name id",
#            default = 0)
    
#     name: StringProperty(
#            name="Use Name",
#            description="The use of the block",
#            default = "Use name...",
#            update=update_roma_filter_by_use)
    
#     floorToFloor: FloatProperty(
#         name="Floor to floor",
#         description="Floor to floor height for the selected use",
#         min=0,
#         max=99,
#         precision=3,
#         default = 3.150,
#         update=update_roma_masses_data)

#     storeys:IntProperty(
#         name="Number of storeys",
#         description="Number of storeys for the selected use",
#         min=1,
#         max=99,
#         default = 1,
#         update=update_roma_masses_data)
    
#     liquid: BoolProperty(
#             name = "Liquid number of storeys",
#             description = "It indicates whether the number of storeys is fixed or variable",
#             default = False,
#             update=update_roma_masses_data)
    
############################            ############################
############################ TYPOLOGY   ############################
############################            ############################

class VIEW3D_PT_RoMa_mass_typology_data(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_label = "Typology"
    bl_parent_id = "VIEW3D_PT_RoMa_mass_data"
    bl_options = {'DEFAULT_CLOSED'}
    
    # if len(bpy.context.scene.roma_typology_uses_name_list) == 0: 
    #         initRomaLists("romaTypologyUsesName")
    
    def draw(self, context):
        scene = context.scene
        
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.
        
        row = layout.row()
        rows = 3
        row.template_list("OBJECT_UL_Typology", "typology_list", scene,
                        "roma_typology_name_list", scene, "roma_typology_name_list_index", rows = rows)
        
        
        col = row.column(align=True)
        col.operator("roma_typology_name_list.new_item", icon='ADD', text="")
        col.separator()
        col.operator("roma_typology_name_list.move_item", icon='TRIA_UP', text="").direction = 'UP'
        col.operator("roma_typology_name_list.move_item", icon='TRIA_DOWN', text="").direction = 'DOWN'
        
        # row = layout.row()
        # row = layout.row(align=True)
        
        # if scene.roma_typology_name_list_index >= 0 and scene.roma_typology_name_list:
        #     item = scene.roma_typology_name_list[scene.roma_typology_name_list_index]
        #     row.prop(item, "name", icon_only=True, text="Typology Name")
            
        ########## typology uses ###############
        #if scene.roma_typology_uses_name_index >= 1:
        row = layout.row()
        # index = scene.roma_typology_name_list_index
        # for el in scene.roma_typology_name_list:
        #     if el.id == index:
        #         txt = "Uses of " + el.name
        #         break
        row.label(text="Uses:")
        row = layout.row()
        rows = 3
        row = layout.row()
        row.template_list("OBJECT_UL_Typology_Uses", "typology_uses_list", scene,
                        "roma_typology_uses_name_list", scene, "roma_typology_uses_name_list_index", rows = rows)
        
        
        col = row.column(align=True)
        col.operator("roma_typology_uses_name_list.new_item", icon='ADD', text="")
        sub = col.row()
        sub.operator("roma_typology_uses_name_list.delete_item", icon='REMOVE', text="")
        if len(scene.roma_typology_uses_name_list) < 2:
            sub.enabled = False
        else:
            sub.enabled = True
            
        
        col.separator()
        col.operator("roma_typology_uses_name_list.move_item", icon='TRIA_UP', text="").direction = 'UP'
        
        col.operator("roma_typology_uses_name_list.move_item", icon='TRIA_DOWN', text="").direction = 'DOWN'

        # use editor        
        row = layout.row(align=True)
        subIndex = context.scene.roma_typology_uses_name_list_index
        subName = context.scene.roma_typology_uses_name_list[subIndex].name
        index = context.scene.roma_use_name_list.find(subName)
        col = layout.column(align=True)
        
        row = col.row(align=True)
        row.prop(context.scene, "roma_typology_uses_name", icon="COMMUNITY", icon_only=True, text="")
        row.prop(context.scene.roma_use_name_list[index],"name", text="")
        row.operator("roma_use_name_list.new_item", icon='ADD', text="")
        
        layout.prop(context.scene.roma_use_name_list[index],"floorToFloor", text="Floor to floor height")
        row = layout.row(align=True)
        sub = row.row()
        sub.prop(context.scene.roma_use_name_list[index],"storeys", text="Number of storeys")
        layout.prop(context.scene.roma_use_name_list[index],"liquid", text="Variable number of storeys")
        if context.scene.roma_use_name_list[index].liquid:
            sub.enabled = False
        else:
            sub.enabled = True
        
            
class OBJECT_UL_Typology(UIList):
    
    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):
        # global selectedTypology
        custom_icon = 'ASSET_MANAGER'

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            #update the uses list for the current typology
            
            # selected_typology_index = context.scene.roma_typology_name_list_index
            # selected_typology_id = context.scene.roma_typology_name_list[selected_typology_index].id
            # if selectedTypology != selected_typology_id:
            #     selectedTypology = selected_typology_id
            #     use_name_list = context.scene.roma_typology_uses_name_list
            #     index = context.scene.roma_typology_uses_name_list_index
            #     # use_name_list.remove(index)
                # use_name_length = len(use_name_list)
                # counter = 0
                # while counter < use_name_length:
                #     bpy.ops.roma_typology_uses_name_list.delete_item()
                #     counter +=1
                
                # print("selected one", selectedTypology, index)
                # context.scene.roma_typology_uses_name_list[index].name = "cappero"
            #print("selected typology: ", context.scene.roma_typology_name_list[selected_typology_index].id)
            
            
            split = layout.split(factor=0.5)
            split.label(text="Id: %d" % (item.id)) 
            # split.label(text=item.name, icon=custom_icon) 
            # item = context.scene.roma_typology_name_list[context.scene.roma_typology_name_list_index]
            split.prop(context.scene.roma_typology_name_list[index],
                       "name",
                       icon_only=True,
                       icon = custom_icon)
            
            
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon = custom_icon)

    def filter_items(self, context, data, propname):
        filtered = []
        ordered = []
        items = getattr(data, propname)
        filtered = [self.bitflag_filter_item] * len(items)
        
        # for i, item in enumerate(items):
        #     if item.id == 0:
        #         filtered[i] &= ~self.bitflag_filter_item
        return filtered, ordered

    def draw_filter(self, context, layout):
        pass
    
class TYPOLOGY_LIST_OT_NewItem(Operator):
    bl_idname = "roma_typology_name_list.new_item"
    bl_label = "Add a new typology"

    def execute(self, context): 
        context.scene.roma_typology_name_list.add()
        # last = len(context.scene.roma_use_name_list)-1
        # if last == 0:
        #     context.scene.roma_use_name_list[0].id = 0
        #     context.scene.roma_use_name_list[0].name = ""
        #     random.seed(datetime.now().timestamp())
        #     rndNumber = float(decimal.Decimal(random.randrange(0,10000000))/10000000)
        #     context.scene.roma_use_name_list[0].RND = rndNumber
        #     context.scene.roma_use_name_list.add()
        temp_list = []    
        for el in context.scene.roma_typology_name_list:
            temp_list.append(el.id)
        last = len(context.scene.roma_typology_name_list)-1
        
        context.scene.roma_typology_name_list[last].id = max(temp_list)+1
        
        # rndNumber = float(decimal.Decimal(random.randrange(0,1000))/1000)
        # context.scene.roma_typology_name_list[last].RND = rndNumber
        bpy.ops.node.update_shader_filter(filter_name="typology")
            
        return{'FINISHED'}
    
class TYPOLOGY_LIST_OT_MoveItem(Operator):
    bl_idname = "roma_typology_name_list.move_item"
    bl_label = "Move an item in the list"

    direction: bpy.props.EnumProperty(items=(('UP', 'Up', ""),
                                              ('DOWN', 'Down', ""),))

    @classmethod
    def poll(cls, context):
        return context.scene.roma_typology_name_list

    def move_index(self):
        index = bpy.context.scene.roma_typology_name_list_index
        list_length = len(bpy.context.scene.roma_typology_name_list) - 1 
        new_index = index + (-1 if self.direction == 'UP' else 1)

        bpy.context.scene.roma_typology_name_list_index = max(0, min(new_index, list_length))

    def execute(self, context):
        roma_typology_name_list = context.scene.roma_typology_name_list
        index = context.scene.roma_typology_name_list_index

        neighbor = index + (-1 if self.direction == 'UP' else 1)
        roma_typology_name_list.move(neighbor, index)
        self.move_index()
        
        # this is because moving up and down values, 
        # doesn't trigger update_typology_uses_function
        context.scene.roma_previous_selected_typology = -1

        return{'FINISHED'}

# update the node "filter by typology" if a new typology is added or
# a typology name has changed
def update_roma_filter_by_typology(self, context):
    bpy.ops.node.update_shader_filter(filter_name="typology")
    return None
            

    

    
class OBJECT_UL_Typology_Uses(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):
       
        custom_icon = 'COMMUNITY'
       
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            id = item.id
            if item.name != "...":
                for el in context.scene.roma_use_name_list:
                    if id == el.id:
                        # floorToFloor = round(el.floorToFloor,3)
                        storeys = el.storeys
                        liquid = el.liquid
                        break
                split = layout.split(factor=0.5)
                col1 = split.column()
                col2 = split.column()
                subSplit = col1.split(factor=0.3)
                subSplit1 = subSplit.column()
                subSplit2 = subSplit.column()
                if liquid:
                    subSplit1.label(text="Id: %d" % (item.id))
                    subSplit2.label(text="Storeys: variable")
                    # split.label(text="", icon = "MOD_LENGTH")
                else:
                    subSplit1.label(text="Id: %d" % (item.id))
                    subSplit2.label(text="Storeys: %s" % (storeys))
#             split.label(text=item.name, icon=custom_icon) 
                    
                col2.label(text=item.name)
            else:
                split = layout.split(factor=0.5)
                split.label(text="")
                split.label(text=item.name)
     

        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon = custom_icon)

    def filter_items(self, context, data, propname):
        filtered = []
        ordered = []
        items = getattr(data, propname)
        filtered = [self.bitflag_filter_item] * len(items)
        
        # for i, item in enumerate(items):
        #     if item.id == 0:
        #         filtered[i] &= ~self.bitflag_filter_item
        return filtered, ordered

    def draw_filter(self, context, layout):
        pass
    
    
class TYPOLOGY_USES_LIST_OT_NewItem(Operator):
    bl_idname = "roma_typology_uses_name_list.new_item"
    bl_label = "Add a new typology use"
    
    @classmethod
    def poll(cls, context):
        return len(context.scene.roma_typology_uses_name_list) <7

    def execute(self, context): 
        context.scene.roma_typology_uses_name_list.add()
        # last = len(context.scene.roma_use_name_list)-1
        # if last == 0:
        #     context.scene.roma_use_name_list[0].id = 0
        #     context.scene.roma_use_name_list[0].name = ""
        #     random.seed(datetime.now().timestamp())
        #     rndNumber = float(decimal.Decimal(random.randrange(0,10000000))/10000000)
        #     context.scene.roma_use_name_list[0].RND = rndNumber
        #     context.scene.roma_use_name_list.add()
        temp_list = []    
        for el in context.scene.roma_typology_uses_name_list:
            temp_list.append(el.id)
        last = len(context.scene.roma_typology_uses_name_list)-1
        
        context.scene.roma_typology_uses_name_list[last].id = max(temp_list)+1
        
        #add the new element to the typology uses list
        # add_new_element_to_typology_uses(context, context.scene.roma_typology_uses_name_list[last].id)    
        return{'FINISHED'}
    
class TYPOLOGY_USES_LIST_OT_DeleteItem(Operator):
    bl_idname = "roma_typology_uses_name_list.delete_item"
    bl_label = "Deletes an item"
    
    @classmethod
    def poll(cls, context):
        return context.scene.roma_typology_uses_name_list
        
    def execute(self, context):
        my_list = context.scene.roma_typology_uses_name_list
        index = context.scene.roma_typology_uses_name_list_index

        my_list.remove(index)
        context.scene.roma_typology_uses_name_list_index = min(max(0, index - 1), len(my_list) - 1)
        
        update_typology_uses_list(context)
        update_roma_masses_data(self, context)
        return{'FINISHED'}
    
class TYPOLOGY_USES_LIST_OT_MoveItem(Operator):
    bl_idname = "roma_typology_uses_name_list.move_item"
    bl_label = "Move an item in the list"

    direction: bpy.props.EnumProperty(items=(('UP', 'Up', ""),
                                              ('DOWN', 'Down', ""),))

    @classmethod
    def poll(cls, context):
        return context.scene.roma_typology_uses_name_list

    def move_index(self):
        index = bpy.context.scene.roma_typology_uses_name_list_index
        list_length = len(bpy.context.scene.roma_typology_uses_name_list) - 1 
        new_index = index + (-1 if self.direction == 'UP' else 1)

        bpy.context.scene.roma_typology_uses_name_list_index = max(0, min(new_index, list_length))

    def execute(self, context):
        roma_typology_uses_name_list = context.scene.roma_typology_uses_name_list
        index = context.scene.roma_typology_uses_name_list_index

        neighbor = index + (-1 if self.direction == 'UP' else 1)
        roma_typology_uses_name_list.move(neighbor, index)
        self.move_index()
        
        update_typology_uses_list(context)
        update_roma_masses_data(self, context)
        return{'FINISHED'}

# when a typology is selected, it is necessary to update the
# uses in the UIList using the ones stored in Scene.roma_typology_uses_name_list 
def update_typology_uses_UI(context):
    from . import initLists
    use_name_list = context.scene.roma_typology_uses_name_list
    # print("updating UI")

    # index = context.scene.roma_typology_uses_name_list_index
    # use_name_length = len(use_name_list)
    # if use_name_length > 0:
        # remove all the entries
        # counter = 0
        # while counter <= use_name_length:
   
    while len(use_name_list) > 0:
        # print("lenght pre", len(use_name_list))
        index = context.scene.roma_typology_uses_name_list_index
        # bpy.ops.roma_typology_uses_name_list.delete_item()
        use_name_list.remove(index)
        context.scene.roma_typology_uses_name_list_index = min(max(0, index - 1), len(use_name_list) - 1)
        # print("lenght post", len(use_name_list))
            # counter +=1
            
    # add the uses stored in the typology to the current typology use UIList        
    selected_typology_index = context.scene.roma_typology_name_list_index
    # selected_typology_id = context.scene.roma_typology_name_list[selected_typology_index].id
    if  len(context.scene.roma_typology_name_list) == 0: 
        initLists()
       
    list = context.scene.roma_typology_name_list[selected_typology_index].useList    
    # print("len", len(list))
    if len(list) > 0:
        split_list = list.split(";")
        for el in split_list:
            context.scene.roma_typology_uses_name_list.add()
            temp_list = []    
            # for el in context.scene.roma_typology_uses_name_list:
            temp_list.append(int(el))
            last = len(context.scene.roma_typology_uses_name_list)-1
            # context.scene.roma_typology_uses_name_list[last].id = max(temp_list)+1
            # look for the correspondent use name in roma_use_name_list
            for use in context.scene.roma_use_name_list:
                if int(el) == use.id:
                    context.scene.roma_typology_uses_name_list[last].id = use.id
                    context.scene.roma_typology_uses_name_list[last].name = use.name 
                    break
            
        
# when a use related to the current typology is updated in the UIList,
# it is necessary to update the relative list in Scene.roma_typology_uses_name_list
def update_typology_uses_list(context):
    selected_typology_index = context.scene.roma_typology_name_list_index
    # selected_typology_id = context.scene.roma_typology_name_list[selected_typology_index].id
    
    #the exististing list is replaced with what is in the UiList
    # print("existing", context.scene.roma_typology_name_list[selected_typology_index].useList)
    
    tmp = ""
    for el in context.scene.roma_typology_uses_name_list:
        tmp += str(el.id) + ";"
    # remove the last ";" in the string
    tmp = tmp[:-1]
    context.scene.roma_typology_name_list[selected_typology_index].useList = tmp
    # if len(context.scene.roma_typology_name_list[selected_typology_id].useList) == 0:
    #     context.scene.roma_typology_name_list[selected_typology_id].useList += str(use_id)
    # else:
    #     context.scene.roma_typology_name_list[selected_typology_id].useList += ";" + str(use_id)
    # print("updated", context.scene.roma_typology_name_list[selected_typology_index].useList)
    
    

# when the typology is selected, the relative uses listed in the UIList need to be updated in the UI
@persistent    
def update_typology_uses_function(self, context):
    # ob = bpy.data.scenes["Scene"].roma_use_name_list
    # depsgraph = bpy.context.evaluated_depsgraph_get()
    # ob_eval = ob.evaluated_get(depsgraph)
    # print("ciao", datetime.now(), depsgraph)
    scene = context.scene
    previous = scene.roma_previous_selected_typology
    current = scene.roma_typology_name_list_index
    if previous != current:
        scene.roma_previous_selected_typology = current
        update_typology_uses_UI(context)
        
# update the typology use in the UIList with the name selected
# in the drop down menu       
def update_typology_uses_name_label(self, context):
    # global useName
    scene = context.scene
    name = scene.roma_typology_uses_name
    # if the typology is newly created, the index is equal to -1 and 
    # therefore there is an out of range error
    # Also, in this case, there are no values to update
    if scene.roma_typology_uses_name_list_index > -1:
        scene.roma_typology_uses_name_list[scene.roma_typology_uses_name_list_index].name = name
        for n in scene.roma_use_name_list:
            if n.name == name:
                scene.roma_typology_uses_name_list[scene.roma_typology_uses_name_list_index].id = n.id
                update_typology_uses_list(context)
                update_roma_masses_data(self, context)
                break    
            
class typology_name_list(PropertyGroup):
    id: IntProperty(
           name="Id",
           description="Typology name id",
           default = 0)
    
    name: StringProperty(
           name="Typology Name",
           description="The typology of the block",
           default="Typology name...",
           update=update_roma_filter_by_typology)
    
    useList: StringProperty(
            name="Uses in the typology",
            description="The uses for the typology",
            default="")
            
class use_name_list(PropertyGroup):
    id: IntProperty(
           name="Id",
           description="Use name id",
           default = 0)
    
    name: StringProperty(
           name="Use Name",
           description="The use of the block",
           default = "Use name...",
           update=update_roma_filter_by_use)
    
    floorToFloor: FloatProperty(
        name="Floor to floor",
        description="Floor to floor height for the selected use",
        min=0,
        max=99,
        precision=3,
        default = 3.150,
        update=update_roma_masses_data)

    storeys:IntProperty(
        name="Number of storeys",
        description="Number of storeys for the selected use",
        min=1,
        max=99,
        default = 1,
        update=update_roma_masses_data)
    
    liquid: BoolProperty(
            name = "Liquid number of storeys",
            description = "It indicates whether the number of storeys is fixed or variable",
            default = False,
            update=update_roma_masses_data)
            
class typology_uses_name_list(PropertyGroup):
    id: IntProperty(
           name="Id",
           description="Typology use name id",
           default = 0)
    
    name: StringProperty(
           name="Typology uses name",
           description="The typology use name",
           default="...",
           update=update_roma_masses_data)
          
    
    
    # position: IntProperty(
    #        name="Use position",
    #        description="Position of the use in the typology (bottom, center, top)",
    #        default = 1)
    
############################            ############################
############################ ROOM       ############################
############################            ############################
        
        
class VIEW3D_PT_RoMa_building_data(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    # bl_category = "RoMa"
    bl_label = "Architecture Data"
    bl_parent_id = "VIEW3D_PT_RoMa_project_data"
    # bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        pass
        
############################        ############################
############################ WALL   ############################
############################        ############################
        
class VIEW3D_PT_RoMa_building_wall_data(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_label = "Wall"
    bl_parent_id = "VIEW3D_PT_RoMa_building_data"
    bl_options = {'DEFAULT_CLOSED'}      
    
    def draw(self, context):
        scene = context.scene
        
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.  
        
        row = layout.row()
       # row.label(text="Wall")
        
        # is_sortable = len(scene.roma_use_name_list) > 1
        rows = 3
        # if is_sortable:
        #     rows = 5
            
        row = layout.row()
        row.template_list("OBJECT_UL_Wall", "wall_list", scene,
                        "roma_wall_name_list", scene, "roma_wall_name_list_index", rows = rows)
        
        
        col = row.column(align=True)
        col.operator("roma_wall_name_list.new_item", icon='ADD', text="")
        col.separator()
        col.operator("roma_wall_name_list.move_item", icon='TRIA_UP', text="").direction = 'UP'
        col.operator("roma_wall_name_list.move_item", icon='TRIA_DOWN', text="").direction = 'DOWN'
        
        # row = layout.row()
        # row = layout.row(align=True)
        # layout.prop(context.scene, "roma_typology_uses_name", icon="COMMUNITY", icon_only=False, text="Type:")
        index = context.scene.roma_wall_name_list_index
        layout.prop(context.scene.roma_wall_name_list[index], "shortName", text="Short name")
        layout.prop(context.scene.roma_wall_name_list[index], "wallThickness", text="Thickness")
        layout.prop(context.scene.roma_wall_name_list[index], "wallOffset", text="Offset")
       
       
       
       
        
        # if scene.roma_wall_name_list_index >= 0 and scene.roma_wall_name_list:
        #     item = scene.roma_wall_name_list[scene.roma_wall_name_list_index]
        #     row.prop(item, "name", icon_only=True, text="Element Name")
            
            
class OBJECT_UL_Wall(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):
       
        custom_icon = 'NODE_TEXTURE'

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            split = layout.split(factor=0.5)
            split.label(text="Id: %d" % (item.id)) 
            # split.label(text=item.name, icon=custom_icon) 
            split.prop(context.scene.roma_wall_name_list[index],
                       "name",
                       icon_only=True,
                       icon = custom_icon)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon = custom_icon)

    def filter_items(self, context, data, propname):
        filtered = []
        ordered = []
        items = getattr(data, propname)
        filtered = [self.bitflag_filter_item] * len(items)
        
        # for i, item in enumerate(items):
        #     if item.id == 0:
        #         filtered[i] &= ~self.bitflag_filter_item
        return filtered, ordered

    def draw_filter(self, context, layout):
        pass
    
class WALL_LIST_OT_NewItem(Operator):
    bl_idname = "roma_wall_name_list.new_item"
    bl_label = "Add a new wall type"

    def execute(self, context): 
        context.scene.roma_wall_name_list.add()
        # last = len(context.scene.roma_use_name_list)-1
        # if last == 0:
        #     context.scene.roma_use_name_list[0].id = 0
        #     context.scene.roma_use_name_list[0].name = ""
        #     random.seed(datetime.now().timestamp())
        #     rndNumber = float(decimal.Decimal(random.randrange(0,10000000))/10000000)
        #     context.scene.roma_use_name_list[0].RND = rndNumber
        #     context.scene.roma_use_name_list.add()
        temp_list = []    
        for el in context.scene.roma_wall_name_list:
            temp_list.append(el.id)
        last = len(context.scene.roma_wall_name_list)-1
        
        context.scene.roma_wall_name_list[last].id = max(temp_list)+1
        # rndNumber = float(decimal.Decimal(random.randrange(0,10000000))/10000000)
        # context.scene.roma_use_name_list[last].RND = rndNumber
            
        return{'FINISHED'}
    
class WALL_LIST_OT_MoveItem(Operator):
    bl_idname = "roma_wall_name_list.move_item"
    bl_label = "Move an item in the list"

    direction: bpy.props.EnumProperty(items=(('UP', 'Up', ""),
                                              ('DOWN', 'Down', ""),))

    @classmethod
    def poll(cls, context):
        return context.scene.roma_wall_name_list

    def move_index(self):
        index = bpy.context.scene.roma_wall_name_list_index
        list_length = len(bpy.context.scene.roma_wall_name_list) - 1 
        new_index = index + (-1 if self.direction == 'UP' else 1)

        bpy.context.scene.roma_wall_name_list_index = max(0, min(new_index, list_length))

    def execute(self, context):
        roma_wall_name_list = context.scene.roma_wall_name_list
        index = context.scene.roma_wall_name_list_index

        neighbor = index + (-1 if self.direction == 'UP' else 1)
        roma_wall_name_list.move(neighbor, index)
        self.move_index()

        return{'FINISHED'}
            
class wall_name_list(PropertyGroup):
    id: IntProperty(
           name="Id",
           description="Wall name id",
           default = 0)
    
    name: StringProperty(
           name="Wall Name",
           description="The name of the wall",
           default="Wall type...")
    
    shortName: StringProperty(
           name="Wall Name",
           description="A short name describing the wall",
           default="WLL")
    
    wallThickness: FloatProperty(
        name="Wall thickness",
        description="The thickness of the wall",
        min=0,
        #max=99,
        precision=3,
        default = 0.300,
        # update=update_roma_masses_data
        )
    
    wallOffset: FloatProperty(
        name="Wall offset",
        description="The offset of the wall from its center line",
        min=0,
        #max=99,
        precision=3,
        default = 0,
        # update=update_roma_masses_data
        )
    
    normal: IntProperty(
           name="Wall Normal",
           description="Invert the normal of the wall",
           default = 1)
    
############################        ############################
############################ FLOOR  ############################
############################        ############################
            

class VIEW3D_PT_RoMa_building_floor_data(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_label = "Floor"
    bl_parent_id = "VIEW3D_PT_RoMa_building_data"
    bl_options = {'DEFAULT_CLOSED'}      
    
    def draw(self, context):
        scene = context.scene
        
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.
        
        row = layout.row()
        #row.label(text="Floor")
        
        # is_sortable = len(scene.roma_use_name_list) > 1
        rows = 3
        # if is_sortable:
        #     rows = 5
            
        row = layout.row()
        row.template_list("OBJECT_UL_Floor", "floor_list", scene,
                        "roma_floor_name_list", scene, "roma_floor_name_list_index", rows = rows)
        
        
        col = row.column(align=True)
        col.operator("roma_floor_name_list.new_item", icon='ADD', text="")
        col.separator()
        col.operator("roma_floor_name_list.move_item", icon='TRIA_UP', text="").direction = 'UP'
        col.operator("roma_floor_name_list.move_item", icon='TRIA_DOWN', text="").direction = 'DOWN'
        
        row = layout.row()
        row = layout.row(align=True)
        
        # if scene.roma_floor_name_list_index >= 0 and scene.roma_floor_name_list:
        #     item = scene.roma_floor_name_list[scene.roma_floor_name_list_index]
        #     row.prop(item, "name", icon_only=True, text="Floor Name")
            
          
class OBJECT_UL_Floor(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):
       
        custom_icon = 'VIEW_PERSPECTIVE'

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            split = layout.split(factor=0.5)
            split.label(text="Id: %d" % (item.id)) 
            # split.label(text=item.name, icon=custom_icon) 
            split.prop(context.scene.roma_floor_name_list[index],
                       "name",
                       icon_only=True,
                       icon = custom_icon)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon = custom_icon)

    def filter_items(self, context, data, propname):
        filtered = []
        ordered = []
        items = getattr(data, propname)
        filtered = [self.bitflag_filter_item] * len(items)
        
        # for i, item in enumerate(items):
        #     if item.id == 0:
        #         filtered[i] &= ~self.bitflag_filter_item
        return filtered, ordered

    def draw_filter(self, context, layout):
        pass
    
class FLOOR_LIST_OT_NewItem(Operator):
    bl_idname = "roma_floor_name_list.new_item"
    bl_label = "Add a new floor type"

    def execute(self, context): 
        context.scene.roma_floor_name_list.add()
        temp_list = []    
        for el in context.scene.roma_floor_name_list:
            temp_list.append(el.id)
        last = len(context.scene.roma_floor_name_list)-1
        
        context.scene.roma_floor_name_list[last].id = max(temp_list)+1
            
        return{'FINISHED'}
    
class FLOOR_LIST_OT_MoveItem(Operator):
    bl_idname = "roma_floor_name_list.move_item"
    bl_label = "Move an item in the list"

    direction: bpy.props.EnumProperty(items=(('UP', 'Up', ""),
                                              ('DOWN', 'Down', ""),))

    @classmethod
    def poll(cls, context):
        return context.scene.roma_floor_name_list

    def move_index(self):
        index = bpy.context.scene.roma_floor_name_list_index
        list_length = len(bpy.context.scene.roma_floor_name_list) - 1 
        new_index = index + (-1 if self.direction == 'UP' else 1)

        bpy.context.scene.roma_floor_name_list_index = max(0, min(new_index, list_length))

    def execute(self, context):
        roma_floor_name_list = context.scene.roma_floor_name_list
        index = context.scene.roma_floor_name_list_index

        neighbor = index + (-1 if self.direction == 'UP' else 1)
        roma_floor_name_list.move(neighbor, index)
        self.move_index()

        return{'FINISHED'}
            
class floor_name_list(PropertyGroup):
    id: IntProperty(
           name="Id",
           description="Floor name id",
           default = 0)
    
    name: StringProperty(
           name="Floor Name",
           description="The name of the floor",
           default="")
    
    # normal: IntProperty(
    #        name="Wall Normal",
    #        description="Invert the normal of the wall",
    #        default = 0) 
        


##############################              #############################
############################## other stuff  #############################
##############################              #############################
class name_with_id(PropertyGroup):
    id: IntProperty(
        name="Id",
        description="Name id",
        default = 0)
    
    name: StringProperty(
        name="Name",
        description="Name",
        default = "")
        

# def update_plot_name_toggle(self, context):
#     if self.plot_name_toggle:
#         bpy.ops.plot_name_OT('INVOKE_DEFAULT')
#     return



############################## modal operator #############################
# class TEST_OT_modal_operator(Operator):
#     bl_idname = "test.modal"
#     bl_label = "Demo modal operator"

#     def modal(self, context, event):
#         if not context.window_manager.test_toggle:
#             context.window_manager.event_timer_remove(self._timer)
#             print("done")
#             return {'FINISHED'}
#         print("pass through")
#         return {'PASS_THROUGH'}

#     def invoke(self, context, event):
#         self._timer = context.window_manager.event_timer_add(0.01, window=context.window)
#         context.window_manager.modal_handler_add(self)
#         print("modal")
#         return {'RUNNING_MODAL'}



