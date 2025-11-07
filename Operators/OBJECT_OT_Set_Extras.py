import bpy 
from bpy.types import Operator

class OBJECT_OT_Set_Vertex_Extra(Operator):
    """Set Vertex Extra float value"""
    bl_idname = "object.set_extras_vertex_value"
    bl_label = "Set Vertex Extra float value"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        mesh = obj.data
        
        try:
            mesh.attributes["mastro_custom_vert"]
            attribute_vertex = context.scene.mastro_attribute_extra_vertex

            mode = obj.mode
            bpy.ops.object.mode_set(mode='OBJECT')
           
            selected_vertices = [v for v in bpy.context.active_object.data.vertices if v.select]
            mesh_attributes = mesh.attributes["mastro_custom_vert"].data.items()
            for vert in selected_vertices:
                index = vert.index
                for mesh_attribute in mesh_attributes:
                    if mesh_attribute[0] == index:
                        mesh_attribute[1].value = attribute_vertex
                
            bpy.ops.object.mode_set(mode=mode)
            return {'FINISHED'}
        except:
            return {'FINISHED'}
        
class OBJECT_OT_Set_Edge_Extra(Operator):
    """Set Edge Extra float value"""
    bl_idname = "object.set_extras_edge_value"
    bl_label = "Set Edge Extra float value"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        mesh = obj.data
        
        try:
            mesh.attributes["mastro_custom_edge"]
            attribute_edge = context.scene.mastro_attribute_extra_edge

            mode = obj.mode
            bpy.ops.object.mode_set(mode='OBJECT')
           
            selected_edges = [e for e in bpy.context.active_object.data.edges if e.select]
            mesh_attributes = mesh.attributes["mastro_custom_edge"].data.items()
            for edge in selected_edges:
                index = edge.index
                for mesh_attribute in mesh_attributes:
                    if mesh_attribute[0] == index:
                        mesh_attribute[1].value = attribute_edge
                
            bpy.ops.object.mode_set(mode=mode)
            return {'FINISHED'}
        except:
            return {'FINISHED'}
        
class OBJECT_OT_Set_Face_Extra(Operator):
    """Set Face Extra float value"""
    bl_idname = "object.set_extras_face_value"
    bl_label = "Set Face Extra float value"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        mesh = obj.data
        
        try:
            mesh.attributes["mastro_custom_face"]
            attribute_face = context.scene.mastro_attribute_extra_face

            mode = obj.mode
            bpy.ops.object.mode_set(mode='OBJECT')
           
            selected_faces = [f for f in bpy.context.active_object.data.polygons if f.select]
            mesh_attributes = mesh.attributes["mastro_custom_face"].data.items()
            for face in selected_faces:
                index = face.index
                for mesh_attribute in mesh_attributes:
                    if mesh_attribute[0] == index:
                        mesh_attribute[1].value = attribute_face
                
            bpy.ops.object.mode_set(mode=mode)
            return {'FINISHED'}
        except:
            return {'FINISHED'}
        
