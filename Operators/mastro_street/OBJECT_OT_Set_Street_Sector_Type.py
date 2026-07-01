import bpy
import bmesh
from bpy.types import Operator
from bpy.props import IntProperty, StringProperty, BoolProperty

from ...Utils.mastro_street.read_write_sector_type import get_sector_layers

# Write one fillet flag (left or right, at endpoint A or B of the active edge)
# and mirror the change to the adjacent edge that shares that sector, keeping
# the whole intersection consistent without any iterative logic (see _propagate).
class OBJECT_OT_Set_Street_Sector_Type(Operator):
    bl_idname = "object.set_street_sector_type"
    bl_label = "Set Street Sector Type"
    bl_options = {'REGISTER', 'UNDO'}

    edge_index: IntProperty(name="Edge Index")
    suffix: StringProperty(name="Suffix", description="A or B — which endpoint (edge.verts[0] or [1])")
    side: StringProperty(name="Side", description="left or right — which polar sector")
    value: BoolProperty(name="Value", description="True = fillet, False = straight offset")

    def execute(self, context):
        obj = context.active_object
        if not (obj and obj.type == "MESH" and
                "MaStro object" in obj.data and
                "MaStro street" in obj.data):
            return {'CANCELLED'}

        bm = bmesh.from_edit_mesh(obj.data)
        bm.edges.ensure_lookup_table()
        bm.verts.ensure_lookup_table()

        try:
            layers = get_sector_layers(bm)
        except KeyError:
            return {'CANCELLED'}

        edge = bm.edges[self.edge_index]
        vert = edge.verts[0] if self.suffix == 'A' else edge.verts[1]

        from ...Handlers.utils.mastro_street.street_sectors import _set_flag, _propagate
        _set_flag(edge, vert, self.side, self.value, layers)
        _propagate(obj, bm, edge, vert, self.side, self.value, layers)

        bmesh.update_edit_mesh(obj.data)
        return {'FINISHED'}
