import bpy
from bpy.types import Menu


class MESH_MT_MaStroCad_Pie(Menu):
    bl_label = "MaStro CAD"

    def draw(self, context):
        pie = self.layout.menu_pie()
        pie.operator("mastrocad.offset",         text="Offset",         icon='MOD_OFFSET')
        pie.operator("mastrocad.trim",            text="Trim",           icon='MOD_EDGESPLIT')
        pie.operator("mastrocad.fillet",          text="Fillet",         icon='SPHERECURVE')
        pie.operator("mastrocad.delete_segment",  text="Delete Segment", icon='X')
