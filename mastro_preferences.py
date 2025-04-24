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
from bpy.types import Operator, AddonPreferences


    
# from bpy.props import IntProperty, FloatVectorProperty #StringProperty, FloatProperty, BoolProperty

class mastro_addon_preferences(AddonPreferences):
    # this must match the add-on name, use '__package__'
    # when defining this in a submodule of a python package.
    # bl_idname = __name__
    bl_idname = __package__

    # filepath: StringProperty(
    #     name="Example File Path",
    #     subtype='FILE_PATH',
    # )
    # number: IntProperty(
    #     name="Example Number",
    #     default=4,
    # )
    # boolean: BoolProperty(
    #     name="Example Boolean",
    #     default=False,
    # )
    fontSize: bpy.props.IntProperty(
        name="Font Size",
        min = 8,
        default = 8
    )
    
    edgeSize: bpy.props.IntProperty(
        name="Edge thickness of the selection",
        min = 1,
        default = 3
    )
    
    fontColor: bpy.props.FloatVectorProperty(
                 name = "Font Color Picker",
                 subtype = "COLOR",
                 size = 4,
                 min = 0.0,
                 max = 1.0,
                 default = (1.0, 1.0, 0.0, 1.0))
    
    edgeColor: bpy.props.FloatVectorProperty(
                 name = "Color of the edges of the selected object",
                 subtype = "COLOR",
                 size = 4,
                 min = 0.0,
                 max = 1.0,
                 default = (1.0, 0.3, 0.0, 0.2))
    
    faceColor: bpy.props.FloatVectorProperty(
                 name = "Color of the selected faces",
                 subtype = "COLOR",
                 size = 4,
                 min = 0.0,
                 max = 1.0,
                 default = (1.0, 0.0, 0.0, 0.4))
    
    toggleSelectionOverlay: bpy.props.BoolProperty(
                name = "Selection overlay",
                default = True,
                description = "Show selection overlay when the MaStro mass is in edit mode"
                )


    def draw(self, context):
        layout = self.layout
        # layout.label(text="MaStro addon preferences")
        # layout.prop(self, "filepath")
        # layout.prop(self, "number")
        # layout.prop(self, "boolean")
        # layout.label(text="Text")
        row = layout.row()
        row.label(text = "Font Size:")
        row.prop(self, "fontSize", icon_only=True)
        row = layout.row()
        row.label(text = "Font Color:")
        row.prop(self, "fontColor", icon_only=True)
        row = layout.row()
        
        layout.separator
        # col = layout.column(align=True)
        row = layout.row()
        row.label(text = "Toggle selection overlay:")
        row.prop(self, "toggleSelectionOverlay", icon_only=True)
        row = layout.row()
        row.label(text = "Edge selection size:")
        row.prop(self, "edgeSize", icon_only=True)
        row = layout.row()
        row.label(text = "Edge selection color:")
        row.prop(self, "edgeColor", icon_only=True)
        row = layout.row()
        row.label(text = "Face selection color:")
        row.prop(self, "faceColor", icon_only=True)
       
        

# class OBJECT_OT_mastro_addon_prefs(Operator):
#     """Display example preferences"""
#     bl_idname = "object.mastro_addon_prefs"
#     bl_label = "MaStro add-on Preferences"
#     bl_options = {'REGISTER', 'UNDO'}

#     def execute(self, context):
#         preferences = context.preferences
#         # addon_prefs = preferences.addons[__name__].preferences
#         addon_prefs = preferences.addons[__package__].preferences


#         # info = ("Path: %s, Number: %d, Boolean %r" %
#         #         (addon_prefs.filepath, addon_prefs.number, addon_prefs.boolean))
#         info = ("Font Size: %s, Font color: %d" %
#                 (addon_prefs.fontSize, addon_prefs.fontColor))

#         self.report({'INFO'}, info)
#         # print(info)

#         return {'FINISHED'}