import bpy 
import bmesh
from bpy.types import Operator
from bpy_extras.object_utils import AddObjectHelper
from bpy_extras import object_utils

from ..Utils.add_attributes_mass import add_mass_attributes
from ..Utils.add_nodes import add_nodes

class OBJECT_OT_Add_Mastro_Mass(Operator, AddObjectHelper):
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
        verts = [
        (+0.0, +0.0,  +0.0),
        (+1.0, +0.0,  +0.0),
        (+1.0, +1.0,  +0.0),
        (+0.0, +1.0,  +0.0),
        ]

        faces = [
            (0, 1, 2, 3),
        ]
        
        #apply size
        for i, v in enumerate(verts):
            verts[i] = v[0] * self.width, v[1] * self.depth, v[2]

        mesh = bpy.data.meshes.new("MaStro mass")

        bm = bmesh.new()

        for v_co in verts:
            bm.verts.new(v_co)

        bm.verts.ensure_lookup_table()
        for f_idx in faces:
            bm.faces.new([bm.verts[i] for i in f_idx])

        bm.to_mesh(mesh)
        mesh.update()

        # add the mesh as an object into the scene with this utility module
        
        object_utils.object_data_add(context, mesh, operator=self)
        
        obj = bpy.context.active_object
        
        
        add_mass_attributes(obj)
            
        add_nodes()
        
        mesh_attributes = obj.data.attributes["mastro_number_of_storeys"].data.items()
        # mesh_attributes[0][1].value = self.storeys
        mesh_attributes[0][1].value = 3

        # add mastro mass geo node to the created object
        geoName = "MaStro Mass"
        obj.modifiers.new(geoName, "NODES")
        group = bpy.data.node_groups["MaStro Mass"]
        obj.modifiers[geoName].node_group = group
        context.view_layer.objects.active = obj
        
        obj.select_set(True)
        return {'FINISHED'}
    