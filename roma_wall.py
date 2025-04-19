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

class VIEW3D_PT_RoMa_Wall(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "RoMa"
    bl_label = "Architecture"
    
    @classmethod
    def poll(cls, context):
        return (context.object is not None and 
                context.object.type == "MESH" and 
                context.object.mode == "EDIT" and
                "RoMa object" in context.object.data and
                "RoMa mass" in context.object.data)
    
    def draw(self, context):
        obj = context.active_object 
        if obj is not None and obj.type == "MESH":
            mode = obj.mode
            if mode == "EDIT":
                scene = context.scene
                layout = self.layout
                layout.use_property_split = True    
                layout.use_property_decorate = False  # No animation.
                
                ################ WALL ######################
                row = layout.row()
                row = layout.row(align=True)
                
                if tuple(bpy.context.scene.tool_settings.mesh_select_mode)[1] == True: #we are selecting edges
                    row.enabled = True
                else:
                    row.enabled = False
                
                row.prop(context.scene, "roma_wall_names", icon="NODE_TEXTURE", icon_only=True, text="Wall Type")
                if len(scene.roma_plot_name_list) >0:
                    row.label(text = scene.roma_wall_name_current[0].name)
                    wallId = scene.roma_wall_name_current[0].id
                    # thickness = round(scene.roma_wall_name_list[wallId].wallThickness,3)
                    thickness = "%.3f" % scene.roma_wall_name_list[wallId].wallThickness
                    layout.label(text = str(thickness))
                    # scene.attribute_wall_thickness = thickness
                    layout.prop(context.scene, 'attribute_wall_thickness', text="Thickness")
                    # layout.prop(context.scene, 'attribute_wall_offset', text="Offset")
                else:
                    row.label(text = "")
                
                
                # layout.prop(context.scene, 'attribute_wall_normal', toggle=True, icon="ARROW_LEFTRIGHT", icon_only=True)
                
                
                ################ FLOOR ######################
                row = layout.row()
                row = layout.row(align=True)
                
                if tuple(bpy.context.scene.tool_settings.mesh_select_mode)[2] == True: #we are selecting edges
                    row.enabled = True
                else:
                    row.enabled = False
                
                row.prop(context.scene, "roma_floor_names", icon="VIEW_PERSPECTIVE", icon_only=True, text="Floor Type")
                if len(scene.roma_floor_name_list) >0:
                    row.label(text = scene.roma_floor_name_current[0].name)
                else:
                    row.label(text = "")
                
############################        ############################
############################ WALL ############################
############################        ############################

class OBJECT_OT_SetWallId(Operator):
    """Set Face Attribute as use of the block"""
    bl_idname = "object.set_attribute_wall_id"
    bl_label = "Set Edge Attribute as Wall type"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        mesh = obj.data

        # attribute_wall_id = context.scene.attribute_wall_id
        
        try:
            mesh.attributes["roma_wall_id"]
            attribute_wall_id = context.scene.attribute_wall_id
            thickness = context.scene.roma_wall_name_list[attribute_wall_id].wallThickness

            mode = obj.mode
            bpy.ops.object.mode_set(mode='OBJECT')
           
            selected_edges = [e for e in bpy.context.active_object.data.edges if e.select]
            mesh_attributes_id = mesh.attributes["roma_wall_id"].data.items()
            mesh_attributes_thickness = mesh.attributes["roma_wall_thickness"].data.items()
            for edge in selected_edges:
                index = edge.index
                for ind, mesh_attribute in enumerate(mesh_attributes_id):
                    if mesh_attribute[0] == index:
                        mesh_attribute[1].value = attribute_wall_id
                        mesh_attributes_thickness[ind][1].value = thickness
            bpy.ops.object.mode_set(mode=mode)
                    
            # self.report({'INFO'}, "Attribute set to face, use: "+str(attribute_mass_use_id))
            return {'FINISHED'}
        except:
            return {'FINISHED'}
        
class OBJECT_OT_SetWallNormal(Operator):
    """Invert the normal of the selected wall"""
    bl_idname = "object.set_attribute_wall_normal"
    bl_label = "Flip the normal of the selected edge"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        mesh = obj.data

        attribute_wall_normal = context.scene.attribute_wall_normal
        
        try:
            mesh.attributes["roma_wall_id"]
            mode = obj.mode
            bpy.ops.object.mode_set(mode='OBJECT')
           
            selected_edges = [e for e in bpy.context.active_object.data.edges if e.select]
            mesh_attributes_normals = mesh.attributes["roma_inverted_normal"].data.items()
            
            for edge in selected_edges:
                index = edge.index
                for mesh_attribute in mesh_attributes_normals:
                    if mesh_attribute[0] == index:
                        # mesh_attribute[1].value = attribute_wall_normal*1 # convert boolean to 0 or 1
                        if attribute_wall_normal:
                            mesh_attribute[1].value = -1
                        else:
                            mesh_attribute[1].value = 1
                
            bpy.ops.object.mode_set(mode=mode)
                    
            # self.report({'INFO'}, "Attribute set to face, use: "+str(attribute_mass_use_id))
            return {'FINISHED'}
        except:
            return {'FINISHED'}
        
def update_wall_normal(self, context):
    bpy.ops.object.set_attribute_wall_normal()

def update_attribute_wall_id(self, context):
    bpy.ops.object.set_attribute_wall_id()
    
def update_wall_name_label(self, context):
    scene = context.scene
    name = scene.roma_wall_names
    scene.roma_wall_name_current[0].name = " " + name
    for n in scene.roma_wall_name_list:
        if n.name == name:
            scene.attribute_wall_id = n.id
            scene.roma_wall_name_current[0].id = n.id
            break 
        
############################        ############################
############################ FLOOR  ############################
############################        ############################

class OBJECT_OT_SetFloorId(Operator):
    """Set Face Attribute as floor type"""
    bl_idname = "object.set_attribute_floor_id"
    bl_label = "Set Face Attribute as Floor Type"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        mesh = obj.data

        attribute_floor_id = context.scene.attribute_floor_id
        
        try:
            mesh.attributes["roma_floor_id"]
            attribute_floor_id = context.scene.attribute_floor_id

            mode = obj.mode
            bpy.ops.object.mode_set(mode='OBJECT')
           
            selected_faces = [f for f in bpy.context.active_object.data.polygons if f.select]
            mesh_attributes_id = mesh.attributes["roma_floor_id"].data.items()
            for face in selected_faces:
                index = face.index
                for mesh_attribute in mesh_attributes_id:
                    if mesh_attribute[0] == index:
                        mesh_attribute[1].value = attribute_floor_id
                
            bpy.ops.object.mode_set(mode=mode)
                    
            # self.report({'INFO'}, "Attribute set to face, use: "+str(attribute_mass_use_id))
            return {'FINISHED'}
        except:
            return {'FINISHED'}
        

def update_attribute_floor_id(self, context):
    bpy.ops.object.set_attribute_floor_id()
    
def update_floor_name_label(self, context):
    scene = context.scene
    name = scene.roma_floor_names
    scene.roma_floor_name_current[0].name = " " + name
    for n in scene.roma_floor_name_list:
        if n.name == name:
            scene.attribute_floor_id = n.id
            scene.roma_floor_name_current[0].id = n.id
            break 
