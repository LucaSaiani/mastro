import bpy
#import bmesh 

from bpy.types import Operator, Panel
        
class VIEW3D_PT_RoMa_vertex(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "RoMa"
    bl_label = "Vertex"
    
    def draw(self, context):
        obj = context.active_object
        mesh = obj.data
        if obj.mode == 'EDIT':
            try:
                mesh.attributes["roma_vertex_custom_attribute"]
            except:
                mesh.attributes.new(name="roma_vertex_custom_attribute", type="INT", domain="POINT")
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.
        
        layout.prop(context.scene, "attribute_vertex", text="Custom Attribute")
    
#class OPERATOR_update_RoMa_wall_attribute(bpy.types.Operator):
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
            mesh.attributes["roma_vertex_custom_attribute"]
            
            # we need to switch from Edit mode to Object mode so the selection gets updated
            mode = obj.mode
            bpy.ops.object.mode_set(mode='OBJECT')

            selected_vertices = [v for v in bpy.context.active_object.data.vertices if v.select]

            mesh_attributes = mesh.attributes["roma_vertex_custom_attribute"].data.items()

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
    
    
# def add_RoMa_wall(self, context):
#     scale_x = self.scale.x
#     # scale_y = self.scale.y

#     verts = [
#         Vector((0, 0, 0)),
#         Vector((10 * scale_x, 0, 0))
#     ]

#     edges = [[0,1]]
#     faces = []

#     mesh = bpy.data.meshes.new(name="RoMa wall")
#     mesh.from_pydata(verts, edges, faces)
#     # useful for development when the mesh may be invalid.
#     # mesh.validate(verbose=True)
#     object_data_add(context, mesh, operator=self)
#     mesh.attributes.new(name="roma_wall_type", type="INT", domain="EDGE")
#     mesh.attributes.new(name="roma_plot_name", type="STRING", domain="FACE")
    
# def add_RoMa_wall_button(self, context):
#     self.layout.operator(
#         OBJECT_OT_add_RoMa_wall.bl_idname,
#         text="RoMa Wall",
#         icon='PLUGIN')
    

    
def update_attribute_vertex(self, context):
    bpy.ops.object.set_attribute_vertex()
 