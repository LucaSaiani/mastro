import bpy
from bpy.types import Operator
from bpy.props import IntProperty

from ...Utils.mastro_street.read_write_sector_type import sector_suffix_for_mesh_edge

# set the intersection-sector type (double fillet / fillet on one side) at the active
# vertex's end of one of its branches, for a MaStro street object
class OBJECT_OT_Set_Street_Sector_Type(Operator):
    bl_idname = "object.set_street_sector_type"
    bl_label = "Set Street Sector Type"
    bl_options = {'REGISTER', 'UNDO'}

    vertex_index: IntProperty(name="Vertex Index")
    edge_index: IntProperty(name="Edge Index")
    sector_type: IntProperty(name="Sector Type")

    def execute(self, context):
        obj = context.active_object
        if not (obj and obj.type == "MESH" and
                "MaStro object" in obj.data and
                "MaStro street" in obj.data):
            return {'CANCELLED'}

        mesh = obj.data
        mode = obj.mode
        bpy.ops.object.mode_set(mode='OBJECT')

        edge = mesh.edges[self.edge_index]
        suffix = sector_suffix_for_mesh_edge(edge, self.vertex_index)
        mesh.attributes[f"mastro_street_sector_type_{suffix}"].data[self.edge_index].value = self.sector_type

        bpy.ops.object.mode_set(mode=mode)
        return {'FINISHED'}
