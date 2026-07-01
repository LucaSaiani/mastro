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


def _make_sector_flag_update(suffix, side):
    def update(self, context):
        from ...Handlers.utils.mastro_street import street_sectors
        if street_sectors._resyncing_sector_type:
            return
        scene = context.scene
        bpy.ops.object.set_street_sector_type(
            edge_index=scene.mastro_street_active_edge,
            suffix=suffix,
            side=side,
            value=getattr(scene, f"mastro_street_sector_{suffix}_{side}"),
        )
    return update


def _make_sector_enum_update(suffix):
    """Translate the 3-button enum (Left/Both/Right) into two bool flags."""
    def update(self, context):
        from ...Handlers.utils.mastro_street import street_sectors
        if street_sectors._resyncing_sector_type:
            return
        scene = context.scene
        val = getattr(scene, f"mastro_street_sector_enum_{suffix}")
        left  = val in ('LEFT',  'BOTH')
        right = val in ('RIGHT', 'BOTH')
        # Write both flags via operator (each triggers its own propagation).
        bpy.ops.object.set_street_sector_type(
            edge_index=scene.mastro_street_active_edge,
            suffix=suffix, side='left',  value=left)
        bpy.ops.object.set_street_sector_type(
            edge_index=scene.mastro_street_active_edge,
            suffix=suffix, side='right', value=right)
    return update


_SECTOR_ENUM_ITEMS = [
    ('LEFT',  "Left",  "Fillet on the left side only",  'ALIGN_LEFT',   0),
    ('BOTH',  "Both",  "Fillet on both sides",          'ALIGN_CENTER', 1),
    ('RIGHT', "Right", "Fillet on the right side only", 'ALIGN_RIGHT',  2),
]

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

    ("mastro_street_active_edge", IntProperty(name="Active Edge Index", default=0)),

    # Four raw bool flags — source of truth, resynced from mesh by the handler.
    ("mastro_street_sector_A_left",  BoolProperty(name="A Left",  default=True, update=_make_sector_flag_update('A', 'left'))),
    ("mastro_street_sector_A_right", BoolProperty(name="A Right", default=True, update=_make_sector_flag_update('A', 'right'))),
    ("mastro_street_sector_B_left",  BoolProperty(name="B Left",  default=True, update=_make_sector_flag_update('B', 'left'))),
    ("mastro_street_sector_B_right", BoolProperty(name="B Right", default=True, update=_make_sector_flag_update('B', 'right'))),

    # Derived 3-button enums for the UI — resynced from the bool flags by the handler.
    ("mastro_street_sector_enum_A", EnumProperty(
        name="Junction A", items=_SECTOR_ENUM_ITEMS, default='BOTH',
        update=_make_sector_enum_update('A'),
    )),
    ("mastro_street_sector_enum_B", EnumProperty(
        name="Junction B", items=_SECTOR_ENUM_ITEMS, default='BOTH',
        update=_make_sector_enum_update('B'),
    )),
]
