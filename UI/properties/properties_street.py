import bpy
from bpy.props import (IntProperty,
                       FloatProperty,
                       EnumProperty,
                       CollectionProperty,
                       BoolProperty,
)

from ...Utils.get_names_from_list import get_names_from_list
from ...Utils.update_attributes import update_attributes_street
from .property_classes_street import mastro_CL_street_name_list


def update_street_active_branch(self, context):
    """Branch index changed (cycling) - resync the type enum to that branch's
    current value, without writing anything (read-only resync, no operator call)."""
    import bmesh
    from ...Handlers.utils.mastro_street.street_sectors import _handle_street_sectors

    obj = context.active_object
    if not (obj and obj.type == "MESH" and obj.mode == 'EDIT' and "MaStro street" in obj.data):
        return
    try:
        bm = bmesh.from_edit_mesh(obj.data)
    except ValueError:
        return
    _handle_street_sectors(context.scene, obj, bm)


def update_street_active_branch_type(self, context):
    """User picked a sector type for the current branch - write it to the edge.

    Skipped while street_sectors.py is resyncing this enum to reflect a branch the
    user just cycled to (not an actual choice) - see its _resyncing_branch_type."""
    from ...Handlers.utils.mastro_street import street_sectors
    if street_sectors._resyncing_branch_type:
        return

    scene = context.scene
    bpy.ops.object.set_street_sector_type(
        vertex_index=scene.mastro_street_active_branch_vertex,
        edge_index=scene.mastro_street_active_branch_edge,
        sector_type=int(scene.mastro_street_active_branch_type),
    )


# =============================================================================
# Scene Properties - Street
# =============================================================================
scene_props_street = [
    ("mastro_attribute_street_id", IntProperty(name="Street Id", default=0)),
    ("mastro_attribute_street_width", FloatProperty(
        name="Street width", default=8, precision=3, subtype="DISTANCE"
    )),
    ("mastro_attribute_street_radius", FloatProperty(
        name="Street radius", default=18, precision=3, subtype="DISTANCE"
    )),

    ("mastro_street_name_list", CollectionProperty(type=mastro_CL_street_name_list)),
    ("mastro_street_name_list_index", IntProperty(name="Street Name", default=0)),
    ("mastro_street_names", EnumProperty(
        name="Street List", description="Street type assigned to the selected edge",
        items=lambda self, context: get_names_from_list(context.scene, context, "mastro_street_name_list"),
        update=update_attributes_street
    )),

    # Cycling index into the active vertex's branches (edges), ordered by polar
    # angle - rebuilt/clamped by the selection-reactive handler whenever the active
    # vertex changes (see Handlers/utils/mastro_street/street_sectors.py).
    ("mastro_street_active_branch", IntProperty(
        name="Branch", description="Index of the branch (edge) to configure, cycling around the active vertex",
        default=0, min=0,
        update=update_street_active_branch
    )),
    # Transient, read-only display of how many branches the active vertex has -
    # used by the panel to clamp/wrap the cycling index.
    ("mastro_street_active_branch_count", IntProperty(name="Branch Count", default=0)),
    # The edge/vertex pair the current branch index resolves to - set by the
    # selection-reactive handler, read by update_street_active_branch_type below.
    ("mastro_street_active_branch_vertex", IntProperty(name="Branch Vertex Index", default=0)),
    ("mastro_street_active_branch_edge", IntProperty(name="Branch Edge Index", default=0)),

    # Whether each side of the active branch can produce a real fillet arc
    # (False when the two branches are nearly parallel — circle_ttr returns None).
    # Set by the selection-reactive handler, read by the panel draw() to disable
    # the corresponding enum buttons without any geometry computation in draw().
    ("mastro_street_branch_prev_valid", BoolProperty(name="Prev Side Valid", default=True)),
    ("mastro_street_branch_next_valid", BoolProperty(name="Next Side Valid", default=True)),

    ("mastro_street_active_branch_type", EnumProperty(
        name="Sector Type", description="How the current branch's end is treated at the intersection",
        items=[
            ('1', "A", "Fillet on one side, offset on the other", 'ALIGN_LEFT', 1),
            ('0', "Both", "Symmetric fillet on both sides", 'ALIGN_CENTER', 0),
            ('2', "B", "Fillet on the other side, offset on this one", 'ALIGN_RIGHT', 2),
        ],
        default='0',
        update=update_street_active_branch_type
    )),
]
