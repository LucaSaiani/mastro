import math
from bpy.props import (IntProperty,
                       FloatProperty,
                       BoolProperty,
                       EnumProperty,
                       CollectionProperty,
                       PointerProperty,
)

from ...Utils.get_names_from_list import get_names_from_list
from ...Utils.update_attributes import *
from ...Utils.getter_setter import *
from .property_classes_arch import (mastro_CL_addon_properties,
                                    mastro_CL_floor_name_list,
                                    mastro_CL_wall_name_list,
                                    mastro_CL_typology_uses_name_list,
                                    mastro_CL_use_name_list,
                                    mastro_CL_typology_name_list,
                                    mastro_CL_building_name_list,
                                    mastro_CL_block_name_list,
                                    mastro_CL_obj_typology_uses_name_list,
)

# =============================================================================
# Scene Properties - Architecture (masses, blocks, typologies, walls, floors)
# =============================================================================
scene_props_arch = [
    # ------------------------------
    # Block and building names
    # ------------------------------
    ("mastro_block_name", EnumProperty(
        name="Block name", description="Current block name",
        items=lambda self, context: get_names_from_list(context.scene, context, "mastro_block_name_list"),
        set = set_attribute_mastro_object_block,
        get = lambda self: get_attribute_mastro_object(self, "block")
    )),
    ("mastro_building_name", EnumProperty(
        name="Building name", description="Current building name",
        items=lambda self, context: get_names_from_list(context.scene, context, "mastro_building_name_list"),
        set = set_attribute_mastro_object_building,
        get = lambda self: get_attribute_mastro_object(self, "building")
    )),

    # ------------------------------
    # Mass / Storey Properties
    # ------------------------------
    ("mastro_attribute_mass_storeys", IntProperty(
        name="Number of Storeys",
        min=1,
        default=3,
        set = set_attribute_mastro_mesh_storeys,
        get = lambda self: get_attribute_mastro_mesh(self, "mastro_number_of_storeys")
    )),
    # the dropdown menu in the mass VIEW3D panel
    ("mastro_typology_names", EnumProperty(
        name="Typology List",
        items=lambda self, context: get_names_from_list(context.scene, context, "mastro_typology_name_list"),
        set = set_attribute_mastro_mesh_uses,
        get = lambda self: get_attribute_mastro_mesh(self, "mastro_typology_id")
    )),

    ("mastro_attribute_mass_typology_id", IntProperty(name="Typology Id", default=0)),
    ("mastro_attribute_mass_overlay_uses", IntProperty(name="Top Floors to Match",
                                                      min=0,
                                                      default=0,
                                                      description="Updates the use of the selected top floors to match the one below",
                                                      set = set_attribute_mastro_overlay_uses,
                                                      get = lambda self: get_attribute_mastro_mesh(self, "mastro_overlay_top" )
    )),
    ("mastro_attribute_mass_undercroft", IntProperty(name="N° of Undercroft Floors",
                                                     min=0,
                                                     default=0,
                                                     description="The number of floors to count from the ground floor level and designate as undercroft",
                                                     set = set_attribute_mastro_undercroft,
                                                     get = lambda self: get_attribute_mastro_mesh(self, "mastro_undercroft")
    )),

    # ------------------------------
    # Block / Building Properties
    # ------------------------------
    ("mastro_attribute_block_side_angle", FloatProperty(
        name="Building Side Angle",
        min=math.radians(-90),
        max=math.radians(90),
        default=0,
        precision=2,
        subtype='ANGLE',
        set = set_attribute_mastro_block_side_angle,
        get = lambda self: get_attribute_mastro_mesh(self, "mastro_side_angle")

    )),
    ("mastro_attribute_block_depth", FloatProperty(
        name="Building Depth",
        min=0,
        default=18,
        precision=3,
        subtype="DISTANCE",
        set = set_attribute_mastro_block_depth,
        get = lambda self: get_attribute_mastro_mesh(self, "mastro_block_depth")
    )),

    # ------------------------------
    # Wall Properties
    # ------------------------------
    # the dropdown menu in the architecture VIEW3D panel
    ("mastro_wall_names", EnumProperty(
        name="Wall List",
        items=lambda self, context: get_names_from_list(context.scene, context, "mastro_wall_name_list"),
        set = set_attribute_mastro_wall_id,
        get = lambda self: get_attribute_mastro_mesh(self, "mastro_wall_id")
    )),
    ("mastro_attribute_wall_normal", BoolProperty(
        default=False,
        set = set_attribute_mastro_wall_normal,
        get = lambda self: get_attribute_mastro_mesh(self, "mastro_inverted_normal")

    )),

    # ------------------------------
    # Floor Properties
    # ------------------------------
    ("mastro_floor_names", EnumProperty(
        name="Floor List",
        items=lambda self, context: get_names_from_list(context.scene, context, "mastro_floor_name_list"),
        set = set_attribute_mastro_floor_id,
        get = lambda self: get_attribute_mastro_mesh(self, "mastro_floor_id")
    )),

    # ------------------------------
    # Mastro Project Data (Collections & EnumProperties)
    # ------------------------------
    ("mastro_block_name_list", CollectionProperty(type=mastro_CL_block_name_list)),
    ("mastro_block_name_list_index", IntProperty(name="Block Name", default=0)),

    ("mastro_building_name_list", CollectionProperty(type=mastro_CL_building_name_list)),
    ("mastro_building_name_list_index", IntProperty(name="Building Name", default=0)),

    ("mastro_use_name_list", CollectionProperty(type=mastro_CL_use_name_list)),

    ("mastro_typology_name_list", CollectionProperty(type=mastro_CL_typology_name_list)),
    ("mastro_typology_name_list_index", IntProperty(name="Typology Name",
                                                    default=0,
                                                    update=update_uses_of_typology)),

    ("mastro_typology_uses_name_list", CollectionProperty(type=mastro_CL_typology_uses_name_list)),
    ("mastro_typology_uses_name_list_index", IntProperty(
        name="Typology Use Name",
        default=0)),
    ("mastro_typology_uses_name", EnumProperty(
        name="Uses",
        description="Select uses to add to the current typology",
        items=lambda self, context: get_names_from_list(context.scene, context, "mastro_use_name_list"),
        update=update_typology_uses_name_label
    )),
    ("mastro_obj_typology_uses_name_list", CollectionProperty(type=mastro_CL_obj_typology_uses_name_list)),
    ("mastro_obj_typology_uses_name_list_index", IntProperty(
        name="Selected Object Typology Uses", default=0
    )),

    ("mastro_wall_name_list", CollectionProperty(type=mastro_CL_wall_name_list)),
    ("mastro_wall_name_list_index", IntProperty(name="Wall Name", default=0)),
    ("mastro_attribute_wall_thickness", FloatProperty(
        name="Wall thickness", default=0.300, precision=3, subtype="DISTANCE"
    )),
    ("mastro_attribute_wall_offset", FloatProperty(
        name="Wall offset", default=0, precision=3, subtype="DISTANCE"
    )),

    ("mastro_floor_name_list", CollectionProperty(type=mastro_CL_floor_name_list)),
    ("mastro_floor_name_list_index", IntProperty(name="Floor Name", default=0)),
]

# =============================================================================
# Object Pointer Properties - Architecture
# =============================================================================
object_props_arch = [
    ("mastro_props", PointerProperty(type=mastro_CL_addon_properties)),
]
