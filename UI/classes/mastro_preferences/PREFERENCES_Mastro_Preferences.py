import json
import os

import bpy
from bpy.types import AddonPreferences

from .... import PREFS_KEY
from ....Utils.add_nodes import apply_shadow_color
from ....Utils.mastro_gis.prefs import PredefCRS, DEFAULT_CRS, APP_DATA
from ....Utils.mastro_gis import settings as mastro_gis_settings

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
    
    projection_suffix: bpy.props.StringProperty(
        name="Projection Suffix",
        default="_projection",
        description="Suffix appended to each 2D projected object and to the parent empty"
    )

    section_offset: bpy.props.FloatProperty(
        name="Section Offset",
        default=0.01,
        min=0.0,
        soft_max=0.1,
        precision=4,
        unit='LENGTH',
        description="Section mesh is moved this distance toward the camera, so it masks projection lines behind it"
    )

    section_color: bpy.props.FloatVectorProperty(
        name        = "Section Color",
        subtype     = "COLOR",
        size        = 3,
        min         = 0.0,
        max         = 1.0,
        default     = (0.8, 0.1, 0.1),
        description = "Initial color set on the MaStro Section Colour node group when materials are first appended",
    )

    shadow_color: bpy.props.FloatVectorProperty(
        name        = "Shadow Color",
        subtype     = "COLOR",
        size        = 3,
        min         = 0.0,
        max         = 1.0,
        default     = (0.1, 0.1, 0.1),
        description = "Initial color set on the MaStro Shadow Colour node group when materials are first appended",
    )

    shadow_offset: bpy.props.FloatProperty(
        name="Shadow Offset",
        default=0.01,
        min=0.0,
        soft_max=0.1,
        precision=4,
        unit='LENGTH',
        description="Shadow mesh is moved this distance away from the camera, so it does not mask projection lines"
    )

    open_file_detection: bpy.props.BoolProperty(
        name="Open File Detection",
        default=True,
        description="When opening a .blend file, warn if another user already has it open"
    )

    show_overlay_settings: bpy.props.BoolProperty(
        name="Overlay Settings",
        default=False
    )

    show_note_settings: bpy.props.BoolProperty(
        name="Note Settings",
        default=False
    )

    show_projection_settings: bpy.props.BoolProperty(
        name="Projection Settings",
        default=False
    )

    show_pen_settings: bpy.props.BoolProperty(
        name="Pens",
        default=False
    )

    show_gis_settings: bpy.props.BoolProperty(
        name="GIS",
        default=False
    )

    # --- GIS: predefined CRS ---
    def listPredefCRS(self, context):
        return [tuple(elem) for elem in json.loads(self.predefCrsJson)]

    predefCrsJson: bpy.props.StringProperty(default=json.dumps(DEFAULT_CRS))

    predefCrs: bpy.props.EnumProperty(
        name="Predefinate CRS",
        description="Choose predefinite Coordinate Reference System",
        items=listPredefCRS
    )

    # --- GIS: basemap cache folder ---
    def getCacheFolder(self):
        return bpy.path.abspath(self.get("cacheFolder", ''))

    def setCacheFolder(self, value):
        if os.access(value, os.X_OK | os.W_OK):
            self["cacheFolder"] = value
        else:
            self["cacheFolder"] = "The selected folder has no write access"

    def getCacheFolder5x(self, v, isSet):
        return bpy.path.abspath(v)

    def setCacheFolder5x(self, newVal, currentVal, isSet):
        if os.access(newVal, os.X_OK | os.W_OK):
            return newVal

    if bpy.app.version[0] >= 5:
        gis_cache_folder: bpy.props.StringProperty(
            name="Cache folder",
            default=APP_DATA,
            description="Define a folder where to store Geopackage SQlite db",
            subtype='DIR_PATH',
            get_transform=getCacheFolder5x,
            set_transform=setCacheFolder5x
        )
    else:
        gis_cache_folder: bpy.props.StringProperty(
            name="Cache folder",
            default=APP_DATA,
            description="Define a folder where to store Geopackage SQlite db",
            subtype='DIR_PATH',
            get=getCacheFolder,
            set=setCacheFolder
        )

    # --- GIS: basemap viewer behaviour ---
    gis_synch_origin: bpy.props.BoolProperty(
        name="Synch. lat/long",
        description='Keep geo origin synchronized with crs origin. Can be slow with remote reprojection services',
        default=True)

    gis_zoom_to_mouse: bpy.props.BoolProperty(
        name="Zoom to mouse",
        description='Zoom towards the mouse pointer position',
        default=True)

    gis_lock_objects: bpy.props.BoolProperty(
        name="Lock objects",
        description='Retain objects geolocation when moving map origin',
        default=True)

    gis_resampling: bpy.props.EnumProperty(
        name="Resampling method",
        description="Choose GDAL's resampling method used for reprojection",
        items=[('NN', 'Nearest Neighboor', ''), ('BL', 'Bilinear', ''), ('CB', 'Cubic', ''), ('CBS', 'Cubic Spline', ''), ('LCZ', 'Lanczos', '')]
    )

    gis_adjust_3dview: bpy.props.BoolProperty(
        name="Adjust 3D view",
        description="Update 3d view grid size and clip distances according to the new imported object's size",
        default=True)

    gis_force_textured_solid: bpy.props.BoolProperty(
        name="Force Viewport Shading: Material Preview",
        description="Switch the viewport to Material Preview shading to display the imported texture/material",
        default=True)

    def updateMapTilerApiKey(self, context):
        mastro_gis_settings.maptiler_api_key = self.gis_maptiler_api_key

    gis_maptiler_api_key: bpy.props.StringProperty(
        name="",
        description="API key for MapTiler Coordinates API (required for EPSG.io migration)",
        update=updateMapTilerApiKey,
        default="ZzKFdpgCVbjFs6HyKe8Z",
    )

    gis_google_api_key: bpy.props.StringProperty(
        name="",
        description="Google Maps Platform API key",
        default="AIzaSyDeabiA2pp5FnWvGzNiH0t-9rlsJZEHhxE",
    )

    gis_google_3dtiles_lod: bpy.props.EnumProperty(
        name="3D Tiles quality",
        description="Level of detail for Google 3D Tiles import",
        items=[
            ("lod1", "Whole city",             "Very low detail, covers a large area"),
            ("lod2", "Districts",              "Low detail"),
            ("lod3", "Groups of buildings",    "Medium detail"),
            ("lod4", "Separate buildings",     "Good detail"),
            ("lod5", "Buildings with details", "High detail"),
            ("lod6", "Maximum detail",         "Highest detail, heavy download"),
        ],
        default="lod3",
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

        # Section: Projection
        box = layout.box()
        box.prop(self,
                 "show_projection_settings",
                 text="2D Projection",
                 icon='TRIA_DOWN' if self.show_projection_settings else 'TRIA_RIGHT',
                 emboss=False)
        if self.show_projection_settings:
            col = box.column(align=True)
            row = col.row()
            row.label(text="Projection Suffix:")
            row.prop(self, "projection_suffix", text="")
            row = col.row()
            row.label(text="Section Offset:")
            row.prop(self, "section_offset", text="")
            row = col.row()
            row.label(text="Shadow Offset:")
            row.prop(self, "shadow_offset", text="")
            row = col.row()
            row.label(text="Section Color:")
            row.prop(self, "section_color", text="")
            row = col.row()
            row.label(text="Shadow Color:")
            row.prop(self, "shadow_color", text="")

        # Section: Pens
        box = layout.box()
        box.prop(self,
                 "show_pen_settings",
                 text="Pens",
                 icon='TRIA_DOWN' if self.show_pen_settings else 'TRIA_RIGHT',
                 emboss=False)
        if self.show_pen_settings:
            scene = context.scene
            if scene is None:
                box.label(text="Open a scene to manage pens.")
            else:
                box.template_list(
                    "PREFERENCES_UL_MaStroCad_All_Pens", "",
                    scene, "mastro_cad_pens",
                    scene, "mastro_cad_pen_index",
                    rows=6,
                )

        # Section: GIS
        box = layout.box()
        box.prop(self,
                 "show_gis_settings",
                 text="GIS",
                 icon='TRIA_DOWN' if self.show_gis_settings else 'TRIA_RIGHT',
                 emboss=False)
        if self.show_gis_settings:
            col = box.column(align=True)

            row = col.row().split(factor=0.5)
            row.prop(self, "predefCrs", text='')
            row.operator("mastrogis.add_predef_crs", icon='ADD')
            row.operator("mastrogis.edit_predef_crs", icon='PREFERENCES')
            row.operator("mastrogis.rmv_predef_crs", icon='REMOVE')
            row.operator("mastrogis.reset_predef_crs", icon='PLAY_REVERSE')

            col.prop(self, "gis_cache_folder")

            row = col.row()
            row.prop(self, "gis_zoom_to_mouse")
            row.prop(self, "gis_lock_objects")
            row.prop(self, "gis_synch_origin")

            row = col.row()
            row.prop(self, "gis_resampling")

            row = col.row()
            row.prop(self, "gis_adjust_3dview")
            row.prop(self, "gis_force_textured_solid")

            row = col.row().split(factor=0.2)
            row.label(text="MapTiler API Key")
            row.prop(self, "gis_maptiler_api_key")

            row = col.row().split(factor=0.2)
            row.label(text="Google API Key")
            row.prop(self, "gis_google_api_key")

            row = col.row()
            row.enabled = bool(self.gis_google_api_key)
            row.prop(self, "gis_google_3dtiles_lod")

        # Section: Open File Detection
        box = layout.box()
        row = box.row()
        row.label(text="Open File Detection:", icon='FILE_BLEND')
        row.prop(self, "open_file_detection", text="Enabled")



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