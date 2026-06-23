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

    clip_range_cutting_plane_height: bpy.props.FloatProperty(
        name="Cutting Plane Height",
        default=1.2,
        min=0.0,
        precision=3,
        unit='LENGTH',
        description=(
            "Standard architectural section height above the floor (Top view) "
            "or below the ceiling (Bottom view): the Level Sets clip range "
            "extends this far past the active level's own elevation, on the "
            "side closest to the camera, instead of stopping exactly at it"
        ),
    )

    create_drawing_at_active_level: bpy.props.BoolProperty(
        name="Create Drawings at Active Level",
        default=True,
        description=(
            "New MaStro drawing objects are placed at the elevation of the "
            "active level in whichever Top/Bottom ortho viewport's Clip "
            "Range is active, instead of at the 3D cursor's Z position"
        ),
    )

    rename_plan_on_relock: bpy.props.BoolProperty(
        name="Rename Plan on Re-lock",
        default=True,
        description=(
            "MaStro plan objects are renamed to \"<level name> - <FFL>\" "
            "every time they are (re-)locked to a level - including locking "
            "an existing plan to a different level - not just when first "
            "created. Disable to keep the name a plan was given untouched"
        ),
    )

    rename_plan_on_level_change: bpy.props.BoolProperty(
        name="Rename Plan on Level Change",
        default=True,
        description=(
            "MaStro plan objects locked to a level are renamed to "
            "\"<level name> - <FFL>\" whenever that level's name or "
            "elevation changes, keeping the name in sync with the level it "
            "follows. Disable to keep the name a plan was given untouched"
        ),
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
        name="Map Tiler API Key",
        description="API key for MapTiler Coordinates API (required for EPSG.io migration)",
        update=updateMapTilerApiKey,
        default="ZzKFdpgCVbjFs6HyKe8Z",
    )

    gis_google_api_key: bpy.props.StringProperty(
        name="Google API Key",
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

        # Section: Projection
        header, panel = layout.panel("mastro_prefs_projection_settings", default_closed=True)
        header.label(text="2D Projection")
        if panel:
            col = panel.column(align=True)
            split = col.split(factor=0.2)
            split.label(text="Projection Suffix:")
            split.prop(self, "projection_suffix", text="")
            split = col.split(factor=0.2)
            split.label(text="Section Offset:")
            split.prop(self, "section_offset", text="")
            split = col.split(factor=0.2)
            split.label(text="Shadow Offset:")
            split.prop(self, "shadow_offset", text="")
            split = col.split(factor=0.2)
            split.label(text="Section Color:")
            split.prop(self, "section_color", text="")
            split = col.split(factor=0.2)
            split.label(text="Shadow Color:")
            split.prop(self, "shadow_color", text="")

        # Section: File
        header, panel = layout.panel("mastro_prefs_file_settings", default_closed=True)
        header.label(text="File")
        if panel:
            split = panel.split(factor=0.2)
            split.label(text="Open File Detection:")
            split.prop(self, "open_file_detection", text="Enabled")

        # Section: GIS
        header, panel = layout.panel("mastro_prefs_gis_settings", default_closed=True)
        header.label(text="GIS")
        if panel:
            col = panel.column(align=True)
            split = layout.split(factor=0.2)
            split.label(text="CRS")
            col = split.column()
            col.prop(self, "predefCrs", text='')
            row = col.row()
            row.operator("mastrogis.add_predef_crs", icon='ADD')
            row.operator("mastrogis.edit_predef_crs", icon='PREFERENCES')
            row.operator("mastrogis.rmv_predef_crs", icon='REMOVE')
            row.operator("mastrogis.reset_predef_crs", icon='PLAY_REVERSE')
            col.prop(self, "gis_maptiler_api_key")


            col.separator()
            split = layout.split(factor=0.2)
            split.label(text="Origin")
            col = split.column()
            col.prop(self, "gis_zoom_to_mouse")
            col.prop(self, "gis_lock_objects")
            col.prop(self, "gis_synch_origin")

            row = col.row()
            row.prop(self, "gis_resampling")

            col.separator()
            split = layout.split(factor=0.2)
            split.label(text="3D Tiles")
            col = split.column()
            col.prop(self, "gis_google_api_key")
            col.enabled = bool(self.gis_google_api_key)
            col.prop(self, "gis_google_3dtiles_lod")

            col.separator()
            split = layout.split(factor=0.2)
            split.label(text="Appeareance")
            col = split.column()
            col.prop(self, "gis_adjust_3dview")
            col.prop(self, "gis_force_textured_solid")
            col.prop(self, "gis_cache_folder")

        # Section: Note
        header, panel = layout.panel("mastro_prefs_note_settings", default_closed=True)
        header.label(text="Geometry Nodes Note")
        if panel:
            col = panel.column(align=True)
            row = col.row()
            row.label(text="Font:")

            split = col.split(factor=0.2)
            split.label(text = "Size:")
            split.prop(self, "noteSize", icon_only=True)

            split = col.split(factor=0.2)
            split.label(text = "Color:")
            split.prop(self, "noteColor",icon_only=True)

        # Section: Level Sets
        header, panel = layout.panel("mastro_prefs_level_sets_settings", default_closed=True)
        header.label(text="Levels")
        if panel:
            split = panel.split(factor=0.2)
            split.label(text="Cutting Plane Height:")
            split.prop(self, "clip_range_cutting_plane_height", text="")

            split = panel.split(factor=0.2)
            split.label(text="Drawing Creation:")
            split.prop(self, "create_drawing_at_active_level", text="Create at active level")

            split = panel.split(factor=0.2)
            split.label(text="Plan Renaming:")
            col = split.column(align=True)
            col.prop(self, "rename_plan_on_relock", text="Rename on re-lock")
            col.prop(self, "rename_plan_on_level_change", text="Rename on level change")

        # Section: Overlay
        header, panel = layout.panel("mastro_prefs_overlay_settings", default_closed=True)
        header.label(text="Overlays")
        if panel:
            col = panel.column(align=True)

            # row = col.row()
            # row.label(text = "Toggle Selection Overlays in Edit Mode:")
            # row.prop(self, "toggleSelectionOverlay", icon_only=True)

            # mass
            row = col.row()
            row.label(text="")
            row = col.row()
            row.label(text="Mass Overlay:")

            split = col.split(factor=0.2)
            split.label(text = "Edge thickness:")
            split.prop(self, "massEdgeSize", icon_only=True)

            split = col.split(factor=0.2)
            split.label(text = "Edge color:")
            split.prop(self, "massEdgeColor", icon_only=True)

            split = col.split(factor=0.2)
            split.label(text = "Face color:")
            split.prop(self, "massFaceColor", icon_only=True)

            # block
            row = col.row()
            row.label(text="")
            row = col.row()
            row.label(text="Block Overlay:")

            split = col.split(factor=0.2)
            split.label(text = "Edge thickness:")
            split.prop(self, "blockEdgeSize", icon_only=True)

            # wall
            row = col.row()
            row.label(text="")

            row = col.row()
            row.label(text="Wall Overlay:")

            split = col.split(factor=0.2)
            split.label(text = "Thickness:")
            split.prop(self, "wallEdgeSize", icon_only=True)

            # street
            row = col.row()
            row.label(text="")
            row = col.row()
            row.label(text="Street Overlay:")

            split = col.split(factor=0.2)
            split.label(text = "Thickness:")
            split.prop(self, "streetEdgeSize", icon_only=True)

            # row = col.row()
            # row.label(text = "Dash length:")
            # row.prop(self, "streetEdgeDashSize", icon_only=True)

            # font
            row = col.row()
            row.label(text="")
            row = col.row()
            row.label(text="Font:")

            split = col.split(factor=0.2)
            split.label(text = "Size:")
            split.prop(self, "fontSize", icon_only=True)

            split = col.split(factor=0.2)
            split.label(text = "Color:")
            split.prop(self, "fontColor", icon_only=True)

        # Section: Pens
        header, panel = layout.panel("mastro_prefs_pen_settings", default_closed=True)
        header.label(text="Pens")
        if panel:
            scene = context.scene
            if scene is None:
                panel.label(text="Open a scene to manage pens.")
            else:
                panel.template_list(
                    "PREFERENCES_UL_MaStroCad_All_Pens", "",
                    scene, "mastro_cad_pens",
                    scene, "mastro_cad_pen_index",
                    rows=6,
                )



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