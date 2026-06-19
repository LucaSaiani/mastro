# -*- coding:utf-8 -*-

#  ***** GPL LICENSE BLOCK *****
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#  All rights reserved.
#  ***** GPL LICENSE BLOCK *****

import logging
log = logging.getLogger(__name__)

import bpy

from .proj.reproj import reprojPt
from .proj.srs import SRS

GIS_MAPS_NAME = "GIS Maps"

'''
Policy :
This module manages in priority the CRS coordinates of the scene's origin and
updates the corresponding longitude/latitude only if it can to do the math.

A scene is considered correctly georeferenced when at least a valid CRS is defined
and the coordinates of scene's origin in this CRS space is set. A geoscene will be
broken if the origin is set but not the CRS or if the origin is only set as longitude/latitude.

Changing the CRS will raise an error if updating existing origin coordinate is not possible.

Both methods setOriginGeo() and setOriginPrj() try a projection task to maintain
coordinates synchronized. Failing reprojection does not abort the exec, but will
trigger deletion of unsynch coordinates. Synchronization can be disable for
setOriginPrj() method only.

Except setOriginGeo() method, dealing directly with longitude/latitude
automatically trigger a reprojection task which will raise an error if failing.

Sequences of methods :
moveOriginPrj() | updOriginPrj() > setOriginPrj() > [reprojPt()]
moveOriginGeo() > updOriginGeo() > reprojPt() > updOriginPrj() > setOriginPrj()

Standalone properties (lon, lat, crsx et crsy) can be edited independently without any extra checks.
'''

class SK():
	"""Alias to Scene Keys used to store georef infos"""
	# latitude and longitude of scene origin in decimal degrees
	LAT = "latitude"
	LON = "longitude"
	#Spatial Reference System Identifier
	# can be directly an EPSG code or formated following the template "AUTH:4326"
	# or a proj4 string definition of Coordinate Reference System (CRS)
	CRS = "SRID"
	# Coordinates of scene origin in CRS space
	CRSX = "crs x"
	CRSY = "crs y"
	# General scale denominator of the map (1:x)
	SCALE = "scale"
	# Current zoom level in the Tile Matrix Set
	ZOOM = "zoom"
	# True if the origin was explicitly fixed to a project point (not 0,0)
	FIXED_ORIGIN = "fixed_origin"



class GeoScene():

	def __init__(self, scn=None):
		if scn is None:
			self.scn = bpy.context.scene
		else:
			self.scn = scn
		self.SK = SK()

	@property
	def _rna_ui(self):
		# get or init the dictionary containing IDprops settings
		rna_ui = self.scn.get('_RNA_UI', None)
		if rna_ui is None:
			self.scn['_RNA_UI'] = {}
			rna_ui = self.scn['_RNA_UI']
		return rna_ui

	def view3dToProj(self, dx, dy):
		'''Convert view3d coords to crs coords'''
		if self.hasOriginPrj:
			x = self.crsx + (dx * self.scale)
			y = self.crsy + (dy * self.scale)
			return x, y
		else:
			raise Exception("Scene origin coordinate is unset")

	def projToView3d(self, dx, dy):
		'''Convert view3d coords to crs coords'''
		if self.hasOriginPrj:
			x = (dx * self.scale) - self.crsx
			y = (dy * self.scale) - self.crsy
			return x, y
		else:
			raise Exception("Scene origin coordinate is unset")

	@property
	def hasCRS(self):
		return SK.CRS in self.scn

	@property
	def hasValidCRS(self):
		if not self.hasCRS:
			return False
		return SRS.validate(self.crs)

	@property
	def isGeoref(self):
		'''A scene is georef if at least a valid CRS is defined and
		the coordinates of scene's origin in this CRS space is set'''
		return self.hasValidCRS and self.hasOriginPrj

	@property
	def isFullyGeoref(self):
		return self.hasValidCRS and self.hasOriginPrj and self.hasOriginGeo

	@property
	def isPartiallyGeoref(self):
		return self.hasCRS or self.hasOriginPrj or self.hasOriginGeo

	@property
	def isBroken(self):
		"""partial georef infos make the geoscene unusuable and broken"""
		return (self.hasCRS and not self.hasValidCRS) \
		or (not self.hasCRS and (self.hasOriginPrj or self.hasOriginGeo)) \
		or (self.hasCRS and self.hasOriginGeo and not self.hasOriginPrj)

	@property
	def hasOriginGeo(self):
		return SK.LAT in self.scn and SK.LON in self.scn

	@property
	def hasOriginPrj(self):
		return SK.CRSX in self.scn and SK.CRSY in self.scn

	def setOriginGeo(self, lon, lat):
		self.lon, self.lat = lon, lat
		try:
			self.crsx, self.crsy = reprojPt(4326, self.crs, lon, lat)
		except Exception as e:
			if self.hasOriginPrj:
				self.delOriginPrj()
				log.warning('Origin proj has been deleted because the property could not be updated', exc_info=True)

	def setOriginPrj(self, x, y, synch=True):
		self.crsx, self.crsy = x, y
		if synch:
			try:
				self.lon, self.lat = reprojPt(self.crs, 4326, x, y)
			except Exception as e:
				if self.hasOriginGeo:
					self.delOriginGeo()
					log.warning('Origin geo has been deleted because the property could not be updated', exc_info=True)
		elif self.hasOriginGeo:
			self.delOriginGeo()
			log.warning('Origin geo has been deleted because coordinate synchronization is disable')

	def updOriginPrj(self, x, y, updObjLoc=True, synch=True):
		'''Update/move scene origin passing absolute coordinates'''
		if not self.hasOriginPrj:
			raise Exception("Cannot update an unset origin.")
		dx = x - self.crsx
		dy = y - self.crsy
		self.setOriginPrj(x, y, synch)
		if updObjLoc:
			self._moveObjLoc(dx, dy)


	def updOriginGeo(self, lon, lat, updObjLoc=True):
		if not self.isGeoref:
			raise Exception("Cannot update geo origin of an ungeoref scene.")
		x, y = reprojPt(4326, self.crs, lon, lat)
		self.updOriginPrj(x, y, updObjLoc)


	def moveOriginGeo(self, dx, dy, updObjLoc=True):
		if not self.hasOriginGeo:
			raise Exception("Cannot move an unset origin.")
		x = self.lon + dx
		y = self.lat + dy
		self.updOriginGeo(x, y, updObjLoc=updObjLoc)

	def moveOriginPrj(self, dx, dy, useScale=True, updObjLoc=True, synch=True):
		'''Move scene origin passing relative deltas.'''
		if not self.hasOriginPrj:
			raise Exception("Cannot move an unset origin.")

		if useScale:
			self.setOriginPrj(self.crsx + dx * self.scale, self.crsy + dy * self.scale, synch)
		else:
			self.setOriginPrj(self.crsx + dx, self.crsy + dy, synch)

		# Set GIS Maps position absolutely based on cumulative geo-origin displacement.
		# initial_crsx/crsy are stored on the object when it is first created.
		# This avoids incremental drift regardless of call order or MOUSEMOVE state.
		gis_maps = self.scn.objects.get(GIS_MAPS_NAME)
		if gis_maps is not None and 'initial_crsx' in gis_maps:
			gis_maps.location.x = -(self.crsx - gis_maps['initial_crsx']) / self.scale
			gis_maps.location.y = -(self.crsy - gis_maps['initial_crsy']) / self.scale

		if updObjLoc:
			self._moveObjLoc(dx, dy)


	def _moveObjLoc(self, dx, dy):
		topParents = [obj for obj in self.scn.objects if not obj.parent]
		for obj in topParents:
			if obj.name == GIS_MAPS_NAME:
				continue  # positioned absolutely in moveOriginPrj
			obj.location.x -= dx
			obj.location.y -= dy


	def getOriginGeo(self):
		return self.lon, self.lat

	def getOriginPrj(self):
		return self.crsx, self.crsy

	def delOriginGeo(self):
		del self.lat
		del self.lon

	def delOriginPrj(self):
		del self.crsx
		del self.crsy

	def delOrigin(self):
		self.delOriginGeo()
		self.delOriginPrj()

	@property
	def crs(self):
		return self.scn.get(SK.CRS, None) #always string
	@crs.setter
	def crs(self, v):
		#Make sure input value is a valid crs string representation
		crs = SRS(v) #will raise an error if the crs is not valid
		#Reproj existing origin. New CRS will not be set if updating existing origin is not possible
		# try first to reproj from origin geo because self.crs can be empty or broken
		if self.hasOriginGeo:
			if crs.isWGS84:
				#if destination crs is wgs84, just assign lonlat to originprj
				self.crsx, self.crsy = self.lon, self.lat
			self.crsx, self.crsy = reprojPt(4326, str(crs), self.lon, self.lat)
		elif self.hasOriginPrj and self.hasCRS:
			if self.hasValidCRS:
				# will raise an error is current crs is empty or invalid
				self.crsx, self.crsy = reprojPt(self.crs, str(crs), self.crsx, self.crsy)
			else:
				raise Exception("Scene origin coordinates cannot be updated because current CRS is invalid.")
		#Set ID prop
		if SK.CRS not in self.scn:
			self._rna_ui[SK.CRS] = {"description": "Map Coordinate Reference System", "default": ''}
		self.scn[SK.CRS] = str(crs)
	@crs.deleter
	def crs(self):
		if SK.CRS in self.scn:
			del self.scn[SK.CRS]


	@property
	def lat(self):
		return self.scn.get(SK.LAT, None)
	@lat.setter
	def lat(self, v):
		if SK.LAT not in self.scn:
			self._rna_ui[SK.LAT] = {"description": "Scene origin latitude", "default": 0.0, "min":-90.0, "max":90.0}
		if -90 <= v <= 90:
			self.scn[SK.LAT] = v
		else:
			raise ValueError('Wrong latitude value '+str(v))
	@lat.deleter
	def lat(self):
		if SK.LAT in self.scn:
			del self.scn[SK.LAT]

	@property
	def lon(self):
		return self.scn.get(SK.LON, None)
	@lon.setter
	def lon(self, v):
		if SK.LON not in self.scn:
			self._rna_ui[SK.LON] = {"description": "Scene origin longitude", "default": 0.0, "min":-180.0, "max":180.0}
		if -180 <= v <= 180:
			self.scn[SK.LON] = v
		else:
			raise ValueError('Wrong longitude value '+str(v))
	@lon.deleter
	def lon(self):
		if SK.LON in self.scn:
			del self.scn[SK.LON]

	@property
	def crsx(self):
		return self.scn.get(SK.CRSX, None)
	@crsx.setter
	def crsx(self, v):
		if SK.CRSX not in self.scn:
			self._rna_ui[SK.CRSX] = {"description": "Scene x origin in CRS space", "default": 0.0}
		if isinstance(v, (int, float)):
			self.scn[SK.CRSX] = v
		else:
			raise ValueError('Wrong x origin value '+str(v))
	@crsx.deleter
	def crsx(self):
		if SK.CRSX in self.scn:
			del self.scn[SK.CRSX]

	@property
	def crsy(self):
		return self.scn.get(SK.CRSY, None)
	@crsy.setter
	def crsy(self, v):
		if SK.CRSY not in self.scn:
			self._rna_ui[SK.CRSY] = {"description": "Scene y origin in CRS space", "default": 0.0}
		if isinstance(v, (int, float)):
			self.scn[SK.CRSY] = v
		else:
			raise ValueError('Wrong y origin value '+str(v))
	@crsy.deleter
	def crsy(self):
		if SK.CRSY in self.scn:
			del self.scn[SK.CRSY]

	@property
	def scale(self):
		return self.scn.get(SK.SCALE, 1)
	@scale.setter
	def scale(self, v):
		if SK.SCALE not in self.scn:
			self._rna_ui[SK.SCALE] = {"description": "Map scale denominator", "default": 1, "min": 1}
		self.scn[SK.SCALE] = v
	@scale.deleter
	def scale(self):
		if SK.SCALE in self.scn:
			del self.scn[SK.SCALE]

	@property
	def zoom(self):
		return self.scn.get(SK.ZOOM, None)
	@zoom.setter
	def zoom(self, v):
		if SK.ZOOM not in self.scn:
			self._rna_ui[SK.ZOOM] = {"description": "Basemap zoom level", "default": 1, "min": 0, "max":25}
		self.scn[SK.ZOOM] = v
	@zoom.deleter
	def zoom(self):
		if SK.ZOOM in self.scn:
			del self.scn[SK.ZOOM]

	@property
	def hasScale(self):
		#return self.scale is not None
		return SK.SCALE in self.scn

	@property
	def hasZoom(self):
		return self.zoom is not None

	@property
	def fixedOrigin(self):
		'''True if the scene origin was explicitly set to a known project
		point (rather than the default 0,0 sentinel) - basemap import locks
		panning/zooming from moving the origin and starts at max zoom when
		this is set. See VIEW3D_OT_MastroGIS_Basemap_Import.'''
		return self.scn.get(SK.FIXED_ORIGIN, False)
	@fixedOrigin.setter
	def fixedOrigin(self, v):
		if SK.FIXED_ORIGIN not in self.scn:
			self._rna_ui[SK.FIXED_ORIGIN] = {
				"description": "Project origin is fixed (not the default 0,0)",
				"default": False,
			}
		self.scn[SK.FIXED_ORIGIN] = v
	@fixedOrigin.deleter
	def fixedOrigin(self):
		if SK.FIXED_ORIGIN in self.scn:
			del self.scn[SK.FIXED_ORIGIN]

