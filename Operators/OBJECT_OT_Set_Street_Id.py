import bpy 
from bpy.types import Operator

from ..Utils.read_street_attribute import read_street_attribute

# set the attributes of the selected edges
class OBJECT_OT_Set_Street_Id(Operator):
    bl_idname = "object.set_attribute_street_id"
    bl_label = "Set Edge Attribute as street type"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        selected_objects = context.selected_objects
        
        for obj in selected_objects:
            if (obj.type == "MESH" and 
                "MaStro object" in context.object.data and
                "MaStro street" in context.object.data):
                mesh = obj.data
                mode = obj.mode
                bpy.ops.object.mode_set(mode='OBJECT')
                selected_edges = [e for e in bpy.context.active_object.data.edges if e.select]
                for edge in selected_edges:
                    edgeIndex = edge.index
                    data = read_street_attribute(context, mesh, edgeIndex)
                    mesh.attributes["mastro_street_id"].data[edgeIndex].value = data["street_id"]
                    mesh.attributes["mastro_street_width"].data[edgeIndex].value = data["width"]/2
                    mesh.attributes["mastro_street_radius"].data[edgeIndex].value = data["radius"]
                bpy.ops.object.mode_set(mode=mode)

        return {'FINISHED'}