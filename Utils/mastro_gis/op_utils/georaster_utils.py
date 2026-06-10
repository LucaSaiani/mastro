# -*- coding:utf-8 -*-

# This file is part of BlenderGIS

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

import bpy, bmesh


def rasterExtentToMesh(name, rast, dx, dy, pxLoc='CORNER', reproj=None):
	'''Build a new mesh that represent a georaster extent'''
	#create mesh
	bm = bmesh.new()
	if pxLoc == 'CORNER':
		pts = [(pt[0], pt[1]) for pt in rast.corners]#shift coords
	elif pxLoc == 'CENTER':
		pts = [(pt[0], pt[1]) for pt in rast.cornersCenter]
	#Reprojection
	if reproj is not None:
		pts = reproj.pts(pts)
	#build shifted flat 3d vertices
	pts = [bm.verts.new((pt[0]-dx, pt[1]-dy, 0)) for pt in pts]#upper left to botton left (clockwise)
	pts.reverse()#bottom left to upper left (anticlockwise --> face up)
	bm.faces.new(pts)
	#Create mesh from bmesh
	mesh = bpy.data.meshes.new(name)
	bm.to_mesh(mesh)
	bm.free()
	return mesh

def geoRastUVmap(obj, uvLayer, rast, dx, dy, reproj=None):
	'''uv map a georaster texture on a given mesh'''
	mesh = obj.data
	#Assign uv coords
	loc = obj.location
	for pg in mesh.polygons:
		for i in pg.loop_indices:
			vertIdx = mesh.loops[i].vertex_index
			pt = list(mesh.vertices[vertIdx].co)
			#adjust coords against object location and shift values to retrieve original point coords
			pt = (pt[0] + loc.x + dx, pt[1] + loc.y + dy)
			if reproj is not None:
				pt = reproj.pt(*pt)
			#Compute UV coords --> pourcent from image origin (bottom left)
			dx_px, dy_px = rast.pxFromGeo(pt[0], pt[1], reverseY=True, round2Floor=False)
			u = dx_px / rast.size[0]
			v = dy_px / rast.size[1]
			#Assign coords
			uvLayer.data[i].uv = [u,v]
