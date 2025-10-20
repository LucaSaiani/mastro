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

def create_socket(ng, in_out='OUTPUT', socket_type="NodeSocketFloat", socket_name="Value",):
    """create a new socket output of given type for given nodegroup"""
    
    #naive support for strandard socket.type notation
    if (socket_type.isupper()):
        socket_type = f'NodeSocket{socket_type.title()}'
    
    sockui = ng.interface.new_socket(socket_name, in_out=in_out, socket_type=socket_type,)
    return sockui


def create_new_nodegroup(name, in_sockets={}, out_sockets={},):
    """create new nodegroup with outputs from given dict {"name":"type",}"""

    ng = bpy.data.node_groups.new(name=name, type='GeometryNodeTree',)
    
    #create main input/output
    in_node = ng.nodes.new('NodeGroupInput')
    in_node.location.x -= 200
    out_node = ng.nodes.new('NodeGroupOutput')
    out_node.location.x += 200

    #create the sockets
    for socket_name, socket_type in in_sockets.items():
        create_socket(ng, in_out='INPUT', socket_type=socket_type, socket_name=socket_name,)
    for socket_name, socket_type in out_sockets.items():
        create_socket(ng, in_out='OUTPUT', socket_type=socket_type, socket_name=socket_name,)
        
    return ng

def set_socket_defvalue(ng, idx, in_out='OUTPUT', value=None,):
    """set the value of the given nodegroups output at given socket idx"""
    
    match in_out:
        case 'OUTPUT':
            ng.nodes["Group Output"].inputs[idx].default_value = value 
        case 'INPUT':
            ng.nodes["Group Input"].outputs[idx].default_value = value 
        case _:
            raise Exception("get_socket_defvalue(): in_out arg not valid")
        
    return None