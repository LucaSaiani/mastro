from bpy.props import EnumProperty, FloatProperty, StringProperty

from ... import PREFS_KEY
from ...Utils.mastro_gis.basemaps import SOURCES
from ...Utils.mastro_gis.geoscene import GeoScene
from ...Utils.mastro_gis.prefs import PredefCRS
from ...Utils.mastro_gis.geo_coords import (
    parse_latitude, parse_longitude, format_latitude, format_longitude,
)


def _gis_source_items(self, context):
    return [(key, src['name'], src['description']) for key, src in SOURCES.items()]


def _gis_origin_crs_items(self, context):
    return PredefCRS.getEnumItems()


def _gis_layer_items(self, context):
    src_key = self.mastro_gis_basemap_source
    if src_key not in SOURCES:
        return [('NONE', 'None', '')]
    layers = SOURCES[src_key]['layers']
    prefs = context.preferences.addons[PREFS_KEY].preferences
    has_google_key = bool(prefs.gis_google_api_key)
    return [
        (key, lay['name'], lay['description']) for key, lay in layers.items()
        if has_google_key or lay.get('service_type') != '3dtiles'
    ]


_gis_origin_lat_parse_ok = True
_gis_origin_lon_parse_ok = True
# True once the user has typed a pending value into the field since the
# origin was last unlocked/unset - takes priority over the live origin so a
# keystroke doesn't immediately get overwritten by the (still old) live
# position. Cleared once the typed value is actually applied (origin
# (re)fixed) or the field is unlocked again.
_gis_origin_lat_staged = False
_gis_origin_lon_staged = False


def reset_origin_staging():
    """Called when the origin is unlocked, or once a staged value has been
    applied, so the fields go back to tracking the live origin."""
    global _gis_origin_lat_staged, _gis_origin_lon_staged
    global _gis_origin_lat_parse_ok, _gis_origin_lon_parse_ok
    _gis_origin_lat_staged = False
    _gis_origin_lon_staged = False
    _gis_origin_lat_parse_ok = True
    _gis_origin_lon_parse_ok = True


def _get_gis_origin_lat(self):
    if not _gis_origin_lat_parse_ok:
        return "Error: could not parse latitude"
    # Once a map import exists, reflect the live geo-origin (which keeps
    # moving while panning in free mode) rather than the stale staging
    # value - unless the user just typed a new pending value that hasn't
    # been applied yet.
    geoscn = GeoScene(self)
    if not _gis_origin_lat_staged and geoscn.hasOriginGeo:
        return format_latitude(geoscn.lat)
    return format_latitude(self.mastro_gis_origin_lat_value)


def _set_gis_origin_lat(self, value):
    global _gis_origin_lat_parse_ok, _gis_origin_lat_staged
    parsed = parse_latitude(value)
    if parsed is not None:
        self.mastro_gis_origin_lat_value = parsed
        _gis_origin_lat_parse_ok = True
        _gis_origin_lat_staged = True
    else:
        _gis_origin_lat_parse_ok = False


def _get_gis_origin_lon(self):
    if not _gis_origin_lon_parse_ok:
        return "Error: could not parse longitude"
    geoscn = GeoScene(self)
    if not _gis_origin_lon_staged and geoscn.hasOriginGeo:
        return format_longitude(geoscn.lon)
    return format_longitude(self.mastro_gis_origin_lon_value)


def _set_gis_origin_lon(self, value):
    global _gis_origin_lon_parse_ok, _gis_origin_lon_staged
    parsed = parse_longitude(value)
    if parsed is not None:
        self.mastro_gis_origin_lon_value = parsed
        _gis_origin_lon_parse_ok = True
        _gis_origin_lon_staged = True
    else:
        _gis_origin_lon_parse_ok = False


def _get_gis_origin_x(self):
    geoscn = GeoScene(self)
    if not _gis_origin_lat_staged and geoscn.hasOriginPrj:
        return geoscn.crsx
    return self.mastro_gis_origin_x_value


def _set_gis_origin_x(self, value):
    global _gis_origin_lat_staged
    self.mastro_gis_origin_x_value = value
    _gis_origin_lat_staged = True


def _get_gis_origin_y(self):
    geoscn = GeoScene(self)
    if not _gis_origin_lon_staged and geoscn.hasOriginPrj:
        return geoscn.crsy
    return self.mastro_gis_origin_y_value


def _set_gis_origin_y(self, value):
    global _gis_origin_lon_staged
    self.mastro_gis_origin_y_value = value
    _gis_origin_lon_staged = True


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
    ("mastro_gis_origin_input", EnumProperty(
        name="Origin Input",
        items=[
            ('LATLON', "Lat/Lon", "Enter the project origin as latitude/longitude"),
            ('PROJECTED', "Projected", "Enter the project origin as projected X/Y coordinates"),
        ],
        default='LATLON',
        description="How the fixed project origin below is entered",
    )),
    ("mastro_gis_origin_lat_value", FloatProperty(default=0.0, min=-90.0, max=90.0)),
    ("mastro_gis_origin_lon_value", FloatProperty(default=0.0, min=-180.0, max=180.0)),
    ("mastro_gis_origin_lat", StringProperty(
        name="Latitude",
        description="Accepts decimal, DMS or NMEA-style notation",
        get=_get_gis_origin_lat,
        set=_set_gis_origin_lat,
    )),
    ("mastro_gis_origin_lon", StringProperty(
        name="Longitude",
        description="Accepts decimal, DMS or NMEA-style notation",
        get=_get_gis_origin_lon,
        set=_set_gis_origin_lon,
    )),
    ("mastro_gis_origin_crs", EnumProperty(
        name="CRS",
        items=_gis_origin_crs_items,
        description="Coordinate reference system the X/Y values below are expressed in",
    )),
    ("mastro_gis_origin_x_value", FloatProperty(default=0.0)),
    ("mastro_gis_origin_y_value", FloatProperty(default=0.0)),
    ("mastro_gis_origin_x", FloatProperty(
        name="X",
        get=_get_gis_origin_x,
        set=_set_gis_origin_x,
    )),
    ("mastro_gis_origin_y", FloatProperty(
        name="Y",
        get=_get_gis_origin_y,
        set=_set_gis_origin_y,
    )),
]
