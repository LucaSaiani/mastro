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

#built-in imports
import math
import os
import threading
import logging
from datetime import datetime
log = logging.getLogger(__name__)

#bpy imports
import bpy
from mathutils import Vector, Matrix
from bpy.types import Operator
from bpy.props import StringProperty, IntProperty, BoolProperty, EnumProperty
import gpu
from gpu_extras.batch import batch_for_shader

#mastro_gis core imports (ported from BlenderGIS)
from ...Utils.mastro_gis import HAS_GDAL, HAS_PIL, HAS_IMGIO
from ...Utils.mastro_gis.proj import reprojBbox, meters2dd
from ...Utils.mastro_gis.basemaps import GRIDS, SOURCES, MapService

from ...Utils.mastro_gis import settings
USER_AGENT = settings.user_agent

from ...Utils.mastro_gis.geoscene import GeoScene, GIS_MAPS_NAME
from ...Utils.mastro_gis.prefs import PredefCRS

from ...Utils.mastro_gis.op_utils import getBBOX, mouseTo3d
from ...Utils.mastro_gis.op_utils import placeObj, adjust3Dview, showTextures, rasterExtentToMesh, geoRastUVmap, addTexture

try:
    from ...Utils.mastro_gis.lib.nominatim import nominatimQuery
except ImportError:
    nominatimQuery = None

from ... import PREFS_KEY as PKG

def _lock_transforms(obj):
    obj.lock_location = (True, True, True)
    obj.lock_rotation = (True, True, True)
    obj.lock_scale    = (True, True, True)


def _get_or_create_empty(scn, name, parent=None):
    obj = scn.objects.get(name)
    if obj is None:
        obj = bpy.data.objects.new(name, None)
        obj.empty_display_type = 'PLAIN_AXES'
        obj.empty_display_size = 0.0
        scn.collection.objects.link(obj)
        if parent is not None:
            obj.parent = parent
        if name == GIS_MAPS_NAME:
            # store the geo-origin at creation time so moveOriginPrj can
            # compute the absolute Blender position of GIS Maps
            from ...Utils.mastro_gis.geoscene import GeoScene
            gs = GeoScene(scn)
            obj['initial_crsx'] = gs.crsx if gs.hasOriginPrj else 0.0
            obj['initial_crsy'] = gs.crsy if gs.hasOriginPrj else 0.0
        _lock_transforms(obj)
    return obj


def _parent_tile(scn, tile_obj, srckey, laykey):
    """Parent tile to its category empty preserving world transform."""
    category = _get_or_create_category_empty(scn, srckey, laykey)
    # tile has no parent yet → matrix_world == location, no depsgraph needed
    world_loc   = tile_obj.location.copy()
    world_scale = tile_obj.scale.copy()
    # category.location is always (0,0,0); its world = GIS Maps location.
    # Read GIS Maps location directly to avoid stale matrix_world after Python moves it.
    gis_maps = scn.objects.get(GIS_MAPS_NAME)
    parent_world = gis_maps.location.copy() if gis_maps is not None else Vector((0, 0, 0))
    tile_obj.parent = category
    tile_obj.matrix_parent_inverse = Matrix.Identity(4)
    tile_obj.location = world_loc - parent_world
    tile_obj.scale    = world_scale
    _lock_transforms(tile_obj)


def _get_or_create_category_empty(scn, srckey, laykey):
    src_name = SOURCES[srckey]['name']
    lay_name = SOURCES[srckey]['layers'][laykey]['name']
    category_name = src_name + " - " + lay_name
    root = _get_or_create_empty(scn, GIS_MAPS_NAME)
    return _get_or_create_empty(scn, category_name, parent=root)


####################

class BaseMap(GeoScene):

	"""Handle a map as background image in Blender"""

	def __init__(self, context, srckey, laykey, grdkey=None):

		#Get context
		self.context = context
		self.scn = context.scene
		GeoScene.__init__(self, self.scn)
		self.area = context.area
		self.area3d = [r for r in self.area.regions if r.type == 'WINDOW'][0]
		self.view3d = self.area.spaces.active
		self.reg3d = self.view3d.region_3d

		#Get cache destination folder in addon preferences
		prefs = context.preferences.addons[PKG].preferences
		cacheFolder = prefs.gis_cache_folder

		self.synchOrj = prefs.gis_synch_origin

		#Get resampling algo preference and set the constant
		MapService.RESAMP_ALG = prefs.gis_resampling

		#Init MapService class
		self.srv = MapService(srckey, cacheFolder)
		self.name = srckey + '_' + laykey + '_' + grdkey + '_' + datetime.now().strftime('%H%M%S')

		#Set destination tile matrix
		if grdkey is None:
			grdkey = self.srv.srcGridKey
		if grdkey == self.srv.srcGridKey:
			self.tm = self.srv.srcTms
		else:
			#Define destination grid in map service
			self.srv.setDstGrid(grdkey)
			self.tm = self.srv.dstTms

		#Init some geoscene props if needed
		if not self.hasCRS:
			self.crs = self.tm.CRS
		if not self.hasOriginPrj:
			self.setOriginPrj(0, 0, self.synchOrj)
		if not self.hasScale:
			self.scale = 1
		if not self.hasZoom:
			self.zoom = 0

		self.lockedZoom = None

		#Set path to tiles mosaic used as background image in Blender
		#We need a format that support transparency so jpg is exclude
		#Writing to tif is generally faster than writing to png
		if bpy.data.is_saved:
			folder = os.path.dirname(bpy.data.filepath) + os.sep
		else:
			# Blender creates a per-session subdirectory in tempdir, cleared on exit
			folder = bpy.app.tempdir
		self.imgPath = folder + self.name + ".tif"

		#Get layer def obj
		self.layer = self.srv.layers[laykey]

		#map keys
		self.srckey = srckey
		self.laykey = laykey
		self.grdkey = grdkey

		self.thread = None
		self.img = None       # bpy image datablock
		self.bkg = None       # empty-image object in scene
		self.viewDstZ = None  # view distance set after place(), used to restore zoom


	def get(self):
		'''Launch run() function in a new thread'''
		self.stop()
		self.srv.start()
		self.thread = threading.Thread(target=self.run)
		self.thread.start()

	def stop(self):
		'''Stop actual thread'''
		if self.srv.running:
			self.srv.stop()
			self.thread.join()

	def run(self):
		"""thread method"""
		self.mosaic = self.request()
		if self.srv.running and self.mosaic is not None:
			#save image
			self.mosaic.save(self.imgPath)
		if self.srv.running:
			#Place background image
			self.place()
		self.srv.stop()

	def moveOrigin(self, dx, dy, useScale=True, updObjLoc=True):
		'''Move scene origin and update props'''
		self.moveOriginPrj(dx, dy, useScale, updObjLoc, self.synchOrj)

	def request(self):
		'''Request map service to build a mosaic of required tiles to cover view3d area'''
		# area.width/height gives actual pixel dimensions; area3d.width returns [1,1] in some states
		w, h = self.area.width, self.area.height

		# Compute bbox in scene CRS from view center + resolution, then reproject if needed
		z = self.lockedZoom if self.lockedZoom is not None else self.zoom
		res = self.tm.getRes(z)
		if self.crs == 'EPSG:4326':
			res = meters2dd(res)
		dx, dy, dz = self.reg3d.view_location
		ox = self.crsx + (dx * self.scale)
		oy = self.crsy + (dy * self.scale)
		xmin = ox - w/2 * res * self.scale
		ymax = oy + h/2 * res * self.scale
		xmax = ox + w/2 * res * self.scale
		ymin = oy - h/2 * res * self.scale
		bbox = (xmin, ymin, xmax, ymax)
		#reproj bbox to destination grid crs if scene crs is different
		if self.crs != self.tm.CRS:
			bbox = reprojBbox(self.crs, self.tm.CRS, bbox)

		log.debug('Bounding box request : {}'.format(bbox))

		if self.srv.srcGridKey == self.grdkey:
			toDstGrid = False
		else:
			toDstGrid = True

		mosaic = self.srv.getImage(self.laykey, bbox, self.zoom, toDstGrid=toDstGrid, outCRS=self.crs)

		return mosaic


	def place(self):
		'''Set map as background image'''

		#Get or load bpy image
		try:
			self.img = [img for img in bpy.data.images if img.filepath == self.imgPath and len(img.packed_files) == 0][0]
		except IndexError:
			self.img = bpy.data.images.load(self.imgPath)

		#Get or load background image
		empties = [obj for obj in self.scn.objects if obj.type == 'EMPTY']
		bkgs = [obj for obj in empties if obj.empty_display_type == 'IMAGE']
		for bkg in bkgs:
			bkg.hide_viewport = True
		try:
			self.bkg = [bkg for bkg in bkgs if bkg.data.filepath == self.imgPath and len(bkg.data.packed_files) == 0][0]
		except IndexError:
			self.bkg = bpy.data.objects.new(self.name, None) #None will create an empty
			self.bkg.empty_display_type = 'IMAGE'
			self.bkg.empty_image_depth = 'BACK'
			self.bkg.data = self.img
			self.scn.collection.objects.link(self.bkg)
		else:
			self.bkg.hide_viewport = False

		#Get some image props
		img_ox, img_oy = self.mosaic.center
		img_w, img_h = self.mosaic.size
		# use actual pixel resolution from the mosaic georef, not the nominal tile res
		res = self.mosaic.pxSize.x

		# empty_display_size=1 means image width equals 1 Blender unit; scale carries the real size
		sizex = img_w * res / self.scale
		sizey = img_h * res / self.scale
		size = max([sizex, sizey])
		self.bkg.empty_display_size = 1
		self.bkg.scale = (size, size, 1)

		# offset so the mosaic center aligns with the geo-origin in scene space
		dx = (self.crsx - img_ox) / self.scale
		dy = (self.crsy - img_oy) / self.scale
		self.bkg.location = (-dx, -dy, 0)

		# adjust clip_end so the full tile is always visible in top ortho view
		needed_clip = max(sizex, sizey) * 10
		for area in self.area.id_data.areas:
			if area.type == 'VIEW_3D':
				space = area.spaces.active
				if space.clip_end < needed_clip:
					space.clip_end = needed_clip
		# Compute the view distance so the viewport shows tiles at native resolution.
		# The formulas below are from the original BlenderGIS code; they may not be
		# perfectly accurate in Blender 2.8+ but give a close enough approximation.
		dst = max([self.area.width, self.area.height])
		z = self.lockedZoom if self.lockedZoom is not None else self.zoom
		res = self.tm.getRes(z)
		dst = dst * res / self.scale
		view3D_aperture = 36  # Blender internal constant
		view3D_zoom = 2       # Blender internal constant
		fov = 2 * math.atan(view3D_aperture / (self.view3d.lens * 2))
		fov = math.atan(math.tan(fov / 2) * view3D_zoom) * 2
		zdst = math.floor((dst / 2) / math.tan(fov / 2))  # floor avoids sub-pixel downscaling
		self.reg3d.view_distance = zdst
		self.viewDstZ = zdst

		#Update image drawing
		self.bkg.data.reload()




####################################
def _set_map_footer(context):
	"""Set the workspace footer with map navigation key hints."""
	def _fn(header, ctx):
		layout = header.layout
		layout.label(text="", icon='MOUSE_MMB')
		layout.label(text="Pan")
		layout.separator()
		layout.label(text="", icon='MOUSE_RMB')
		layout.label(text="Confirm")
	context.workspace.status_text_set(_fn)


def drawInfosText(self, context):
	try:
		_ = self.map
	except ReferenceError:
		return
	#Get contexts
	scn = context.scene
	#Get map props stored in scene
	geoscn = GeoScene(scn)
	zoom = geoscn.zoom
	scale = geoscn.scale
	#
	txt = "Map view : "
	txt += "Zoom " + str(zoom)
	if self.map.lockedZoom is not None:
		txt += " (Locked)"
	txt += " - Scale 1:" + str(int(scale))
	# cursor crs coords
	txt += ' ' + str((int(self.posx), int(self.posy)))
	# progress
	txt += ' ' + self.progress
	context.area.header_text_set(txt)


def drawZoomBox(self, context):
	try:
		_ = self.zoomBoxMode
	except ReferenceError:
		return
	if self.zoomBoxMode and not self.zoomBoxDrag:
		# before selection starts draw infinite cross
		px, py = self.zb_xmax, self.zb_ymax
		p1 = (0, py, 0)
		p2 = (context.area.width, py, 0)
		p3 = (px, 0, 0)
		p4 = (px, context.area.height, 0)
		coords = [p1, p2, p3, p4]
		shader = gpu.shader.from_builtin('UNIFORM_COLOR')
		batch = batch_for_shader(shader, 'LINES', {"pos": coords})
		shader.bind()
		shader.uniform_float("color", (0, 0, 0, 1))
		batch.draw(shader)

	elif self.zoomBoxMode and self.zoomBoxDrag:
		p1 = (self.zb_xmin, self.zb_ymin, 0)
		p2 = (self.zb_xmin, self.zb_ymax, 0)
		p3 = (self.zb_xmax, self.zb_ymax, 0)
		p4 = (self.zb_xmax, self.zb_ymin, 0)
		coords = [p1, p2, p2, p3, p3, p4, p4, p1]
		shader = gpu.shader.from_builtin('UNIFORM_COLOR')
		batch = batch_for_shader(shader, 'LINES', {"pos": coords})
		shader.bind()
		shader.uniform_float("color", (0, 0, 0, 1))
		batch.draw(shader)


###############

class VIEW3D_OT_map_start(Operator):

	bl_idname = "mastrogis.map_start"
	bl_description = 'Toggle 2d map navigation'
	bl_label = "Basemap"
	bl_options = {'REGISTER'}

	#special function to auto redraw an operator popup called through invoke_props_dialog
	def check(self, context):
		return True

	def listSources(self, context):
		srcItems = []
		for srckey, src in SOURCES.items():
			#put each item in a tuple (key, label, tooltip)
			srcItems.append( (srckey, src['name'], src['description']) )
		return srcItems

	def listGrids(self, context):
		grdItems = []
		src = SOURCES[self.src]
		for gridkey, grd in GRIDS.items():
			#put each item in a tuple (key, label, tooltip)
			if gridkey == src['grid']:
				#insert at first position
				grdItems.insert(0, (gridkey, grd['name']+' (source)', grd['description']) )
			else:
				grdItems.append( (gridkey, grd['name'], grd['description']) )
		return grdItems

	def listLayers(self, context):
		layItems = []
		src = SOURCES[self.src]
		for laykey, lay in src['layers'].items():
			#put each item in a tuple (key, label, tooltip)
			layItems.append( (laykey, lay['name'], lay['description']) )
		return layItems


	src: EnumProperty(
				name = "Map",
				description = "Choose map service source",
				items = listSources
				)

	grd: EnumProperty(
				name = "Grid",
				description = "Choose cache tiles matrix",
				items = listGrids
				)

	lay: EnumProperty(
				name = "Layer",
				description = "Choose layer",
				items = listLayers
				)


	dialog: StringProperty(default='MAP') # 'MAP', 'SEARCH', 'OPTIONS'

	query: StringProperty(name="Go to")

	zoom: IntProperty(name='Zoom level', min=0, max=25)

	recenter: BoolProperty(name='Center to existing objects')

	def draw(self, context):
		addonPrefs = context.preferences.addons[PKG].preferences
		scn = context.scene
		layout = self.layout

		if self.dialog == 'SEARCH':
				layout.prop(self, 'query')
				layout.prop(self, 'zoom', slider=True)

		elif self.dialog == 'OPTIONS':
			#viewPrefs = context.preferences.view
			#layout.prop(viewPrefs, "use_zoom_to_mouse")
			layout.prop(addonPrefs, "gis_zoom_to_mouse")
			layout.prop(addonPrefs, "gis_lock_objects")
			layout.prop(addonPrefs, "gis_lock_origin")
			layout.prop(addonPrefs, "gis_synch_origin")

		elif self.dialog == 'MAP':
			layout.prop(self, 'src', text='Source')
			layout.prop(self, 'lay', text='Layer')
			col = layout.column()
			if not HAS_GDAL:
				col.enabled = False
				col.label(text='(No raster reprojection support)')
			col.prop(self, 'grd', text='Tile matrix set')

			#srcCRS = GRIDS[SOURCES[self.src]['grid']]['CRS']
			grdCRS = GRIDS[self.grd]['CRS']
			row = layout.row()
			#row.alignment = 'RIGHT'
			desc = PredefCRS.getName(grdCRS)
			if desc is not None:
				row.label(text='CRS: ' + desc)
			else:
				row.label(text='CRS: ' + grdCRS)

			row = layout.row()
			row.prop(self, 'recenter')

			#row = layout.row()
			#row.label(text='Map scale:')
			#row.prop(scn, '["'+SK.SCALE+'"]', text='')


	def invoke(self, context, event):

		if not HAS_PIL and not HAS_GDAL and not HAS_IMGIO:
			self.report({'ERROR'}, "No imaging library available. ImageIO module was not correctly installed.")
			return {'CANCELLED'}

		if not context.area.type == 'VIEW_3D':
			self.report({'WARNING'}, "View3D not found, cannot run operator")
			return {'CANCELLED'}

		#Update zoom
		geoscn = GeoScene(context.scene)
		if geoscn.hasZoom:
			self.zoom = geoscn.zoom

		#Display dialog
		return context.window_manager.invoke_props_dialog(self)

	def execute(self, context):
		scn = context.scene
		geoscn = GeoScene(scn)
		prefs = context.preferences.addons[PKG].preferences

		#check cache folder
		folder = prefs.gis_cache_folder
		if folder == "" or not os.path.exists(folder):
			self.report({'ERROR'}, "Please define a valid cache folder path in addon's preferences")
			return {'CANCELLED'}
		if not os.access(folder, os.X_OK | os.W_OK):
			self.report({'ERROR'}, "The selected cache folder has no write access")
			return {'CANCELLED'}

		if self.dialog == 'MAP':
			grdCRS = GRIDS[self.grd]['CRS']
			if geoscn.isBroken:
				self.report({'ERROR'}, "Scene georef is broken, please fix it beforehand")
				return {'CANCELLED'}
			#set scene crs as grid crs
			#if not geoscn.hasCRS:
				#geoscn.crs = grdCRS
			#Check if raster reproj is needed
			if geoscn.hasCRS and geoscn.crs != grdCRS and not HAS_GDAL:
				self.report({'ERROR'}, "Please install gdal to enable raster reprojection support")
				return {'CANCELLED'}

		#Move scene origin to the researched place
		if self.dialog == 'SEARCH':
			r = bpy.ops.mastrogis.map_search('EXEC_DEFAULT', query=self.query)
			if r == {'CANCELLED'}:
				self.report({'INFO'}, "No location found")
			else:
				geoscn.zoom = self.zoom


		#Start map viewer operator
		self.dialog = 'MAP' #reinit dialog type
		bpy.ops.mastrogis.map_viewer('INVOKE_DEFAULT', srckey=self.src, laykey=self.lay, grdkey=self.grd, recenter=self.recenter)

		return {'FINISHED'}




###############


class VIEW3D_OT_map_viewer(Operator):

	bl_idname = "mastrogis.map_viewer"
	bl_description = 'Toggle 2d map navigation'
	bl_label = "Map viewer"
	bl_options = {'INTERNAL'}

	srckey: StringProperty()

	grdkey: StringProperty()

	laykey: StringProperty()

	recenter: BoolProperty()

	@classmethod
	def poll(cls, context):
		return context.area.type == 'VIEW_3D'


	def _cleanup(self, context):
		"""Remove timer, draw handlers, and status text; must be called before returning from modal."""
		if getattr(self, 'timer', None) is not None:
			context.window_manager.event_timer_remove(self.timer)
			self.timer = None
		for attr in ('_drawTextHandler', '_drawZoomBoxHandler'):
			handler = getattr(self, attr, None)
			if handler is not None:
				try:
					bpy.types.SpaceView3D.draw_handler_remove(handler, 'WINDOW')
				except Exception:
					pass
			setattr(self, attr, None)
		context.area.header_text_set(None)
		context.workspace.status_text_set(None)

	def __del__(self):
		for attr in ('_drawTextHandler', '_drawZoomBoxHandler'):
			handler = getattr(self, attr, None)
			if handler is not None:
				try:
					bpy.types.SpaceView3D.draw_handler_remove(handler, 'WINDOW')
				except Exception:
					pass
		if getattr(self, 'restart', False):
			bpy.ops.mastrogis.map_start('INVOKE_DEFAULT', src=self.srckey, lay=self.laykey, grd=self.grdkey, dialog=self.dialog)


	def invoke(self, context, event):

		self.restart = False
		self.dialog = 'MAP' # dialog name for MAP_START >> string in  ['MAP', 'SEARCH', 'OPTIONS']

		self.moveFactor = 0.1

		self.prefs = context.preferences.addons[PKG].preferences
		#Option to adjust or not objects location when panning
		self.updObjLoc = self.prefs.gis_lock_objects #if georef is locked then we need to adjust object location after each pan

		#Add draw callback to view space
		args = (self, context)
		self._drawTextHandler = bpy.types.SpaceView3D.draw_handler_add(drawInfosText, args, 'WINDOW', 'POST_PIXEL')
		self._drawZoomBoxHandler = bpy.types.SpaceView3D.draw_handler_add(drawZoomBox, args, 'WINDOW', 'POST_PIXEL')

		#Add modal handler and init a timer
		context.window_manager.modal_handler_add(self)
		self.timer = context.window_manager.event_timer_add(0.04, window=context.window)

		#Switch to top view ortho (center to origin)
		view3d = context.area.spaces.active
		bpy.ops.view3d.view_axis(type='TOP')
		view3d.region_3d.view_perspective = 'ORTHO'
		context.scene.cursor.location = (0, 0, 0)
		if not self.prefs.gis_lock_origin:
			# center on existing GIS tiles if any, otherwise go to origin
			existing = [o for o in context.scene.objects
						if o.type == 'EMPTY' and o.empty_display_type == 'IMAGE']
			if existing:
				xs = [o.matrix_world.translation.x for o in existing]
				ys = [o.matrix_world.translation.y for o in existing]
				cx = (min(xs) + max(xs)) / 2
				cy = (min(ys) + max(ys)) / 2
				view3d.region_3d.view_location = (cx, cy, 0)
			else:
				view3d.region_3d.view_location = (0, 0, 0)

		#Init some properties
		# tag if map is currently drag
		self.inMove = False
		# mouse crs coordinates reported in draw callback
		self.posx, self.posy = 0, 0
		# thread progress infos reported in draw callback
		self.progress = ''
		# Zoom box
		self.zoomBoxMode = False
		self.zoomBoxDrag = False
		self.zb_xmin, self.zb_xmax = 0, 0
		self.zb_ymin, self.zb_ymax = 0, 0

		#Get map
		self.map = BaseMap(context, self.srckey, self.laykey, self.grdkey)

		if self.recenter and len(context.scene.objects) > 0:
			scnBbox = getBBOX.fromScn(context.scene).to2D()
			w, h = scnBbox.dimensions
			px_diag = math.sqrt(context.area.width**2 + context.area.height**2)
			dst_diag = math.sqrt( w**2 + h**2 )
			targetRes = dst_diag / px_diag
			z = self.map.tm.getNearestZoom(targetRes, rule='lower')
			resFactor = self.map.tm.getFromToResFac(self.map.zoom, z)
			context.region_data.view_distance *= resFactor
			x, y = scnBbox.center
			if self.prefs.gis_lock_origin:
				context.region_data.view_location = (x, y, 0)
			else:
				self.map.moveOrigin(x, y)
			self.map.zoom = z

		self.map.get()

		_set_map_footer(context)

		return {'RUNNING_MODAL'}


	def modal(self, context, event):

		context.area.tag_redraw()
		scn = bpy.context.scene

		if event.type == 'TIMER':
			#report thread progression
			self.progress = self.map.srv.report
			return {'PASS_THROUGH'}


		if event.type in ['WHEELUPMOUSE', 'NUMPAD_PLUS']:

			if event.value == 'PRESS':

				if event.alt:
					# map scale up
					self.map.scale *= 10
					self.map.place()
					#Scale existing objects
					for obj in scn.objects:
						obj.location /= 10
						obj.scale /= 10

				elif event.ctrl:
					# view3d zoom up
					dst = context.region_data.view_distance
					context.region_data.view_distance -= dst * self.moveFactor
					if self.prefs.gis_zoom_to_mouse:
						mouseLoc = mouseTo3d(context, event.mouse_region_x, event.mouse_region_y)
						viewLoc = context.region_data.view_location
						deltaVect = (mouseLoc - viewLoc) * self.moveFactor
						viewLoc += deltaVect
				else:
					# map zoom up
					if self.map.zoom < self.map.layer.zmax and self.map.zoom < self.map.tm.nbLevels-1:
						self.map.zoom += 1
						if self.map.lockedZoom is None:
							resFactor = self.map.tm.getNextResFac(self.map.zoom)
							if not self.prefs.gis_zoom_to_mouse:
								context.region_data.view_distance *= resFactor
							else:
								#Progressibly zoom to cursor
								dst = context.region_data.view_distance
								dst2 = dst * resFactor
								context.region_data.view_distance = dst2
								mouseLoc = mouseTo3d(context, event.mouse_region_x, event.mouse_region_y)
								viewLoc = context.region_data.view_location
								moveFactor = (dst - dst2) / dst
								deltaVect = (mouseLoc - viewLoc) * moveFactor
								if self.prefs.gis_lock_origin:
									viewLoc += deltaVect
								else:
									dx, dy, dz = deltaVect
									if not self.prefs.gis_lock_objects and self.map.bkg is not None:
										self.map.bkg.location  -= deltaVect
									self.map.moveOrigin(dx, dy, updObjLoc=self.updObjLoc)
						self.map.get()


		if event.type in ['WHEELDOWNMOUSE', 'NUMPAD_MINUS']:

			if event.value == 'PRESS':

				if event.alt:
					#map scale down
					s = self.map.scale / 10
					if s < 1: s = 1
					self.map.scale = s
					self.map.place()
					#Scale existing objects
					for obj in scn.objects:
						obj.location *= 10
						obj.scale *= 10

				elif event.ctrl:
					#view3d zoom down
					dst = context.region_data.view_distance
					context.region_data.view_distance += dst * self.moveFactor
					if self.prefs.gis_zoom_to_mouse:
						mouseLoc = mouseTo3d(context, event.mouse_region_x, event.mouse_region_y)
						viewLoc = context.region_data.view_location
						deltaVect = (mouseLoc - viewLoc) * self.moveFactor
						viewLoc -= deltaVect
				else:
					#map zoom down
					if self.map.zoom > self.map.layer.zmin and self.map.zoom > 0:
						self.map.zoom -= 1
						if self.map.lockedZoom is None:
							resFactor = self.map.tm.getPrevResFac(self.map.zoom)
							if not self.prefs.gis_zoom_to_mouse:
								context.region_data.view_distance *= resFactor
							else:
								#Progressibly zoom to cursor
								dst = context.region_data.view_distance
								dst2 = dst * resFactor
								context.region_data.view_distance = dst2
								mouseLoc = mouseTo3d(context, event.mouse_region_x, event.mouse_region_y)
								viewLoc = context.region_data.view_location
								moveFactor = (dst - dst2) / dst
								deltaVect = (mouseLoc - viewLoc) * moveFactor
								if self.prefs.gis_lock_origin:
									viewLoc += deltaVect
								else:
									dx, dy, dz = deltaVect
									if not self.prefs.gis_lock_objects and self.map.bkg is not None:
										self.map.bkg.location  -= deltaVect
									self.map.moveOrigin(dx, dy, updObjLoc=self.updObjLoc)
						self.map.get()



		if event.type == 'MOUSEMOVE':

			#Report mouse location coords in projeted crs
			loc = mouseTo3d(context, event.mouse_region_x, event.mouse_region_y)
			self.posx, self.posy = self.map.view3dToProj(loc.x, loc.y)

			if self.zoomBoxMode:
				self.zb_xmax, self.zb_ymax = event.mouse_region_x, event.mouse_region_y

			#Drag background image (edit its offset values)
			if self.inMove:
				loc1 = mouseTo3d(context, self.x1, self.y1)
				loc2 = mouseTo3d(context, event.mouse_region_x, event.mouse_region_y)
				dlt = loc1 - loc2
				if event.ctrl or self.prefs.gis_lock_origin:
					context.region_data.view_location = self.viewLoc1 + dlt
				else:
					#Move background image
					if self.map.bkg is not None:
						self.map.bkg.location[0] = self.offx1 - dlt.x
						self.map.bkg.location[1] = self.offy1 - dlt.y
					#Move existing objects (only top level parent)
					if self.updObjLoc:
						topParents = [obj for obj in scn.objects if not obj.parent]
						for i, obj in enumerate(topParents):
							if obj == self.map.bkg: #the background empty used as basemap
								continue
							loc1 = self.objsLoc1[i]
							obj.location.x = loc1.x - dlt.x
							obj.location.y = loc1.y - dlt.y


		if event.type in {'LEFTMOUSE', 'MIDDLEMOUSE'}:

			if event.value == 'PRESS' and not self.zoomBoxMode:
				#Get click mouse position and background image offset (if exist)
				self.x1, self.y1 = event.mouse_region_x, event.mouse_region_y
				self.viewLoc1 = context.region_data.view_location.copy()
				if not event.ctrl:
					#Stop thread now, because we don't know when the mouse click will be released
					self.map.stop()
					if not self.prefs.gis_lock_origin:
						if self.map.bkg is not None:
							self.offx1 = self.map.bkg.location[0]
							self.offy1 = self.map.bkg.location[1]
						#Store current location of each objects (only top level parent)
						self.objsLoc1 = [obj.location.copy() for obj in scn.objects if not obj.parent]
				#Tag that map is currently draging
				self.inMove = True

			if event.value == 'RELEASE' and not self.zoomBoxMode:
				self.inMove = False
				if not event.ctrl:
					if not self.prefs.gis_lock_origin:
						#Compute final shift
						loc1 = mouseTo3d(context, self.x1, self.y1)
						loc2 = mouseTo3d(context, event.mouse_region_x, event.mouse_region_y)
						dlt = loc1 - loc2
						self.map.moveOrigin(dlt.x, dlt.y, updObjLoc=False)
					self.map.get()


			if event.value == 'PRESS' and self.zoomBoxMode:
				self.zoomBoxDrag = True
				self.zb_xmin, self.zb_ymin = event.mouse_region_x, event.mouse_region_y

			if event.value == 'RELEASE' and self.zoomBoxMode:
				#Get final zoom box
				xmax = max(event.mouse_region_x, self.zb_xmin)
				ymax = max(event.mouse_region_y, self.zb_ymin)
				xmin = min(event.mouse_region_x, self.zb_xmin)
				ymin = min(event.mouse_region_y, self.zb_ymin)
				#Exit zoom box mode
				self.zoomBoxDrag = False
				self.zoomBoxMode = False
				context.window.cursor_set('DEFAULT')
				#Compute the move to box origin
				w = xmax - xmin
				h = ymax - ymin
				cx = xmin + w/2
				cy = ymin + h/2
				loc = mouseTo3d(context, cx, cy)
				#Compute target resolution
				px_diag = math.sqrt(context.area.width**2 + context.area.height**2)
				mapRes = self.map.tm.getRes(self.map.zoom)
				dst_diag = math.sqrt( (w*mapRes)**2 + (h*mapRes)**2)
				targetRes = dst_diag / px_diag
				z = self.map.tm.getNearestZoom(targetRes, rule='lower')
				resFactor = self.map.tm.getFromToResFac(self.map.zoom, z)
				#Preview
				context.region_data.view_distance *= resFactor
				if self.prefs.gis_lock_origin:
					context.region_data.view_location = loc
				else:
					self.map.moveOrigin(loc.x, loc.y, updObjLoc=self.updObjLoc)
				self.map.zoom = z
				self.map.get()


		if event.type in ['LEFT_CTRL', 'RIGHT_CTRL']:

			if event.value == 'PRESS':
				self._viewDstZ = context.region_data.view_distance
				self._viewLoc = context.region_data.view_location.copy()

			if event.value == 'RELEASE':
				#restore view 3d distance and location
				context.region_data.view_distance = self._viewDstZ
				context.region_data.view_location = self._viewLoc


		#NUMPAD MOVES (3D VIEW or MAP)
		if event.value == 'PRESS' and event.type in ['NUMPAD_2', 'NUMPAD_4', 'NUMPAD_6', 'NUMPAD_8']:
			delta = self.map.bkg.scale.x * self.moveFactor
			if event.type == 'NUMPAD_4':
				if event.ctrl or self.prefs.gis_lock_origin:
					context.region_data.view_location += Vector( (-delta, 0, 0) )
				else:
					self.map.moveOrigin(-delta, 0, updObjLoc=self.updObjLoc)
			if event.type == 'NUMPAD_6':
				if event.ctrl or self.prefs.gis_lock_origin:
					context.region_data.view_location += Vector( (delta, 0, 0) )
				else:
					self.map.moveOrigin(delta, 0, updObjLoc=self.updObjLoc)
			if event.type == 'NUMPAD_2':
				if event.ctrl or self.prefs.gis_lock_origin:
					context.region_data.view_location += Vector( (0, -delta, 0) )
				else:
					self.map.moveOrigin(0, -delta, updObjLoc=self.updObjLoc)
			if event.type == 'NUMPAD_8':
				if event.ctrl or self.prefs.gis_lock_origin:
					context.region_data.view_location += Vector( (0, delta, 0) )
				else:
					self.map.moveOrigin(0, delta, updObjLoc=self.updObjLoc)
			if not event.ctrl:
				self.map.get()

		#SWITCH LAYER
		if event.type == 'SPACE':
			self.map.stop()
			self._cleanup(context)
			self.restart = True
			return {'FINISHED'}

		#GO TO
		if event.type == 'G':
			self.map.stop()
			self._cleanup(context)
			self.restart = True
			self.dialog = 'SEARCH'
			return {'FINISHED'}

		#OPTIONS
		if event.type == 'O':
			self.map.stop()
			self._cleanup(context)
			self.restart = True
			self.dialog = 'OPTIONS'
			return {'FINISHED'}

		#Lock/unlock 3d view zoom distance
		if event.type == 'L' and event.value == 'PRESS':
			if self.map.lockedZoom is None:
				self.map.lockedZoom = self.map.zoom
			else:
				self.map.lockedZoom = None
				self.map.get()


		#ZOOM BOX
		if event.type == 'B' and event.value == 'PRESS':
			self.map.stop()
			self.zoomBoxMode = True
			self.zb_xmax, self.zb_ymax = event.mouse_region_x, event.mouse_region_y
			context.window.cursor_set('CROSSHAIR')

		#EXPORT
		if event.type == 'E' and event.value == 'PRESS':
			#
			if not self.map.srv.running and self.map.mosaic is not None:
				self.map.stop()
				self._cleanup(context)

				#Copy image to new datablock
				bpyImg = bpy.data.images.load(self.map.imgPath) #(self.map.img.filepath)
				name = 'EXPORT_' + self.map.srckey + '_' + self.map.laykey + '_' + self.map.grdkey
				bpyImg.name = name
				bpyImg.pack()

				#Add new attribute to GeoRaster (used by geoRastUVmap function)
				rast = self.map.mosaic
				setattr(rast, 'bpyImg', bpyImg)

				#Create Mesh
				dx, dy = self.map.getOriginPrj()
				mesh = rasterExtentToMesh(name, rast, dx, dy, pxLoc='CORNER')

				#Create object
				obj = placeObj(mesh, name)

				#UV mapping
				uvTxtLayer = mesh.uv_layers.new(name='rastUVmap')# Add UV map texture layer
				geoRastUVmap(obj, uvTxtLayer, rast, dx, dy)

				#Create material
				mat = bpy.data.materials.new('rastMat')
				obj.data.materials.append(mat)
				addTexture(mat, bpyImg, uvTxtLayer)

				#Adjust 3d view and display textures
				if self.prefs.gis_adjust_3dview:
					adjust3Dview(context, getBBOX.fromObj(obj))
				if self.prefs.gis_force_textured_solid:
					showTextures(context)

				for obj in context.scene.objects:
					if obj.type == 'EMPTY' and obj.empty_display_type == 'IMAGE':
						obj.hide_viewport = False
				if self.map.bkg is not None:
					_parent_tile(context.scene, self.map.bkg, self.map.srckey, self.map.laykey)
					if self.map.bkg.data is not None:
						self.map.bkg.data.pack()
				return {'FINISHED'}

		#EXIT
		if event.type in {'ESC', 'RIGHTMOUSE', 'RET', 'NUMPAD_ENTER'} and event.value == 'PRESS':
			if self.zoomBoxMode:
				self.zoomBoxDrag = False
				self.zoomBoxMode = False
				context.window.cursor_set('DEFAULT')
			else:
				self.map.stop()
				self._cleanup(context)
				for obj in context.scene.objects:
					if obj.type == 'EMPTY' and obj.empty_display_type == 'IMAGE':
						obj.hide_viewport = False
				if self.map.bkg is not None:
					_parent_tile(context.scene, self.map.bkg, self.map.srckey, self.map.laykey)
					if self.map.bkg.data is not None:
						self.map.bkg.data.pack()
				return {'CANCELLED'}



		return {'RUNNING_MODAL'}



####################################

class VIEW3D_OT_map_search(bpy.types.Operator):

	bl_idname = "mastrogis.map_search"
	bl_description = 'Search for a place and move scene origin to it'
	bl_label = "Map search"
	bl_options = {'INTERNAL'}

	query: StringProperty(name="Go to")

	def invoke(self, context, event):
		geoscn = GeoScene(context.scene)
		if geoscn.isBroken:
			self.report({'ERROR'}, "Scene georef is broken")
			return {'CANCELLED'}
		return context.window_manager.invoke_props_dialog(self)

	def execute(self, context):
		geoscn = GeoScene(context.scene)
		prefs = context.preferences.addons[PKG].preferences
		try:
			results = nominatimQuery(self.query, referer='bgis', user_agent=USER_AGENT)
		except Exception as e:
			log.error('Failed Nominatim query', exc_info=True)
			return {'CANCELLED'}
		if len(results) == 0:
			return {'CANCELLED'}
		else:
			log.debug('Nominatim search results : {}'.format([r['display_name'] for r in results]))
			result = results[0]
			lat, lon = float(result['lat']), float(result['lon'])
			if geoscn.isGeoref:
				geoscn.updOriginGeo(lon, lat, updObjLoc=prefs.gis_lock_objects)
			else:
				geoscn.setOriginGeo(lon, lat)
		return {'FINISHED'}



class VIEW3D_OT_MastroGIS_Basemap_Import(Operator):
    """Launch the interactive map viewer using the source and layer selected in the panel."""
    bl_idname  = "mastrogis.basemap_import"
    bl_label   = "Import Basemap"
    bl_options = {'REGISTER'}

    def execute(self, context):
        scn  = context.scene
        src  = scn.mastro_gis_basemap_source
        lay  = scn.mastro_gis_basemap_layer
        if src not in SOURCES:
            self.report({'ERROR'}, "No source selected")
            return {'CANCELLED'}
        grd = SOURCES[src].get('grid', '')
        bpy.ops.mastrogis.map_viewer('INVOKE_DEFAULT', srckey=src, laykey=lay, grdkey=grd, recenter=False)
        return {'FINISHED'}


classes = [
    VIEW3D_OT_map_start,
    VIEW3D_OT_map_viewer,
    VIEW3D_OT_map_search,
    VIEW3D_OT_MastroGIS_Basemap_Import,
]
