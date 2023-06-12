import bpy
import bmesh

# selected_face_index = -1
checkingFace = False
changed_massAttribute = False

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
            global changed_massAttribute
            changed_massAttribute = True
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
            global changed_massAttribute
            changed_massAttribute = True
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
            global changed_massAttribute
            changed_massAttribute = True
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
            
            global changed_massAttribute
            changed_massAttribute = True
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
         
        #layout.active = bool(context.active_object.mode=='EDIT')
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
        # if context.active_object.mode=='EDIT':
        #     print("pippa")
            #bpy.ops.wm.mouse_position('INVOKE_DEFAULT')
        #     obj = context.active_object 
        #     obj.update_from_editmode()
        #     mesh = obj.data
        #     activeFace = mesh.polygons[mesh.polygons.active]
        #     print("cappero", activeFace.index)
            #bpy.ops.object.mode_set(mode='OBJECT')
            #context.scene.attribute_mass_storeys = activeFace.index
            #       bpy.ops.object.mode_set(mode='EDIT')
            

    
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
    mesh.update()
    # useful for development when the mesh may be invalid.
    # mesh.validate(verbose=True)
    object_data_add(context, mesh, operator=self)
    mesh.attributes.new(name="roma_facade_type", type="INT", domain="EDGE")
    mesh.attributes.new(name="roma_number_of_storeys_per_face", type="INT", domain="EDGE")
    
    mesh.attributes.new(name="roma_plot_name", type="STRING", domain="FACE")
    mesh.attributes.new(name="roma_block_name", type="STRING", domain="FACE")
    mesh.attributes.new(name="roma_use_name", type="STRING", domain="FACE")
    mesh.attributes.new(name="roma_number_of_storeys", type="INT", domain="FACE")
    mesh.attributes.new(name="roma_GEA", type="FLOAT", domain="FACE")
    
    obj = bpy.data.objects.new("RoMa Mass", mesh)
    
    for face in obj.data.polygons:
        mesh_plot = mesh.attributes["roma_plot_name"].data.items()
        mesh_plot[0][1].value = "Plot Name"
        
        mesh_block = mesh.attributes["roma_block_name"].data.items()
        mesh_block[0][1].value = "Block Name"
        
        mesh_use = mesh.attributes["roma_use_name"].data.items()
        mesh_use[0][1].value = "Use"
    
        mesh_Storeys = mesh.attributes["roma_number_of_storeys"].data.items()
        mesh_Storeys[0][1].value = 3
        
        mesh_GEA = mesh.attributes["roma_GEA"].data.items()
        mesh_GEA[0][1].value = 0
    
    
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
    
def get_face_attribute(scene):
    global checkingFace
    global changed_massAttribute
    if changed_massAttribute is True:
        changed_massAttribute = False
        checkingFace = False
    if checkingFace is False:
        checkingFace = True
        obj = bpy.context.active_object
        if obj.mode == 'EDIT':
            obj.update_from_editmode()
            mesh = obj.data
            
            # activeFace = mesh.polygons[mesh.polygons.active]
            selected_faces = [p for p in mesh.polygons if p.select]
            selected_indices = []
            for f in selected_faces:
                selected_indices.append(f.index)
            # print("selected faces", f.index)

            bpy.ops.mesh.select_all(action = 'DESELECT')

            bm = bmesh.from_edit_mesh(mesh)

            # print("active face index",activeFace.index)
            bMesh_plot = bm.faces.layers.string["roma_plot_name"]
            bMesh_block = bm.faces.layers.string["roma_block_name"]
            bMesh_use = bm.faces.layers.string["roma_use_name"]
            bMesh_storeys = bm.faces.layers.int["roma_number_of_storeys"]

            if bm.faces.active is not None:
                bMesh_active = bm.faces.active.index
                for bmFace in bm.faces:
                    plot = bmFace[bMesh_plot]
                    block = bmFace[bMesh_block]
                    use = bmFace[bMesh_use]
                    storey = bmFace[bMesh_storeys]
                    if bm.faces.active is not None and bmFace.index == bMesh_active:
                        #active = " active"
                        if isinstance (plot, str):
                            bpy.context.scene.attribute_mass_plot_name = plot
                        if isinstance (block, str):
                            bpy.context.scene.attribute_mass_block_name = block
                        if isinstance (use, str):
                            bpy.context.scene.attribute_mass_use_name = use
                        bpy.context.scene.attribute_mass_storeys = storey
                        
                        # print(plot, block, use, storey)
                        break
                    # else:
                    #     active = ""
                    #     print("face",active, " ", bmFace.index, "=", value)
        
                # print("selected faces:", selected_indices)

            bm = bmesh.from_edit_mesh(mesh)
            for f in bm.faces:
                #print("controllo", f.index)
                if f.index in selected_indices:
                    f.select_set(True)
                    #print("seleziono", f.index)
            bm.free()  # free and prevent further access
            checkingFace = False
            # print("Done", checkingFace)