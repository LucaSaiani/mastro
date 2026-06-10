import math
import bpy
from bpy.types import PropertyGroup
from bpy.props import (IntProperty,
                       FloatProperty,
                       BoolProperty,
                       StringProperty,
                       EnumProperty,
                       PointerProperty,
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
