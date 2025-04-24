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
#import bmesh 

from bpy.types import Operator, Panel
        
class VIEW3D_PT_MaStro_vertex(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MaStro"
    bl_label = "Vertex"
    
    def draw(self, context):
        obj = context.active_object
        mesh = obj.data
        if obj.mode == 'EDIT':
            try:
                mesh.attributes["mastro_vertex_custom_attribute"]
            except:
                mesh.attributes.new(name="mastro_vertex_custom_attribute", type="INT", domain="POINT")
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.
        
        layout.prop(context.scene, "attribute_vertex", text="Custom Attribute")
    
#class OPERATOR_update_MaStro_wall_attribute(bpy.types.Operator):
class OBJECT_OT_SetVertexAttribute(Operator):
    """Assign a wall type to the selected edge"""
    bl_idname = "object.set_attribute_vertex"
    bl_label = "Assign a custom value to the selected vertex"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        mesh = obj.data
        
        attribute_vertex = bpy.context.scene.attribute_vertex
        try:
            mesh.attributes["mastro_vertex_custom_attribute"]
            
            # we need to switch from Edit mode to Object mode so the selection gets updated
            mode = obj.mode
            bpy.ops.object.mode_set(mode='OBJECT')

            selected_vertices = [v for v in bpy.context.active_object.data.vertices if v.select]

            mesh_attributes = mesh.attributes["mastro_vertex_custom_attribute"].data.items()

            for vertex in selected_vertices:
                index = vertex.index
                for mesh_attribute in mesh_attributes:
                    if mesh_attribute[0] == index:
                        mesh_attribute[1].value = attribute_vertex

            # back to whatever mode we were in
            bpy.ops.object.mode_set(mode=mode)
                    
            self.report({'INFO'}, "Attribute set to vertex "+str(attribute_vertex))
            return {'FINISHED'}
        except:
            return {'FINISHED'}    
    
    
# def add_MaStro_wall(self, context):
#     scale_x = self.scale.x
#     # scale_y = self.scale.y

#     verts = [
#         Vector((0, 0, 0)),
#         Vector((10 * scale_x, 0, 0))
#     ]

#     edges = [[0,1]]
#     faces = []

#     mesh = bpy.data.meshes.new(name="MaStro wall")
#     mesh.from_pydata(verts, edges, faces)
#     # useful for development when the mesh may be invalid.
#     # mesh.validate(verbose=True)
#     object_data_add(context, mesh, operator=self)
#     mesh.attributes.new(name="mastro_wall_type", type="INT", domain="EDGE")
#     mesh.attributes.new(name="mastro_plot_name", type="STRING", domain="FACE")
    
# def add_MaStro_wall_button(self, context):
#     self.layout.operator(
#         OBJECT_OT_add_MaStro_wall.bl_idname,
#         text="MaStro Wall",
#         icon='PLUGIN')
    

    
def update_attribute_vertex(self, context):
    bpy.ops.object.set_attribute_vertex()
 