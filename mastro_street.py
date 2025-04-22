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
from bpy.types import Operator, Panel

class VIEW3D_PT_RoMa_Road(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "RoMa"
    bl_label = "Road"
    
    @classmethod
    def poll(cls, context):
        return (context.object is not None and
                context.selected_objects != [] and 
                context.object.type == "MESH" and 
                "RoMa object" in context.object.data and
                "RoMa road" in context.object.data)
    
    def draw(self, context):
        obj = context.object
        if obj is not None and obj.type == "MESH":
            mode = obj.mode
            if mode == "OBJECT":
                scene = context.scene
                
                layout = self.layout
                layout.use_property_split = True    
                layout.use_property_decorate = False  # No animation.
                
                # row = layout.row()
                row = layout.row(align=True)
                
                layout.prop(obj.roma_props, "roma_option_attribute", text="Option")
                layout.prop(obj.roma_props, "roma_phase_attribute", text="Phase")
                    
            elif mode == "EDIT":
                scene = context.scene
                
                layout = self.layout
                layout.use_property_split = True    
                layout.use_property_decorate = False  # No animation.
                
                if tuple(bpy.context.scene.tool_settings.mesh_select_mode)[1] == True: #we are selecting edges
                    layout.enabled = True
                else:
                    layout.enabled = False
                
                row = layout.row(align=True)

                row.prop(context.scene, "roma_road_names", icon="NODE_TEXTURE", icon_only=True, text="Road Type")
                if len(scene.roma_road_name_list) >0:
                    row.label(text = scene.roma_road_name_current[0].name)
                    # roadId = scene.roma_road_name_current[0].id
                else:
                    row.label(text = "")
                
# set the attributes of the selected edges
class OBJECT_OT_SetRoadId(Operator):
    bl_idname = "object.set_attribute_road_id"
    bl_label = "Set Edge Attribute as road type"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        mesh = obj.data
        mode = obj.mode
        bpy.ops.object.mode_set(mode='OBJECT')
        selected_edges = [e for e in bpy.context.active_object.data.edges if e.select]
        for edge in selected_edges:
            edgeIndex = edge.index
            data = read_mesh_attributes_roads(context, mesh, edgeIndex)
            mesh.attributes["roma_road_id"].data[edgeIndex].value = data["road_id"]
            mesh.attributes["roma_road_width"].data[edgeIndex].value = data["width"]
            mesh.attributes["roma_road_radius"].data[edgeIndex].value = data["radius"]
        bpy.ops.object.mode_set(mode=mode)
        return {'FINISHED'}
        
# function to read the roads parameters:
# if the function is run by the user when in edit mode the roadId is read from 
# context.scene.attribute_road_id, else the road id is updated from the
# road panel and the roadId used is the one stored in the edge
def read_mesh_attributes_roads(context, mesh, edgeIndex, roadSet=None):
    if roadSet == None:
        road_id = context.scene.attribute_road_id
    else:
      road_id = roadSet
    projectRoads = context.scene.roma_road_name_list
    

    data = {"road_id" : road_id,
            "width" : projectRoads[road_id].roadWidth,
            "radius" : projectRoads[road_id].roadRadius
            }  
    return data

# Update the road label in the UI and all the relative data in the selected edges
def update_attributes_road(self, context):
    scene = context.scene
    name = scene.roma_road_names
    for n in scene.roma_road_name_list:
        if n.name == name:
            scene.attribute_road_id = n.id
            bpy.ops.object.set_attribute_road_id()
            scene.roma_road_name_current[0].id = n.id
            scene.roma_road_name_current[0].name = n.name
            break 
        
