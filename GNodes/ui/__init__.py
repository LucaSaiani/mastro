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

from .menus import (

    MASTRO_MT_add_gn_menu,
    append_menus, 
    remove_menus,

    )

# from .panels import (

#     NODEBOOSTER_PT_tool_search,
#     NODEBOOSTER_PT_tool_color_palette,
#     NODEBOOSTER_PT_tool_frame,
#     NODEBOOSTER_PT_shortcuts_memo,
#     NODEBOOSTER_PT_active_node,

#     )


classes = (
    MASTRO_MT_add_gn_menu,
    )


def load_ui():
    append_menus()
    return None


def unload_ui():
    remove_menus()
    return None