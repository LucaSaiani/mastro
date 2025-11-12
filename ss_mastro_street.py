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
from bpy.types import Operator, Panel

# class VIEW3D_PT_MaStro_Street(Panel):
#     bl_space_type = "VIEW_3D"
#     bl_region_type = "UI"
#     bl_category = "MaStro"
#     bl_label = "Street"
    
#     @classmethod
#     def poll(cls, context):
#         return (context.object is not None and
#                 # context.selected_objects != [] and 
#                 context.object.type == "MESH" and 
#                 "MaStro object" in context.object.data and
#                 "MaStro street" in context.object.data)
    
#     def draw(self, context):
#         obj = context.object
#         if obj is not None and obj.type == "MESH":
#             mode = obj.mode
#             if mode == "OBJECT":
#                 scene = context.scene
                
#                 layout = self.layout
#                 layout.use_property_split = True    
#                 layout.use_property_decorate = False  # No animation.
                
#                 # row = layout.row()
#                 row = layout.row(align=True)
                
#                 # layout.prop(obj.mastro_props, "mastro_option_attribute", text="Option")
#                 # layout.prop(obj.mastro_props, "mastro_phase_attribute", text="Phase")
                    
#             elif mode == "EDIT":
#                 scene = context.scene
                
#                 layout = self.layout
#                 layout.use_property_split = True    
#                 layout.use_property_decorate = False  # No animation.
                
#                 if tuple(bpy.context.scene.tool_settings.mesh_select_mode)[1] == True: #we are selecting edges
#                     layout.enabled = True
#                 else:
#                     layout.enabled = False
                
#                 row = layout.row(align=True)

#                 row.prop(context.scene, "mastro_street_names", icon="NODE_TEXTURE", icon_only=True, text="Street Type")
#                 if len(scene.mastro_street_name_list) >0:
#                     row.label(text = scene.mastro_street_name_current[0].name)
#                     # streetId = scene.mastro_street_name_current[0].id
#                 else:
#                     row.label(text = "")
                
# # set the attributes of the selected edges
# class OBJECT_OT_SetStreetId(Operator):
#     bl_idname = "object.set_attribute_street_id"
#     bl_label = "Set Edge Attribute as street type"
#     bl_options = {'REGISTER', 'UNDO'}
    
#     def execute(self, context):
#         obj = context.active_object
#         mesh = obj.data
#         mode = obj.mode
#         bpy.ops.object.mode_set(mode='OBJECT')
#         selected_edges = [e for e in bpy.context.active_object.data.edges if e.select]
#         for edge in selected_edges:
#             edgeIndex = edge.index
#             data = read_mesh_attributes_streets(context, mesh, edgeIndex)
#             mesh.attributes["mastro_street_id"].data[edgeIndex].value = data["street_id"]
#             mesh.attributes["mastro_street_width"].data[edgeIndex].value = data["width"]/2
#             mesh.attributes["mastro_street_radius"].data[edgeIndex].value = data["radius"]
#         bpy.ops.object.mode_set(mode=mode)
#         return {'FINISHED'}
        
# # function to read the streets parameters:
# # if the function is run by the user when in edit mode the streetId is read from 
# # context.scene.attribute_street_id, else the street id is updated from the
# # street panel and the streetId used is the one stored in the edge
# def read_mesh_attributes_streets(context, mesh, edgeIndex, streetSet=None):
#     if streetSet == None:
#         street_id = context.scene.attribute_street_id
#     else:
#       street_id = streetSet
#     projectStreets = context.scene.mastro_street_name_list

#     index = next((i for i, elem in enumerate(projectStreets) if elem.id == street_id), None)
#     data = {"street_id" : street_id,
#             "width" : projectStreets[index].streetWidth,
#             "radius" : projectStreets[index].streetRadius
#             }  
#     return data

# # Update the street label in the UI and all the relative data in the selected edges
# def update_attributes_street(self, context):
#     scene = context.scene
#     name = scene.mastro_street_names
#     for n in scene.mastro_street_name_list:
#         if n.name == name:
#             scene.attribute_street_id = n.id
#             bpy.ops.object.set_attribute_street_id()
#             scene.mastro_street_name_current[0].id = n.id
#             scene.mastro_street_name_current[0].name = n.name
#             break 
        
