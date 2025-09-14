# Copyright (C) 2022-2025 Luca Saiani

# luca.saiani@gmail.com

# Created by Luca Saiani
# This is part of MaStro addon for Blender

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
from types import SimpleNamespace
# from bpy.app.handlers import persistent

from . mastro_massing import read_mesh_attributes_uses, update_mesh_face_attributes_storeys
from . mastro_wall import read_mesh_attributes_walls
from . mastro_street import read_mesh_attributes_streets

import random
# import decimal
# from datetime import datetime

# class previous_selection(PropertyGroup):
#     objectName: StringProperty(
#            name="Name",
#            description="",
#            default = "")
    
#     faceId: IntProperty(
#            name="Id",
#            description="")

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


# def initMastroLists(listName):
#     if listName == "mastroTypologyName":
#         bpy.context.scene.mastro_typology_name_list.add()
#         bpy.context.scene.mastro_typology_name_list[0].id = 0
#         bpy.context.scene.mastro_typology_name_list[0].name = "Typology name... "
#         bpy.context.scene.mastro_typology_name_list[0].useList = "0"
#     elif listName == "mastroTypologyUsesName":
#         bpy.context.scene.oma_typology_uses_name_list.add()
#         bpy.context.scene.mastro_typology_uses_name_list[0].id = 0
#         bpy.context.scene.mastro_typology_uses_name_list[0].name = bpy.context.scene.mastro_use_name_list[0].name
       

    
class update_GN_Filter_OT(Operator):
    """Update the GN node Filter by Use"""
    bl_idname = "node.update_gn_filter"
    bl_label = "Update the GN filter by Use"
    
    filter_name: bpy.props.StringProperty(name="Filter type name")
        
    def newGroup (self, groupName, type):
        # if self.filter_name == "plot": attributeName = "mastro_plot_id"
        # elif self.filter_name == "block": attributeName = "mastro_block_id"
        if self.filter_name == "use": attributeName = "mastro_use"
        elif self.filter_name == "typology": attributeName = "mastro_typology_id"
        elif self.filter_name == "wall type": attributeName = "mastro_wall_id"
        elif self.filter_name == "street type": attributeName = "mastro_street_id"
        elif self.filter_name == "plot side": attributeName = "mastro_plot_side"

        # GN group
        group = bpy.data.node_groups.new(groupName,'GeometryNodeTree')
        group.default_group_node_width = 200
        
        group_input = group.nodes.new("NodeGroupInput")
        group_output = group.nodes.new('NodeGroupOutput')
        
        # group_menu = group.nodes.new("GeometryNodeMenuSwitch")
        # group_evaluate_point = group.nodes.new("GeometryNodeFieldOnDomain")
        # group_evaluate_edge = group.nodes.new("GeometryNodeFieldOnDomain")
        # group_evaluate_face = group.nodes.new("GeometryNodeFieldOnDomain")
        # group_evaluate_spline = group.nodes.new("GeometryNodeFieldOnDomain")
        # group_evaluate_instance = group.nodes.new("GeometryNodeFieldOnDomain")


        
        # Add named attribute
        named_attribute_node = group.nodes.new(type="GeometryNodeInputNamedAttribute")
        named_attribute_node.data_type = 'INT'
        named_attribute_node.inputs[0].default_value = attributeName
            
        group_input.location = (-600,0)
        # group_menu.location = (-300,0)
        group_output.location = (600, 0)
        named_attribute_node.location = (0,-100)
        return(group)
        
        
    def execute(self, context):
        name = "MaStro Filter by " + self.filter_name.title()
                    
        if name not in bpy.data.node_groups:
            filterBy_Group = self.newGroup(name, "GN")
        else:
            filterBy_Group = bpy.data.node_groups[name]
                
        nodes = filterBy_Group.nodes
        
        # group_input = nodes["Group Input"]
        group_output = nodes["Group Output"]
        named_attribute_node = nodes["Named Attribute"]
                    
        filterNodeIds = []
        filterNodeDescriptions = []
        for node in nodes:
            if node.type == "COMPARE":
                tmpId = node.inputs[3].default_value
                filterNodeIds.append(tmpId)
                filterNodeDescriptions.append(filterBy_Group.interface.items_tree[tmpId].description)
            
        if len(filterNodeIds) == 0:
            lastId = -1           
        else:
            lastId = max(filterNodeIds)
            
        if self.filter_name == "use": listToLoop = bpy.context.scene.mastro_use_name_list
        elif self.filter_name == "typology": listToLoop = bpy.context.scene.mastro_typology_name_list
        elif self.filter_name == "wall type": listToLoop = bpy.context.scene.mastro_wall_name_list
        elif self.filter_name == "street type": listToLoop = bpy.context.scene.mastro_street_name_list
        elif self.filter_name == "plot side": listToLoop = [
                                                            SimpleNamespace(id=0, name="External Side"),
                                                            SimpleNamespace(id=1, name="Internal Side"),
                                                            SimpleNamespace(id=2, name="Lateral Side")
                                                        ]
        
        for el in listToLoop:
            if hasattr(el, "id"):
                #a new name has been added
                if el.id not in filterNodeIds:
                    if lastId >= 0:
                        node_y_location = nodes["Compare " + str(lastId)].location[1] -25
                    else:
                        node_y_location = 0
                    
                    compare_node = filterBy_Group.nodes.new(type="FunctionNodeCompare")
                    compare_node.data_type = 'INT'
                    compare_node.operation = 'EQUAL'
                    compare_node.inputs[3].default_value = el.id
                        
                    compare_node.location = (300, node_y_location-35)
                    compare_node.hide = True
                    compare_node.label="="+str(el.id)
                    compare_node.name="Compare "+str(el.id)
                    lastId = el.id
                    
                    #Add the Output Sockets and change their Default Value
                    if el.name == "":
                        if self.filter_name == "use": elName = "Use name..."
                        elif self.filter_name == "typology": elName = "Typology name..."
                        elif self.filter_name == "wall type": elName = "Wall name..."
                        elif self.filter_name == "steet type": lelName = "Street name..."
                    else:
                        elName = el.name
                    descr = "id: " + str(el.id) + " - " + elName
                    filterBy_Group.interface.new_socket(name=elName,description=descr,in_out ="OUTPUT", socket_type="NodeSocketBool")
            
                    #Add Links
                    index = len(group_output.inputs) -2
                    filterBy_Group.links.new(named_attribute_node.outputs[0], compare_node.inputs[2])
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
        if self.filter_name == "plot": attributeName = "mastro_plot_id"
        elif self.filter_name == "block": attributeName = "mastro_block_id"
        elif self.filter_name == "use": attributeName = "mastro_use"
        elif self.filter_name == "typology": attributeName = "mastro_typology_id"
        
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
        #     if type == "GN": name = "MaStro Geometry Filter by " + self.filter_name
        #     else: name = "MaStro Shader Filter by " + self.filter_name
        name = "MaStro Filter by " + self.filter_name.title()

        if name not in bpy.data.node_groups:
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
        
        
        if self.filter_name == "plot": listToLoop = bpy.context.scene.mastro_plot_name_list
        elif self.filter_name == "block": listToLoop = bpy.context.scene.mastro_block_name_list
        elif self.filter_name == "use": listToLoop = bpy.context.scene.mastro_use_name_list
        elif self.filter_name == "typology": listToLoop = bpy.context.scene.mastro_typology_name_list
        
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
                    filterBy_Group.links.new(named_attribute_node.outputs[0], compare_node.inputs[0])
                    filterBy_Group.links.new(compare_node.outputs[0], group_output.inputs[index])

                # a name has been renamed
                elif ("id: " + str(el.id) + " - " + str(el.name)) not in filterNodeDescriptions:
                    for i, desc in enumerate(filterNodeDescriptions):
                        if i == int(el.id):
                            filterBy_Group.interface.items_tree[i].name = str(el.name)
                            filterBy_Group.interface.items_tree[i].description = "id: " + str(el.id) + " - " + str(el.name)
        return {'FINISHED'}
    

class VIEW3D_PT_MaStro_project_data(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    # bl_category = "MaStro"
    bl_label = "MaStro"
    bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        # obj = context.object

        # col = layout.column(align=True)
        # col.prop(context.window_manager, 'toggle_selection_overlay', icon_only=False)
        # layout.separator()


class VIEW3D_PT_MaStro_show_data(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    # bl_category = "MaStro"
    bl_label = "Show Overlays"
    bl_parent_id = "VIEW3D_PT_MaStro_project_data"
    # bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 0
    
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
        col = layout.column(heading="Plot & Mass", align=True)
        col.prop(context.window_manager, 'toggle_storey_number', icon_only=False)
        col.separator()
        col.prop(context.window_manager, 'toggle_typology_name', icon_only=False)
        col.prop(context.window_manager, 'toggle_plot_typology_color', icon_only=False)
        col.separator()
        col.prop(context.window_manager, 'toggle_plot_normal', icon_only=False)
        col.separator()
        col.prop(context.window_manager, 'toggle_block_name', icon_only=False)
        col.prop(context.window_manager, 'toggle_plot_name', icon_only=False)
        
        # col = layout.column(heading="Plot", align=True)
        
        
        # col.prop(context.window_manager, 'toggle_storey_number', icon_only=False)
        # col.prop(context.window_manager, 'toggle_typology_name', icon_only=False)
        # col.prop(context.window_manager, 'toggle_block_name', icon_only=False)
        # col.prop(context.window_manager, 'toggle_plot_name', icon_only=False)
        
        # col.separator()
        col = layout.column(heading="Wall", align = True)
        col.prop(context.window_manager, 'toggle_wall_type', icon_only=False)
        col.prop(context.window_manager, 'toggle_wall_normal', icon_only=False)
        # col.separator()
        col = layout.column(heading="Floor", align = True)
        col.prop(context.window_manager, 'toggle_floor_name', icon_only=False)
        col = layout.column(heading="Street", align=True)
        col.prop(context.window_manager, 'toggle_street_color', icon_only=False)
        
############################      ############################
############################ MASS ############################
############################      ############################
           
class VIEW3D_PT_MaStro_mass_data(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    # bl_category = "MaStro"
    bl_label = ""
    bl_parent_id = "VIEW3D_PT_MaStro_project_data"
    # bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 1

    
    # @classmethod
    # def poll(cls, context):
    #     return (context.object is not None)
    
    def draw_header(self, context):
        layout = self.layout
        # split = layout.split(factor=.9)
        row = layout.row()
        row.label(text="Mass")
        # row.prop(context.window_manager, "toggle_auto_update_mass_data", text="", icon="FILE_REFRESH")
        
        
    def draw(self, context):
        pass
      
############################        ############################
############################ PLOT   ############################
############################        ############################ 
            
class VIEW3D_PT_MaStro_mass_plot_data(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_label = "Plot"
    bl_parent_id = "VIEW3D_PT_MaStro_mass_data"
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
                        "mastro_plot_name_list", scene, "mastro_plot_name_list_index", rows = rows)
        
        
        col = row.column(align=True)
        col.operator("mastro_plot_name_list.new_item", icon='ADD', text="")
        # col.operator("mastro_wall_type_list.delete_item", icon='REMOVE', text="")
        col.separator()
        col.operator("mastro_plot_name_list.move_item", icon='TRIA_UP', text="").direction = 'UP'
        col.operator("mastro_plot_name_list.move_item", icon='TRIA_DOWN', text="").direction = 'DOWN'
        
        # row = layout.row()
        # row = layout.row(align=True)
        # row.prop(context.scene, "mastro_plot_names", icon="MOD_BOOLEAN", icon_only=True, text="")
        # row.operator("scene.add_plot_name", icon="ADD", text="New")
        
        # if scene.mastro_plot_name_list_index >= 0 and scene.mastro_plot_name_list:
        #     item = scene.mastro_plot_name_list[scene.mastro_plot_name_list_index]
        #     row.prop(item, "name", icon_only=True, text="Plot Name")
            
        # row.prop(item, "index")
        
class OBJECT_UL_Plot(UIList):
    """Plot name UIList."""
    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):
       
        # We could write some code to decide which icon to use here...
        custom_icon = 'MOD_BOOLEAN'

        # Make sure your code supports all 3 layout types
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            
            # split.label(text="Index: %d" % (index))
            
            split = layout.split(factor=0.4)
            split.label(text="Id: %d" % (item.id)) 
            # split.label(text=item.name, icon=custom_icon) 
            split.prop(context.scene.mastro_plot_name_list[index],
                       "name",
                       icon_only=True,
                       icon = custom_icon)
            
            # layout.alignment = 'LEFT'
            # layout.label(text=item.name, icon="MOD_BOOLEAN")
            
            
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon = custom_icon)

        # self.filter_zero_id(context, data, "mastro_plot_name_list")


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
    bl_idname = "mastro_plot_name_list.new_item"
    bl_label = "Add a new plot"

    def execute(self, context): 
        context.scene.mastro_plot_name_list.add()
        # last = len(context.scene.mastro_plot_name_list)-1
        # if last == 0:
        #     context.scene.mastro_plot_name_list[0].id = 0
        #     context.scene.mastro_plot_name_list[0].name = ""
        #     random.seed(datetime.now().timestamp())
        #     rndNumber = float(decimal.Decimal(random.randrange(0,10000000))/10000000)
        #     context.scene.mastro_plot_name_list[0].RND = rndNumber
        #     context.scene.mastro_plot_name_list.add()
        temp_list = []    
        for el in context.scene.mastro_plot_name_list:
            temp_list.append(el.id)
        last = len(context.scene.mastro_plot_name_list)-1
        
        context.scene.mastro_plot_name_list[last].id = max(temp_list)+1
        # rndNumber = float(decimal.Decimal(random.randrange(0,1000))/1000)
        # context.scene.mastro_plot_name_list[last].RND = rndNumber
        bpy.ops.node.update_shader_filter(filter_name="plot")   
        return{'FINISHED'}
    
class PLOT_LIST_OT_MoveItem(Operator):
    bl_idname = "mastro_plot_name_list.move_item"
    bl_label = "Move an item in the list"

    direction: bpy.props.EnumProperty(items=(('UP', 'Up', ""),
                                              ('DOWN', 'Down', ""),))

    @classmethod
    def poll(cls, context):
        return context.scene.mastro_plot_name_list

    def move_index(self):
        index = bpy.context.scene.mastro_plot_name_list_index
        list_length = len(bpy.context.scene.mastro_plot_name_list) - 1 
        new_index = index + (-1 if self.direction == 'UP' else 1)

        bpy.context.scene.mastro_plot_name_list_index = max(0, min(new_index, list_length))

    def execute(self, context):
        mastro_plot_name_list = context.scene.mastro_plot_name_list
        index = context.scene.mastro_plot_name_list_index

        neighbor = index + (-1 if self.direction == 'UP' else 1)
        mastro_plot_name_list.move(neighbor, index)
        self.move_index()

        return{'FINISHED'}
    
# update the node "filter by plot" if a new plot is added or
# a plot name has changed
def update_mastro_filter_by_plot(self, context):
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
           update=update_mastro_filter_by_plot)
    
    # RND: FloatProperty(
    #        name="Random Value per Plot",
    #        description="A random value assigned to each plot",
    #        default = 0)
        
############################        ############################
############################ BLOCK  ############################
############################        ############################

    
class VIEW3D_PT_MaStro_mass_block_data(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_label = "Block"
    bl_parent_id = "VIEW3D_PT_MaStro_mass_data"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        scene = context.scene
        
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.
        
        row = layout.row()
        
        #row.label(text="Block")
        # row.prop(context.window_manager, 'toggle_block_name', toggle=True, icon="HIDE_OFF", icon_only=True)
        
        # is_sortable = len(scene.mastro_block_name_list) > 1
        rows = 3
        # if is_sortable:
        #     rows = 5
            
        row = layout.row()
        row.template_list("OBJECT_UL_Block", "block_list", scene,
                        "mastro_block_name_list", scene, "mastro_block_name_list_index", rows = rows)
        
        
        col = row.column(align=True)
        col.operator("mastro_block_name_list.new_item", icon='ADD', text="")
        col.separator()
        col.operator("mastro_block_name_list.move_item", icon='TRIA_UP', text="").direction = 'UP'
        col.operator("mastro_block_name_list.move_item", icon='TRIA_DOWN', text="").direction = 'DOWN'
        
        # row = layout.row()
        # row = layout.row(align=True)
        
        # if scene.mastro_block_name_list_index >= 0 and scene.mastro_block_name_list:
        #     item = scene.mastro_block_name_list[scene.mastro_block_name_list_index]
        #     row.prop(item, "name", icon_only=True, text="Block Name")
            
            
class OBJECT_UL_Block(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):
       
        custom_icon = 'HOME'

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            split = layout.split(factor=0.4)
            split.label(text="Id: %d" % (item.id)) 
            # split.label(text=item.name, icon=custom_icon) 
            split.prop(context.scene.mastro_block_name_list[index],
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
    bl_idname = "mastro_block_name_list.new_item"
    bl_label = "Add a new block"

    def execute(self, context): 
        context.scene.mastro_block_name_list.add()
        # last = len(context.scene.mastro_block_name_list)-1
        # if last == 0:
        #     context.scene.mastro_block_name_list[0].id = 0
        #     context.scene.mastro_block_name_list[0].name = ""
        #     random.seed(datetime.now().timestamp())
        #     rndNumber = float(decimal.Decimal(random.randrange(0,10000000))/10000000)
        #     context.scene.mastro_block_name_list[0].RND = rndNumber
        #     context.scene.mastro_block_name_list.add()
        temp_list = []    
        for el in context.scene.mastro_block_name_list:
            temp_list.append(el.id)
        last = len(context.scene.mastro_block_name_list)-1
        
        context.scene.mastro_block_name_list[last].id = max(temp_list)+1
        # rndNumber = float(decimal.Decimal(random.randrange(0,1000))/1000)
        # context.scene.mastro_block_name_list[last].RND = rndNumber
        bpy.ops.node.update_shader_filter(filter_name="block")
        return{'FINISHED'}
    
class BLOCK_LIST_OT_MoveItem(Operator):
    bl_idname = "mastro_block_name_list.move_item"
    bl_label = "Move an item in the list"

    direction: bpy.props.EnumProperty(items=(('UP', 'Up', ""),
                                              ('DOWN', 'Down', ""),))

    @classmethod
    def poll(cls, context):
        return context.scene.mastro_block_name_list

    def move_index(self):
        index = bpy.context.scene.mastro_block_name_list_index
        list_length = len(bpy.context.scene.mastro_block_name_list) - 1 
        new_index = index + (-1 if self.direction == 'UP' else 1)

        bpy.context.scene.mastro_block_name_list_index = max(0, min(new_index, list_length))

    def execute(self, context):
        mastro_block_name_list = context.scene.mastro_block_name_list
        index = context.scene.mastro_block_name_list_index

        neighbor = index + (-1 if self.direction == 'UP' else 1)
        mastro_block_name_list.move(neighbor, index)
        self.move_index()

        return{'FINISHED'}
    
# update the node "filter by block" if a new block is added or
# a block name has changed
def update_mastro_filter_by_block(self, context):
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
           update=update_mastro_filter_by_block)
    

    

    
# class USE_LIST_OT_MoveItem(Operator):
#     bl_idname = "mastro_use_name_list.move_item"
#     bl_label = "Move an item in the list"

#     direction: bpy.props.EnumProperty(items=(('UP', 'Up', ""),
#                                               ('DOWN', 'Down', ""),))

#     @classmethod
#     def poll(cls, context):
#         return context.scene.mastro_use_name_list

#     def move_index(self):
#         index = bpy.context.scene.mastro_use_name_list_index
#         list_length = len(bpy.context.scene.mastro_use_name_list) - 1 
#         new_index = index + (-1 if self.direction == 'UP' else 1)

#         bpy.context.scene.mastro_use_name_list_index = max(0, min(new_index, list_length))

#     def execute(self, context):
#         mastro_use_name_list = context.scene.mastro_use_name_list
#         index = context.scene.mastro_use_name_list_index

#         neighbor = index + (-1 if self.direction == 'UP' else 1)
#         mastro_use_name_list.move(neighbor, index)
#         self.move_index()

#         return{'FINISHED'}



# update the node "filter by use" if a new use is added or
# a use name has changed
# also updates the names of mastro_typology_uses_name_list_index  
def update_mastro_filter_by_use(self, context):
    from . import initLists
    bpy.ops.node.update_gn_filter(filter_name="use")
    bpy.ops.node.update_shader_filter(filter_name="use")
    
    # updating mastro_typology_uses_name_list_index
    current_list = context.scene.mastro_typology_uses_name_list
    for i, el in enumerate(current_list):
        name = context.scene.mastro_use_name_list[el.id].name
        context.scene.mastro_typology_uses_name_list[i].name = name
    # updating the names in bpy.context.scene.mastro_obj_typology_uses_name_list
    # if they are shown in the MaStro panel in the 3dView
    usesUiList = context.scene.mastro_obj_typology_uses_name_list
    subIndex = context.scene.mastro_typology_uses_name_list_index
    if  len(context.scene.mastro_typology_uses_name_list) == 0: 
        initLists()
    subName = context.scene.mastro_typology_uses_name_list[subIndex].name
    useIndex = context.scene.mastro_use_name_list.find(subName)
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
#            update=update_mastro_filter_by_use)
    
#     floorToFloor: FloatProperty(
#         name="Floor to floor",
#         description="Floor to floor height for the selected use",
#         min=0,
#         max=99,
#         precision=3,
#         default = 3.150,
#         update=update_mastro_masses_data)

#     storeys:IntProperty(
#         name="Number of storeys",
#         description="Number of storeys for the selected use",
#         min=1,
#         max=99,
#         default = 1,
#         update=update_mastro_masses_data)
    
#     liquid: BoolProperty(
#             name = "Liquid number of storeys",
#             description = "It indicates whether the number of storeys is fixed or variable",
#             default = False,
#             update=update_mastro_masses_data)
    
############################            ############################
############################ TYPOLOGY   ############################
############################            ############################

class VIEW3D_PT_MaStro_mass_typology_data(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_label = "Typology"
    bl_parent_id = "VIEW3D_PT_MaStro_mass_data"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        scene = context.scene
        
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.
        
        row = layout.row()
        rows = 3
        row.template_list("OBJECT_UL_Typology", "typology_list", scene,
                        "mastro_typology_name_list", scene, "mastro_typology_name_list_index", rows = rows)
        
        
        col = row.column(align=True)
        col.operator("mastro_typology_name_list.new_item", icon='ADD', text="")
        col.operator("mastro_typology_name_list.duplicate_item", icon='COPYDOWN', text="")
        col.separator()
        col.operator("mastro_typology_name_list.move_item", icon='TRIA_UP', text="").direction = 'UP'
        col.operator("mastro_typology_name_list.move_item", icon='TRIA_DOWN', text="").direction = 'DOWN'
            
        ########## typology uses ###############
        row = layout.row()
        row.label(text="Uses:")
        row = layout.row()
        rows = 3
        row = layout.row()
        row.template_list("OBJECT_UL_Typology_Uses", "typology_uses_list", scene,
                        "mastro_typology_uses_name_list", scene, "mastro_typology_uses_name_list_index", rows = rows)
        
        
        col = row.column(align=True)
        col.operator("mastro_typology_uses_name_list.new_item", icon='ADD', text="")
        sub = col.row()
        sub.operator("mastro_typology_uses_name_list.delete_item", icon='REMOVE', text="")
        if len(scene.mastro_typology_uses_name_list) < 2:
            sub.enabled = False
        else:
            sub.enabled = True
            
        
        col.separator()
        col.operator("mastro_typology_uses_name_list.move_item", icon='TRIA_UP', text="").direction = 'UP'
        
        col.operator("mastro_typology_uses_name_list.move_item", icon='TRIA_DOWN', text="").direction = 'DOWN'

        # use editor        
        row = layout.row(align=True)
        subIndex = context.scene.mastro_typology_uses_name_list_index
        subName = context.scene.mastro_typology_uses_name_list[subIndex].name
        index = context.scene.mastro_use_name_list.find(subName)
        col = layout.column(align=True)
        
        row = col.row(align=True)
       
        row.prop(context.scene, "mastro_typology_uses_name", icon="COMMUNITY", icon_only=True, text="")
        row.prop(context.scene.mastro_use_name_list[index],"name", text="")
        row.operator("mastro_use_name_list.new_item", icon='ADD', text="")
        
        layout.prop(context.scene.mastro_use_name_list[index],"floorToFloor", text="Floor to floor height")
        row = layout.row(align=True)
        sub = row.row()
        sub.prop(context.scene.mastro_use_name_list[index],"storeys", text="Number of storeys")
        layout.prop(context.scene.mastro_use_name_list[index],"liquid", text="Variable number of storeys")
        if context.scene.mastro_use_name_list[index].liquid:
            sub.enabled = False
        else:
            sub.enabled = True
        layout.prop(context.scene.mastro_use_name_list[index],"void", text="Void")
        # sub = layout.row()
        # sub.active = not(context.window_manager.toggle_auto_update_mass_data)
        # sub.prop(context.scene.mastro_use_name_list[index],"void", text="Update")
        # sub.operator("object.update_all_mastro_meshes_attributes").attributeToUpdate="all"
        row = layout.row(align=True)
        
        row.operator("object.update_all_mastro_meshes_attributes").attributeToUpdate="all"
        row.prop(context.window_manager, "toggle_auto_update_mass_data", text="", icon="FILE_REFRESH")
        
            
            
class OBJECT_UL_Typology(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):
        # global selectedTypology
        custom_icon = 'ASSET_MANAGER'

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            split = layout.split(factor=0.4)
            sub = split.split()
            sub.label(text="Id: %d" % (item.id)) 
            sub.prop(context.scene.mastro_typology_name_list[index], "typologyEdgeColor", text="")
            split.prop(context.scene.mastro_typology_name_list[index],
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
    '''Add a new typology'''
    bl_idname = "mastro_typology_name_list.new_item"
    bl_label = "New typology"

    def execute(self, context): 
        context.scene.mastro_typology_name_list.add()
        temp_list = []    
        for el in context.scene.mastro_typology_name_list:
            temp_list.append(el.id)
        last = len(context.scene.mastro_typology_name_list)-1
        context.scene.mastro_typology_name_list[last].id = max(temp_list)+1
        context.scene.mastro_typology_name_list[last].typologyEdgeColor = [random.random(), random.random(), random.random()]
        # add a use to the newly created typology
        current_typology_id = context.scene.mastro_typology_name_list[last].id
        bpy.context.scene.mastro_typology_name_list[current_typology_id].useList = "0"
        # bpy.ops.mastro_typology_uses_name_list.new_item()
        
        bpy.ops.node.update_shader_filter(filter_name="typology")
        # update the filter shader
        return{'FINISHED'}


class TYPOLOGY_LIST_OT_DuplicateItem(Operator):
    '''Make a duplicate of the current typology and its uses'''
    bl_idname = "mastro_typology_name_list.duplicate_item"
    bl_label = "Duplicate typology"

    def execute(self, context): 
        # get the index of the current element
        index = context.scene.mastro_typology_name_list_index
        nameToCopy = context.scene.mastro_typology_name_list[index].name
        usesToCopy = context.scene.mastro_typology_name_list[index].useList
        # create a new entry
        context.scene.mastro_typology_name_list.add()
        temp_list = []    
        for el in context.scene.mastro_typology_name_list:
            temp_list.append(el.id)
        last = len(context.scene.mastro_typology_name_list)-1
        context.scene.mastro_typology_name_list[last].id = max(temp_list)+1
        # copy data to the new entry
        context.scene.mastro_typology_name_list[last].name = nameToCopy + " copy"
        context.scene.mastro_typology_name_list[last].useList = usesToCopy
        context.scene.mastro_typology_name_list[last].typologyEdgeColor = [random.random(), random.random(), random.random()]
        
        bpy.ops.node.update_gn_filter(filter_name="typology")
        bpy.ops.node.update_shader_filter(filter_name="typology")
        return{'FINISHED'}
    
class TYPOLOGY_LIST_OT_MoveItem(Operator):
    '''Move the selected typology up or down in the list'''
    bl_idname = "mastro_typology_name_list.move_item"
    bl_label = "Move typology"

    direction: bpy.props.EnumProperty(items=(('UP', 'Up', ""),
                                              ('DOWN', 'Down', ""),))

    @classmethod
    def poll(cls, context):
        return context.scene.mastro_typology_name_list

    def move_index(self):
        index = bpy.context.scene.mastro_typology_name_list_index
        list_length = len(bpy.context.scene.mastro_typology_name_list) - 1 
        new_index = index + (-1 if self.direction == 'UP' else 1)

        bpy.context.scene.mastro_typology_name_list_index = max(0, min(new_index, list_length))

    def execute(self, context):
        mastro_typology_name_list = context.scene.mastro_typology_name_list
        index = context.scene.mastro_typology_name_list_index

        neighbor = index + (-1 if self.direction == 'UP' else 1)
        mastro_typology_name_list.move(neighbor, index)
        self.move_index()
        
        # this is because moving up and down values, 
        # doesn't trigger update_typology_uses_function
        context.scene.mastro_previous_selected_typology = -1

        return{'FINISHED'}

# update the node "filter by typology" if a new typology is added or
# a typology name has changed
def update_mastro_filter_by_typology(self, context):
    bpy.ops.node.update_gn_filter(filter_name="typology")
    bpy.ops.node.update_shader_filter(filter_name="typology")
    return None

# show the uses related to the selected typology    
class OBJECT_UL_Typology_Uses(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):
        custom_icon = 'COMMUNITY'

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            id = item.id
            if item.name != "...":
                for el in context.scene.mastro_use_name_list:
                    if id == el.id:
                        # floorToFloor = round(el.floorToFloor,3)
                        storeys = el.storeys
                        liquid = el.liquid
                        break
                split = layout.split(factor=0.4)
                col1 = split.column()
                col2 = split.column()
                subSplit = col1.split(factor=0.4)
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
                split = layout.split(factor=0.4)
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
    
# Add a new use to the list of uses of the selected typology. 
# Uses are limited to seven uses for each typology
class TYPOLOGY_USES_LIST_OT_NewItem(Operator):
    '''Add a new use to the typology. 
The number of uses is limited to 7 for each typology'''
    bl_idname = "mastro_typology_uses_name_list.new_item"
    bl_label = "Add use"
    
    @classmethod
    def poll(cls, context):
        return len(context.scene.mastro_typology_uses_name_list) <7

    def execute(self, context): 
        context.scene.mastro_typology_uses_name_list.add()
        temp_list = []    
        for el in context.scene.mastro_typology_uses_name_list:
            temp_list.append(el.id)
        last = len(context.scene.mastro_typology_uses_name_list)-1
        
        context.scene.mastro_typology_uses_name_list[last].id = max(temp_list)+1
        context.scene.mastro_street_name_list[last].typologyEdgeColor = [random.random(), random.random(), random.random()]
        return{'FINISHED'}

class TYPOLOGY_USES_LIST_OT_DeleteItem(Operator):
    '''Remove the use from the current typology'''
    bl_idname = "mastro_typology_uses_name_list.delete_item"
    bl_label = "Remove"
    
    @classmethod
    def poll(cls, context):
        return context.scene.mastro_typology_uses_name_list
        
    def execute(self, context):
        my_list = context.scene.mastro_typology_uses_name_list
        index = context.scene.mastro_typology_uses_name_list_index

        my_list.remove(index)
        context.scene.mastro_typology_uses_name_list_index = min(max(0, index - 1), len(my_list) - 1)
        
        update_typology_uses_list(context)
        return{'FINISHED'}
    
# Move the selected use up or down in the list
class TYPOLOGY_USES_LIST_OT_MoveItem(Operator):
    '''Move the selected use up or down in the list'''
    bl_idname = "mastro_typology_uses_name_list.move_item"
    bl_label = "Move use"

    direction: bpy.props.EnumProperty(items=(('UP', 'Up', ""),
                                              ('DOWN', 'Down', ""),))

    @classmethod
    def poll(cls, context):
        return context.scene.mastro_typology_uses_name_list

    def move_index(self):
        index = bpy.context.scene.mastro_typology_uses_name_list_index
        list_length = len(bpy.context.scene.mastro_typology_uses_name_list) - 1 
        new_index = index + (-1 if self.direction == 'UP' else 1)

        bpy.context.scene.mastro_typology_uses_name_list_index = max(0, min(new_index, list_length))

    def execute(self, context):
        mastro_typology_uses_name_list = context.scene.mastro_typology_uses_name_list
        index = context.scene.mastro_typology_uses_name_list_index

        neighbor = index + (-1 if self.direction == 'UP' else 1)
        mastro_typology_uses_name_list.move(neighbor, index)
        self.move_index()
        
        update_typology_uses_list(context)
        return{'FINISHED'}

# Add a new use to the list of the uses for the current project
class USE_LIST_OT_NewItem(Operator):
    '''Add a new use'''
    bl_idname = "mastro_use_name_list.new_item"
    bl_label = "New use"

    def execute(self, context): 
        context.scene.mastro_use_name_list.add()
        temp_list = []    
        for el in context.scene.mastro_use_name_list:
            temp_list.append(el.id)
        last = len(context.scene.mastro_use_name_list)-1
        
        id = max(temp_list)+1
        context.scene.mastro_use_name_list[last].id = id
        
        subIndex = context.scene.mastro_typology_uses_name_list_index
        context.scene.mastro_typology_uses_name_list[subIndex].name = context.scene.mastro_use_name_list[last].name
        context.scene.mastro_typology_uses_name_list[subIndex].id = id
        update_typology_uses_list(context)
        
        bpy.ops.node.update_gn_filter(filter_name="use")
        bpy.ops.node.update_shader_filter(filter_name="use")
        return{'FINISHED'}

# # when a typology is selected, it is necessary to update the
# # uses in the UIList using the ones stored in Scene.mastro_typology_uses_name_list 
class UPDATE_USE_LIST_OT(Operator):
    bl_idname = "ui.mastro_update_use_list"
    bl_label = "Update Use List"
    
    def execute(self, context):
        scene = context.scene
        # previous = scene.mastro_previous_selected_typology
        # current = scene.mastro_typology_name_list_index
        # if previous != current:
        scene.mastro_previous_selected_typology = scene.mastro_typology_name_list_index
        use_name_list = scene.mastro_typology_uses_name_list
        while len(use_name_list) > 0:
            index = scene.mastro_typology_uses_name_list_index
            use_name_list.remove(index)
            scene.mastro_typology_uses_name_list_index = min(max(0, index - 1), len(use_name_list) - 1)
        # add the uses stored in the typology to the current typology use UIList        
        selected_typology_index = scene.mastro_typology_name_list_index
        if len(scene.mastro_typology_name_list) > 0:
            list = scene.mastro_typology_name_list[selected_typology_index].useList    
            split_list = list.split(";")
            for el in split_list:
                scene.mastro_typology_uses_name_list.add()
                temp_list = []    
                temp_list.append(int(el))
                last = len(scene.mastro_typology_uses_name_list)-1
                # look for the correspondent use name in mastro_use_name_list
                for use in scene.mastro_use_name_list:
                    if int(el) == use.id:
                        scene.mastro_typology_uses_name_list[last].id = use.id
                        scene.mastro_typology_uses_name_list[last].name = use.name 
                        break
        return{'FINISHED'}
            
        
# when a use related to the current typology is updated in the UIList,
# it is necessary to update the relative list in Scene.mastro_typology_uses_name_list
def update_typology_uses_list(context):
    selected_typology_index = context.scene.mastro_typology_name_list_index
    # the exististing list is replaced with what is in the UiList
    # the format of the list is 2;5;1 with numbers indicating the Id of the use
    tmp = ""
    for el in context.scene.mastro_typology_uses_name_list:
        tmp += str(el.id) + ";"
    # remove the last ";" in the string
    tmp = tmp[:-1]
    context.scene.mastro_typology_name_list[selected_typology_index].useList = tmp
        
# update the typology use in the UIList with the name selected
# in the drop down menu in the Typology Uses UI
def update_typology_uses_name_label(self, context):
    scene = context.scene
    name = scene.mastro_typology_uses_name
    # if the typology is newly created, the index is equal to -1 and 
    # therefore there is an out of range error
    # Also, in this case, there are no values to update
    if scene.mastro_typology_uses_name_list_index > -1:
        scene.mastro_typology_uses_name_list[scene.mastro_typology_uses_name_list_index].name = name
        for n in scene.mastro_use_name_list:
            if n.name == name:
                scene.mastro_typology_uses_name_list[scene.mastro_typology_uses_name_list_index].id = n.id
                update_typology_uses_list(context)
                break
            
# When typology or use is edited/changed in the UI, it is necessary
# to update all the existing MaStro meshes with the updated data
# this is for useList
def update_all_mastro_meshes_useList(self, context):
    if context.window_manager.toggle_auto_update_mass_data:
        updates = "all"
        bpy.ops.object.update_all_mastro_meshes_attributes(attributeToUpdate=updates)

# this is for the floor to floor height
def update_all_mastro_meshes_floorToFloor(self, context):
    if context.window_manager.toggle_auto_update_mass_data:
        updates = "floorToFloor"
        bpy.ops.object.update_all_mastro_meshes_attributes(attributeToUpdate=updates)
    
# this is for the number of storeys
def update_all_mastro_meshes_numberOfStoreys(self, context):
    if context.window_manager.toggle_auto_update_mass_data:
        updates = "numberOfStoreys"
        bpy.ops.object.update_all_mastro_meshes_attributes(attributeToUpdate=updates)
    
# this is for the void
def update_all_mastro_meshes_void(self, context):
    if context.window_manager.toggle_auto_update_mass_data:
        updates = "void"
        bpy.ops.object.update_all_mastro_meshes_attributes(attributeToUpdate=updates)
        
# this is for the wall thickness
def update_all_mastro_wall_thickness(self, context):
    updates = "wall_thickness"
    bpy.ops.object.update_all_mastro_meshes_attributes(attributeToUpdate=updates)
    
# this is for the wall offset
def update_all_mastro_wall_offset(self, context):
    updates = "wall_offset"
    bpy.ops.object.update_all_mastro_meshes_attributes(attributeToUpdate=updates)

        
# Operator to update the attributes of all the MaStro meshes in the scene        
class OBJECT_OT_update_all_MaStro_meshes_attributes(Operator):
    bl_idname = "object.update_all_mastro_meshes_attributes"
    # bl_label = "Update the attributes of all the MaStro meshes in the scene"
    bl_label = "Update"
    bl_options = {'REGISTER', 'UNDO'}
    
    attributeToUpdate: bpy.props.StringProperty(name="Attribute to update")
    
    def execute(self, context):
        objs = bpy.data.objects
        # get the current active object
        activeObj = bpy.context.active_object
        if hasattr(activeObj, "type"):
            activeObjMode = activeObj.mode
            
        for obj in objs:
            if obj is not None and obj.type == 'MESH' and "MaStro object" in obj.data and "MaStro mass" in obj.data:
                # it is necessary to set the object to visibile in order to make it active
                if obj.visible_get():
                    alreadyVisible = True
                else:
                    alreadyVisible = False
                    obj.hide_set(False)
                
                # check if the collection is visible or not
                collections = obj.users_collection
                used_collection = False
                alreadyVisibleCollection = False
                for collection in collections:
                    if not collection.hide_viewport:
                        used_collection = True
                        alreadyVisibleCollection = True
                        break
                    else:
                        collection.hide_viewport = False
                        layer_collection = bpy.context.view_layer.layer_collection.children.get(collection.name)
                        if hasattr(layer_collection, "exclude"):
                            layer_collection.exclude = False
                            used_collection = True
                            break
                # Only the linked objects are updated
                if used_collection == True:
                    # bpy.context.scene.collection.children.link(collection)
                    # print(f"Touching {obj.name}")
                    bpy.context.view_layer.objects.active = obj
                    mesh = obj.data
                    objMode = obj.mode
                    bpy.ops.object.mode_set(mode='OBJECT')
                    
                    faces = context.active_object.data.polygons
                    if hasattr(mesh, "attributes") and "mastro_typology_id" in mesh.attributes:
                        for face in faces:
                            # print(f"Object {obj.name} face {face.index}")
                            faceIndex = face.index
                            if [i for i in ["all", "floorToFloor", "void"] if i in self.attributeToUpdate]:
                                typology = mesh.attributes["mastro_typology_id"].data[faceIndex].value
                                data = read_mesh_attributes_uses(context, mesh, faceIndex, typologySet = typology)
                                if [i for i in ["all"] if i in self.attributeToUpdate]:
                                    # mesh.attributes["mastro_typology_id"].data[faceIndex].value = data["typology_id"]
                                    mesh.attributes["mastro_list_use_id_A"].data[faceIndex].value = data["use_id_list_A"]
                                    mesh.attributes["mastro_list_use_id_B"].data[faceIndex].value = data["use_id_list_B"]
                                if [i for i in ["all", "floorToFloor"] if i in self.attributeToUpdate]:
                                    mesh.attributes["mastro_list_height_A"].data[faceIndex].value = data["height_A"]
                                    mesh.attributes["mastro_list_height_B"].data[faceIndex].value = data["height_B"]
                                    mesh.attributes["mastro_list_height_C"].data[faceIndex].value = data["height_C"]
                                    mesh.attributes["mastro_list_height_D"].data[faceIndex].value = data["height_D"]
                                    mesh.attributes["mastro_list_height_E"].data[faceIndex].value = data["height_E"]
                                if [i for i in ["all", "void"] if i in self.attributeToUpdate]:
                                    mesh.attributes["mastro_list_void"].data[faceIndex].value = data["void"]
                                    
                            if [i for i in ["all", "numberOfStoreys"] if i in self.attributeToUpdate]:
                                storeys = mesh.attributes["mastro_number_of_storeys"].data[faceIndex].value
                                data = update_mesh_face_attributes_storeys(context, mesh, faceIndex, storeysSet = storeys)
                                if [i for i in ["all", "numberOfStoreys"] if i in self.attributeToUpdate]:
                                    mesh.attributes["mastro_number_of_storeys"].data[faceIndex].value = data["numberOfStoreys"]
                                    mesh.attributes["mastro_list_storey_A"].data[faceIndex].value = data["storey_list_A"]
                                    mesh.attributes["mastro_list_storey_B"].data[faceIndex].value = data["storey_list_B"]
                            # print(f"Done face {face.index}")
                        
                    edges = context.active_object.data.edges
                    if hasattr(mesh, "attributes") and "mastro_wall_id" in mesh.attributes:
                        for edge in edges:
                            edgeIndex = edge.index
                            wall_id = mesh.attributes["mastro_wall_id"].data[edgeIndex].value
                            data = read_mesh_attributes_walls(context, mesh, edgeIndex, wallSet = wall_id)
                            if [i for i in ["wall_thickness"] if i in self.attributeToUpdate]:
                                mesh.attributes["mastro_wall_thickness"].data[edgeIndex].value = data["wall_thickness"]
                            elif [i for i in ["wall_offset"] if i in self.attributeToUpdate]:
                                mesh.attributes["mastro_wall_offset"].data[edgeIndex].value = data["wall_offset"]
        
                    bpy.ops.object.mode_set(mode=objMode)
                    
                    # If the object was hidden, it is set to hidden again
                    # Also the collection is set to the previous status
                    # In case it has changed
                    if alreadyVisible == False:
                        obj.hide_set(True)
                    if alreadyVisibleCollection == False:
                        collection.hide_viewport = True
                        layer_collection = bpy.context.view_layer.layer_collection.children.get(collection.name)
                        # if hasattr(layer_collection, "exclude"):
                        layer_collection.exclude = True
                        # if used_collection == False:
                        #     bpy.context.scene.collection.children.unlink(collection)
                    
                   

        # return the focus to the current active object
        if hasattr(activeObj, "type"):
            bpy.context.view_layer.objects.active = activeObj
            bpy.ops.object.mode_set(mode=activeObjMode)
        return {'FINISHED'}
        

       
    
            
class typology_name_list(PropertyGroup):
    id: IntProperty(
           name="Id",
           description="Typology id",
           default = 0)
    
    name: StringProperty(
           name="Name",
           description="The name of the typology",
           default="Typology name...",
           update=update_mastro_filter_by_typology)
    
    useList: StringProperty(
            name="Use",
            description="The uses for the typology",
            default="",
            update=update_all_mastro_meshes_useList)
    
    typologyEdgeColor: bpy.props.FloatVectorProperty(
        name = "Color of the edges of the typology to be shown in the overlay",
        subtype = "COLOR",
        size = 3,
        min = 0.0,
        max = 1.0,
        default = (0.0, 0.7, 0.0))
            
class use_name_list(PropertyGroup):
    id: IntProperty(
           name="Id",
           description="Use name id",
           default = 0)
    
    name: StringProperty(
           name="Name",
           description="The name of the use",
           default = "Use name...",
           update=update_mastro_filter_by_use)
    
    floorToFloor: FloatProperty(
        name="Height",
        description="Floor to floor height of the selected use",
        min=0,
        max=99,
        precision=3,
        default = 3.150,
        update=update_all_mastro_meshes_floorToFloor)

    storeys:IntProperty(
        name="Storeys",
        description="Number of storeys of the selected use.\nIf \"Variable number of storeys\" is selected, this value is ignored",
        min=1,
        max=99,
        default = 1,
        update=update_all_mastro_meshes_numberOfStoreys)
    
    liquid: BoolProperty(
            name = "Liquid number of storeys",
            description = "It indicates whether the number of storeys is fixed or variable\nIf selected it has the priority on \"Number of storeys\"",
            default = False,
            update=update_all_mastro_meshes_numberOfStoreys)
    
    void: BoolProperty(
            name = "Void",
            description = "It indicates whether the use is considered to be a void volume in the mass, or not",
            default = False,
            update=update_all_mastro_meshes_void)
            
class typology_uses_name_list(PropertyGroup):
    id: IntProperty(
           name="Id",
           description="The typology use name id",
           default = 0)
    
    name: StringProperty(
           name="Name",
           description="The typology use name",
           default="...")
        #    update=update_mastro_masses_data)
          
    
    
    # position: IntProperty(
    #        name="Use position",
    #        description="Position of the use in the typology (bottom, center, top)",
    #        default = 1)

    
        
############################                ############################
############################ ARCHITECURE    ############################
############################                ############################
        
        
class VIEW3D_PT_MaStro_building_data(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    # bl_category = "MaStro"
    bl_label = "Architecture"
    bl_parent_id = "VIEW3D_PT_MaStro_project_data"
    # bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 2
    
    def draw(self, context):
        pass
        
############################        ############################
############################ WALL   ############################
############################        ############################
        
class VIEW3D_PT_MaStro_building_wall_data(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_label = "Wall"
    bl_parent_id = "VIEW3D_PT_MaStro_building_data"
    bl_options = {'DEFAULT_CLOSED'}      
    
    def draw(self, context):
        scene = context.scene
        
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.  
        
        row = layout.row()
       # row.label(text="Wall")
        
        # is_sortable = len(scene.mastro_use_name_list) > 1
        rows = 3
        # if is_sortable:
        #     rows = 5
            
        row = layout.row()
        row.template_list("OBJECT_UL_Wall", "wall_list", scene,
                        "mastro_wall_name_list", scene, "mastro_wall_name_list_index", rows = rows)
        
        
        col = row.column(align=True)
        col.operator("mastro_wall_name_list.new_item", icon='ADD', text="")
        col.separator()
        col.operator("mastro_wall_name_list.move_item", icon='TRIA_UP', text="").direction = 'UP'
        col.operator("mastro_wall_name_list.move_item", icon='TRIA_DOWN', text="").direction = 'DOWN'
        
        # row = layout.row()
        # row = layout.row(align=True)
        # layout.prop(context.scene, "mastro_typology_uses_name", icon="COMMUNITY", icon_only=False, text="Type:")
        index = context.scene.mastro_wall_name_list_index
        # layout.prop(context.scene.mastro_wall_name_list[index], "shortName", text="Short name")
        if len(context.scene.mastro_wall_name_list) > 0:
            layout.prop(context.scene.mastro_wall_name_list[index], "wallThickness", text="Thickness")
            layout.prop(context.scene.mastro_wall_name_list[index], "wallOffset", text="Offset")
        # layout.prop(context.scene.mastro_wall_name_list[index], "wallEdgeColor", text="Color Overlay")
       
       
       
       
        
        # if scene.mastro_wall_name_list_index >= 0 and scene.mastro_wall_name_list:
        #     item = scene.mastro_wall_name_list[scene.mastro_wall_name_list_index]
        #     row.prop(item, "name", icon_only=True, text="Element Name")
            
            
class OBJECT_UL_Wall(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):
       
        custom_icon = 'NODE_TEXTURE'

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            split = layout.split(factor=0.4)
            sub = split.split()
            sub.label(text="Id: %d" % (item.id)) 
            sub.prop(context.scene.mastro_wall_name_list[index], "wallEdgeColor", text="")

            split.prop(context.scene.mastro_wall_name_list[index],
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
    bl_idname = "mastro_wall_name_list.new_item"
    bl_label = "Add a new wall type"

    def execute(self, context): 
        context.scene.mastro_wall_name_list.add()

        temp_list = []    
        for el in context.scene.mastro_wall_name_list:
            temp_list.append(el.id)
        last = len(context.scene.mastro_wall_name_list)-1
        
        context.scene.mastro_wall_name_list[last].id = max(temp_list)+1
        context.scene.mastro_wall_name_list[last].wallEdgeColor = [random.random(), random.random(), random.random()]
        
        bpy.ops.node.update_gn_filter(filter_name="wall type")    
        return{'FINISHED'}
    
class WALL_LIST_OT_MoveItem(Operator):
    bl_idname = "mastro_wall_name_list.move_item"
    bl_label = "Move an item in the list"

    direction: bpy.props.EnumProperty(items=(('UP', 'Up', ""),
                                              ('DOWN', 'Down', ""),))

    @classmethod
    def poll(cls, context):
        return context.scene.mastro_wall_name_list

    def move_index(self):
        index = bpy.context.scene.mastro_wall_name_list_index
        list_length = len(bpy.context.scene.mastro_wall_name_list) - 1 
        new_index = index + (-1 if self.direction == 'UP' else 1)

        bpy.context.scene.mastro_wall_name_list_index = max(0, min(new_index, list_length))

    def execute(self, context):
        mastro_wall_name_list = context.scene.mastro_wall_name_list
        index = context.scene.mastro_wall_name_list_index

        neighbor = index + (-1 if self.direction == 'UP' else 1)
        mastro_wall_name_list.move(neighbor, index)
        self.move_index()

        return{'FINISHED'}
    
# update the node "filter by wall type" if a new wall type is added or
# a wall typey name has changed
def update_mastro_filter_by_wall_type(self, context):
    bpy.ops.node.update_gn_filter(filter_name="wall type")
    # bpy.ops.node.update_shader_filter(filter_name="wall type")
    return None
            
class wall_name_list(PropertyGroup):
    id: IntProperty(
           name="Id",
           description="Wall name id",
           default = 0)
    
    name: StringProperty(
           name="Wall Name",
           description="The name of the wall",
           default="Wall type...",
           update=update_mastro_filter_by_wall_type)
    
    # shortName: StringProperty(
    #        name="Wall Name",
    #        description="A short name describing the wall",
    #        default="WLL")
    
    wallThickness: FloatProperty(
        name="Wall thickness",
        description="The thickness of the wall",
        min=0,
        #max=99,
        precision=3,
        default = 0.300,
        update=update_all_mastro_wall_thickness
        )
    
    wallOffset: FloatProperty(
        name="Wall offset",
        description="The offset of the wall from its center line",
        min=0,
        #max=99,
        precision=3,
        default = 0,
        update=update_all_mastro_wall_offset
        )
    
    normal: IntProperty(
           name="Wall Normal",
           description="Invert the normal of the wall",
           default = 1)
    
    wallEdgeColor: bpy.props.FloatVectorProperty(
        name = "Color of the edges of the wall to be shown in the overlay",
        subtype = "COLOR",
        size = 3,
        min = 0.0,
        max = 1.0,
        default = (0.0, 0.0, 1.0))
    
############################        ############################
############################ FLOOR  ############################
############################        ############################
            

class VIEW3D_PT_MaStro_building_floor_data(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_label = "Floor"
    bl_parent_id = "VIEW3D_PT_MaStro_building_data"
    bl_options = {'DEFAULT_CLOSED'}      
    
    def draw(self, context):
        scene = context.scene
        
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.
        
        row = layout.row()
        #row.label(text="Floor")
        
        # is_sortable = len(scene.mastro_use_name_list) > 1
        rows = 3
        # if is_sortable:
        #     rows = 5
            
        row = layout.row()
        row.template_list("OBJECT_UL_Floor", "floor_list", scene,
                        "mastro_floor_name_list", scene, "mastro_floor_name_list_index", rows = rows)
        
        
        col = row.column(align=True)
        col.operator("mastro_floor_name_list.new_item", icon='ADD', text="")
        col.separator()
        col.operator("mastro_floor_name_list.move_item", icon='TRIA_UP', text="").direction = 'UP'
        col.operator("mastro_floor_name_list.move_item", icon='TRIA_DOWN', text="").direction = 'DOWN'
        
        row = layout.row()
        row = layout.row(align=True)
        
        # if scene.mastro_floor_name_list_index >= 0 and scene.mastro_floor_name_list:
        #     item = scene.mastro_floor_name_list[scene.mastro_floor_name_list_index]
        #     row.prop(item, "name", icon_only=True, text="Floor Name")
            
          
class OBJECT_UL_Floor(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):
       
        custom_icon = 'VIEW_PERSPECTIVE'

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            split = layout.split(factor=0.4)
            split.label(text="Id: %d" % (item.id)) 
            # split.label(text=item.name, icon=custom_icon) 
            split.prop(context.scene.mastro_floor_name_list[index],
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
    bl_idname = "mastro_floor_name_list.new_item"
    bl_label = "Add a new floor type"

    def execute(self, context): 
        context.scene.mastro_floor_name_list.add()
        temp_list = []    
        for el in context.scene.mastro_floor_name_list:
            temp_list.append(el.id)
        last = len(context.scene.mastro_floor_name_list)-1
        
        context.scene.mastro_floor_name_list[last].id = max(temp_list)+1
            
        return{'FINISHED'}
    
class FLOOR_LIST_OT_MoveItem(Operator):
    bl_idname = "mastro_floor_name_list.move_item"
    bl_label = "Move an item in the list"

    direction: bpy.props.EnumProperty(items=(('UP', 'Up', ""),
                                              ('DOWN', 'Down', ""),))

    @classmethod
    def poll(cls, context):
        return context.scene.mastro_floor_name_list

    def move_index(self):
        index = bpy.context.scene.mastro_floor_name_list_index
        list_length = len(bpy.context.scene.mastro_floor_name_list) - 1 
        new_index = index + (-1 if self.direction == 'UP' else 1)

        bpy.context.scene.mastro_floor_name_list_index = max(0, min(new_index, list_length))

    def execute(self, context):
        mastro_floor_name_list = context.scene.mastro_floor_name_list
        index = context.scene.mastro_floor_name_list_index

        neighbor = index + (-1 if self.direction == 'UP' else 1)
        mastro_floor_name_list.move(neighbor, index)
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
        
############################        ############################
############################ STREET   ############################
############################        ############################
        
        
class VIEW3D_PT_MaStro_street_data(Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    # bl_category = "MaStro"
    bl_label = "Street"
    bl_parent_id = "VIEW3D_PT_MaStro_project_data"
    # bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 3
    
    def draw(self, context):
        scene = context.scene
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.  
        
        row = layout.row()
        
        # is_sortable = len(scene.mastro_use_name_list) > 1
        rows = 3
        # if is_sortable:
        #     rows = 5
            
        row = layout.row()
        row.template_list("OBJECT_UL_Street", "street_list", scene,
                        "mastro_street_name_list", scene, "mastro_street_name_list_index", rows = rows)
        
        
        col = row.column(align=True)
        col.operator("mastro_street_name_list.new_item", icon='ADD', text="")
        col.separator()
        col.operator("mastro_street_name_list.move_item", icon='TRIA_UP', text="").direction = 'UP'
        col.operator("mastro_street_name_list.move_item", icon='TRIA_DOWN', text="").direction = 'DOWN'
        
        index = context.scene.mastro_street_name_list_index
        if len(context.scene.mastro_street_name_list) > 0:
            layout.prop(context.scene.mastro_street_name_list[index], "streetWidth", text="Width")
            layout.prop(context.scene.mastro_street_name_list[index], "streetRadius", text="Radius")
        # else:
        #     from . import initLists
        #     initLists()
        # layout.prop(context.scene.mastro_street_name_list[index], "streetEdgeColor", text="Color Overlay")
       
class OBJECT_UL_Street(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):
       
        custom_icon = 'NODE_TEXTURE'

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            split = layout.split(factor=0.4)
            # split.label(text="Id: %d" % (item.id)) 
            sub = split.split()
            sub.label(text="Id: %d" % (item.id)) 
            sub.prop(context.scene.mastro_street_name_list[index], "streetEdgeColor", text="")
            
            # split.label(text=item.name, icon=custom_icon) 
            split.prop(context.scene.mastro_street_name_list[index],
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
    
class STREET_LIST_OT_NewItem(Operator):
    bl_idname = "mastro_street_name_list.new_item"
    bl_label = "Add a new street type"

    def execute(self, context): 
        context.scene.mastro_street_name_list.add()
        
        temp_list = []    
        for el in context.scene.mastro_street_name_list:
            temp_list.append(el.id)
        last = len(context.scene.mastro_street_name_list)-1
        
        context.scene.mastro_street_name_list[last].id = max(temp_list)+1
        context.scene.mastro_street_name_list[last].streetEdgeColor = [random.random(), random.random(), random.random()]
        
        bpy.ops.node.update_gn_filter(filter_name="street type")
            
        return{'FINISHED'}
    
class STREET_LIST_OT_MoveItem(Operator):
    bl_idname = "mastro_street_name_list.move_item"
    bl_label = "Move an item in the list"

    direction: bpy.props.EnumProperty(items=(('UP', 'Up', ""),
                                              ('DOWN', 'Down', ""),))

    @classmethod
    def poll(cls, context):
        return context.scene.mastro_street_name_list

    def move_index(self):
        index = bpy.context.scene.mastro_street_name_list_index
        list_length = len(bpy.context.scene.mastro_street_name_list) - 1 
        new_index = index + (-1 if self.direction == 'UP' else 1)

        bpy.context.scene.mastro_street_name_list_index = max(0, min(new_index, list_length))

    def execute(self, context):
        mastro_street_name_list = context.scene.mastro_street_name_list
        index = context.scene.mastro_street_name_list_index

        neighbor = index + (-1 if self.direction == 'UP' else 1)
        mastro_street_name_list.move(neighbor, index)
        self.move_index()

        return{'FINISHED'}
    
def update_all_mastro_street_width(self, context):
    updates = "width"
    bpy.ops.object.update_all_mastro_street_attributes(attributeToUpdate=updates)
    
def update_all_mastro_street_radius(self, context):
    updates = "radius"
    bpy.ops.object.update_all_mastro_street_attributes(attributeToUpdate=updates)
    
# Operator to update the attributes of all the MaStro streets in the scene        
class OBJECT_OT_update_all_MaStro_street_attributes(Operator):
    bl_idname = "object.update_all_mastro_street_attributes"
    bl_label = "Update"
    bl_options = {'REGISTER', 'UNDO'}
    
    attributeToUpdate: bpy.props.StringProperty(name="Attribute to update")
    
    def execute(self, context):
        objs = bpy.data.objects
        # get the current active object
        activeObj = bpy.context.active_object
        if hasattr(activeObj, "type"):
            activeObjMode = activeObj.mode
            
        for obj in objs:
            if obj is not None and obj.type == 'MESH' and "MaStro object" in obj.data and "MaStro street" in obj.data:
                # it is necessary to set the object to visibile in order to make it active
                if obj.visible_get():
                    alreadyVisible = True
                else:
                    alreadyVisible = False
                    obj.hide_set(False)
                
                # check if the collection is visible or not
                collections = obj.users_collection
                used_collection = False
                alreadyVisibleCollection = False
                for collection in collections:
                    if not collection.hide_viewport:
                        used_collection = True
                        alreadyVisibleCollection = True
                        break
                    else:
                        collection.hide_viewport = False
                        layer_collection = bpy.context.view_layer.layer_collection.children.get(collection.name)
                        if hasattr(layer_collection, "exclude"):
                            layer_collection.exclude = False
                            used_collection = True
                            break
                # Only the linked objects are updated
                if used_collection == True:
                    bpy.context.view_layer.objects.active = obj
                    mesh = obj.data
                    objMode = obj.mode
                    bpy.ops.object.mode_set(mode='OBJECT')
                    edges = context.active_object.data.edges
                    for edge in edges:
                        edgeIndex = edge.index
                        street_id = mesh.attributes["mastro_street_id"].data[edgeIndex].value
                        data = read_mesh_attributes_streets(context, mesh, edgeIndex, streetSet = street_id)
                        if [i for i in ["width"] if i in self.attributeToUpdate]:
                            mesh.attributes["mastro_street_width"].data[edgeIndex].value = data["width"]/2
                        elif [i for i in ["radius"] if i in self.attributeToUpdate]:
                            mesh.attributes["mastro_street_radius"].data[edgeIndex].value = data["radius"]
                    bpy.ops.object.mode_set(mode=objMode)
                    
                    # If the object was hidden, it is set to hidden again
                    # Also the collection is set to the previous status
                    # In case it has changed
                    if alreadyVisible == False:
                        obj.hide_set(True)
                    if alreadyVisibleCollection == False:
                        collection.hide_viewport = True
                        layer_collection = bpy.context.view_layer.layer_collection.children.get(collection.name)
                        layer_collection.exclude = True

        # return the focus to the current active object
        if hasattr(activeObj, "type"):
            bpy.context.view_layer.objects.active = activeObj
            bpy.ops.object.mode_set(mode=activeObjMode)
        return {'FINISHED'}
        
# update the node "filter by street type" if a new street type is added or
# a street type name has changed
def update_mastro_filter_by_street_type(self, context):
    bpy.ops.node.update_gn_filter(filter_name="street type")
    # bpy.ops.node.update_shader_filter(filter_name="street type")
    return None

class street_name_list(PropertyGroup):
    id: IntProperty(
           name="Id",
           description="Street name id",
           default = 0)
    
    name: StringProperty(
           name="Street type Name",
           description="The type name of the street",
           default="Street type...",
           update=update_mastro_filter_by_street_type)
    
    streetWidth: FloatProperty(
        name="Street width",
        description="The width of the street",
        min=0,
        #max=99,
        precision=3,
        default = 8,
        update=update_all_mastro_street_width)
    
    streetRadius: FloatProperty(
        name="Street radius",
        description="The radius of the street",
        min=0,
        #max=99,
        precision=3,
        default = 16,
        update=update_all_mastro_street_radius)
    
    streetEdgeColor: bpy.props.FloatVectorProperty(
        name = "Color of the edges of the street to be shown in the overlay",
        subtype = "COLOR",
        size = 3,
        min = 0.0,
        max = 1.0,
        default = (1.0, 0.0, 0.0))
        

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



