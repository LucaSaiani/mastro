import math
import bpy
from bpy.types import PropertyGroup
from bpy.props import (IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       BoolProperty,
                       StringProperty,
                       CollectionProperty,
                       EnumProperty,
                       PointerProperty,
)

from ...Utils.update_attributes import *
from ...Utils.on_active_layer_changed import on_active_layer_changed

# ------------------------------
# Addon Properties
# ------------------------------
class mastro_CL_addon_properties(PropertyGroup):
    """Per-object custom properties stored in obj.mastro_props."""
    mastro_block_attribute: IntProperty(
        name="MaStro Block Attribute",
        default=1,
        min=1,
        description="Block name"
    )
    
    mastro_building_attribute: IntProperty(
        name="MaStro Building Attribute",
        default=1,
        min=1,
        description="Building name"
    )
    
class mastro_CL_constraint_XY_settings(PropertyGroup):
    """Scene-level toggle for the XY translation/rotation constraint operators."""
    constraint_xy_on: BoolProperty(
        name = 'XY constraints',
        default = False,
        description = 'Toggle XY constraint behaviour globally'
    )
    
# ------------------------------
# Generic Properties
# ------------------------------   
class mastro_CL_name_with_id(PropertyGroup):
    """Generic (name, id) pair used for single-item current-selection trackers."""
    id: IntProperty(
        name="Id",
        description="Name id",
        default = 0)

    name: StringProperty(
        name="Name",
        description="Name",
        default = "")
    
# ------------------------------
# Building Properties
# ------------------------------
class mastro_CL_building_name_list(PropertyGroup):
    """One entry in the project's building list."""
    id: IntProperty(
           name="Id",
           description="Building name id",
           default = 0)
    
    name: StringProperty(
           name="Building Name",
           description="The name of the building",
           default="Building name",
           update=update_mastro_filter_by_building)

# ------------------------------
# Block Properties
# ------------------------------
class mastro_CL_block_name_list(PropertyGroup):
    """One entry in the project's block list."""
    id: IntProperty(
           name="Id",
           description="Block name id",
           default = 0)
    
    name: StringProperty(
           name="Block Name",
           description="The name of the block",
           default="Block name",
           update=update_mastro_filter_by_block)
    
# ------------------------------
# Typology Properties
# ------------------------------
class mastro_CL_typology_name_list(PropertyGroup):
    """One entry in the project's typology list. useList encodes the ordered sequence of use IDs as a semicolon-separated string (e.g. '2;1;3'), listed top-to-bottom."""
    id: IntProperty(
           name="Id",
           description="Typology id",
           default = 0)
    
    name: StringProperty(
           name="Name",
           description="",
           default="Typology name",
           update=update_mastro_filter_by_typology)
    
    useList: StringProperty(
            name="Use",
            description="The uses for the typology",
            default="",
            update=update_all_mastro_meshes_useList)
    
    typologyEdgeColor: bpy.props.FloatVectorProperty(
        name = "Color of the edges of the typology to be shown in the overlay",
        subtype = "COLOR",
        size = 3,
        min = 0.0,
        max = 1.0,
        default = (0.0, 0.7, 0.0))
    
class mastro_CL_obj_typology_uses_name_list(PropertyGroup):
    """Transient per-face/per-edge use breakdown shown in the VIEW3D panel."""
    id: IntProperty( name="Id",
                    description="Obj typology use name id", 
                    default = 0) 
    nameId: IntProperty( name="nameId", 
                        description="The id of the name in the main uses list", 
                        default = 0) 
    name: StringProperty( name="Obj floor use name", 
                         description="The use associated to that set of floors", 
                         default="") 
    storeys: IntProperty( name="Number of storeys", 
                         description="The number of storeys associated to that use", 
                         default = 1)
    
class mastro_CL_typology_uses_name_list(PropertyGroup):
    """Editable sub-list of uses shown in the typology panel."""
    id: IntProperty(
           name="Id",
           description="The typology use name id",
           default = 0)
    
    name: StringProperty(
           name="Name",
           description="The typology use name",
           default="...")
    
class mastro_CL_use_name_list(PropertyGroup):
    """One use type (e.g. Residential, Office) with its floor-to-floor height and storey rules."""
    id: IntProperty(
           name="Id",
           description="Use name id",
           default = 0)
    
    name: StringProperty(
           name="Name",
           description="The name of the use",
           default = "Use name",
           update=update_mastro_nodes_by_use)
    
    floorToFloor: FloatProperty(
        name="Height",
        description="Floor to floor height of the selected use",
        min=0,
        max=99,
        precision=3,
        default = 3.150,
        unit='LENGTH',
        update=update_all_mastro_meshes_floorToFloor)

    storeys:IntProperty(
        name="Storeys",
        description="Number of storeys of the selected use.\nIf \"Variable number of storeys\" is selected, this value is ignored",
        min=1,
        max=99,
        default = 1,
        update=update_all_mastro_meshes_numberOfStoreys)
    
    liquid: BoolProperty(
            name = "Variable storeys",
            description = "When enabled, the number of storeys for this use is distributed dynamically to fill the remaining floors after fixed uses are placed. Takes priority over the fixed storey count.",
            default = False,
            update=update_all_mastro_meshes_numberOfStoreys)
    
    # undercroft: BoolProperty(
    #         name = "undercroft",
    #         description = "It indicates whether the use is considered to be a undercroft volume in the mass, or not",
    #         default = False)
    


    
# ------------------------------
# Floor Properties
# ------------------------------
class mastro_CL_floor_name_list(PropertyGroup):
    """One entry in the project's floor-type list."""
    id: IntProperty(
           name="Id",
           description="Floor name id",
           default = 0)
    
    name: StringProperty(
           name="Floor Name",
           description="The name of the floor",
           default="Floor type")
    
# ------------------------------
# Wall Properties
# ------------------------------
class mastro_CL_wall_name_list(PropertyGroup):
    """One wall type with thickness, offset, normal direction, and overlay color."""
    id: IntProperty(
           name="Id",
           description="Wall name id",
           default = 0)
    
    name: StringProperty(
           name="Wall Name",
           description="The name of the wall",
           default="Wall type",
           update=update_mastro_filter_by_wall_type)
  
    wallThickness: FloatProperty(
        name="Wall thickness",
        description="The thickness of the wall",
        min=0,
        #max=99,
        precision=3,
        default = 0.300,
        unit='LENGTH',
        # update=update_all_mastro_wall_thickness
        )
    
    wallOffset: FloatProperty(
        name="Wall offset",
        description="The offset of the wall from its center line",
        min=0,
        #max=99,
        precision=3,
        default = 0,
        unit='LENGTH',
        # update=update_all_mastro_wall_offset
        )
    
    normal: IntProperty(
           name="Wall Normal",
           description="Invert the normal of the wall",
           default = 1)
    
    wallEdgeColor: FloatVectorProperty(
        name = "Color of the edges of the wall to be shown in the overlay",
        subtype = "COLOR",
        size = 3,
        min = 0.0,
        max = 1.0,
        default = (0.0, 0.0, 1.0))


# ------------------------------
# Street Properties
# ------------------------------
class mastro_CL_street_name_list(PropertyGroup):
    """One street type with width, corner radius, and overlay color."""
    id: IntProperty(
           name="Id",
           description="Street name id",
           default = 0)
    
    name: StringProperty(
           name="Street type Name",
           description="The type name of the street",
           default="Street type",
           update=update_mastro_filter_by_street_type)
    
    streetWidth: FloatProperty(
        name="Street width",
        description="The width of the street",
        min=0,
        #max=99,
        precision=3,
        default = 8,
        unit='LENGTH',
        update=update_all_mastro_street_width)
    
    streetRadius: FloatProperty(
        name="Street radius",
        description="The radius of the street",
        min=0,
        #max=99,
        precision=3,
        default = 16,
        unit='LENGTH',
        update=update_all_mastro_street_radius)
    
    streetEdgeColor: FloatVectorProperty(
        name = "Color of the edges of the street to be shown in the overlay",
        subtype = "COLOR",
        size = 3,
        min = 0.0,
        max = 1.0,
        default = (1.0, 0.0, 0.0))

# ------------------------------
# Node editor Properties
# ------------------------------
class mastro_CL_Sticky_Note(PropertyGroup):
    """Marks a NodeFrame as a MaStro sticky note so it can be styled and identified."""
    customNote: BoolProperty(
        name="Custom Note",
        description="Indicates if this NodeFrame is a custom sticky note",
        default=False
    )


# ------------------------------
# View Layer Manager Properties
# ------------------------------

def _on_slot_name_changed(self, context):
    """Propagate a user rename of a shadow slot to the actual Blender view layer."""
    scene = context.scene
    # If a view layer with the new name already exists, this is a sync update — not a rename.
    if scene.view_layers.get(self.name):
        self.prev_name = self.name
        return
    old_vl = scene.view_layers.get(self.prev_name)
    if old_vl:
        old_vl.name = self.name
        self.prev_name = self.name


class mastro_CL_layer_slot(PropertyGroup):
    """One entry in the view-layer shadow list — stores the layer name and its previous name for rename detection."""
    name: StringProperty(update=_on_slot_name_changed)
    prev_name: StringProperty()


class mastro_CL_layer_manager_props(PropertyGroup):
    """Scene-level container for the view-layer shadow list and its active index."""
    layer_slots: CollectionProperty(type=mastro_CL_layer_slot)
    active_index: IntProperty(
        default=0,
        update=on_active_layer_changed,
    )


# ------------------------------
# Projector Properties
# ------------------------------

class mastro_CL_projector_properties(PropertyGroup):
    # ── Enable ────────────────────────────────────────────────────────────────

    enabled: BoolProperty(
        name        = "Projection",
        default     = False,
        description = "Enable this camera for 2D projection and shadow bake",
    )

    # ── Sampling ──────────────────────────────────────────────────────────────

    sampling_method: EnumProperty(
        name        = "Sampling Method",
        default     = 'UNIFORM',
        description = "Visibility sampling strategy along each projected edge",
        items       = [
            ('UNIFORM',  "Uniform",
             "Sample visibility at evenly spaced intervals along each edge. "
             "Reliable and predictable — recommended for most scenes"),
        ]
    )
    segment_length: FloatProperty(
        name        = "Segment Length",
        default     = 0.02,
        min         = 0.001,
        soft_max    = 0.5,
        precision   = 3,
        description = (
            "Sampling precision in NDC screen space (range 0..2 per axis). "
            "Smaller = more samples, more accurate visibility transitions. "
            "Independent of object size or distance from camera"
        ),
    )
    ray_offset: FloatProperty(
        name        = "Ray Offset",
        default     = 1e-4,
        min         = 0.0,
        precision   = 6,
        unit        = 'LENGTH',
        description = "World-space offset applied to ray origins to avoid self-intersection"
    )

    # ── Output ────────────────────────────────────────────────────────────────

    include_hidden: BoolProperty(
        name        = "Include Hidden",
        default     = False,
        description = "Also include hidden lines (as separate edges in a dedicated empty)"
    )
    only_selected_objects: BoolProperty(
        name        = "Only Selected Objects",
        default     = False,
        description = (
            "Project only the selected objects. All visible objects still "
            "participate in occlusion calculations"
        )
    )
    place_on_camera_plane: BoolProperty(
        name        = "Place on Camera Plane",
        default     = False,
        description = "Place the result in front of the camera plane"
    )
    flat_angle_threshold: FloatProperty(
        name        = "Flat Angle Threshold",
        default     = math.radians(5.0),
        min         = 0.0,
        max         = math.radians(180.0),
        soft_max    = math.radians(90.0),
        precision   = 1,
        unit        = 'ROTATION',
        description = (
            "Edges shared by two nearly-parallel faces of the SAME object "
            "are hidden when the angle between their normals is below this "
            "threshold. Edges between different materials or different objects "
            "are always shown regardless of this setting"
        )
    )
    remove_overlapping_boundary: BoolProperty(
        name        = "Remove Overlapping Boundary",
        default     = True,
        description = (
            "Remove overlapping portions of boundary edges (single-face edges) "
            "within the same object before projection. "
            "Only active when Flat Angle Threshold is greater than 0"
        )
    )
    compute_silhouette: BoolProperty(
        name        = "Compute Silhouette",
        default     = False,
        description = (
            "Identify and tag silhouette edges — edges on the boundary between "
            "camera-facing and back-facing faces (or mesh boundary edges). "
            "Silhouette edges are always included regardless of Flat Angle Threshold "
            "and are assigned to dedicated vertex groups on the output mesh"
        )
    )
    # ── Shadow / Light ────────────────────────────────────────────────────────

    shadow_method: EnumProperty(
        name        = "Method",
        description = "Algorithm used to compute shadows",
        default     = 'RENDER',
        items       = [
            ('RENDER',     "Render",     "Bake shadows by rendering with the Workbench engine"),
            ('SILHOUETTE', "Silhouette", "Compute shadows geometrically by projecting sun-visible faces"),
        ],
    )

    cutter_detection: EnumProperty(
        name        = "Cutter Detection",
        description = "Spatial acceleration used to find camera-facing occluders for each shadow polygon",
        default     = 'AABB',
        items       = [
            ('AABB', "AABB",
             "Bounding-box pre-filter: skip polygons whose UV bounding boxes do not "
             "overlap the shadow polygon. Fast and simple — recommended for most scenes"),
            ('BVH',  "BVH Tree",
             "Build a BVH tree of all camera-facing polygons and query only the "
             "candidates that overlap each shadow polygon. Best for scenes with "
             "many polygons"),
        ],
    )

    grid_subdivisions: IntProperty(
        name        = "Grid Subdivisions",
        description = (
            "Number of tiles along the camera's longest axis. "
            "Each tile is 256 px; more tiles = higher total resolution"
        ),
        default     = 10,
        min         = 1,
        max         = 100,
    )
    render_boundary_res: IntProperty(
        name        = "Boundary Resolution",
        description = (
            "Target pixels on the short side when sampling the shadow boundary. "
            "Higher = finer border detail, more vertices"
        ),
        default     = 400,
        min         = 50,
        max         = 2000,
    )
    render_interior_res: IntProperty(
        name        = "Interior Resolution",
        description = (
            "Target pixels on the short side when sampling the shadow interior. "
            "Lower = fewer interior triangles, faster"
        ),
        default     = 100,
        min         = 20,
        max         = 500,
    )

    virtual_azimuth: FloatProperty(
        name        = "Azimuth",
        default     = math.radians(315.0),
        min         = 0.0,
        max         = math.radians(360.0),
        subtype     = 'ANGLE',
        description = "Shadow direction, counterclockwise",
    )
    virtual_elevation: FloatProperty(
        name        = "Elevation",
        default     = math.radians(45.0),
        min         = math.radians(0.1),
        max         = math.radians(90.0),
        subtype     = 'ANGLE',
        description = "Angle of the virtual light source above the horizon",
    )
    light_space: EnumProperty(
        name        = "Space",
        default     = 'WORLD',
        description = "Reference frame for the virtual light direction",
        items       = [
            ('WORLD',  "World",  "Azimuth and elevation are in world space"),
            ('CAMERA', "Camera", "Azimuth and elevation are relative to the camera view — useful for consistent shadow direction across all elevations"),
        ],
    )

    def _light_poll(self, obj):
        return obj.type == 'LIGHT' and obj.data.type in ('SUN', 'AREA')

    light_source: bpy.props.PointerProperty(
        name        = "Light",
        type        = bpy.types.Object,
        poll        = _light_poll,
        description = "Sun or Area light. When set, overrides the virtual light source",
    )
    run_projection: BoolProperty(
        name        = "2D Projection",
        description = "Run the 2D projection when clicking Run",
        default     = True,
    )
    run_shadows: BoolProperty(
        name        = "Shadows",
        description = "Run the shadow bake when clicking Run",
        default     = True,
    )
    active_for_batch: BoolProperty(
        name        = "Active",
        default     = True,
        description = "Include this camera in batch calculation",
    )

    # ── Advanced ──────────────────────────────────────────────────────────────

    camera_clipping: BoolProperty(
        name        = "Camera Clipping",
        default     = False,
        description = (
            "Clip projected geometry using the camera clipping planes. "
            "Edges beyond the far clip plane are truncated at the boundary; "
            "faces that straddle it generate an additional section line"
        )
    )
    compute_intersections: BoolProperty(
        name        = "Compute Intersections",
        default     = False,
        description = (
            "Calculate and project the intersection curves between "
            "interpenetrating objects. Enable only when objects overlap in 3D"
        )
    )
    snap_orphans: BoolProperty(
        name        = "Snap Orphans",
        default     = True,
        description = (
            "Move each orphan endpoint to the nearest point on the projected "
            "wire of the occluder that caused the cut"
        )
    )
    merge_by_distance: BoolProperty(
        name        = "Merge by Distance",
        default     = True,
        description = (
            "Merge vertices closer than the specified threshold before snapping. "
            "Helps clean up near-coincident vertices produced by the projection"
        )
    )
    merge_distance: FloatProperty(
        name        = "Merge Distance",
        default     = 1e-5,
        min         = 0.0,
        precision   = 6,
        soft_max    = 0.01,
        unit        = 'LENGTH',
        description = (
            "Maximum distance between vertices to be merged. "
            "Operates in 2D projection space — values smaller than "
            "segment_length are typical"
        )
    )

    # ── Output format ─────────────────────────────────────────────────────────

    convert_to_grease_pencil: BoolProperty(
        name        = "Convert to Grease Pencil",
        default     = False,
        description = "Convert all projection and shadow output meshes to Grease Pencil objects after generation",
    )


class mastro_CL_projector_batch_item(PropertyGroup):
    camera_name: StringProperty()


class mastro_CL_projector_scene_props(PropertyGroup):
    # ── Runtime state ─────────────────────────────────────────────────────────
    is_running:       BoolProperty(default=False)
    proj_is_running:  BoolProperty(default=False)

    # ── Batch queue ───────────────────────────────────────────────────────────
    batch_queue:  bpy.props.CollectionProperty(type=mastro_CL_projector_batch_item)
    batch_cursor: IntProperty(default=0)

