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
    bl_label = "Add RoMa Mass"
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
    
class SetFaceAttributeOperator_mass_storeys(bpy.types.Operator):
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
            mesh.attributes["Mass_Number_of_Storeys"]
            attribute_mass_storeys = context.scene.attribute_mass_storeys
           
            # we need to switch from Edit mode to Object mode so the selection gets updated
            mode = obj.mode
            bpy.ops.object.mode_set(mode='OBJECT')
           
            selected_faces = [p for p in bpy.context.active_object.data.polygons if p.select]
            mesh_attributes = mesh.attributes["Mass_Number_of_Storeys"].data.items()
            for face in selected_faces:
                index = face.index
                for mesh_attribute in mesh_attributes:
                    if mesh_attribute[0] == index:
                        mesh_attribute[1].value = attribute_mass_storeys
           
            # back to whatever mode we were in
            bpy.ops.object.mode_set(mode=mode)
                    
            self.report({'INFO'}, "Attribute set to face "+str(attribute_mass_storeys))
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
        
        col = layout.column()
        subcol = col.column()
        subcol.active = bool(context.active_object.mode=='EDIT')
        subcol.prop(context.scene, "attribute_mass_storeys", text="N° of Storeys")

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
        Vector((-1 * scale_x, -1 * scale_y, 0)),
        Vector((1 * scale_x, -1 * scale_y, 0)),
        Vector((1 * scale_x, 1 * scale_y, 0)),
        Vector((-1 * scale_x, 1 * scale_y, 0))
    ]

    edges = []
    faces = [[0,1,2,3]]

    mesh = bpy.data.meshes.new(name="RoMa Mass")
    mesh.from_pydata(verts, edges, faces)
    # useful for development when the mesh may be invalid.
    # mesh.validate(verbose=True)
    object_data_add(context, mesh, operator=self)
    mesh.attributes.new(name="Mass_Number_of_Storeys", type="INT", domain="FACE")
    
def add_RoMa_Mass_button(self, context):
    self.layout.operator(
        OBJECT_OT_add_RoMa_Mass.bl_idname,
        text="Add RoMa Mass",
        icon='PLUGIN')
    
def update_attribute_mass_storeys(self, context):
    try:
        if context.area.type == 'VIEW_3D':
            bpy.ops.object.set_attribute_mass_storeys()
    except:
        pass