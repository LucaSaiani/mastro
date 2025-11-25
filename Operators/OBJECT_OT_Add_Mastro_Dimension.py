import bpy 
import bmesh
from bpy.types import Operator
from bpy_extras.object_utils import AddObjectHelper
from bpy_extras import object_utils

from ..Utils.add_nodes import add_nodes

class OBJECT_OT_Add_Mastro_Dimension(Operator, AddObjectHelper):
    """Add a MaStro linear dimension"""
    bl_idname = "object.mastro_add_mastro_dimension"
    bl_label = "Dimension"
    bl_options = {'REGISTER', 'UNDO'}
      
    def execute(self, context):
        verts = [
        (+0.0, +0.0, +0.0),
        (+0.0, +0.0, +1.0)
        ]

        edges = [
            (0, 1)
        ]

        mesh = bpy.data.meshes.new("MaStro Dimension")

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
        
        add_nodes()

        # add mastro dimension geo node to the created object
        geoName = "MaStro Dimension"
        obj.modifiers.new(geoName, "NODES")
        group = bpy.data.node_groups["MaStro Dimension"]
        obj.modifiers[geoName].node_group = group
        context.view_layer.objects.active = obj
        
        obj.select_set(True)
        return {'FINISHED'}