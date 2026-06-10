import bpy
from bpy.types import Panel


class VIEW3D_PT_MastroGIS_Basemap(Panel):
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "MaStro"
    bl_label       = "GIS"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split    = True
        layout.use_property_decorate = False
        scn = context.scene

        col = layout.column(align=True)
        col.prop(scn, "mastro_gis_basemap_source", text="Source")
        col.prop(scn, "mastro_gis_basemap_layer",  text="Layer")

        layout.separator()
        layout.operator(
            "mastrogis.basemap_import",
            text="Open Map Viewer",
            icon='WORLD',
        )
