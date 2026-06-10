import json
import logging
log = logging.getLogger(__name__)
import os

import bpy
from bpy.props import StringProperty, EnumProperty, BoolProperty
from bpy.types import Operator

from .proj.reproj import MapTilerCoordinates
from .proj.srs import SRS
from . import settings

from ... import PREFS_KEY as PKG


def getAppData():
	home = os.path.expanduser('~')
	loc = os.path.join(home, '.bgis')
	if not os.path.exists(loc):
		os.mkdir(loc)
	return loc

APP_DATA = getAppData()


DEFAULT_CRS = [
	('EPSG:3857', 'Web Mercator', 'Worldwide projection, high distortions, not suitable for precision modelling'),
	('EPSG:4326', 'WGS84 latlon', 'Longitude and latitude in degrees, DO NOT USE AS SCENE CRS (this system is defined only for reprojection tasks')
]


class PredefCRS():

	'''
	Collection of utility methods (callable at class level) to deal with predefined CRS dictionary
	Can be used by others operators that need to fill their own crs enum
	'''

	@staticmethod
	def getData():
		'''Load the json string'''
		prefs = bpy.context.preferences.addons[PKG].preferences
		return json.loads(prefs.predefCrsJson)

	@classmethod
	def getName(cls, key):
		'''Return the convenient name of a given srid or None if this crs does not exist in the list'''
		data = cls.getData()
		try:
			return [entry[1] for entry in data if entry[0] == key][0]
		except IndexError:
			return None

	@classmethod
	def getEnumItems(cls):
		'''Return a list of predefined crs usable to fill a bpy EnumProperty'''
		return [tuple(entry) for entry in cls.getData()]


#################
# Collection of operators to manage predefined CRS

class MASTROGIS_OT_add_predef_crs(Operator):
	bl_idname = "mastrogis.add_predef_crs"
	bl_description = 'Add predefinate CRS'
	bl_label = "Add"
	bl_options = {'INTERNAL'}

	crs: StringProperty(name = "Definition",  description = "Specify EPSG code or Proj4 string definition for this CRS")
	name: StringProperty(name = "Description", description = "Choose a convenient name for this CRS")
	desc: StringProperty(name = "Description", description = "Add a description or comment about this CRS")

	def check(self, context):
		return True

	def search(self, context):

		apiKey = settings.maptiler_api_key

		if not apiKey:
			log.error("No Maptiler API key")
			return

		mtc = MapTilerCoordinates(apiKey=apiKey)
		results = mtc.search(self.query)
		self.results = json.dumps(results)
		if results:
			self.crs = 'EPSG:' + str(results[0]['id']['code'])
			self.name = results[0]['name']

	def updEnum(self, context):
		crsItems = []
		if self.results != '':
			for result in json.loads(self.results):
				srid = 'EPSG:' + str(result['id']['code'])
				crsItems.append( (str(result['id']['code']), result['name'], srid) )
		return crsItems

	def fill(self, context):
		if self.results != '':
			crs = [crs for crs in json.loads(self.results) if str(crs['id']['code']) == self.crsEnum][0]
			self.crs = 'EPSG:' + str(crs['id']['code'])
			self.desc = crs['name']

	query: StringProperty(name='Query', description='Hit enter to process the search', update=search)

	results: StringProperty()

	crsEnum: EnumProperty(name='Results', description='Select the desired CRS', items=updEnum, update=fill)

	search: BoolProperty(name='Search', description='Search for coordinate system into EPSG database', default=False)

	def invoke(self, context, event):
		return context.window_manager.invoke_props_dialog(self)

	def draw(self, context):
		layout = self.layout
		layout.prop(self, 'search')
		if self.search:
			prefs = context.preferences.addons[PKG].preferences
			if not prefs.gis_maptiler_api_key:
				layout.label(text="Searching require a MapTiler API key", icon_value=3)
				layout.prop(prefs, "gis_maptiler_api_key", text='API Key')
			else:
				layout.prop(self, 'query')
				layout.prop(self, 'crsEnum')
			layout.separator()
		layout.prop(self, 'crs')
		layout.prop(self, 'name')
		layout.prop(self, 'desc')

	def execute(self, context):
		if not SRS.validate(self.crs):
			self.report({'ERROR'}, 'Invalid CRS')
		if self.crs.isdigit():
			self.crs = 'EPSG:' + self.crs
		#append the new crs def to json string
		prefs = context.preferences.addons[PKG].preferences
		data = json.loads(prefs.predefCrsJson)
		data.append((self.crs, self.name, self.desc))
		prefs.predefCrsJson = json.dumps(data)
		context.area.tag_redraw()
		return {'FINISHED'}

class MASTROGIS_OT_rmv_predef_crs(Operator):

	bl_idname = "mastrogis.rmv_predef_crs"
	bl_description = 'Remove predefinate CRS'
	bl_label = "Remove"
	bl_options = {'INTERNAL'}

	def execute(self, context):
		prefs = context.preferences.addons[PKG].preferences
		key = prefs.predefCrs
		if key != '':
			data = json.loads(prefs.predefCrsJson)
			data = [e for e in data if e[0] != key]
			prefs.predefCrsJson = json.dumps(data)
		context.area.tag_redraw()
		return {'FINISHED'}

class MASTROGIS_OT_reset_predef_crs(Operator):

	bl_idname = "mastrogis.reset_predef_crs"
	bl_description = 'Reset predefinate CRS'
	bl_label = "Reset"
	bl_options = {'INTERNAL'}

	def execute(self, context):
		prefs = context.preferences.addons[PKG].preferences
		prefs.predefCrsJson = json.dumps(DEFAULT_CRS)
		context.area.tag_redraw()
		return {'FINISHED'}

class MASTROGIS_OT_edit_predef_crs(Operator):

	bl_idname = "mastrogis.edit_predef_crs"
	bl_description = 'Edit predefinate CRS'
	bl_label = "Edit"
	bl_options = {'INTERNAL'}

	crs: StringProperty(name = "EPSG code or Proj4 string",  description = "Specify EPSG code or Proj4 string definition for this CRS")
	name: StringProperty(name = "Description", description = "Choose a convenient name for this CRS")
	desc: StringProperty(name = "Name", description = "Add a description or comment about this CRS")

	def invoke(self, context, event):
		prefs = context.preferences.addons[PKG].preferences
		key = prefs.predefCrs
		if key == '':
			return {'CANCELLED'}
		data = json.loads(prefs.predefCrsJson)
		entry = [entry for entry in data if entry[0] == key][0]
		self.crs, self.name, self.desc = entry
		return context.window_manager.invoke_props_dialog(self)

	def execute(self, context):
		prefs = context.preferences.addons[PKG].preferences
		key = prefs.predefCrs
		data = json.loads(prefs.predefCrsJson)

		if SRS.validate(self.crs):
			data = [entry for entry in data if entry[0] != key] #deleting
			data.append((self.crs, self.name, self.desc))
			prefs.predefCrsJson = json.dumps(data)
			context.area.tag_redraw()
		else:
			self.report({'ERROR'}, 'Invalid CRS')

		return {'FINISHED'}


classes = [
	MASTROGIS_OT_add_predef_crs,
	MASTROGIS_OT_rmv_predef_crs,
	MASTROGIS_OT_reset_predef_crs,
	MASTROGIS_OT_edit_predef_crs,
]


def register():
	for cls in classes:
		bpy.utils.register_class(cls)


def unregister():
	for cls in reversed(classes):
		bpy.utils.unregister_class(cls)
