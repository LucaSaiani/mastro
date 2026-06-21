import bpy
from bpy.types import Panel


class VIEW3D_PT_Mastro_Convert(Panel):
    """Converters for turning a plain object into a MaStro mass, street or
    drawing. Hidden for objects that are already a MaStro type, and for
    MaStro albums/frames, which aren't convertible targets."""
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "MaStro"
    bl_label       = "Convert"
    bl_parent_id   = "VIEW3D_PT_Mastro_Panel"
    bl_order       = 0

    @classmethod
    def poll(cls, context):
        obj = context.object
        if obj is None:
            return True
        if obj.get("MaStro album") or obj.get("MaStro frame"):
            return False
        if obj.type == "MESH" and "MaStro object" in obj.data:
            return False
        return True

    def draw(self, context):
        layout = self.layout
        layout.operator("object.mastro_convert_to_mastro_mass", text="to MaStro Mass")
        layout.operator("object.mastro_convert_to_mastro_street", text="to MaStro Street")
        layout.operator("object.mastro_convert_to_mastro_cad", text="to MaStro Drawing")
