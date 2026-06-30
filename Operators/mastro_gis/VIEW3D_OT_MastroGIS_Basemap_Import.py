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
from ...Utils.mastro_gis.proj import reprojBbox, reprojPt, meters2dd
from ...Utils.mastro_gis.basemaps import GRIDS, SOURCES, MapService

from ...Utils.mastro_gis.geoscene import GeoScene, GIS_MAPS_NAME

from ...Utils.mastro_gis.op_utils import getBBOX, mouseTo3d
from ...Utils.mastro_gis.op_utils import placeObj, adjust3Dview, showTextures, rasterExtentToMesh, geoRastUVmap, addTexture

from ...UI.properties.properties_gis import reset_origin_staging

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

		#Get layer def obj
		self.layer = self.srv.layers[laykey]

		#Init some geoscene props if needed
		if not self.hasCRS:
			self.crs = self.tm.CRS
		# hasOriginPrj alone is not a reliable "already initialized" guard:
		# the free-pan branch below stamps (0,0) as a sentinel on first use,
		# which would otherwise permanently hide the fixed-origin option.
		# fixedOrigin is the real "don't touch it again" guard - once set,
		# it's never re-evaluated (this is what keeps it stable across
		# subsequent imports).
		just_fixed = False
		if not self.fixedOrigin:
			gis_props = self.scn
			# If a previous fixed/free-pan origin already exists, fixing a new
			# one must relocate the existing maps (and any other top-level
			# objects) so they stay correctly positioned relative to it,
			# instead of leaving them stranded at the old position.
			had_origin = self.hasOriginPrj
			old_crsx, old_crsy = (self.crsx, self.crsy) if had_origin else (0.0, 0.0)
			if gis_props.mastro_gis_origin_input == 'LATLON' and (gis_props.mastro_gis_origin_lat_value != 0.0 or gis_props.mastro_gis_origin_lon_value != 0.0):
				self.setOriginGeo(gis_props.mastro_gis_origin_lon_value, gis_props.mastro_gis_origin_lat_value)
				self.fixedOrigin = True
				just_fixed = True
			elif gis_props.mastro_gis_origin_input == 'PROJECTED' and (gis_props.mastro_gis_origin_x_value != 0.0 or gis_props.mastro_gis_origin_y_value != 0.0):
				# the user enters X/Y in whatever CRS they picked, not
				# necessarily the map's own CRS - reproject to it first
				input_crs = gis_props.mastro_gis_origin_crs
				if input_crs and input_crs != self.crs:
					try:
						x, y = reprojPt(input_crs, self.crs, gis_props.mastro_gis_origin_x_value, gis_props.mastro_gis_origin_y_value)
					except Exception as e:
						raise Exception(
							"Could not convert from {} to {}: {}. This CRS pair isn't covered by the "
							"local builtin formula (WGS84<->WebMercator/UTM only); install GDAL or PyProj, "
							"or set a MapTiler API key in Preferences > GIS to use the remote fallback."
							.format(input_crs, self.crs, e)
						) from e
				else:
					x, y = gis_props.mastro_gis_origin_x_value, gis_props.mastro_gis_origin_y_value
				self.setOriginPrj(x, y, self.synchOrj)
				self.fixedOrigin = True
				just_fixed = True
			elif not self.hasOriginPrj:
				self.setOriginPrj(0, 0, self.synchOrj)

			if just_fixed and had_origin:
				dx = self.crsx - old_crsx
				dy = self.crsy - old_crsy
				gis_maps = self.scn.objects.get(GIS_MAPS_NAME)
				if gis_maps is not None and 'initial_crsx' in gis_maps:
					gis_maps.location.x = -(self.crsx - gis_maps['initial_crsx']) / self.scale
					gis_maps.location.y = -(self.crsy - gis_maps['initial_crsy']) / self.scale
				self._moveObjLoc(dx, dy)

			if just_fixed:
				reset_origin_staging()
		if not self.hasScale:
			self.scale = 1
		if just_fixed or not self.hasZoom:
			if self.fixedOrigin:
				self.zoom = min(self.layer.zmax, self.tm.nbLevels - 1)
			else:
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

		#map keys
		self.srckey = srckey
		self.laykey = laykey
		self.grdkey = grdkey

		self.thread = None
		self.img = None       # bpy image datablock
		self.bkg = None       # empty-image object in scene
		self.viewDstZ = None  # view distance set after place(), used to restore zoom
		self.needsPlace = False  # set by run() (background thread) for the
		                          # modal's main-thread TIMER handler to pick
		                          # up - place() touches bpy.data/GPU state
		                          # and crashes if called off the main thread


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
		"""thread method - network/CPU only, no bpy/GPU calls: place() must
		run on the main thread (see the modal's TIMER handler)"""
		self.mosaic = self.request()
		if self.srv.running and self.mosaic is not None:
			#save image
			self.mosaic.save(self.imgPath)
		if self.srv.running:
			self.needsPlace = True
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


HANDLE_RADIUS = 8  # px, hit-test and draw radius for selection rect corners

def drawSelectionRect(self, context):
	"""Draw the 3D tiles area selection rectangle with 4 draggable corner handles."""
	try:
		_ = self.sel_rect
	except ReferenceError:
		return
	x0, y0, x1, y1 = self.sel_rect
	shader = gpu.shader.from_builtin('UNIFORM_COLOR')

	# rectangle outline
	corners = [(x0, y0, 0), (x0, y1, 0), (x1, y1, 0), (x1, y0, 0)]
	lines = [corners[0], corners[1], corners[1], corners[2],
	         corners[2], corners[3], corners[3], corners[0]]
	batch = batch_for_shader(shader, 'LINES', {"pos": lines})
	shader.bind()
	shader.uniform_float("color", (1.0, 0.6, 0.0, 1.0))
	gpu.state.line_width_set(3.0)
	batch.draw(shader)
	gpu.state.line_width_set(1.0)

	# corner handles as filled squares
	r = HANDLE_RADIUS
	for cx, cy, _ in corners:
		sq = [
			(cx - r, cy - r, 0), (cx + r, cy - r, 0), (cx + r, cy + r, 0),
			(cx - r, cy - r, 0), (cx + r, cy + r, 0), (cx - r, cy + r, 0),
		]
		batch = batch_for_shader(shader, 'TRIS', {"pos": sq})
		shader.bind()
		shader.uniform_float("color", (1.0, 0.6, 0.0, 1.0))
		batch.draw(shader)


def _sel_rect_corners(sel_rect):
	"""Return the 4 corners of sel_rect as (x, y) tuples: BL, TL, TR, BR."""
	x0, y0, x1, y1 = sel_rect
	return [(x0, y0), (x0, y1), (x1, y1), (x1, y0)]


def _hit_handle(sel_rect, mx, my):
	"""Return index 0-3 of the corner handle under the mouse, or None."""
	for i, (cx, cy) in enumerate(_sel_rect_corners(sel_rect)):
		if abs(mx - cx) <= HANDLE_RADIUS and abs(my - cy) <= HANDLE_RADIUS:
			return i
	return None


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


	def _origin_changed(self, context):
		"""Tag the sidebar (N-panel) for redraw so the live origin labels in
		VIEW3D_PT_MastroGIS_Basemap update while panning in free mode."""
		for region in context.area.regions:
			if region.type == 'UI':
				region.tag_redraw()

	def _cleanup(self, context):
		"""Remove timer, draw handlers, and status text; must be called before returning from modal."""
		if getattr(self, 'timer', None) is not None:
			context.window_manager.event_timer_remove(self.timer)
			self.timer = None
		for attr in ('_drawTextHandler', '_drawZoomBoxHandler', '_drawSelRectHandler'):
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
		for attr in ('_drawTextHandler', '_drawZoomBoxHandler', '_drawSelRectHandler'):
			handler = getattr(self, attr, None)
			if handler is not None:
				try:
					bpy.types.SpaceView3D.draw_handler_remove(handler, 'WINDOW')
				except Exception:
					pass


	def invoke(self, context, event):

		self.moveFactor = 0.1

		self.prefs = context.preferences.addons[PKG].preferences
		#Option to adjust or not objects location when panning
		self.updObjLoc = self.prefs.gis_lock_objects #if georef is locked then we need to adjust object location after each pan

		# in 3D Tiles mode the SAT layer is used as a visual reference
		self.is_3dtiles = (self.laykey == "3D")
		if self.is_3dtiles:
			self.laykey = "SAT"

		#Add draw callback to view space
		args = (self, context)
		self._drawTextHandler = bpy.types.SpaceView3D.draw_handler_add(drawInfosText, args, 'WINDOW', 'POST_PIXEL')
		self._drawZoomBoxHandler = bpy.types.SpaceView3D.draw_handler_add(drawZoomBox, args, 'WINDOW', 'POST_PIXEL')
		self._drawSelRectHandler = None

		#Add modal handler and init a timer
		context.window_manager.modal_handler_add(self)
		self.timer = context.window_manager.event_timer_add(0.04, window=context.window)

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

		#Get map - this is what actually fixes the project origin on first use
		#(see BaseMap.__init__), so lockOrigin below must be computed after it
		self.map = BaseMap(context, self.srckey, self.laykey, self.grdkey)

		#Lock the origin once this scene has a fixed project origin (just set
		#above, or from a previous import)
		self.lockOrigin = self.map.fixedOrigin

		#Switch to top view ortho (center to origin)
		view3d = context.area.spaces.active
		bpy.ops.view3d.view_axis(type='TOP')
		view3d.region_3d.view_perspective = 'ORTHO'
		context.scene.cursor.location = (0, 0, 0)
		if not self.lockOrigin:
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
			if self.lockOrigin:
				context.region_data.view_location = (x, y, 0)
			else:
				self.map.moveOrigin(x, y)
				self._origin_changed(context)
			self.map.zoom = z

		self.map.get()

		if self.is_3dtiles:
			# initialize selection rectangle centered in the viewport (1/3 of the area size)
			w, h = context.area.width, context.area.height
			margin_x, margin_y = w // 3, h // 3
			self.sel_rect = [margin_x, margin_y, w - margin_x, h - margin_y]
			self.drag_handle = None  # index 0-3 of the corner being dragged, or None
			self._drawSelRectHandler = bpy.types.SpaceView3D.draw_handler_add(
				drawSelectionRect, (self, context), 'WINDOW', 'POST_PIXEL'
			)

		_set_map_footer(context)

		return {'RUNNING_MODAL'}


	def modal(self, context, event):

		context.area.tag_redraw()
		scn = bpy.context.scene

		if event.type == 'TIMER':
			#report thread progression
			self.progress = self.map.srv.report
			# place() touches bpy.data/GPU state - it must run here on the
			# main thread, never directly inside run()'s background thread
			if self.map.needsPlace:
				self.map.needsPlace = False
				self.map.place()
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
								if self.lockOrigin:
									viewLoc += deltaVect
								else:
									dx, dy, dz = deltaVect
									if not self.prefs.gis_lock_objects and self.map.bkg is not None:
										self.map.bkg.location  -= deltaVect
									self.map.moveOrigin(dx, dy, updObjLoc=self.updObjLoc)
									self._origin_changed(context)
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
								if self.lockOrigin:
									viewLoc += deltaVect
								else:
									dx, dy, dz = deltaVect
									if not self.prefs.gis_lock_objects and self.map.bkg is not None:
										self.map.bkg.location  -= deltaVect
									self.map.moveOrigin(dx, dy, updObjLoc=self.updObjLoc)
									self._origin_changed(context)
						self.map.get()



		if event.type == 'MOUSEMOVE':

			#Report mouse location coords in projeted crs
			loc = mouseTo3d(context, event.mouse_region_x, event.mouse_region_y)
			self.posx, self.posy = self.map.view3dToProj(loc.x, loc.y)

			if self.is_3dtiles and self.drag_handle is not None:
				# drag the active corner; the opposite corner stays fixed
				mx, my = event.mouse_region_x, event.mouse_region_y
				x0, y0, x1, y1 = self.sel_rect
				# corners order: BL=0, TL=1, TR=2, BR=3
				if self.drag_handle == 0:
					self.sel_rect = [mx, my, x1, y1]
				elif self.drag_handle == 1:
					self.sel_rect = [mx, y0, x1, my]
				elif self.drag_handle == 2:
					self.sel_rect = [x0, y0, mx, my]
				elif self.drag_handle == 3:
					self.sel_rect = [x0, my, mx, y1]

			if self.zoomBoxMode:
				self.zb_xmax, self.zb_ymax = event.mouse_region_x, event.mouse_region_y

			#Drag background image (edit its offset values)
			if self.inMove:
				loc1 = mouseTo3d(context, self.x1, self.y1)
				loc2 = mouseTo3d(context, event.mouse_region_x, event.mouse_region_y)
				dlt = loc1 - loc2
				if event.ctrl or self.lockOrigin:
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
							if obj.name == GIS_MAPS_NAME: #positioned absolutely via initial_crsx/crsy
								continue
							loc1 = self.objsLoc1[i]
							obj.location.x = loc1.x - dlt.x
							obj.location.y = loc1.y - dlt.y


		if event.type == 'LEFTMOUSE' and self.is_3dtiles:
			if event.value == 'PRESS':
				hit = _hit_handle(self.sel_rect, event.mouse_region_x, event.mouse_region_y)
				if hit is not None:
					self.drag_handle = hit
					return {'RUNNING_MODAL'}
			elif event.value == 'RELEASE':
				self.drag_handle = None
				return {'RUNNING_MODAL'}

		if event.type in {'LEFTMOUSE', 'MIDDLEMOUSE'}:

			if event.value == 'PRESS' and not self.zoomBoxMode:
				#Get click mouse position and background image offset (if exist)
				self.x1, self.y1 = event.mouse_region_x, event.mouse_region_y
				self.viewLoc1 = context.region_data.view_location.copy()
				if not event.ctrl:
					#Stop thread now, because we don't know when the mouse click will be released
					self.map.stop()
					if not self.lockOrigin:
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
					if not self.lockOrigin:
						#Compute final shift
						loc1 = mouseTo3d(context, self.x1, self.y1)
						loc2 = mouseTo3d(context, event.mouse_region_x, event.mouse_region_y)
						dlt = loc1 - loc2
						self.map.moveOrigin(dlt.x, dlt.y, updObjLoc=False)
						self._origin_changed(context)
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
				if self.lockOrigin:
					context.region_data.view_location = loc
				else:
					self.map.moveOrigin(loc.x, loc.y, updObjLoc=self.updObjLoc)
					self._origin_changed(context)
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
				if event.ctrl or self.lockOrigin:
					context.region_data.view_location += Vector( (-delta, 0, 0) )
				else:
					self.map.moveOrigin(-delta, 0, updObjLoc=self.updObjLoc)
					self._origin_changed(context)
			if event.type == 'NUMPAD_6':
				if event.ctrl or self.lockOrigin:
					context.region_data.view_location += Vector( (delta, 0, 0) )
				else:
					self.map.moveOrigin(delta, 0, updObjLoc=self.updObjLoc)
					self._origin_changed(context)
			if event.type == 'NUMPAD_2':
				if event.ctrl or self.lockOrigin:
					context.region_data.view_location += Vector( (0, -delta, 0) )
				else:
					self.map.moveOrigin(0, -delta, updObjLoc=self.updObjLoc)
					self._origin_changed(context)
			if event.type == 'NUMPAD_8':
				if event.ctrl or self.lockOrigin:
					context.region_data.view_location += Vector( (0, delta, 0) )
				else:
					self.map.moveOrigin(0, delta, updObjLoc=self.updObjLoc)
					self._origin_changed(context)
			if not event.ctrl:
				self.map.get()

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
				if not self.map.fixedOrigin:
					self.map.fixedOrigin = True
				return {'FINISHED'}

		#EXIT
		if event.type in {'ESC', 'RIGHTMOUSE', 'RET', 'NUMPAD_ENTER'} and event.value == 'PRESS':
			if self.zoomBoxMode:
				self.zoomBoxDrag = False
				self.zoomBoxMode = False
				context.window.cursor_set('DEFAULT')
			elif self.is_3dtiles and event.type in {'RET', 'NUMPAD_ENTER', 'RIGHTMOUSE'}:
				# confirm: convert screen rect to geo bbox and launch importer
				self.map.stop()
				self._cleanup(context)
				# remove temporary reference basemap from scene
				if self.map.bkg is not None:
					bpy.data.objects.remove(self.map.bkg, do_unlink=True)
				# the SAT reference layer was only a temporary guide - other
				# previously placed basemap tiles must stay visible
				for obj in context.scene.objects:
					if obj.type == 'EMPTY' and obj.empty_display_type == 'IMAGE':
						obj.hide_viewport = False
				x0, y0, x1, y1 = self.sel_rect
				corners_3d = [mouseTo3d(context, x, y) for x, y in
				              [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]]
				xs = [self.map.crsx + c.x * self.map.scale for c in corners_3d]
				ys = [self.map.crsy + c.y * self.map.scale for c in corners_3d]
				bbox = (min(xs), min(ys), max(xs), max(ys))
				lod = self.prefs.gis_google_3dtiles_lod
				bpy.ops.mastrogis.google_3dtiles_import(
					'EXEC_DEFAULT',
					bbox_xmin=bbox[0], bbox_ymin=bbox[1],
					bbox_xmax=bbox[2], bbox_ymax=bbox[3],
					lod=lod,
					api_key=self.prefs.gis_google_api_key
				)
				if not self.map.fixedOrigin:
					self.map.fixedOrigin = True
				return {'FINISHED'}
			elif self.is_3dtiles and event.type == 'ESC':
				# cancel: remove temporary basemap
				self.map.stop()
				self._cleanup(context)
				if self.map.bkg is not None:
					bpy.data.objects.remove(self.map.bkg, do_unlink=True)
				for obj in context.scene.objects:
					if obj.type == 'EMPTY' and obj.empty_display_type == 'IMAGE':
						obj.hide_viewport = False
				return {'CANCELLED'}
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
				# Closing the viewer after a first successful download fixes the
				# project origin where it currently stands (whether the user got
				# there via manual coordinates or by panning) - every subsequent
				# import is then placed relative to it instead of moving it.
				if not self.map.fixedOrigin:
					self.map.fixedOrigin = True
				return {'CANCELLED'}



		return {'RUNNING_MODAL'}



####################################



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
        try:
            bpy.ops.mastrogis.map_viewer('INVOKE_DEFAULT', srckey=src, laykey=lay, grdkey=grd, recenter=False)
        except RuntimeError as e:
            # Most likely cause: the Projected origin's CRS isn't one of the
            # cases the local builtin formula covers (WGS84<->WebMercator/
            # UTM) and GDAL/PyProj aren't available either, so reprojection
            # fell back to the remote MapTiler service, which needs an API
            # key (Preferences > GIS > MapTiler API Key).
            self.report({'ERROR'}, "Could not open the map viewer: {}".format(e))
            return {'CANCELLED'}
        return {'FINISHED'}


class VIEW3D_OT_MastroGIS_Unlock_Origin(Operator):
    """Allow changing the fixed project origin; existing maps are relocated to the new origin once one is set"""
    bl_idname  = "mastrogis.unlock_origin"
    bl_label   = "Unlock Origin"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        GeoScene(context.scene).fixedOrigin = False
        # Also clear the staged manual-input coordinates: if the origin was
        # originally fixed by typing lat/lon/x/y, those values are still
        # non-zero here, and BaseMap.__init__ would otherwise immediately
        # re-fix the origin back to them on the very next "Download Basemap"
        # click - before the user gets a chance to pan to a new location.
        scn = context.scene
        scn.mastro_gis_origin_lat_value = 0.0
        scn.mastro_gis_origin_lon_value = 0.0
        scn.mastro_gis_origin_x_value = 0.0
        scn.mastro_gis_origin_y_value = 0.0
        reset_origin_staging()
        return {'FINISHED'}


class VIEW3D_OT_MastroGIS_3DTiles_Import(Operator):
    """Download Google 3D Tiles for the selected area and embed textures in the .blend file."""
    bl_idname  = "mastrogis.google_3dtiles_import"
    bl_label   = "Import Google 3D Tiles"
    bl_options = {'REGISTER'}

    bbox_xmin: bpy.props.FloatProperty()
    bbox_ymin: bpy.props.FloatProperty()
    bbox_xmax: bpy.props.FloatProperty()
    bbox_ymax: bpy.props.FloatProperty()
    lod:       bpy.props.StringProperty(default="lod3")
    api_key:   bpy.props.StringProperty()

    def execute(self, context):
        self._tiles_done = 0
        context.area.header_text_set("3D Tiles: downloading…")

        # Both pivots must stay anchored to ONE fixed point for the scene's
        # whole lifetime (GIS Maps' original anchor), never the
        # current/panned-to origin. GIS Maps' own compensating shift assumes
        # ALL of its children's "intrinsic" (pre-shift) position was
        # computed relative to that SAME single anchor - if the translation
        # pivot instead tracked the current pan position, two overlapping
        # downloads taken after panning to different spots would place the
        # SAME real-world building at two different Blender positions, even
        # though each individual download is internally consistent.
        # Rotation has its own, separate reason to need a fixed anchor:
        # Earth's curvature makes "up" differ measurably between two points
        # even a few tens of km apart.
        geoscn = GeoScene(context.scene)
        gis_maps = context.scene.objects.get(GIS_MAPS_NAME)
        if gis_maps is not None and 'initial_crsx' in gis_maps and geoscn.hasValidCRS:
            pivot = reprojPt(geoscn.crs, 4326, gis_maps['initial_crsx'], gis_maps['initial_crsy'])
        else:
            pivot = (geoscn.lon, geoscn.lat) if geoscn.hasOriginGeo else None
        rotation_pivot = pivot

        prefs_for_lod = context.preferences.addons[PKG].preferences
        lod_items = prefs_for_lod.bl_rna.properties['gis_google_3dtiles_lod'].enum_items
        lod_label = lod_items[self.lod].name if self.lod in lod_items else self.lod
        tile_root_name = f"3D {lod_label}"

        try:
            from ...Utils.mastro_gis.threed_tiles import download_tiles
            num_tiles, errors = download_tiles(
                bbox=(self.bbox_xmin, self.bbox_ymin, self.bbox_xmax, self.bbox_ymax),
                lod=self.lod,
                api_key=self.api_key,
                progress_cb=self._on_progress,
                pivot=pivot,
                rotation_pivot=rotation_pivot,
                tile_root_name=tile_root_name,
            )
        except Exception as e:
            context.area.header_text_set(None)
            self.report({'ERROR'}, f"3D Tiles import failed: {e}")
            return {'CANCELLED'}

        context.area.header_text_set(None)

        if errors:
            self.report({'WARNING'}, f"3D Tiles: {num_tiles} tiles imported with errors: {'; '.join(errors)}")
        else:
            self.report({'INFO'}, f"3D Tiles: {num_tiles} tiles imported")

        # embed all tile textures in the .blend file
        for img in bpy.data.images:
            if not img.packed_files and img.filepath:
                try:
                    img.pack()
                except Exception:
                    pass

        prefs = context.preferences.addons[PKG].preferences
        if prefs.gis_adjust_3dview:
            # Use only the geometry just downloaded (this LOD's tile_root
            # children), not the whole scene - the scene may still contain
            # GIS Maps/empties from earlier, much wider-zoomed basemap
            # sessions, which would otherwise inflate the bbox to a
            # planet-sized clip distance.
            tile_root = context.scene.objects.get(tile_root_name)
            if tile_root is not None and tile_root.children:
                bbox = getBBOX.fromObj(tile_root.children[0])
                for child in tile_root.children[1:]:
                    bbox += getBBOX.fromObj(child)
                adjust3Dview(context, bbox)
        if prefs.gis_force_textured_solid:
            showTextures(context)

        return {'FINISHED'}

    def _on_progress(self, done, _total):
        self._tiles_done = done


classes = [
    VIEW3D_OT_map_viewer,
    VIEW3D_OT_MastroGIS_Basemap_Import,
    VIEW3D_OT_MastroGIS_Unlock_Origin,
    VIEW3D_OT_MastroGIS_3DTiles_Import,
]
