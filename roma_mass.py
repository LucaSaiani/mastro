import bpy

from bpy.props import FloatVectorProperty
from bpy_extras.object_utils import (
        AddObjectHelper,
        object_data_add
)
from mathutils import Vector
from bpy.types import Operator, Panel

class OBJECT_OT_add_RoMa_Mass(Operator, AddObjectHelper):
    """Create a new RoMa Mass"""
    bl_idname = "mesh.add_roma_mass"
    bl_label = "RoMa Mass"
    bl_options = {'REGISTER', 'UNDO'}

    scale: FloatVectorProperty(
        name="scale",
        default=(1.0, 1.0, 1.0),
        subtype='TRANSLATION',
        description="scaling",
    )

    def execute(self, context):

        add_RoMa_Mass(self, context)
        return {'FINISHED'}
    
class OBJECT_OT_SetPlotName(Operator):
    """Set Face Attribute as name of the plot"""
    bl_idname = "object.set_attribute_mass_plot_name"
    bl_label = "Set Face Attribute as Name of the Plot"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        mesh = obj.data

        attribute_mass_plot_name = context.scene.attribute_mass_plot_name
        
        # a custom attribute is assigned to the edges
       
        try:
            mesh.attributes["roma_plot_name"]
            attribute_mass_plot_name = context.scene.attribute_mass_plot_name
           
            # we need to switch from Edit mode to Object mode so the selection gets updated
            mode = obj.mode
            bpy.ops.object.mode_set(mode='OBJECT')
           
            selected_faces = [p for p in bpy.context.active_object.data.polygons if p.select]
            mesh_attributes = mesh.attributes["roma_plot_name"].data.items()
            
            for face in selected_faces:
                index = face.index
                for mesh_attribute in mesh_attributes:
                    if mesh_attribute[0] == index:
                        mesh_attribute[1].value = attribute_mass_plot_name
           
            # back to whatever mode we were in
            bpy.ops.object.mode_set(mode=mode)
                    
            self.report({'INFO'}, "Attribute set to face, plot: "+str(attribute_mass_plot_name))
            return {'FINISHED'}
        except:
            return {'FINISHED'}
        
class OBJECT_OT_SetBlockName(Operator):
    """Set Face Attribute as name of the block"""
    bl_idname = "object.set_attribute_mass_block_name"
    bl_label = "Set Face Attribute as Name of the Block"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        mesh = obj.data

        attribute_mass_block_name = context.scene.attribute_mass_block_name
        
        # a custom attribute is assigned to the edges
       
        try:
            mesh.attributes["roma_block_name"]
            attribute_mass_block_name = context.scene.attribute_mass_block_name
           
            # we need to switch from Edit mode to Object mode so the selection gets updated
            mode = obj.mode
            bpy.ops.object.mode_set(mode='OBJECT')
           
            selected_faces = [p for p in bpy.context.active_object.data.polygons if p.select]
            mesh_attributes = mesh.attributes["roma_block_name"].data.items()
            
            for face in selected_faces:
                index = face.index
                for mesh_attribute in mesh_attributes:
                    if mesh_attribute[0] == index:
                        mesh_attribute[1].value = attribute_mass_block_name
           
            # back to whatever mode we were in
            bpy.ops.object.mode_set(mode=mode)
                    
            self.report({'INFO'}, "Attribute set to face, block: "+str(attribute_mass_block_name))
            return {'FINISHED'}
        except:
            return {'FINISHED'}
        
class OBJECT_OT_SetUseName(Operator):
    """Set Face Attribute as use of the block"""
    bl_idname = "object.set_attribute_mass_use_name"
    bl_label = "Set Face Attribute as Use of the Block"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        mesh = obj.data

        attribute_mass_use_name = context.scene.attribute_mass_use_name
        
        # a custom attribute is assigned to the edges
       
        try:
            mesh.attributes["roma_use_name"]
            attribute_mass_use_name = context.scene.attribute_mass_use_name
           
            # we need to switch from Edit mode to Object mode so the selection gets updated
            mode = obj.mode
            bpy.ops.object.mode_set(mode='OBJECT')
           
            selected_faces = [p for p in bpy.context.active_object.data.polygons if p.select]
            mesh_attributes = mesh.attributes["roma_use_name"].data.items()
            
            for face in selected_faces:
                index = face.index
                for mesh_attribute in mesh_attributes:
                    if mesh_attribute[0] == index:
                        mesh_attribute[1].value = attribute_mass_use_name
           
            # back to whatever mode we were in
            bpy.ops.object.mode_set(mode=mode)
                    
            self.report({'INFO'}, "Attribute set to face, use: "+str(attribute_mass_use_name))
            return {'FINISHED'}
        except:
            return {'FINISHED'}
    
class OBJECT_OT_SetMassStoreys(Operator):
    """Set Face Attribute as Number of Mass Storeys"""
    bl_idname = "object.set_attribute_mass_storeys"
    bl_label = "Set Face Attribute as number of Mass Storeys"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        mesh = obj.data

        attribute_mass_storeys = context.scene.attribute_mass_storeys
        
        # a custom attribute is assigned to the edges
       
        try:
            mesh.attributes["roma_number_of_storeys"]
            attribute_mass_storeys = context.scene.attribute_mass_storeys
           
            # we need to switch from Edit mode to Object mode so the selection gets updated
            mode = obj.mode
            bpy.ops.object.mode_set(mode='OBJECT')
           
            selected_faces = [p for p in bpy.context.active_object.data.polygons if p.select]
            mesh_attributes = mesh.attributes["roma_number_of_storeys"].data.items()
            
            for face in selected_faces:
                index = face.index
                for mesh_attribute in mesh_attributes:
                    if mesh_attribute[0] == index:
                        mesh_attribute[1].value = attribute_mass_storeys
           
            # back to whatever mode we were in
            bpy.ops.object.mode_set(mode=mode)
                    
            self.report({'INFO'}, "Attribute set to face, number of storeys: "+str(attribute_mass_storeys))
            return {'FINISHED'}
        except:
            return {'FINISHED'}
        
class VIEW3D_PT_RoMa_Mass(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "RoMa"
    bl_label = "Mass"
    
    def draw(self, context):
        
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.
        
        # col = layout.column()
        # subcol = col.column()
        layout.active = bool(context.active_object.mode=='EDIT')
        layout.prop(context.scene, "attribute_mass_plot_name", text="Plot Name")
        layout.prop(context.scene, "attribute_mass_block_name", text="Block Name")
        layout.prop(context.scene, "attribute_mass_use_name", text="Use Name")
        layout.prop(context.scene, "attribute_mass_storeys", text="N° of storeys")

        # row = layout.row()
        # row.prop(context.scene, "attribute_mass_storeys", text="Number of Storeys")
        # if context.active_object.mode=='EDIT':
        #     row.enabled = True
        # else:
        #     row.enabled = False
        
def add_RoMa_Mass(self, context):
    scale_x = self.scale.x
    scale_y = self.scale.y

    verts = [
        Vector((-2 * scale_x, -2 * scale_y, 0)),
        Vector((2 * scale_x, -2 * scale_y, 0)),
        Vector((2 * scale_x, 2 * scale_y, 0)),
        Vector((-2 * scale_x, 2 * scale_y, 0))
    ]

    edges = []
    faces = [[0,1,2,3]]

    mesh = bpy.data.meshes.new(name="RoMa Mass")
    mesh.from_pydata(verts, edges, faces)
    # useful for development when the mesh may be invalid.
    # mesh.validate(verbose=True)
    object_data_add(context, mesh, operator=self)
    mesh.attributes.new(name="roma_facade_type", type="INT", domain="EDGE")
    mesh.attributes.new(name="roma_number_of_storeys_per_face", type="INT", domain="EDGE")
    
    mesh.attributes.new(name="roma_plot_name", type="STRING", domain="FACE")
    mesh.attributes.new(name="roma_block_name", type="STRING", domain="FACE")
    mesh.attributes.new(name="roma_use_name", type="STRING", domain="FACE")
    storeyAttribute = mesh.attributes.new(name="roma_number_of_storeys", type="INT", domain="FACE")
    
    for face in mesh.polygons:
        storeyAttribute.data[face.index].value = 3
    
    
def add_RoMa_Mass_button(self, context):
    self.layout.operator(
        OBJECT_OT_add_RoMa_Mass.bl_idname,
        text="RoMa Mass",
        icon='PLUGIN')
    
def update_attribute_mass_plot_name(self, context):
    bpy.ops.object.set_attribute_mass_plot_name()
    
def update_attribute_mass_block_name(self, context):
    bpy.ops.object.set_attribute_mass_block_name()
    
def update_attribute_mass_use_name(self, context):
    bpy.ops.object.set_attribute_mass_use_name()
        
def update_attribute_mass_storeys(self, context):
    bpy.ops.object.set_attribute_mass_storeys()
   