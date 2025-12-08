import bpy 
import bmesh 
from bpy.types import Operator
from bpy_extras.object_utils import AddObjectHelper
from bpy_extras import object_utils

from ..Utils.add_attributes_mass import add_mass_attributes
from ..Utils.add_nodes import add_nodes


class OBJECT_OT_Add_Mastro_Block(Operator, AddObjectHelper):
    """Add a MaStro mablockss"""
    bl_idname = "object.mastro_add_mastro_block"
    bl_label = "Block"
    bl_options = {'REGISTER', 'UNDO'}
    
    # width: bpy.props.FloatProperty(
    #     name="Width",
    #     description="MaStro mass width",
    #     # min=0.01, max=100.0,
    #     min=0,
    #     default=12,
    # )
    
    # depth: bpy.props.FloatProperty(
    #     name="Depth",
    #     description="MaStro block depth",
    #     # min=0.01, max=100.0,
    #     min=0,
    #     default=16,
    # )
    
    # storeys: bpy.props.IntProperty(
    #         name="Number of Storeys",
    #         description="Number of storeys of the block masses",
    #         min = 1,
    #         default = 3)
    
    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'
    
    def execute(self, context):

        verts = [
        (+0.0, +0.0,  +0.0),
        (+30.0, +0.0,  +0.0),
        (+47.321, +10.0,  +0.0),
        (+47.321, +40.0,  +0.0),
        ]
    
        edges = [
            (0,1),
            (1,2),
            (2,3)
        ]

        mesh = bpy.data.meshes.new("MaStro block")

        bm = bmesh.new()

        for v_co in verts:
            bm.verts.new(v_co)

        bm.verts.ensure_lookup_table()
        for e_idx in edges:
            bm.edges.new([bm.verts[i] for i in e_idx])

        bm.to_mesh(mesh)
        mesh.update()

        # add the mesh as an object into the scene with this utility module
        
        object_utils.object_data_add(context, mesh, operator=self)
        
        obj = bpy.context.active_object
        
        
        
            
        add_nodes()
        
        # mesh_attributes = obj.data.attributes["mastro_number_of_storeys_EDGE"].data.items()
        # for edge in mesh.edges:
        #     index = edge.index
        #     for mesh_attribute in mesh_attributes:
        #         if mesh_attribute[0]  == index:
        #             mesh_attribute[1].value = 3
        # write_bmesh_storey_attribute(bm, bm.edges, 3, "EDGE")
        # typology_id = bpy.context.scene.mastro_typology_name_list_index
        # write_bmesh_use_attribute(bm, bm.edges, typology_id , "EDGE")
        

        # add mastro block and mastro mass geo node to the created object
        bm.free
        geoName = "MaStro Block"
        obj.modifiers.new(geoName, "NODES")
        group = bpy.data.node_groups["MaStro Block"]
        obj.modifiers[geoName].node_group = group
        context.view_layer.objects.active = obj
        
        geoName = "MaStro Mass"
        obj.modifiers.new(geoName, "NODES")
        group = bpy.data.node_groups["MaStro Mass"]
        obj.modifiers[geoName].node_group = group
        context.view_layer.objects.active = obj
        
        obj.select_set(True)
        
        add_mass_attributes(obj, "MaStro block")
        
        return {'FINISHED'}
