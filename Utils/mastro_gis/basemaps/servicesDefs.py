# -*- coding:utf-8 -*-

import math

####################################

#        Tiles maxtrix definitions

####################################

# Three ways to define a grid (inpired by http://mapproxy.org/docs/1.8.0/configuration.html#id6):
# - submit a list of resolutions > "resolutions": [32,16,8,4] (This parameters override the others)
# - submit just "resFactor", initial res is computed such as at zoom level zero, 1 tile covers whole bounding box
# - submit "resFactor" and "initRes"


# About Web Mercator
# Technically, the Mercator projection is defined for any latitude up to (but not including)
# 90 degrees, but it makes sense to cut it off sooner because it grows exponentially with
# increasing latitude. The logic behind this particular cutoff value, which is the one used
# by Google Maps, is that it makes the projection square. That is, the rectangle is equal in
# the X and Y directions. In this case the maximum latitude attained must correspond to y = w/2.
# y = 2*pi*R / 2 = pi*R --> y/R = pi
# lat = atan(sinh(y/R)) = atan(sinh(pi))
# wm_origin = (-20037508, 20037508) with 20037508 = GRS80.perimeter / 2

cutoff_lat = math.atan(math.sinh(math.pi)) * 180/math.pi #= 85.05112°


GRIDS = {


	"WM" : {
		"name" : 'Web Mercator',
		"description" : 'Global grid in web mercator projection',
		"CRS": 'EPSG:3857',
		"bbox": [-180, -cutoff_lat, 180, cutoff_lat], #w,s,e,n
		"bboxCRS": 'EPSG:4326',
		#"bbox": [-20037508, -20037508, 20037508, 20037508],
		#"bboxCRS": 3857,
		"tileSize": 256,
		"originLoc": "NW", #North West or South West
		"resFactor" : 2
	},


	"WGS84" : {
		"name" : 'WGS84',
		"description" : 'Global grid in wgs84 projection',
		"CRS": 'EPSG:4326',
		"bbox": [-180, -90, 180, 90], #w,s,e,n
		"bboxCRS": 'EPSG:4326',
		"tileSize": 256,
		"originLoc": "NW", #North West or South West
		"resFactor" : 2
	},

	#this one produce valid MBtiles files, because origin is bottom left
	"WM_SW" : {
		"name" : 'Web Mercator TMS',
		"description" : 'Global grid in web mercator projection, origin South West',
		"CRS": 'EPSG:3857',
		"bbox": [-180, -cutoff_lat, 180, cutoff_lat], #w,s,e,n
		"bboxCRS": 'EPSG:4326',
		#"bbox": [-20037508, -20037508, 20037508, 20037508],
		#"bboxCRS": 'EPSG:3857',
		"tileSize": 256,
		"originLoc": "SW", #North West or South West
		"resFactor" : 2
	},


}


####################################

#        Sources definitions

####################################

#With TMS or WMTS, grid must match the one used by the service
#With WMS you can use any grid you want but the grid CRS must
#match one of those provided by the WMS service

#The grid associated to the source define the CRS
#A source can have multiple layers but have only one grid
#so to support multiple grid it's necessary to duplicate source definition

SOURCES = {


	###############
	# TMS examples
	###############


	"GOOGLE" : {
		"name" : 'Google',
		"description" : 'Google map',
		"service": 'TMS',
		"grid": 'WM',
		"quadTree": False,
		"layers" : {
			"SAT" : {"urlKey" : 's', "name" : 'Satellite', "description" : '', "format" : 'jpeg', "zmin" : 0, "zmax" : 22},
			"MAP" : {"urlKey" : 'm', "name" : 'Map', "description" : '', "format" : 'png', "zmin" : 0, "zmax" : 22},
			# not a raster layer: triggers 3D Tiles import mode in the basemap modal
			"3D"  : {"urlKey" : 's', "name" : '3D Tiles', "description" : 'Select an area to import Google 3D Tiles', "format" : 'jpeg', "zmin" : 0, "zmax" : 22, "service_type": "3dtiles"}
		},
		"urlTemplate": "http://mt0.google.com/vt/lyrs={LAY}&x={X}&y={Y}&z={Z}",
		"referer": "https://www.google.com/maps"
	},


	"OSM" : {
		"name" : 'OSM',
		"description" : 'Open Street Map',
		"service": 'TMS',
		"grid": 'WM',
		"quadTree": False,
		"layers" : {
			"MAPNIK" : {"urlKey" : '', "name" : 'Mapnik', "description" : '', "format" : 'png', "zmin" : 0, "zmax" : 19}
		},
		"urlTemplate": "https://tile.openstreetmap.org/{Z}/{X}/{Y}.png",
		"referer": "" #https://www.openstreetmap.org will return 418 error
	},


	"BING" : {
		"name" : 'Bing',
		"description" : 'Microsoft Bing Map',
		"service": 'TMS',
		"grid": 'WM',
		"quadTree": True,
		"layers" : {
			"SAT" : {"urlKey" : 'A', "name" : 'Satellite', "description" : '', "format" : 'jpeg', "zmin" : 0, "zmax" : 22},
			"MAP" : {"urlKey" : 'G', "name" : 'Map', "description" : '', "format" : 'png', "zmin" : 0, "zmax" : 22}
		},
		"urlTemplate": "http://ak.dynamic.t0.tiles.virtualearth.net/comp/ch/{QUADKEY}?it={LAY}",
		"referer": "http://www.bing.com/maps"
	},


	"ESRI" : {
		"name" : 'Esri',
		"description" : 'Esri ArcGIS',
		"service": 'TMS',
		"grid": 'WM',
		"quadTree": False,
		"layers" : {
			"AERIAL" : {"urlKey" : 'World_Imagery', "name" : 'Aerial', "description" : '', "format" : 'jpeg', "zmin" : 0, "zmax" : 23},
			"NATGEO" : {"urlKey" : 'NatGeo_World_Map', "name" : 'National Geographic', "description" : '', "format" : 'jpeg', "zmin" : 0, "zmax" : 16},
			"USATOPO" : {"urlKey" : 'USA_Topo_Maps', "name" : 'USA Topo', "description" : '', "format" : 'jpeg', "zmin" : 0, "zmax" : 15},
			"PHYSICAL" : {"urlKey" : 'World_Physical_Map', "name" : 'Physical', "description" : '', "format" : 'jpeg', "zmin" : 0, "zmax" : 8},
			"RELIEF" : {"urlKey" : 'World_Shaded_Relief', "name" : 'Shaded Relief', "description" : '', "format" : 'jpeg', "zmin" : 0, "zmax" : 13},
			"STREET" : {"urlKey" : 'World_Street_Map', "name" : 'Street Map', "description" : '', "format" : 'jpeg', "zmin" : 0, "zmax" : 23},
			"TOPO" : {"urlKey" : 'World_Topo_Map', "name" : 'Topo with relief', "description" : '', "format" : 'jpeg', "zmin" : 0, "zmax" : 23},
			"TERRAINB" : {"urlKey" : 'World_Terrain_Base', "name" : 'Terrain Base', "description" : '', "format" : 'jpeg', "zmin" : 0, "zmax" : 13},
			"CANVASLIGHTB" : {"urlKey" : 'Canvas/World_Light_Gray_Base', "name" : 'Canvas Light Gray Base', "description" : '', "format" : 'jpeg', "zmin" : 0, "zmax" : 23},
			"CANVASDARKB" : {"urlKey" : 'Canvas/World_Dark_Gray_Base', "name" : 'Canvas Dark Gray Base', "description" : '', "format" : 'jpeg', "zmin" : 0, "zmax" : 23},
			"OCEANB" : {"urlKey" : 'Ocean/World_Ocean_Base', "name" : 'Ocean Base', "description" : '', "format" : 'jpeg', "zmin" : 0, "zmax" : 23}
		},
		"urlTemplate": "https://server.arcgisonline.com/ArcGIS/rest/services/{LAY}/MapServer/tile/{Z}/{Y}/{X}",
		"referer": "https://server.arcgisonline.com/arcgis/rest/services"
	},


}
