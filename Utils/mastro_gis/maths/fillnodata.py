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




########################################
# Inpainting function
# http://astrolitterbox.blogspot.fr/2012/03/healing-holes-in-arrays-in-python.html
# https://github.com/gasagna/openpiv-python/blob/master/openpiv/src/lib.pyx


import numpy as np

DTYPEf = np.float32
#DTYPEi = np.int32


def replace_nans(array, max_iter, tolerance, kernel_size=1, method='localmean'):
	"""
	Replace NaN elements in an array using an iterative image inpainting algorithm.
	The algorithm is the following:
	1) For each element in the input array, replace it by a weighted average
	of the neighbouring elements which are not NaN themselves. The weights depends
	of the method type. If ``method=localmean`` weight are equal to 1/( (2*kernel_size+1)**2 -1 )
	2) Several iterations are needed if there are adjacent NaN elements.
	If this is the case, information is "spread" from the edges of the missing
	regions iteratively, until the variation is below a certain threshold.

	Parameters
	----------
	array : 2d np.ndarray
	an array containing NaN elements that have to be replaced

	max_iter : int
	the number of iterations

	kernel_size : int
	the size of the kernel, default is 1

	method : str
	the method used to replace invalid values. Valid options are 'localmean', 'idw'.

	Returns
	-------
	filled : 2d np.ndarray
	a copy of the input array, where NaN elements have been replaced.
	"""

	filled = np.empty( [array.shape[0], array.shape[1]], dtype=DTYPEf)
	kernel = np.empty( (2*kernel_size+1, 2*kernel_size+1), dtype=DTYPEf )

	# indices where array is NaN
	inans, jnans = np.nonzero( np.isnan(array) )

	# number of NaN elements
	n_nans = len(inans)

	# arrays which contain replaced values to check for convergence
	replaced_new = np.zeros( n_nans, dtype=DTYPEf)
	replaced_old = np.zeros( n_nans, dtype=DTYPEf)

	# depending on kernel type, fill kernel array
	if method == 'localmean':
		# weight are equal to 1/( (2*kernel_size+1)**2 -1 )
		for i in range(2*kernel_size+1):
			for j in range(2*kernel_size+1):
				kernel[i,j] = 1
		#print(kernel, 'kernel')
	elif method == 'idw':
		kernel = np.array([[0, 0.5, 0.5, 0.5,0],
				  [0.5,0.75,0.75,0.75,0.5],
				  [0.5,0.75,1,0.75,0.5],
				  [0.5,0.75,0.75,0.5,1],
				  [0, 0.5, 0.5 ,0.5 ,0]])
		#print(kernel, 'kernel')
	else:
		raise ValueError("method not valid. Should be one of 'localmean', 'idw'.")

	# fill new array with input elements
	for i in range(array.shape[0]):
		for j in range(array.shape[1]):
			filled[i,j] = array[i,j]

	# make several passes
	# until we reach convergence
	for it in range(max_iter):
		#print('Fill NaN iteration', it)
		# for each NaN element
		for k in range(n_nans):
			i = inans[k]
			j = jnans[k]

			# initialize to zero
			filled[i,j] = 0.0
			n = 0

			# loop over the kernel
			for I in range(2*kernel_size+1):
				for J in range(2*kernel_size+1):

					# if we are not out of the boundaries
					if i+I-kernel_size < array.shape[0] and i+I-kernel_size >= 0:
						if j+J-kernel_size < array.shape[1] and j+J-kernel_size >= 0:

							# if the neighbour element is not NaN itself.
							if filled[i+I-kernel_size, j+J-kernel_size] == filled[i+I-kernel_size, j+J-kernel_size] :

								# do not sum itself
								if I-kernel_size != 0 and J-kernel_size != 0:

									# convolve kernel with original array
									filled[i,j] = filled[i,j] + filled[i+I-kernel_size, j+J-kernel_size]*kernel[I, J]
									n = n + 1*kernel[I,J]
			# divide value by effective number of added elements
			if n != 0:
				filled[i,j] = filled[i,j] / n
				replaced_new[k] = filled[i,j]
			else:
				filled[i,j] = np.nan

		# check if mean square difference between values of replaced
		# elements is below a certain tolerance
		#print('tolerance', np.mean( (replaced_new-replaced_old)**2 ))
		if np.mean( (replaced_new-replaced_old)**2 ) < tolerance:
			break
		else:
			for l in range(n_nans):
				replaced_old[l] = replaced_new[l]

	return filled

