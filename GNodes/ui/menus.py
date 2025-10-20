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

from ..customnodes import classes as MASTROCUSTOMCLASSES


class MASTRO_MT_add_gn_menu(bpy.types.Menu):

    bl_idname = "MASTRO_MT_add_gn_menu"
    bl_label  = "MaStro"

    @classmethod
    def poll(cls, context):
        return (bpy.context.space_data.tree_type == 'GeometryNodeTree')

    def draw(self, context):
        for cls in MASTROCUSTOMCLASSES:
            if ('_NG_' in cls.__name__):
                op = self.layout.operator("node.add_node", text=cls.bl_label,)
                op.type = cls.bl_idname
                op.use_transform = True

        return None


def mastro_addGNmenu_append(self, context,):

    self.layout.menu("MASTRO_MT_add_gn_menu", text="MaStro Filter",)

    return None 

def mastro_nodemenu_append(self, context):

    layout = self.layout 
    layout.separator()
    layout.operator("mastro.node_purge_unused", text="Purge Unused Nodes",)

    return None


def append_menus():

    bpy.types.NODE_MT_add.append(mastro_addGNmenu_append)
    bpy.types.NODE_MT_node.append(mastro_nodemenu_append)

    return None

def remove_menus():
    menus = (bpy.types.NODE_MT_add, bpy.types.NODE_MT_node,)
    for menu in menus:
        for f in menu._dyn_ui_initialize().copy():
            if (f.__name__=='mastro_addGNmenu_append'):
                menu.remove(f)
            if (f.__name__=='mastro_addGNmenu_append'):
                menu.remove(f)

    return None