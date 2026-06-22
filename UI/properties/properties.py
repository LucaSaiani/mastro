import bpy
from bpy.props import (IntProperty,
                       BoolProperty,
                       PointerProperty

)

from ...Handlers.classes.showAttributes import update_show_attributes
from ...Utils.update_attributes import *

from .properties_layer import scene_pointer_props_layer
from .properties_street import scene_props_street
from .properties_levels import scene_props_levels
from .properties_pdf import scene_pointer_props_pdf
from .properties_arch import scene_props_arch, object_props_arch
from .properties_custom_properties import scene_props_custom_properties
from .properties_projector import camera_props_projector, scene_pointer_props_projector
from .properties_constraints import scene_pointer_props_constraints
from .properties_gn import node_frame_props_gn
from .properties_extras import scene_props_extras
from .properties_cad import scene_props_cad, camera_props_cad, window_manager_props_cad
from .properties_gis import scene_props_gis
from .properties_print import scene_pointer_props_print
from .property_classes_pdf_frame import mastro_CL_frame_settings
from .property_classes_album import mastro_CL_album_settings

                                

# from ... import mastro_wall
# from ... import mastro_massing
# from ... import mastro_geometryNodes
# from ... import mastro_project_data
# from ... import mastro_menu
# from ... import mastro_schedule
# from ... import mastro_street
    
# =============================================================================
# WindowManager Properties
# =============================================================================
window_manager_props = [
    # ------------------------------
    # Overlay Toggles
    # ------------------------------
    ("mastro_toggle_show_overlays", BoolProperty(
        default=False, 
        update=update_show_attributes
    )),
    ("mastro_toggle_show_data_edit_mode", BoolProperty(
        name="Edit Mode Overlays",
        default=True,
        description=(
            "Show selection overlay when the MaStro mass, block "
            "or street is in edit mode"
        )
    )),
    ("mastro_toggle_block_name", BoolProperty(name="Block Name", default=False)),
    ("mastro_toggle_building_name", BoolProperty(name="Building Name", default=False)),
    ("mastro_toggle_typology_name", BoolProperty(name="Typology Name", default=False)),
    ("mastro_toggle_block_typology_color", BoolProperty(name="Typology Color", default=False)),
    ("mastro_toggle_block_normal", BoolProperty(name="Inverted Normal", default=False)),
    ("mastro_toggle_wall_type", BoolProperty(name="Type", default=False)),
    ("mastro_toggle_wall_normal", BoolProperty(name="Inverted Normal", default=False)),
    ("mastro_toggle_floor_name", BoolProperty(name="Type", default=False)),
    ("mastro_toggle_storey_number", BoolProperty(name="Number of Storeys", default=False)),
    ("mastro_toggle_street_color", BoolProperty(name="Type", default=False)),

    # ------------------------------
    # Auto-update toggle
    # ------------------------------
    ("mastro_toggle_auto_update_mass_data", BoolProperty(
        name="Auto Update Mass Data",
        default=True,
        update=update_all_mastro_meshes_useList,
    )),

    *window_manager_props_cad,
]

# =============================================================================
# Scene Properties
# =============================================================================
scene_props = [
    *scene_props_extras,

    *scene_props_street,

    *scene_props_levels,

    # ------------------------------
    # Geometry Nodes / Object Selection
    # ------------------------------
    # ("mastro_geometry_menu_switch", EnumProperty(
    #     items=(("POINT", "Point", ""), ("EDGE", "Edge", ""), ("FACE", "Face", "")),
    #     default="EDGE",
    #     update=mastro_geometryNodes.updateGroup
    # )),
    # ("mastro_group_node_number_of_split", IntProperty(
    #     name="Number of split", default=1, min=1, update=mastro_geometryNodes.updateGroup
    # )),
    # ("mastro_previous_selection_object_name", bpy.props.StringProperty(
    #     name="Previously selected object name", default="",
    #     description="Store the name of the previous selected object"
    # )),
    # ("mastro_previous_selection_face_id", IntProperty(
    #     name="Previously selected face Id", default=-1,
    #     description="Store the id of the previous selected face"
    # )),
    # ("mastro_previous_selection_edge_id", IntProperty(
    #     name="Previously selected edge Id", default=-1,
    #     description="Store the id of the previous selected edge"
    # )),
    ("mastro_previous_selection_vert_id", IntProperty(
        name="Previously selected vert Id", default=-1,
        description="Store the id of the previous selected vertex"
    )),
    ("mastro_previous_edge_number", IntProperty(
        name="Previously number of edges", default=-1,
        description="Store the number of edges of the previous selection"
    )),
    
    *scene_props_arch,

    *scene_props_custom_properties,

    *scene_props_cad,

    *scene_props_gis,
]

# =============================================================================
# Object / Node Pointer Properties
# =============================================================================
object_props = [
    *object_props_arch,
    ("mastro_frame_settings", PointerProperty(type=mastro_CL_frame_settings)),
    ("mastro_album_settings", PointerProperty(type=mastro_CL_album_settings)),
]

scene_pointer_props = [
    *scene_pointer_props_constraints,
    *scene_pointer_props_layer,
    # ("mastro_key_dictionary", CollectionProperty(type=mastro_schedule.MaStro_string_item)),
    *scene_pointer_props_projector,
    *scene_pointer_props_pdf,
    *scene_pointer_props_print,
]

camera_props = [
    *camera_props_projector,
    *camera_props_cad,
]
node_frame_props = [
    *node_frame_props_gn,
]

# =============================================================================
# Register / Unregister
# =============================================================================
def register():
    for name, prop in window_manager_props:
        setattr(bpy.types.WindowManager, name, prop)
    for name, prop in scene_props:
        setattr(bpy.types.Scene, name, prop)
    for name, prop in object_props:
        setattr(bpy.types.Object, name, prop)
    for name, prop in scene_pointer_props:
        setattr(bpy.types.Scene, name, prop)
    for name, prop in node_frame_props:
        setattr(bpy.types.NodeFrame, name, prop)
    for name, prop in camera_props:
        setattr(bpy.types.Camera, name, prop)


def unregister():
    for name, _ in window_manager_props:
        delattr(bpy.types.WindowManager, name)
    for name, _ in scene_props:
        delattr(bpy.types.Scene, name)
    for name, _ in object_props:
        delattr(bpy.types.Object, name)
    for name, _ in scene_pointer_props:
        delattr(bpy.types.Scene, name)
    for name, _ in node_frame_props:
        delattr(bpy.types.NodeFrame, name)
    for name, _ in camera_props:
        delattr(bpy.types.Camera, name)
        
