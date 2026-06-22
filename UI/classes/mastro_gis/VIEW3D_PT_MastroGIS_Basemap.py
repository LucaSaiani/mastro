import bpy
from bpy.types import Panel
from ....Utils.mastro_gis.geoscene import GeoScene
from .... import PREFS_KEY


class VIEW3D_PT_MastroGIS_Basemap(Panel):
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "MaStro"
    bl_label       = "GIS"
    bl_options = {'DEFAULT_CLOSED'} 

    def draw(self, context):
        layout = self.layout
        layout.use_property_split    = True
        layout.use_property_decorate = False
        scn = context.scene

        col = layout.column(align=True)
        col.prop(scn, "mastro_gis_basemap_source", text="Source")
        col.prop(scn, "mastro_gis_basemap_layer",  text="Layer")

        is_3dtiles = (scn.mastro_gis_basemap_source == "GOOGLE" and scn.mastro_gis_basemap_layer == "3D")
        if is_3dtiles:
            prefs = context.preferences.addons[PREFS_KEY].preferences
            layout.prop(prefs, "gis_google_3dtiles_lod", text="Quality")

        geoscn = GeoScene(scn)
        layout.separator()
        if geoscn.fixedOrigin:
            split = layout.split(factor=0.4)
            split.alignment = 'RIGHT'
            split.label(text="Origin")
            split.operator("mastrogis.unlock_origin", text="Unlock", icon='LOCKED')
        else:
            layout.prop(scn, "mastro_gis_origin_input", text="Origin")
        col = layout.column(align=True)
        col.enabled = not geoscn.fixedOrigin
        if scn.mastro_gis_origin_input == 'LATLON':
            col.prop(scn, "mastro_gis_origin_lat", icon='URL', text="Latitude")
            col.prop(scn, "mastro_gis_origin_lon", icon='URL', text="Longitude")
        else:
            if geoscn.fixedOrigin:
                # X/Y are now expressed in the map's own CRS (reprojected from
                # whatever CRS was picked at input time), not the picked one
                col.label(text="CRS: {}".format(geoscn.crs or "?"))
            else:
                col.prop(scn, "mastro_gis_origin_crs", text="CRS")
            col.prop(scn, "mastro_gis_origin_x", text="X")
            col.prop(scn, "mastro_gis_origin_y", text="Y")

        layout.separator()
        layout.operator(
            "mastrogis.basemap_import",
            text="Download Basemap",
            icon='IMPORT',
        )
