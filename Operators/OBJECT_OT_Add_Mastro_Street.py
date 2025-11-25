import bpy
import bmesh
from bpy.types import Operator
from bpy_extras.object_utils import AddObjectHelper
from bpy_extras import object_utils

from ..Utils.add_attributes_street import add_street_attributes
from ..Utils.add_nodes import add_nodes

class OBJECT_OT_Add_Mastro_Street(Operator, AddObjectHelper):
    """Add a MaStro street"""
    bl_idname = "object.mastro_add_mastro_street"
    bl_label = "Street"
    bl_options = {'REGISTER', 'UNDO'}
    
    # width: bpy.props.FloatProperty(
    #     name="Width",
    #     description="MaStro street width",
    #     # min=0.01, max=100.0,
    #     min=0,
    #     default=8,
    # )
    
    # radius: bpy.props.FloatProperty(
    #     name="Radius",
    #     description="MaStro street radius",
    #     # min=0.01, max=100.0,
    #     min=0,
    #     default=16,
    # )
    
  
    def execute(self, context):
        verts = [
        (+0.0, +0.0, +0.0),
        (+22.0, +28.0, +0.0),
        (+56.0, +35.0,  +0.0),
        (-42.0, +38.0, +0.0),
        (-70.0, +20.0, +0.0),
        (-22.0, -25.0, +0.0),
        (-31.0, -61.0, +0.0)
        ]

        edges = [
            (0, 1),
            (1, 2),
            (0,3),
            (3,4),
            (0,5),
            (5,6)
        ]

        mesh = bpy.data.meshes.new("MaStro street")

        bm = bmesh.new()

        for v_co in verts:
            bm.verts.new(v_co)

        bm.verts.ensure_lookup_table()
        for e_idx in edges:
            bm.edges.new((bm.verts[e_idx[0]], bm.verts[e_idx[1]]))

        bm.to_mesh(mesh)
        mesh.update()

        # add the mesh as an object into the scene with this utility module
        
        object_utils.object_data_add(context, mesh, operator=self)
        
        obj = bpy.context.active_object

        add_street_attributes(obj)
            
        add_nodes()
        
        
        # mesh_attributes = obj.data.attributes["mastro_number_of_storeys"].data.items()
        # mesh_attributes[0][1].value = self.storeys

        # add mastro street geo node to the created object
        geoName = "MaStro Street"
        obj.modifiers.new(geoName, "NODES")
        group = bpy.data.node_groups["MaStro Street"]
        obj.modifiers[geoName].node_group = group
        context.view_layer.objects.active = obj
        
        obj.select_set(True)
        return {'FINISHED'}
    
