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
import bmesh 
import os
import addon_utils
from bpy.types import Menu, Operator, Panel
from bpy_extras.io_utils import ExportHelper
from bpy_extras.object_utils import AddObjectHelper
from bpy.props import StringProperty

from . import icons
import random, math, mathutils, csv

from decimal import Decimal #, ROUND_HALF_DOWN
from datetime import datetime
# from bpy.utils import resource_path
from pathlib import Path

contexts = ['OBJECT', "EDIT_MESH"]

# header_aggregateData = ["Option", "Phase", "Plot Name", "Block Name", "Use", "N. of Storeys", "Footprint", "Perimeter", "Wall area", "GEA"]
# header_granularData = ["Option", "Phase", "Plot Name", "Block Name", "Use", "Floor", "Level", "GEA", "Perimeter", "Wall area"]
    
# floorToFloorLevel = 4.2

mass_attribute_set = [

            # {
            # "attr" : "mastro_vertex_custom_attribute",
            # "attr_type" :  "INT",
            # "attr_domain" :  "POINT",
            # "attr_default" : 0
            # },
            {
            "attr" :  "mastro_wall_id",
            "attr_type" :  "INT",
            "attr_domain" :  "EDGE",
            "attr_default" : 0
            },
            {
            "attr" :  "mastro_wall_thickness",
            "attr_type" :  "FLOAT",
            "attr_domain" :  "EDGE",
            "attr_default" : 0.300
            },
            {
            "attr" :  "mastro_wall_offset",
            "attr_type" :  "FLOAT",
            "attr_domain" :  "EDGE",
            "attr_default" : 0
            },
            {
            "attr" :  "mastro_inverted_normal",
            "attr_type" :  "INT",
            "attr_domain" :  "EDGE",
            "attr_default" : 0
            },
            # {
            # "attr" :  "mastro_number_of_storeys_per_face",
            # "attr_type" :  "INT",
            # "attr_domain" :  "EDGE"
            # },
            # {
            # "attr" :  "mastro_plot_id",
            # "attr_type" :  "INT",
            # "attr_domain" :  "FACE",
            # "attr_default" : 0
            # },
            # {
            # "attr" :  "mastro_plot_RND",
            # "attr_type" :  "FLOAT",
            # "attr_domain" :  "FACE",
            # "attr_default" : 0
            # },
            # {
            # "attr" :  "mastro_block_id",
            # "attr_type" :  "INT",
            # "attr_domain" :  "FACE",
            # "attr_default" : 0
            # },
            # {
            # "attr" :  "mastro_block_RND",
            # "attr_type" :  "FLOAT",
            # "attr_domain" :  "FACE",
            # "attr_default" : 0
            # },
            # {
            # "attr" :  "mastro_use_id",
            # "attr_type" :  "INT",
            # "attr_domain" :  "FACE",
            # "attr_default" : 0
            # },
            # {
            # "attr" :  "mastro_use_RND",
            # "attr_type" :  "FLOAT",
            # "attr_domain" :  "FACE",
            # "attr_default" : 0
            # },
            {
            "attr" :  "mastro_typology_id",
            "attr_type" :  "INT",
            "attr_domain" :  "FACE",
            # "attr_default" : "typology id"
            },
            {
            "attr" :  "mastro_list_use_id_A",
            "attr_type" :  "INT",
            "attr_domain" :  "FACE",
            # "attr_default" : 0
            },
             {
            "attr" :  "mastro_list_use_id_B",
            "attr_type" :  "INT",
            "attr_domain" :  "FACE",
            # "attr_default" : 0
            },
            {
            "attr" :  "mastro_list_storey_A",
            "attr_type" :  "INT",
            "attr_domain" :  "FACE",
            # "attr_default" : 0
            },
            {
            "attr" :  "mastro_list_storey_B",
            "attr_type" :  "INT",
            "attr_domain" :  "FACE",
            # "attr_default" : 0
            },
            {
            "attr" :  "mastro_list_height_A",
            "attr_type" :  "INT",
            "attr_domain" :  "FACE",
            # "attr_default" : 0
            },
            {
            "attr" :  "mastro_list_height_B",
            "attr_type" :  "INT",
            "attr_domain" :  "FACE",
            # "attr_default" : 0
            },
            {
            "attr" :  "mastro_list_height_C",
            "attr_type" :  "INT",
            "attr_domain" :  "FACE",
            # "attr_default" : 0
            },
            {
            "attr" :  "mastro_list_height_D",
            "attr_type" :  "INT",
            "attr_domain" :  "FACE",
            # "attr_default" : 0
            },
            {
            "attr" :  "mastro_list_height_E",
            "attr_type" :  "INT",
            "attr_domain" :  "FACE",
            # "attr_default" : 0
            },
            {
            "attr" :  "mastro_list_void",
            "attr_type" :  "INT",
            "attr_domain" :  "FACE",
            # "attr_default" : 0
            },
            {
            "attr" :  "mastro_floor_id",
            "attr_type" :  "INT",
            "attr_domain" :  "FACE",
            "attr_default" : 0
            },
            {
            "attr" :  "mastro_number_of_storeys",
            "attr_type" :  "INT",
            "attr_domain" :  "FACE",
            "attr_default" : 1
            },
]

plot_attribute_set = [
            {
            "attr" :  "mastro_typology_id",
            "attr_type" :  "INT",
            "attr_domain" :  "EDGE",
            },
            {
            "attr" :  "mastro_list_use_id_A",
            "attr_type" :  "INT",
            "attr_domain" :  "EDGE",
            },
             {
            "attr" :  "mastro_list_use_id_B",
            "attr_type" :  "INT",
            "attr_domain" :  "EDGE",
            },
            {
            "attr" :  "mastro_list_storey_A",
            "attr_type" :  "INT",
            "attr_domain" :  "EDGE",
            },
            {
            "attr" :  "mastro_list_storey_B",
            "attr_type" :  "INT",
            "attr_domain" :  "EDGE",
            },
            {
            "attr" :  "mastro_list_height_A",
            "attr_type" :  "INT",
            "attr_domain" :  "EDGE",
            },
            {
            "attr" :  "mastro_list_height_B",
            "attr_type" :  "INT",
            "attr_domain" :  "EDGE",
            },
            {
            "attr" :  "mastro_list_height_C",
            "attr_type" :  "INT",
            "attr_domain" :  "EDGE",
            },
            {
            "attr" :  "mastro_list_height_D",
            "attr_type" :  "INT",
            "attr_domain" :  "EDGE",
            },
            {
            "attr" :  "mastro_list_height_E",
            "attr_type" :  "INT",
            "attr_domain" :  "EDGE",
            },
            {
            "attr" :  "mastro_list_void",
            "attr_type" :  "INT",
            "attr_domain" :  "EDGE",
            },
            {
            "attr" :  "mastro_floor_id",
            "attr_type" :  "INT",
            "attr_domain" :  "EDGE",
            "attr_default" : 0
            },
            {
            "attr" :  "mastro_number_of_storeys",
            "attr_type" :  "INT",
            "attr_domain" :  "EDGE",
            "attr_default" : 1
            },
            {
            "attr" :  "mastro_plot_depth",
            "attr_type" :  "FLOAT",
            "attr_domain" :  "EDGE",
            "attr_default" : 18
            },
            {
            "attr" :  "mastro_wall_id",
            "attr_type" :  "INT",
            "attr_domain" :  "EDGE",
            "attr_default" : 0
            },
            {
            "attr" :  "mastro_wall_thickness",
            "attr_type" :  "FLOAT",
            "attr_domain" :  "EDGE",
            "attr_default" : 0.300
            },
            {
            "attr" :  "mastro_wall_offset",
            "attr_type" :  "FLOAT",
            "attr_domain" :  "EDGE",
            "attr_default" : 0
            },
            {
            "attr" :  "mastro_inverted_normal",
            "attr_type" :  "BOOLEAN",
            "attr_domain" :  "EDGE",
            "attr_default" : 0
            },
]

street_attribute_set = [
            {
            "attr" :  "mastro_street_id",
            "attr_type" :  "INT",
            "attr_domain" :  "EDGE",
            "attr_default" : 0
            },
            {
            "attr" :  "mastro_street_width",
            "attr_type" :  "FLOAT",
            "attr_domain" :  "EDGE",
            "attr_default" : 8
            },
            {
            "attr" :  "mastro_street_radius",
            "attr_type" :  "FLOAT",
            "attr_domain" :  "EDGE",
            "attr_default" : 16
            }
]

# Defines class for custom properties
class mastroAddonProperties(bpy.types.PropertyGroup):
    # mastro_option_attribute: bpy.props.IntProperty(
    #     name="MaStro Option Attribute",
    #     default=1,
    #     min=1,
    #     description="The project option of the building"
    # )
    
    # mastro_phase_attribute: bpy.props.IntProperty(
    #     name="MaStro Phase Attribute",
    #     default=1,
    #     min=1,
    #     description="The construction phase of the building"
    # )
    
    mastro_plot_attribute: bpy.props.IntProperty(
        name="MaStro Plot Attribute",
        default=1,
        min=1,
        description="Plot name"
    )
    
    mastro_block_attribute: bpy.props.IntProperty(
        name="MaStro Block Attribute",
        default=1,
        min=1,
        description="Block name"
    )
    
# class faceEdge():
#      def __init__(self, index = None, face = None, storeys = None, topStorey = None, length = None, perimeter = None):
#         #  self.objName = objName
#          self.index = index
#          self.face = face
#          self.storeys = storeys
#          self.topStorey = topStorey
#          self.length = length
#          self.perimeter = perimeter
         

# class MaStro_Menu(Menu):
#     bl_idname = "VIEW3D_MT_custom_menu"
#     bl_label = "MaStro"

#     def draw(self, context):
#         layout = self.layout
#         #layout.active = bool(context.active_object.mode!='EDIT  ')
#         layout.operator(MaStro_MenuOperator_add_MaStro_mass.bl_idname)
#         layout.operator(MaStro_MenuOperator_convert_to_MaStro_mass.bl_idname)
#         layout.separator()
#         printAggregate = layout.operator(MaStro_MenuOperator_PrintData.bl_idname, text="Print the data of the mass in compact form")
#         printAggregate.text = "aggregate"
#         printGranular = layout.operator(MaStro_MenuOperator_PrintData.bl_idname, text="Print the data of the mass in extended form")
#         printGranular.text = "granular"
#         layout.operator(MaStro_MenuOperator_ExportCSV.bl_idname)
        # layout.separator()
        # layout.operator(MaStro_Operator_transform_orientation.bl_idname)
        
# panel to show operators when a non mastro object is selected
class VIEW3D_PT_MaStro_Panel(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MaStro"
    bl_label = "MaStro"
    
    @classmethod
    def poll(cls, context):
        return  (context.object is None or
                #  context.selected_objects == [] or
                    (context.object.type != "MESH" if context.object else True) or
                    ("MaStro object" not in context.object.data if context.object and context.object.type == "MESH" else False)
        )
    
    def draw(self, context):
        scene = context.scene
        layout = self.layout
        # layout.operator(MaStro_MenuOperator_add_MaStro_mass.bl_idname)
        layout.operator(MaStro_MenuOperator_convert_to_MaStro_mass.bl_idname)
        # layout.operator(MaStro_MenuOperator_add_MaStro_street.bl_idname)
        layout.operator(MaStro_MenuOperator_convert_to_MaStro_street.bl_idname)

class MaStro_MenuOperator_add_MaStro_mass(Operator, AddObjectHelper):
    """Add a MaStro mass"""
    bl_idname = "object.mastro_add_mastro_mass"
    bl_label = "Mass"
    bl_options = {'REGISTER', 'UNDO'}
    
    width: bpy.props.FloatProperty(
        name="Width",
        description="MaStro mass width",
        # min=0.01, max=100.0,
        min=0,
        default=12,
    )
    
    depth: bpy.props.FloatProperty(
        name="Depth",
        description="MaStro mass depth",
        # min=0.01, max=100.0,
        min=0,
        default=8,
    )
    
    # storeys: bpy.props.IntProperty(
    #         name="Number of Storeys",
    #         description="Number of storeys of the mass",
    #         min = 1,
    #         default = 3)
    
    
    def execute(self, context):

        verts_loc, faces = add_mastro_mass(
            self.width,
            self.depth,
        )

        mesh = bpy.data.meshes.new("MaStro mass")

        bm = bmesh.new()

        for v_co in verts_loc:
            bm.verts.new(v_co)

        bm.verts.ensure_lookup_table()
        for f_idx in faces:
            bm.faces.new([bm.verts[i] for i in f_idx])

        bm.to_mesh(mesh)
        mesh.update()

        # add the mesh as an object into the scene with this utility module
        from bpy_extras import object_utils
        object_utils.object_data_add(context, mesh, operator=self)
        
        obj = bpy.context.active_object
        obj.select_set(True)
        
        addMassAttributes(obj)
            
        addNodes()
        
        mesh_attributes = obj.data.attributes["mastro_number_of_storeys"].data.items()
        # mesh_attributes[0][1].value = self.storeys
        mesh_attributes[0][1].value = 3

        # add mastro mass geo node to the created object
        geoName = "MaStro Mass"
        obj.modifiers.new(geoName, "NODES")
        group = bpy.data.node_groups["MaStro Mass"]
        obj.modifiers[geoName].node_group = group
        context.view_layer.objects.active = obj
        return {'FINISHED'}
    
def add_mastro_mass(width, depth):
    """
    This function takes inputs and returns vertex and face arrays.
    no actual mesh data creation is done here.
    """

    verts = [
        (+0.0, +0.0,  +0.0),
        (+1.0, +0.0,  +0.0),
        (+1.0, +1.0,  +0.0),
        (+0.0, +1.0,  +0.0),
        ]

    faces = [
        (0, 1, 2, 3),
    ]

    # apply size
    for i, v in enumerate(verts):
        verts[i] = v[0] * width, v[1] * depth, v[2]

    return verts, faces

class MaStro_MenuOperator_add_MaStro_plot(Operator, AddObjectHelper):
    """Add a MaStro maplotss"""
    bl_idname = "object.mastro_add_mastro_plot"
    bl_label = "Plot"
    bl_options = {'REGISTER', 'UNDO'}
    
    # width: bpy.props.FloatProperty(
    #     name="Width",
    #     description="MaStro mass width",
    #     # min=0.01, max=100.0,
    #     min=0,
    #     default=12,
    # )
    
    # depth: bpy.props.FloatProperty(
    #     name="Depth",
    #     description="MaStro plot depth",
    #     # min=0.01, max=100.0,
    #     min=0,
    #     default=16,
    # )
    
    # storeys: bpy.props.IntProperty(
    #         name="Number of Storeys",
    #         description="Number of storeys of the plot masses",
    #         min = 1,
    #         default = 3)
    
    
    def execute(self, context):

        verts_loc, edges = add_mastro_plot()

        mesh = bpy.data.meshes.new("MaStro plot")

        bm = bmesh.new()

        for v_co in verts_loc:
            bm.verts.new(v_co)

        bm.verts.ensure_lookup_table()
        for e_idx in edges:
            bm.edges.new([bm.verts[i] for i in e_idx])

        bm.to_mesh(mesh)
        mesh.update()

        # add the mesh as an object into the scene with this utility module
        from bpy_extras import object_utils
        object_utils.object_data_add(context, mesh, operator=self)
        
        obj = bpy.context.active_object
        obj.select_set(True)
        
        addPlotAttributes(obj)
            
        addNodes()
        
        mesh_attributes = obj.data.attributes["mastro_number_of_storeys_EDGE"].data.items()
        for edge in mesh.edges:
            index = edge.index
            for mesh_attribute in mesh_attributes:
                if mesh_attribute[0]  == index:
                    mesh_attribute[1].value = 3

        # add mastro plot and mastro mass geo node to the created object
        geoName = "MaStro Plot"
        obj.modifiers.new(geoName, "NODES")
        group = bpy.data.node_groups["MaStro Plot"]
        obj.modifiers[geoName].node_group = group
        context.view_layer.objects.active = obj
        
        geoName = "MaStro Mass"
        obj.modifiers.new(geoName, "NODES")
        group = bpy.data.node_groups["MaStro Mass"]
        obj.modifiers[geoName].node_group = group
        context.view_layer.objects.active = obj
        return {'FINISHED'}
    
def add_mastro_plot():
    """
    This function takes inputs and returns vertex and face arrays.
    no actual mesh data creation is done here.
    """

    verts = [
        (+0.0, +0.0,  +0.0),
        (+30.0, +0.0,  +0.0),
        (+47.321, +10.0,  +0.0),
        (+47.321, +40.0,  +0.0),
        ]
    
    edges = [
        (0,1),
        (1,2),
        (2,3)
    ]
    # faces = [
    #     (0, 1, 2, 3),
    # ]

    return verts, edges

class MaStro_MenuOperator_add_MaStro_street(Operator, AddObjectHelper):
    """Add a MaStro street"""
    bl_idname = "object.mastro_add_mastro_street"
    bl_label = "Street"
    bl_options = {'REGISTER', 'UNDO'}
    
    # width: bpy.props.FloatProperty(
    #     name="Width",
    #     description="MaStro street width",
    #     # min=0.01, max=100.0,
    #     min=0,
    #     default=8,
    # )
    
    # radius: bpy.props.FloatProperty(
    #     name="Radius",
    #     description="MaStro street radius",
    #     # min=0.01, max=100.0,
    #     min=0,
    #     default=16,
    # )
    
  
    def execute(self, context):

        verts_loc, edges = add_mastro_street(
            # self.width,
            # self.radius,
        )

        mesh = bpy.data.meshes.new("MaStro street")

        bm = bmesh.new()

        for v_co in verts_loc:
            bm.verts.new(v_co)

        bm.verts.ensure_lookup_table()
        for e_idx in edges:
            bm.edges.new((bm.verts[e_idx[0]], bm.verts[e_idx[1]]))

        bm.to_mesh(mesh)
        mesh.update()

        # add the mesh as an object into the scene with this utility module
        from bpy_extras import object_utils
        object_utils.object_data_add(context, mesh, operator=self)
        
        obj = bpy.context.active_object
        obj.select_set(True)
        
        addStreetAttributes(obj)
            
        addNodes()
        
        
        # mesh_attributes = obj.data.attributes["mastro_number_of_storeys"].data.items()
        # mesh_attributes[0][1].value = self.storeys

        # add mastro street geo node to the created object
        geoName = "MaStro Street"
        obj.modifiers.new(geoName, "NODES")
        group = bpy.data.node_groups["MaStro Street"]
        obj.modifiers[geoName].node_group = group
        context.view_layer.objects.active = obj
        return {'FINISHED'}
    
def add_mastro_street():
    """
    This function takes inputs and returns vertex and face arrays.
    no actual mesh data creation is done here.
    """

    verts = [
        (+0.0, +0.0, +0.0),
        (+22.0, +28.0, +0.0),
        (+56.0, +35.0,  +0.0),
        (-42.0, +38.0, +0.0),
        (-70.0, +20.0, +0.0),
        (-22.0, -25.0, +0.0),
        (-31.0, -61.0, +0.0)
        ]

    edges = [
        (0, 1),
        (1, 2),
        (0,3),
        (3,4),
        (0,5),
        (5,6)
    ]

    # # apply size
    # for i, v in enumerate(verts):
    #     verts[i] = v[0] * width, v[1] * depth, v[2]

    return verts, edges

    
# class VIEW3D_MT_mastro_add(bpy.types.Menu):
#     bl_label = "MaStro"
#     bl_idname = "VIEW3D_MT_mastro_add"

#     def draw(self, context):
#         # self.layout.operator(MaStro_MenuOperator_add_MaStro_plot.bl_idname, icon='MESH_CUBE')
#         # self.layout.operator(MaStro_MenuOperator_add_MaStro_mass.bl_idname, icon='MESH_CUBE')
#         # self.layout.separator()
#         # self.layout.operator(MaStro_MenuOperator_add_MaStro_street.bl_idname, icon='MESH_CUBE')
#         layout = self.layout

#         # Icona custom come primo elemento
#         my_icon = icons.icon_id('mastro')
#         layout.operator("mastro.icon_preview", text="", icon_value=my_icon)

#         # Poi i tuoi operatori custom
#         layout.operator("mesh.primitive_cube_add", icon="MESH_CUBE")
#         layout.operator("mesh.primitive_uv_sphere_add", icon="MESH_UVSPHERE")

# add the entry to the add menu
def mastro_add_menu_func(self, context):
    self.layout.separator()
    myIcon = icons.icon_id("plot")
    self.layout.operator(MaStro_MenuOperator_add_MaStro_plot.bl_idname, icon_value=myIcon)
    myIcon = icons.icon_id("mass")
    self.layout.operator(MaStro_MenuOperator_add_MaStro_mass.bl_idname, icon_value=myIcon)
    myIcon = icons.icon_id("street")
    self.layout.operator(MaStro_MenuOperator_add_MaStro_street.bl_idname, icon_value=myIcon)
    
    
class MaStro_MenuOperator_convert_to_MaStro_mass(Operator):
    bl_idname = "object.mastro_convert_to_mastro_mass"
    bl_label = "Convert the selected mesh to a MaStro mass"
    
    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'
    
    def execute(self, context):
        selected_objects = bpy.context.selected_objects
        selected_meshes = [obj for obj in selected_objects if obj.type == 'MESH']
        # mode = None
        for obj in selected_meshes:
            addMassAttributes(obj)
            
        addNodes()
        # initLists()
        return {'FINISHED'}

class MaStro_MenuOperator_convert_to_MaStro_street(Operator):
    bl_idname = "object.mastro_convert_to_mastro_street"
    bl_label = "Convert the selected mesh to a MaStro street"
    
    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'
    
    def execute(self, context):
        selected_objects = bpy.context.selected_objects
        selected_meshes = [obj for obj in selected_objects if obj.type == 'MESH']
        # mode = None
        for obj in selected_meshes:
            addStreetAttributes(obj)
            
        addNodes()
        # initLists()
        return {'FINISHED'}
    
# assign the mass attributes to the selected object
def addMassAttributes(obj):
    # obj.mastro_props['mastro_option_attribute'] = 1
    # obj.mastro_props['mastro_phase_attribute'] = 1
    obj.mastro_props['mastro_plot_attribute'] = 0
    obj.mastro_props['mastro_block_attribute'] = 0
    mesh = obj.data
    mesh["MaStro object"] = True
    mesh["MaStro mass"] = True
    
    typology_id = bpy.context.scene.mastro_typology_name_list_index
    projectUses = bpy.context.scene.mastro_use_name_list
    
    use_list = bpy.context.scene.mastro_typology_name_list[typology_id].useList
    useSplit = use_list.split(";")

    use_id_list_A = "1"
    use_id_list_B = "1"
    storey_list_A = "1"
    storey_list_B = "1"
    height_A = "1"
    height_B = "1"
    height_C = "1"
    height_D = "1"
    height_E = "1"
    liquidPosition = []
    fixedStoreys = 0
    numberOfStoreys = 3 # default value for initial number of storeys
    void = "1"
    
    for enum,el in enumerate(useSplit):
        if int(el) < 10:
            tmpUse = "0" + el
        else:
            tmpUse = str(el)
       
        # print(el[0], el[1])
        use_id_list_A += tmpUse[0]
        use_id_list_B += tmpUse[1]
        
        
            
        for use in projectUses:
            if use.id == int(el):
                # number of storeys for the use
                # if a use is "liquid" the number of storeys is set as 00
                if use.liquid: 
                    storeys = "00"
                    liquidPosition.append(enum)
                else:
                    fixedStoreys += use.storeys
                    storeys = str(use.storeys)
                    if use.storeys < 10:
                        storeys = "0" + storeys

                storey_list_A += storeys[0]
                storey_list_B += storeys[1]
                
                void += str(int(use.void))
                
                height = str(round(use.floorToFloor,3))
                if use.floorToFloor < 10:
                    height = "0" + height
                height_A += height[0]
                height_B += height[1]
                try:
                    # height[3]
                    height_C += height[3]
                    try:
                        height_D += height[4]
                        try:
                            height_E += height[5]
                        except:
                            height_E += "0"
                    except:
                        height_D += "0"
                        height_E += "0"
                except:
                    height_C += "0"
                    height_D += "0"
                    height_E += "0"
                break
            
        storeyCheck = numberOfStoreys - fixedStoreys - len(liquidPosition)
        # if the typology has more storeys than the selected mass
        # some extra storeys are added
        if storeyCheck < 1: 
            bpy.context.scene.attribute_mass_storeys = fixedStoreys + len(liquidPosition)
        storeyLeft = numberOfStoreys - fixedStoreys
        
        # the 1 at the start of the number is removed
        storey_list_A = storey_list_A[1:]
        storey_list_B = storey_list_B[1:]  
        if len(liquidPosition) > 0:
            n = storeyLeft/len(liquidPosition)
            liquidStoreyNumber = math.floor(n)

            insert = str(liquidStoreyNumber)
            if liquidStoreyNumber < 10:
                insert = "0" + insert
                
            index = 0
            while index < len(liquidPosition):
                el = liquidPosition[index]
                # if the rounding of the liquid storeys is uneven,
                # the last liquid floor is increased of 1 storeyx
                if index == len(liquidPosition) -1 and  math.modf(n)[0] > 0:
                    insert = str(liquidStoreyNumber +1) 
                    if liquidStoreyNumber +1 < 10:
                        insert = "0" + insert

                storey_list_A = storey_list_A[:el] + insert[0] + storey_list_A[el +1:]
                storey_list_B = storey_list_B[:el] + insert[1] + storey_list_B[el +1:]
                # print("el", el)
                index += 1
        # the 1 is readded
        storey_list_A = "1" + storey_list_A  
        storey_list_B = "1" + storey_list_B
            
    for a in mass_attribute_set:
        try:
            mesh.attributes[a["attr"]]
        except:
            if a["attr_domain"] is None: # to set custom attributes to the object, not to vertex, edge or face
                obj[a["attr"]] = a["attr_default"]
            else:
                mesh.attributes.new(name=a["attr"], type=a["attr_type"], domain=a["attr_domain"])
                if a["attr_domain"] == 'FACE':
                    attribute = mesh.attributes[a["attr"]].data.items()
                    for face in mesh.polygons:
                        index = face.index
                        for mesh_attribute in attribute:
                            if mesh_attribute[0]  == index:
                                if a["attr"] == "mastro_typology_id":
                                    mesh_attribute[1].value = bpy.context.scene.mastro_typology_name_list[typology_id].id
                                elif a["attr"] == "mastro_list_use_id_A": 
                                    mesh_attribute[1].value = int(use_id_list_A)
                                elif a["attr"] == "mastro_list_use_id_B": 
                                    mesh_attribute[1].value = int(use_id_list_B)
                                elif a["attr"] == "mastro_list_storey_A":
                                    mesh_attribute[1].value = int(storey_list_A)
                                elif a["attr"] == "mastro_list_storey_B":
                                    mesh_attribute[1].value = int(storey_list_B)
                                elif a["attr"] == "mastro_list_height_A":
                                    mesh_attribute[1].value = int(height_A)
                                elif a["attr"] == "mastro_list_height_B":
                                    mesh_attribute[1].value = int(height_B)
                                elif a["attr"] == "mastro_list_height_C":
                                    mesh_attribute[1].value = int(height_C)
                                elif a["attr"] == "mastro_list_height_D":
                                    mesh_attribute[1].value = int(height_D)
                                elif a["attr"] == "mastro_list_height_E":
                                    mesh_attribute[1].value = int(height_E)
                                elif a["attr"] == "mastro_list_void":
                                    mesh_attribute[1].value = int(void)
                                break
                elif a["attr_domain"] == 'EDGE':
                    attribute = mesh.attributes[a["attr"]].data.items()
                    for edge in mesh.edges:
                        index = edge.index
                        for mesh_attribute in attribute:
                            if mesh_attribute[0]  == index:
                                mesh_attribute[1].value = a["attr_default"]
                                break
                #     
                #     attribute[0][1].value = None

# assign the mass attributes to the selected object
def addPlotAttributes(obj):
    obj.mastro_props['mastro_plot_attribute'] = 0
    obj.mastro_props['mastro_block_attribute'] = 0
    mesh = obj.data
    mesh["MaStro object"] = True
    mesh["MaStro plot"] = True
    
    typology_id = bpy.context.scene.mastro_typology_name_list_index
    projectUses = bpy.context.scene.mastro_use_name_list
    
    use_list = bpy.context.scene.mastro_typology_name_list[typology_id].useList
    useSplit = use_list.split(";")

    use_id_list_A = "1"
    use_id_list_B = "1"
    storey_list_A = "1"
    storey_list_B = "1"
    height_A = "1"
    height_B = "1"
    height_C = "1"
    height_D = "1"
    height_E = "1"
    liquidPosition = []
    fixedStoreys = 0
    numberOfStoreys = 3 # default value for initial number of storeys
    void = "1"
    
    for enum,el in enumerate(useSplit):
        if int(el) < 10:
            tmpUse = "0" + el
        else:
            tmpUse = str(el)
       
        # print(el[0], el[1])
        use_id_list_A += tmpUse[0]
        use_id_list_B += tmpUse[1]
        
        
            
        for use in projectUses:
            if use.id == int(el):
                # number of storeys for the use
                # if a use is "liquid" the number of storeys is set as 00
                if use.liquid: 
                    storeys = "00"
                    liquidPosition.append(enum)
                else:
                    fixedStoreys += use.storeys
                    storeys = str(use.storeys)
                    if use.storeys < 10:
                        storeys = "0" + storeys

                storey_list_A += storeys[0]
                storey_list_B += storeys[1]
                
                void += str(int(use.void))
                
                height = str(round(use.floorToFloor,3))
                if use.floorToFloor < 10:
                    height = "0" + height
                height_A += height[0]
                height_B += height[1]
                try:
                    # height[3]
                    height_C += height[3]
                    try:
                        height_D += height[4]
                        try:
                            height_E += height[5]
                        except:
                            height_E += "0"
                    except:
                        height_D += "0"
                        height_E += "0"
                except:
                    height_C += "0"
                    height_D += "0"
                    height_E += "0"
                break
            
        storeyCheck = numberOfStoreys - fixedStoreys - len(liquidPosition)
        # if the typology has more storeys than the selected mass
        # some extra storeys are added
        if storeyCheck < 1: 
            bpy.context.scene.attribute_mass_storeys = fixedStoreys + len(liquidPosition)
        storeyLeft = numberOfStoreys - fixedStoreys
        
        # the 1 at the start of the number is removed
        storey_list_A = storey_list_A[1:]
        storey_list_B = storey_list_B[1:]  
        if len(liquidPosition) > 0:
            n = storeyLeft/len(liquidPosition)
            liquidStoreyNumber = math.floor(n)

            insert = str(liquidStoreyNumber)
            if liquidStoreyNumber < 10:
                insert = "0" + insert
                
            index = 0
            while index < len(liquidPosition):
                el = liquidPosition[index]
                # if the rounding of the liquid storeys is uneven,
                # the last liquid floor is increased of 1 storeyx
                if index == len(liquidPosition) -1 and  math.modf(n)[0] > 0:
                    insert = str(liquidStoreyNumber +1) 
                    if liquidStoreyNumber +1 < 10:
                        insert = "0" + insert

                storey_list_A = storey_list_A[:el] + insert[0] + storey_list_A[el +1:]
                storey_list_B = storey_list_B[:el] + insert[1] + storey_list_B[el +1:]
                # print("el", el)
                index += 1
        # the 1 is readded
        storey_list_A = "1" + storey_list_A  
        storey_list_B = "1" + storey_list_B
            
    for a in plot_attribute_set:
        try:
            mesh.attributes[a["attr"]]
        except:
            if a["attr_domain"] is None: # to set custom attributes to the object, not to vertex, edge or face
                obj[a["attr"]] = a["attr_default"]
            else:
                edge_attr_name = f"{a['attr']}_EDGE"
                face_attr_name = a['attr']
                
                mesh.attributes.new(name=edge_attr_name, type=a["attr_type"], domain="EDGE")
                mesh.attributes.new(name=face_attr_name, type=a["attr_type"], domain="FACE")

                if a["attr_domain"] == 'EDGE':
                    attribute = mesh.attributes[edge_attr_name].data.items()
                    for edge in mesh.edges:
                        index = edge.index
                        for mesh_attribute in attribute:
                            if mesh_attribute[0]  == index:
                                if a["attr"] == "mastro_typology_id":
                                    mesh_attribute[1].value = bpy.context.scene.mastro_typology_name_list[typology_id].id
                                elif a["attr"] == "mastro_list_use_id_A": 
                                    mesh_attribute[1].value = int(use_id_list_A)
                                elif a["attr"] == "mastro_list_use_id_B": 
                                    mesh_attribute[1].value = int(use_id_list_B)
                                elif a["attr"] == "mastro_list_storey_A":
                                    mesh_attribute[1].value = int(storey_list_A)
                                elif a["attr"] == "mastro_list_storey_B":
                                    mesh_attribute[1].value = int(storey_list_B)
                                elif a["attr"] == "mastro_list_height_A":
                                    mesh_attribute[1].value = int(height_A)
                                elif a["attr"] == "mastro_list_height_B":
                                    mesh_attribute[1].value = int(height_B)
                                elif a["attr"] == "mastro_list_height_C":
                                    mesh_attribute[1].value = int(height_C)
                                elif a["attr"] == "mastro_list_height_D":
                                    mesh_attribute[1].value = int(height_D)
                                elif a["attr"] == "mastro_list_height_E":
                                    mesh_attribute[1].value = int(height_E)
                                elif a["attr"] == "mastro_list_void":
                                    mesh_attribute[1].value = int(void)
                                else:
                                    mesh_attribute[1].value = a["attr_default"]
                                break
                            
# add street attributes to the selected object
def addStreetAttributes(obj):
    # obj.mastro_props['mastro_option_attribute'] = 1
    # obj.mastro_props['mastro_phase_attribute'] = 1
    mesh = obj.data
    mesh["MaStro object"] = True
    mesh["MaStro street"] = True
    
    street_id = bpy.context.scene.mastro_street_name_list_index
    width = bpy.context.scene.mastro_street_name_list[street_id].streetWidth
    radius = bpy.context.scene.mastro_street_name_list[street_id].streetRadius
    
    for a in street_attribute_set:
        try:
            mesh.attributes[a["attr"]]
        except:
            if a["attr_domain"] is None: # to set custom attributes to the object, not to vertex, edge or face
                obj[a["attr"]] = a["attr_default"]
            else:
                mesh.attributes.new(name=a["attr"], type=a["attr_type"], domain=a["attr_domain"])
                if a["attr_domain"] == 'EDGE':
                    attribute = mesh.attributes[a["attr"]].data.items()
                    for edge in mesh.edges:
                        index = edge.index
                        for mesh_attribute in attribute:
                            if mesh_attribute[0]  == index:
                                if a["attr"] == "mastro_street_id":
                                    mesh_attribute[1].value = street_id
                                elif a["attr"] == "mastro_street_width": 
                                    mesh_attribute[1].value = width
                                elif a["attr"] == "mastro_street_radius": 
                                    mesh_attribute[1].value = radius
                                break
    
# import the mastro nodes in the file
def addNodes():
    for mod in addon_utils.modules():
        if mod.bl_info['name'] == 'MaStro':
            my_addon_path = Path(mod.__file__).parent.resolve()
            break

    # my_addon_path = Path(bpy.utils.user_resource('EXTENSIONS'))
    blend_file_path = my_addon_path / "mastro.blend"
    # if not os.path.isdir(blend_file_path): blend_file_path = my_addon_path / "vscode_development/mastro/mastro.blend"
    inner_path = "NodeTree"
    
    geoNodes_list = ("MaStro Mass", "MaStro Plot", "MaStro Street")

    for group in geoNodes_list:
        if group not in bpy.data.node_groups:
            bpy.ops.wm.append(
                filepath=str(blend_file_path / inner_path / group),
                directory=str(blend_file_path / inner_path),
                filename = group
                )   

    

        
    
    
    
# class MaStro_MenuOperator_PrintData(Operator):
#     bl_idname = "object.mastro_print_data"
#     bl_label = "Print the data of the mass"
    
#     text : bpy.props.StringProperty (
#         name = "text",
#         default = "aggregate"
#     )

#     def execute(self, context):
#         roughData = []
#         csvData = []
#         csvTemp = []
#         objects = [obj for obj in bpy.context.scene.objects]
#         for obj in objects:
#             if obj.visible_get() and obj.type == "MESH" and "MaStro object" in obj.data:
#                 csvTemp.append(get_mass_data(obj))
#         for sublist in csvTemp:
#             roughData.extend(sublist)
            
#         if self.text == "aggregate":
#             csvData = aggregateData(roughData)
#         else:
#             csvData = granularData(roughData)
        
#         print("")
#         print("")
#         tab = "\t"
#         for r, row in enumerate(csvData):
#             string = ""
#             for el in row:
#                 if isinstance(el, float): # if the entry is a float, it is rounded
#                      el = Decimal(el)
#                      el = el.quantize(Decimal('0.001'))
                     
#                 i = 1
#                 tabs = tab
#                 while i < 3:
#                     if len(str(el) + tabs) >= 9:
#                         break
#                     else:
#                         i += 1
#                         t = 1
#                         while t < i-1:
#                             tabs = tabs + tab
#                             t += 1
                
        
#         # level = Decimal(level)
#         # level = level.quantize(Decimal('0.001'))
        
                    
#                 string = string + str(el) + tabs
#             if r == 1: print("--------------------------------------------------------------------------------------------------------------------------------------------------------------")
#             print(f"{string}")
#         print("")
        
#         return {'FINISHED'}
    
# class MaStro_MenuOperator_ExportCSV(Operator, ExportHelper):
#     """Export the data of the visibile MaStro Objects as a CSV file"""
#     bl_idname = "object.mastro_export_csv"
#     bl_label = "Export data as CSV"
    
#     filename_ext = ".csv"
#     filter_glob: StringProperty(
#         default="*.csv",
#         options={'HIDDEN'},
#         maxlen=255,  # Max internal buffer length, longer would be clamped.
#     )
    
#     filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    
#     def execute(self, context):
#         return writeCSV(context, self.filepath)

class MaStro_Operator_transform_orientation(Operator):
    """Create transform orientation from the last selected edge or the last two vertices"""
    bl_idname = "transform.set_orientation_from_selection"
    bl_label = "Selection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.object
        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, "Select a mesh object")
            return {'CANCELLED'}

        # Ensure we're in Edit Mesh mode
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(obj.data)

        p1, p2 = None, None

        # Caso 1: ultimo edge selezionato
        if bm.select_history and isinstance(bm.select_history[-1], bmesh.types.BMEdge):
            last_edge = bm.select_history[-1]
            v1, v2 = last_edge.verts
            p1 = obj.matrix_world @ v1.co
            p2 = obj.matrix_world @ v2.co

        # Caso 2: ultimi due vertici selezionati
        else:
            verts_in_history = [elem for elem in bm.select_history if isinstance(elem, bmesh.types.BMVert)]
            if len(verts_in_history) >= 2:
                v1, v2 = verts_in_history[-2:]
                p1 = obj.matrix_world @ v1.co
                p2 = obj.matrix_world @ v2.co

        if not p1 or not p2:
            self.report({'ERROR'}, "Select at least one edge or two vertices")
            return {'CANCELLED'}

        # Project points onto XY plane
        p1 = p1.copy(); p1.z = 0
        p2 = p2.copy(); p2.z = 0

        # Compute tangent
        tangent = (p2 - p1).normalized()

        # Build axes
        y_axis = tangent
        x_axis = mathutils.Vector((0, 0, 1)).cross(y_axis)
        if x_axis.length == 0:
            x_axis = mathutils.Vector((1, 0, 0))
        z_axis = y_axis.cross(x_axis)

        # Normalize
        x_axis.normalize()
        y_axis.normalize()
        z_axis.normalize()

        # Matrix
        matrix = mathutils.Matrix((x_axis, y_axis, z_axis)).transposed()

        # Create transform orientation
        bpy.ops.transform.create_orientation(name="Selection", use=True, overwrite=True)
        orientation = context.scene.transform_orientation_slots[0]
        orientation.custom_orientation.matrix = matrix
        context.scene.transform_orientation_slots[0].type = 'Selection'

        # Stay in Edit Mode
        bpy.ops.object.mode_set(mode='EDIT')

        return {'FINISHED'}

# Replace the existing Orientations pie menu, adding custom orientations
# class VIEW3D_MT_orientations_pie(Menu):
#     bl_label = "Orientation"

#     def draw(self, context):
#         obj = context.object
        
#         layout = self.layout
#         pie = layout.menu_pie()
#         scene = context.scene

#         pie.prop(scene.transform_orientation_slots[0], "type", expand=True)
        
#         custom = pie.column()
#         gap = custom.column()
#         gap.separator()
#         gap.scale_y = 25
#         custom_menu = custom.box().column()
#         # custom_menu.scale_y=1.3
#         # custom_menu.label(text="Custom:")
       
#         custom_menu.operator("transform.create_orientation", text="New", icon='ADD', emboss=False).use = True
#         if obj.mode == 'EDIT' and obj is not None and obj.type == 'MESH':
#             custom_menu.operator("transform.set_orientation_from_selection", text="New from Edge", icon='EDGESEL', emboss=False)
#         # custom_menu.prop(scene.transform_orientation_slots[0], "type", expand=True)
#         # orient_slot = scene.transform_orientation_slots[0]
#         # orientation = orient_slot.custom_orientation
#         # custom_menu.prop(orient_slot, "type", expand=True)
#         custom_orientations = bpy.context.scene.transform_orientation_slots[0]
#         if custom_orientations:
#             custom_names = [ori.name for ori in custom_orientations]
        
       
       

        
# Replace the existing Transform Orientations panel in the UI, adding "orientation from edge"
class VIEW3D_PT_transform_orientations(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Transform Orientations"
    bl_ui_units_x = 8

    def draw(self, context):
        
        obj = context.object
        
        # constaint_xy_settings = context.scene.constraint_xy_setting
        # if obj is None or obj.type != 'MESH':
        #     self.report({'ERROR'}, "Select a mesh object")
        #     return {'CANCELLED'}
        
        layout = self.layout
        layout.label(text="Transform Orientations")
        
        scene = context.scene
        orient_slot = scene.transform_orientation_slots[0]
        orientation = orient_slot.custom_orientation
      

        row = layout.row()
        col = row.column(align=True)
        
        col = row.column(align=True)
        col.prop(orient_slot, "type", expand=True)
         
        col_operators = row.column(align=True)
        # icon_value = icons.icon_id('AC_ON') if constaint_xy_settings.constraint_xy_on else icons.icon_id('AC_OFF')
        # col_operators.prop(constaint_xy_settings, 'constraint_xy_on', text='', icon_value=icon_value)
       
        col_operators.operator("transform.create_orientation", text="", icon='ADD', emboss=False)
        # this creates a new orientation from the selected edge
        if obj.mode == 'EDIT' and obj is not None and obj.type == 'MESH':
            col_operators.operator("transform.set_orientation_from_selection", text="", icon="EDGESEL", emboss=False)
        
        if orientation:
            row = layout.row(align=False)
            row.prop(orientation, "name", text="", icon='OBJECT_ORIGIN')
            row.operator("transform.delete_orientation", text="", icon='X', emboss=False)

# # Extend the existing Transform Orientations panel in the UI
# def extend_transform_operation_panel(self, context):
#     layout = self.layout
#     layout.operator("transform.set_orientation_from_selection", text="Set Orientation from Edge")
        
class ConstraintXYSettings(bpy.types.PropertyGroup):
    """Property Group for all xy constraint scene properties"""
    constraint_xy_on: bpy.props.BoolProperty(
        name = 'XY constraints',
        default = False,
        description = 'Toggle XY constraint behaviour globally'
    )
    # last_custom_orientation: bpy.props.StringProperty(
    #     name = 'Auto-constraint last custom orientation',
    #     default = "",
    #     description = 'Used to store the last used custom orientation so we can clean it up next transform (there is a crash if deleted with the current operator and then locking to an axis manually'
    # )
            
# define the constraint to xy axis button
def constraint_xy_button(self, context):
    """Draws the xy constraint toggle"""
    if context.mode not in contexts:
        return
    constaint_xy_settings = context.scene.constraint_xy_setting
    layout = self.layout
    row = layout.row(align=True)
    icon_value = icons.icon_id('xy_on') if constaint_xy_settings.constraint_xy_on else icons.icon_id('xy_off')
    row.prop(constaint_xy_settings, "constraint_xy_on", text="", icon_value=icon_value)
    
    
def aggregateData(roughData):
    roughData = sorted(roughData, key=lambda x:(x[0], x[1], x[2], x[3], x[4]))
        
    data = []
    data.append(roughData[0])

    for el in roughData[1:]:
        if el[:5] == data[-1][:5]:
            prev_storeys = data[-1][5]
            # update number of storeys
            storeys = el[5]
            if storeys > prev_storeys:
                data[-1][5] = storeys
            # sum footprint
            data[-1][7] += el[7]
            # sum perimeter
            data[-1][8] += el[8]
            # sum wall
            data[-1][9] += el[9]
            # sum GEA
            data[-1][10] += el[10]
        else:
            data.append(el)
            
    # remove unwanted elements
    for index, el in enumerate(data):
        del data[index][11] #edge
        del data[index][6] #level
        
    data = sorted(data, key=lambda x:(x[0], x[1], x[2], x[3], x[4]))
    data.insert(0, header_aggregateData)

    return(data)


# def granularData(roughData):
#     roughData = sorted(roughData, key=lambda x:(x[0], x[1], x[2], x[3], x[4], x[6]))
    
#     data = []
#     data.append(roughData[0])

#     for el in roughData[1:]:
#         if el[:6] == data[-1][:6]:
#             # prev_storeys = data[-1][5]
#             # # update number of storeys
#             # storeys = el[5]
#             # if storeys > prev_storeys:
#             #     data[-1][5] = storeys
#             # sum footprint
#             data[-1][7] += el[7]
#             # sum perimeter
#             data[-1][8] += el[8]
#             # sum wall
#             data[-1][9] += el[9]
#         else:
#            data.append(el)
           
#     expandedData = []
#     for index, el in reversed(list(enumerate(data))):
#         # if there is more than one floor,
#         # it is necessary to unwrap data
#         if el[5] > 1:
#             edges = el[11]
            
#             for i, e in enumerate(range(el[5]), 1):
#                 floor = i
#                 level = el[6] + (floorToFloorLevel * i)
                
#                 perimeter = 0
#                 for edge in edges:
#                     if edge.perimeter == True:
#                         perimeter += edge.length
#                     else:
#                         # check if the current storey is in the range of that edge. 
#                         # The range is the maximum number of storey for that edge minus the number of the visible storey
#                         if floor >= (edge.topStorey - edge.storeys +1):
#                             perimeter += edge.length
#                             # print(edge.index, edge.face, edge.length, edge.storeys, edge.topStorey)
#                 # perimeter = None
#                 wallArea = perimeter * floorToFloorLevel
#                 expandedData.append([el[0], el[1], el[2], el[3], el[4], floor, level, el[7], perimeter, wallArea])
#             del data[index]
            
#     data.extend(expandedData)
    
#     # remove unwanted elements
#     for index, el in enumerate(data):
#         if len(data[index]) == 12: # only some entryes have the element we want to delete
#             del data[index][11] #edge
#         if len(data[index]) == 11: # only some entryes have the element we want to delete
#             del data[index][10] #GEA
    
#     #once all the levels are set, it is necessary to group the ones with the same features
#     data = sorted(data, key=lambda x:(x[0], x[1], x[2], x[3], x[4], x[5]))
    
#     granularData = []
#     granularData.append(data[0])

#     for el in data[1:]:
#         if el[:6] == granularData[-1][:6]:
#             # sum footprint
#             granularData[-1][7] += el[7]
#             # sum perimeter
#             granularData[-1][8] += el[8]
#             # sum wall
#             granularData[-1][9] += el[9]
#         else:
#            granularData.append(el)
        
#     granularData.insert(0, header_granularData)

#     return(granularData)
    
   
# def writeCSV(context, filepath):
#     csvData = []
#     data = []
#     dataRough = []

#     objects = [obj for obj in bpy.context.scene.objects]

#     for obj in objects:
#         if obj.visible_get() and obj.type == "MESH" and "MaStro object" in obj.data:
#             dataRough.append(get_mass_data(obj))

#     for sublist in dataRough:
#         data.extend(sublist)
        
#     csvData = granularData(data)

#     with open(filepath, 'w', newline='') as csvfile:
#         writer = csv.writer(csvfile)
#         writer.writerows(csvData)

#     print(f"Data saved to {filepath}")
#     return {'FINISHED'}
    
    
# Callback function to add drop down menu
# def mastro_menu(self, context):
#     layout = self.layout
#     layout.menu(MaStro_Menu.bl_idname)


# def get_mass_data(obj):
#     #mesh = obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
#     if "mastro_option_attribute" in obj.mastro_props.keys():
#         option = obj.mastro_props['mastro_option_attribute']
#     else:
#         option = None
        
#     if "mastro_phase_attribute" in obj.mastro_props.keys():
#         phase = obj.mastro_props['mastro_phase_attribute']
#     else:
#         phase = None
    
#     phase = obj.mastro_props['mastro_phase_attribute']
    
#     mesh = obj.data
    
#     bm = bmesh.new()
#     bm.from_mesh(mesh)
        
#     data = []
    
#     # bm_layer_plot = bm.faces.layers.int["mastro_plot_id"]
#     # bm_layer_block = bm.faces.layers.int["mastro_block_id"]
#     bm_layer_typology = bm.faces.layers.int["mastro_typology_id"]
#     bm_layer_storey = bm.faces.layers.int["mastro_number_of_storeys"]
    
#     for f in bm.faces:
#         edges = []
#         #plot
#         # for n in bpy.context.scene.mastro_plot_name_list:
#         #     if n.id == f[bm_layer_plot]:
#         #         plot = n.name
#         #         break

#         #block
#         # for n in bpy.context.scene.mastro_block_name_list:
#         #     if n.id == f[bm_layer_block]:
#         #         block = n.name
#         #         break

#         #typology
#         for n in bpy.context.scene.mastro_typology_name_list:
#             if n.id == f[bm_layer_typology]:
#                 typology = n.name
#                 break

#         storeys = f[bm_layer_storey]

#         footprint = f.calc_area()

#         GEA = footprint * storeys
        
#         #perimeter        
#         perimeter = 0
#         common_edges = []
#         for e in f.edges:
#             edge = faceEdge()
#             # edge.objName = obj.name
#             edge.index = e.index
#             edge.face = f.index
#             edge.length = e.calc_length()
#             edge.topStorey = storeys
#             edge.storeys = None
#             # if there is no angle, then the edge is not a edge in common between faces
#             try:
#                 angle = e.calc_face_angle()
#                 common_edges.append(e.index)
#                 edge.perimeter = False
#             except ValueError:
#                 perimeter += edge.length
#                 edge.perimeter = True
#                 edge.storeys = storeys
#             edges.append(edge)
        
#         #wall area
#         # this is the area of the perimeter walls
       
#         wall_area = perimeter * floorToFloorLevel * storeys
#         # but if the faces having an edge in common have different storey numbers,
#         # then the difference is added to the wall area
#         for index in common_edges:
#             for fa in bm.faces: 
#                 if f.index != fa.index: #there is no point in evaluating the same face
#                     for ed in fa.edges:
#                         if index == ed.index:
#                             if f[bm_layer_storey] > fa[bm_layer_storey]:
#                                 diff = f[bm_layer_storey] - fa[bm_layer_storey]
#                                 length = ed.calc_length()
#                                 wall_area += length * diff * floorToFloorLevel
#                                 for ed in edges:
#                                     if ed.index == index:
#                                         ed.storeys = diff 
#                                         break
        
#         # removes the edges marked as not perimeter 
#         # and are duplicates of the edges that are visibile
#         for index, edge in reversed(list(enumerate(edges))):
#             if edge.storeys == None:
#                 edges.pop(index)
        
#         #lowest Z coordinate of the face
#         obj_origin_z = obj.location[2]
#         face_z = f.calc_center_median()[2]
#         level = obj_origin_z + face_z
        
#         # GEA = Decimal(GEA)
#         # GEA = GEA.quantize(Decimal('0.01'), rounding=ROUND_HALF_DOWN)
        
#         # wall_area = Decimal(wall_area)
#         # wall_area = wall_area.quantize(Decimal('0.01'), rounding=ROUND_HALF_DOWN)
        
#         # perimeter = Decimal(perimeter)
#         # perimeter = perimeter.quantize(Decimal('0.01'), rounding=ROUND_HALF_DOWN)
        
#         # footprint = Decimal(footprint)
#         # footprint = footprint.quantize(Decimal('0.01'), rounding=ROUND_HALF_DOWN)
        
#         # level = Decimal(level)
#         # level = level.quantize(Decimal('0.001'))
        
#         data.append([option, phase, plot, block, typology, storeys, level, footprint, perimeter, wall_area, GEA, edges])
            
#     return(data)
