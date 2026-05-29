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
                        description="The ID of the name in the main uses list", 
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
           description="Use name ID",
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
# Custom properties
# ------------------------------
class mastro_CL_custom_property_string_name_list(PropertyGroup):
    """One string option within a STRING custom property."""
    id: IntProperty(
           name="Id",
           description="The string option id",
           default=0)
    name: StringProperty(
           name="Name",
           description="The string option name",
           default="")


class mastro_CL_custom_property_name_list(PropertyGroup):
    """Defines a custom property shared by all MaStro objects in the scene.
    Each entry in the scene list corresponds to one custom property slot.
    The property is stored as a custom property on every MaStro object,
    keyed by the entry name with a leading underscore (e.g. "_My Property").
    property_type determines which value, min, max, step and precision
    fields are active; the others are ignored at runtime.
    """
    id: IntProperty(name="Id", default=0)

    previous_name: StringProperty(name="Previous Name", default="")

    name: StringProperty(
        name="Name",
        default="Custom Property",
        update=rename_custom_property_key)

    property_type: EnumProperty(
        name="Type",
        items=[
            ('INT',    "Integer", ""),
            ('FLOAT',  "Float",   ""),
            ('BOOL',   "Boolean", ""),
            ('STRING', "String",  ""),
        ],
        default='INT')

    default_int:    IntProperty(name="Default", default=0)
    default_float:  FloatProperty(name="Default", default=0.0)
    default_bool:   BoolProperty(name="Default", default=False)

    min_int:   IntProperty(name="Min")
    max_int:   IntProperty(name="Max", default=1)
    min_float: FloatProperty(name="Min", default=0.0)
    max_float: FloatProperty(name="Max", default=1.0)

    step_int:       IntProperty(name="Step", default=1)
    step_float:     FloatProperty(name="Step", default=0.1)
    precision_float: IntProperty(name="Precision", default=3)

    description: StringProperty(name="Description", default="")

    assign_to_mass   : BoolProperty(name="Assign to Mass/Block", default=True)
    assign_to_street : BoolProperty(name="Assign to Street",     default=True)

    committed: BoolProperty(name="Committed", default=False)

    string_options      : CollectionProperty(type=mastro_CL_custom_property_string_name_list)
    string_options_index: IntProperty(name="String Option", default=0)
    
    
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
        update=update_mastro_street_width)
    
    streetRadius: FloatProperty(
        name="Street radius",
        description="The radius of the street",
        min=0,
        #max=99,
        precision=3,
        default = 16,
        unit='LENGTH',
        update=update_mastro_street_radius)
    
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
def _sync_note_text(self, context):
    """Push text_content into the linked bpy.data.texts block."""
    import bpy as _bpy
    node_tree = getattr(getattr(context, 'space_data', None), 'edit_tree', None)
    if node_tree is None:
        return
    active = node_tree.nodes.active
    if active is None or not getattr(active, 'text', None):
        return
    text_block = active.text
    text_block.clear()
    text_block.write(self.text_content)


class mastro_CL_Sticky_Note(PropertyGroup):
    """Marks a NodeFrame as a MaStro sticky note so it can be styled and identified."""
    customNote: BoolProperty(
        name="Custom Note",
        description="Indicates if this NodeFrame is a custom sticky note",
        default=False
    )
    text_content: StringProperty(
        name="Note",
        description="Sticky note text — synced to the NodeFrame text block",
        default="",
        update=_sync_note_text,
    )


# ------------------------------
# View Layer Manager Properties
# ------------------------------

class mastro_CL_layer_slot(PropertyGroup):
    """One entry in the view-layer shadow list — stores the layer name and its previous name for rename detection."""

    def _on_slot_name_changed(self, context):
        """Propagate a user rename of a shadow slot to the actual Blender view layer."""
        scene = context.scene
        if scene.view_layers.get(self.name):
            self.prev_name = self.name
            return
        old_vl = scene.view_layers.get(self.prev_name)
        if old_vl:
            old_vl.name = self.name
            self.prev_name = self.name

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
    source_collection: PointerProperty(
        name        = "Source Collection",
        type        = bpy.types.Collection,
        description = (
            "Limit projection and shadows to objects in this collection "
            "(and its sub-collections). Leave empty to use all visible scene objects"
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

    def _light_poll(self, obj):
        return obj.type == 'LIGHT' and obj.data.type in ('SUN', 'AREA')

    def _on_light_source_changed(self, context):
        pass

    def _on_virtual_light_changed(self, context):
        pass
        self["_prev_light_key"] = new_key

    virtual_azimuth: FloatProperty(
        name        = "Azimuth",
        default     = math.radians(315.0),
        min         = 0.0,
        max         = math.radians(360.0),
        subtype     = 'ANGLE',
        description = "Shadow direction, counterclockwise",
        update      = _on_virtual_light_changed,
    )
    virtual_elevation: FloatProperty(
        name        = "Elevation",
        default     = math.radians(45.0),
        min         = math.radians(0.1),
        max         = math.radians(90.0),
        subtype     = 'ANGLE',
        description = "Angle of the virtual light source above the horizon",
        update      = _on_virtual_light_changed,
    )
    light_camera_lock: BoolProperty(
        name        = "Camera Lock",
        description = "Azimuth and elevation are relative to the camera view — useful for consistent shadow direction across all elevations. When off, the direction is in world space",
        default     = False,
        update      = _on_virtual_light_changed,
    )

    light_source: bpy.props.PointerProperty(
        name        = "Light",
        type        = bpy.types.Object,
        poll        = _light_poll,
        update      = _on_light_source_changed,
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
        default     = True,
        description = (
            "Clip projected geometry using the camera clipping planes. "
            "Edges beyond the far clip plane are truncated at the boundary; "
            "faces that straddle it generate an additional section line"
        )
    )
    compute_intersections: BoolProperty(
        name        = "Intersections",
        default     = True,
        description = (
            "Handle objects that physically intersect each other: clips shadow "
            "caster faces against the receiver plane and projects the intersection "
            "curves between interpenetrating volumes. Enable only when objects overlap in 3D"
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
        default     = True,
        description = "Convert all projection and shadow output meshes to Grease Pencil objects after generation",
    )


class mastro_CL_projector_batch_item(PropertyGroup):
    camera_name: StringProperty()


class mastro_CL_camera_set_item(PropertyGroup):
    camera_name: StringProperty()


class mastro_CL_camera_set(PropertyGroup):
    name:       StringProperty(name="Name", default="Set")
    is_default: BoolProperty(default=False)
    cameras:    bpy.props.CollectionProperty(type=mastro_CL_camera_set_item)


class mastro_CL_pdf_frame_item(PropertyGroup):
    frame_name: StringProperty()


class mastro_CL_pdf_set(PropertyGroup):
    name:       StringProperty(name="Name", default="PDF Set")
    bind_pages: BoolProperty(name="Bind Pages", default=False)
    frames:     bpy.props.CollectionProperty(type=mastro_CL_pdf_frame_item)


class mastro_CL_pdf_scene_props(PropertyGroup):
    pdf_sets:                bpy.props.CollectionProperty(type=mastro_CL_pdf_set)
    active_set_index:        IntProperty(default=0, min=0)
    active_frame_index:      IntProperty(default=0, min=0)
    all_frames:              bpy.props.CollectionProperty(type=mastro_CL_pdf_frame_item)
    filter_set_members_only: BoolProperty(
        name        = "Show assigned only",
        default     = False,
        description = "Show only frames assigned to this set",
    )


class mastro_CL_projector_scene_props(PropertyGroup):
    # ── Runtime state ─────────────────────────────────────────────────────────
    is_running:       BoolProperty(default=False)
    proj_is_running:  BoolProperty(default=False)

    # ── Batch queue ───────────────────────────────────────────────────────────
    batch_queue:  bpy.props.CollectionProperty(type=mastro_CL_projector_batch_item)
    batch_cursor: IntProperty(default=0)

    # ── Camera sets ───────────────────────────────────────────────────────────
    camera_sets:              bpy.props.CollectionProperty(type=mastro_CL_camera_set)
    active_set_index:         IntProperty(default=0, min=0)
    active_camera_index:      IntProperty(default=0, min=0)
    filter_set_members_only:  BoolProperty(
        name        = "Show assigned only",
        default     = False,
        description = "Show only cameras assigned to this set",
    )

