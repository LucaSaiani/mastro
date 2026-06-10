
import bpy
from mathutils import Vector
from bpy_extras.view3d_utils import region_2d_to_location_3d, region_2d_to_vector_3d

from .. import BBOX

def mouseTo3d(context, x, y):
	'''Convert event.mouse_region to world coordinates'''
	if context.area.type != 'VIEW_3D':
		raise Exception('Wrong context')
	coords = (x, y)
	reg = context.region
	reg3d = context.region_data
	vec = region_2d_to_vector_3d(reg, reg3d, coords)
	loc = region_2d_to_location_3d(reg, reg3d, coords, vec) #WARNING, this function return indeterminate value when view3d clip distance is too large
	return loc


def placeObj(mesh, objName):
	'''Build and add a new object from a given mesh'''
	bpy.ops.object.select_all(action='DESELECT')
	#create an object with that mesh
	obj = bpy.data.objects.new(objName, mesh)
	# Link object to scene
	bpy.context.scene.collection.objects.link(obj)
	bpy.context.view_layer.objects.active = obj
	obj.select_set(True)
	#bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
	return obj


def adjust3Dview(context, bbox, zoomToSelect=True):
	'''adjust all 3d views clip distance to match the submited bbox'''
	dst = round(max(bbox.dimensions))
	k = 5 #increase factor
	dst = dst * k
	# set each 3d view
	areas = context.screen.areas
	for area in areas:
		if area.type == 'VIEW_3D':
			space = area.spaces.active
			if dst < 100:
				space.clip_start = 1
			elif dst < 1000:
				space.clip_start = 10
			else:
				space.clip_start = 100
			#Adjust clip end distance if the new obj is largest than actual setting
			if space.clip_end < dst:
				if dst > 10000000:
					dst = 10000000 #too large clip distance broke the 3d view
				space.clip_end = dst
			if zoomToSelect:
				overrideContext = context.copy()
				overrideContext['area'] = area
				overrideContext['region'] = area.regions[-1]
				if bpy.app.version[0] > 3:
					with context.temp_override(**overrideContext):
						bpy.ops.view3d.view_selected()
				else:
					bpy.ops.view3d.view_selected(overrideContext)


def showTextures(context):
	'''Force view mode with textures'''
	scn = context.scene
	for area in context.screen.areas:
		if area.type == 'VIEW_3D':
			space = area.spaces.active
			if space.shading.type == 'SOLID':
				space.shading.color_type = 'TEXTURE'


def addTexture(mat, img, uvLay, name='texture'):
	'''Set a new image texture to a given material and following a given uv map'''
	engine = bpy.context.scene.render.engine
	mat.use_nodes = True
	node_tree = mat.node_tree
	node_tree.nodes.clear()
	# create uv map node
	uvMapNode = node_tree.nodes.new('ShaderNodeUVMap')
	uvMapNode.uv_map = uvLay.name
	uvMapNode.location = (-800, 200)
	# create image texture node
	textureNode = node_tree.nodes.new('ShaderNodeTexImage')
	textureNode.image = img
	textureNode.extension = 'CLIP'
	textureNode.show_texture = True
	textureNode.location = (-400, 200)
	# Create BSDF diffuse node
	diffuseNode = node_tree.nodes.new('ShaderNodeBsdfPrincipled')#ShaderNodeBsdfDiffuse
	diffuseNode.location = (0, 200)
	# Create output node
	outputNode = node_tree.nodes.new('ShaderNodeOutputMaterial')
	outputNode.location = (400, 200)
	# Connect the nodes
	node_tree.links.new(uvMapNode.outputs['UV'] , textureNode.inputs['Vector'])
	node_tree.links.new(textureNode.outputs['Color'] , diffuseNode.inputs['Base Color'])#diffuseNode.inputs['Color'])
	node_tree.links.new(diffuseNode.outputs['BSDF'] , outputNode.inputs['Surface'])


class getBBOX():

	'''Utilities to build BBOX object from various Blender context'''

	@staticmethod
	def fromObj(obj, applyTransform = True):
		'''Create a 3D BBOX from Blender object'''
		if applyTransform:
			boundPts = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
		else:
			boundPts = obj.bound_box
		xmin = min([pt[0] for pt in boundPts])
		xmax = max([pt[0] for pt in boundPts])
		ymin = min([pt[1] for pt in boundPts])
		ymax = max([pt[1] for pt in boundPts])
		zmin = min([pt[2] for pt in boundPts])
		zmax = max([pt[2] for pt in boundPts])
		return BBOX(xmin=xmin, ymin=ymin, zmin=zmin, xmax=xmax, ymax=ymax, zmax=zmax)

	@classmethod
	def fromScn(cls, scn):
		'''Create a 3D BBOX from Blender Scene
		union of bounding box of all objects containing in the scene'''
		#objs = scn.collection.objects
		objs = [obj for obj in scn.collection.all_objects if obj.empty_display_type != 'IMAGE']
		if len(objs) == 0:
			scnBbox = BBOX(0,0,0,0,0,0)
		else:
			scnBbox = cls.fromObj(objs[0])
		for obj in objs:
			bbox = cls.fromObj(obj)
			scnBbox += bbox
		return scnBbox
