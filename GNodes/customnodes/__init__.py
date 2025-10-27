# Copyright (C) 2022-2025 Luca Saiani

# luca.saiani@gmail.com

# Created by Luca Saiani
# This is part of MaStro addon for Blender

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import bpy

from .windowinfo import MASTRO_NG_windowinfo

classes = (
    MASTRO_NG_windowinfo,
    )

def load_properties():

    bpy.types.Scene.windowInfoNodeCounter = bpy.props.IntProperty(
                                        name="Window Into Node Counter",
                                        default=0,
                                        description="Keep track of the number of Window Info Nodes that are used in the scene")
                                        # update = mastro_massing.update_attributes_mastro_mesh)

    return None

def unload_properties():

    del bpy.types.Scene.windowInfoNodeCounter 

    return None