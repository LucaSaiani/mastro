from bpy.props import EnumProperty

from ...Utils.mastro_gis.basemaps import SOURCES


def _gis_source_items(self, context):
    return [(key, src['name'], src['description']) for key, src in SOURCES.items()]


def _gis_layer_items(self, context):
    src_key = self.mastro_gis_basemap_source
    if src_key not in SOURCES:
        return [('NONE', 'None', '')]
    layers = SOURCES[src_key]['layers']
    return [(key, lay['name'], lay['description']) for key, lay in layers.items()]


# =============================================================================
# Scene Properties - GIS
# =============================================================================
scene_props_gis = [
    ("mastro_gis_basemap_source", EnumProperty(
        name="Source",
        items=_gis_source_items,
        description="Map service source",
    )),
    ("mastro_gis_basemap_layer", EnumProperty(
        name="Layer",
        items=_gis_layer_items,
        description="Map layer",
    )),
]
