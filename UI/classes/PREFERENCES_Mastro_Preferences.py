import bpy
from bpy.types import AddonPreferences

from ... import PREFS_KEY

"""User preference panel"""
class PREFERENCES_Mastro_Preferences(AddonPreferences):
    # this must match the add-on name, use '__package__'
    # when defining this in a submodule of a python package.
    # bl_idname = __package__
    # bl_idname = "bl_ext.vscode_development.mastro"
    bl_idname = PREFS_KEY

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
    
    noteSize: bpy.props.IntProperty(
        name="Font Size",
        min = 8,
        max = 64,
        default = 12
    )
    
    noteColor: bpy.props.FloatVectorProperty(
                 name = "Font Color Picker",
                 subtype = "COLOR",
                 size = 3,
                 min = 0.0,
                 max = 1.0,
                 default = (0.58, 0.392, 0.103))
    
    fontSize: bpy.props.IntProperty(
        name="Font Size",
        min = 8,
        default = 16
    )
    
    fontColor: bpy.props.FloatVectorProperty(
                 name = "Font Color Picker",
                 subtype = "COLOR",
                 size = 4,
                 min = 0.0,
                 max = 1.0,
                 default = (1.0, 1.0, 0.0, 1.0))
    
    massEdgeSize: bpy.props.IntProperty(
        name="Edge thickness of the selected mass",
        min = 1,
        max = 10,
        default = 3
    )
    
    massEdgeColor: bpy.props.FloatVectorProperty(
                 name = "Color of the edges of the selected mass",
                 subtype = "COLOR",
                 size = 4,
                 min = 0.0,
                 max = 1.0,
                 default = (1.0, 0.0, 0.0, 0.1))
    
    massFaceColor: bpy.props.FloatVectorProperty(
                 name = "Color of the selected faces of the active masss",
                 subtype = "COLOR",
                 size = 4,
                 min = 0.0,
                 max = 1.0,
                 default = (1.0, 0.0, 0.0, 0.4))
    
    blockEdgeSize: bpy.props.IntProperty(
        name="Edge thickness of the selected block",
        min = 1,
        max = 10,
        default = 3
    )
    
    wallEdgeSize: bpy.props.IntProperty(
        name="Edge thickness of the selected wall",
        min = 1,
        max = 10,
        default = 4
    )
    
    streetEdgeSize: bpy.props.IntProperty(
        name="Edge thickness of the selected street",
        min = 1,
        max = 10,
        default = 4
    )
    
    # streetEdgeDashSize: bpy.props.IntProperty(
    #     name="The dash size representing the selected street",
    #     min = 1,
    #     max = 20,
    #     default = 5
    # )
    
    # toggleSelectionOverlay: bpy.props.BoolProperty(
    #             name = "Selection overlay",
    #             default = True,
    #             description = "Show selection overlay when the MaStro mass, block or street is in edit mode"
    #             )
    
    show_overlay_settings: bpy.props.BoolProperty(
        name="Overlay Settings",
        default=False
    )

    show_note_settings: bpy.props.BoolProperty(
        name="Note Settings",
        default=False
    )


    def draw(self, context):
        layout = self.layout

        # Section: Overlay
        box = layout.box()
        box.prop(self, 
                 "show_overlay_settings", 
                 text="Overlays", 
                 icon='TRIA_DOWN' if self.show_overlay_settings else 'TRIA_RIGHT', 
                 emboss=False)
        if self.show_overlay_settings:
            col = box.column(align=True)
            
            # row = col.row()
            # row.label(text = "Toggle Selection Overlays in Edit Mode:")
            # row.prop(self, "toggleSelectionOverlay", icon_only=True)
            
            # mass
            row = col.row()
            row.label(text="")
            row = col.row()
            row.label(text="Mass Overlay:")
            
            row = col.row()
            row.label(text = "Edge thickness:")
            row.prop(self, "massEdgeSize", icon_only=True)
            
            row = col.row()
            row.label(text = "Edge color:")
            row.prop(self, "massEdgeColor", icon_only=True)
            
            row = col.row()
            row.label(text = "Face color:")
            row.prop(self, "massFaceColor", icon_only=True)
            
            # block
            row = col.row()
            row.label(text="")
            row = col.row()
            row.label(text="Block Overlay:")
            
            row = col.row()
            row.label(text = "Edge thickness:")
            row.prop(self, "blockEdgeSize", icon_only=True)
            
            # wall
            row = col.row()
            row.label(text="")

            row = col.row()
            row.label(text="Wall Overlay:")

            row = col.row()
            row.label(text = "Thickness:")
            row.prop(self, "wallEdgeSize", icon_only=True)
            
            # street
            row = col.row()
            row.label(text="")
            row = col.row()
            row.label(text="Street Overlay:")

            row = col.row()
            row.label(text = "Thickness:")
            row.prop(self, "streetEdgeSize", icon_only=True)

            # row = col.row()
            # row.label(text = "Dash length:")
            # row.prop(self, "streetEdgeDashSize", icon_only=True)
                       
            # font
            row = col.row()
            row.label(text="")
            row = col.row()
            row.label(text="Font:")

            row = col.row()
            row.label(text = "Size:")
            row.prop(self, "fontSize", icon_only=True)

            row = col.row()
            row.label(text = "Color:")
            row.prop(self, "fontColor", icon_only=True)
            
        # Section: Note
        box = layout.box()
        box.prop(self, 
                 "show_note_settings", 
                 text="Node Note", 
                 icon='TRIA_DOWN' if self.show_note_settings else 'TRIA_RIGHT', 
                 emboss=False)
        if self.show_note_settings:
            col = box.column(align=True) 
            row = col.row()
            row.label(text="Font:")

            row = col.row()
            row.label(text = "Size:")
            row.prop(self, "noteSize", icon_only=True)

            row = col.row()
            row.label(text = "Color:")
            row.prop(self, "noteColor",icon_only=True)



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