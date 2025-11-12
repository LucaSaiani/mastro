import bpy
from bpy.props import (IntProperty, 
                       FloatProperty, 
                       EnumProperty,
                       BoolProperty, 
                       CollectionProperty,
                       PointerProperty
                       
)
import math

from ...Handlers.classes.showAttributes import update_show_attributes
from ...Utils.get_names_from_list import get_names_from_list
from ...Utils.update_attributes import *

from .class_properties import ( mastroAddonProperties,
                                constraintXYSettings,
                                name_with_id,
                                street_name_list,
                                floor_name_list,
                                wall_name_list,
                                typology_uses_name_list,
                                use_name_list,
                                typology_name_list,
                                building_name_list,
                                block_name_list,
                                obj_typology_uses_name_list
)
                                
                                

# from ... import mastro_wall
# from ... import mastro_massing
from ... import mastro_geometryNodes
# from ... import mastro_project_data
# from ... import mastro_menu
from ... import mastro_schedule
# from ... import mastro_street

# =============================================================================
# WindowManager Properties
# =============================================================================
window_manager_props = [
    # ------------------------------
    # Overlay Toggles
    # ------------------------------
    ("toggle_show_overlays", BoolProperty(
        default=False, 
        update=update_show_attributes
    )),
    ("toggle_show_data_edit_mode", BoolProperty(
        name="Edit Mode Overlays",
        default=True,
        description=(
            "Show selection overlay when the MaStro mass, block "
            "or street is in edit mode"
        )
    )),
    ("toggle_block_name", BoolProperty(name="Block Name", default=False)),
    ("toggle_building_name", BoolProperty(name="Building Name", default=False)),
    ("toggle_typology_name", BoolProperty(name="Typology Name", default=False)),
    ("toggle_block_typology_color", BoolProperty(name="Typology Color", default=False)),
    ("toggle_block_normal", BoolProperty(name="Inverted Normal", default=False)),
    ("toggle_wall_type", BoolProperty(name="Type", default=False)),
    ("toggle_wall_normal", BoolProperty(name="Inverted Normal", default=False)),
    ("toggle_floor_name", BoolProperty(name="Type", default=False)),
    ("toggle_storey_number", BoolProperty(name="Number of Storeys", default=False)),
    ("toggle_street_color", BoolProperty(name="Type", default=False)),

    # ------------------------------
    # Auto-update toggle
    # ------------------------------
    ("toggle_auto_update_mass_data", BoolProperty(name="Auto Update Mass Data", default=True)),
]

# =============================================================================
# Scene Properties
# =============================================================================
scene_props = [
    # ------------------------------
    # Mass / Storey Properties
    # ------------------------------
    ("attribute_mass_storeys", IntProperty(
        name="Number of Storeys",
        min=1,
        default=3,
        update=update_attributes_mastro_mesh_storeys
    )),
    ("attribute_mass_block_id", IntProperty(name="Block Id", default=0)),
    ("attribute_mass_building_id", IntProperty(name="Building Id", default=0)),
    ("attribute_mass_typology_id", IntProperty(name="Typology Id", default=0)),
    ("attribute_mass_extend_uses", IntProperty(name="Top Floors to Match", default=0, description="Updates the use of the selected top floors to match the one below")),

    # ------------------------------
    # Street Properties
    # ------------------------------
    ("attribute_street_id", IntProperty(name="Street Id", default=0)),
    ("attribute_street_width", FloatProperty(
        name="Street width", default=8, precision=3, subtype="DISTANCE"
    )),
    ("attribute_street_radius", FloatProperty(
        name="Street radius", default=18, precision=3, subtype="DISTANCE"
    )),

    # ------------------------------
    # Wall Properties
    # ------------------------------
    ("attribute_wall_id", IntProperty(
        name="Wall Id", default=0, update=update_attributes_mastro_wall_id
    )),
    ("attribute_wall_thickness", FloatProperty(
        name="Wall thickness", default=0.300, precision=3, subtype="DISTANCE"
    )),
    ("attribute_wall_offset", FloatProperty(
        name="Wall offset", default=0, precision=3, subtype="DISTANCE"
    )),
    ("attribute_wall_normal", BoolProperty(
        default=False, update=update_attributes_mastro_wall_normal
    )),

    # ------------------------------
    # Floor Properties
    # ------------------------------
    ("attribute_floor_id", IntProperty(
        name="Floor Id", default=0, update=update_attributes_mastro_floor_id
    )),

    # ------------------------------
    # Block / Building Properties
    # ------------------------------
    ("attribute_block_side_angle", FloatProperty(
        name="Building Side Angle",
        min=math.radians(-90),
        max=math.radians(90),
        default=0,
        precision=2,
        subtype='ANGLE',
        update=update_attributes_mastro_block_side_angle
    )),
    ("attribute_block_depth", FloatProperty(
        name="The depth of the building",
        min=0,
        default=18,
        precision=3,
        subtype="DISTANCE",
        update=update_attributes_mastro_block_depth
    )),
    # ("attribute_block_normal", BoolProperty(
    #     default=False, update=update_attributes_mastro_block_normal
    # )),

    # ------------------------------
    # Geometry Nodes / Object Selection
    # ------------------------------
    ("geometryMenuSwitch", EnumProperty(
        items=(("POINT", "Point", ""), ("EDGE", "Edge", ""), ("FACE", "Face", "")),
        default="EDGE",
        update=mastro_geometryNodes.updateGroup
    )),
    ("mastro_group_node_number_of_split", IntProperty(
        name="Number of split", default=1, min=1, update=mastro_geometryNodes.updateGroup
    )),
    ("previous_selection_object_name", bpy.props.StringProperty(
        name="Previously selected object name", default="",
        description="Store the name of the previous selected object"
    )),
    ("previous_selection_face_id", IntProperty(
        name="Previously selected face Id", default=-1,
        description="Store the id of the previous selected face"
    )),
    ("previous_selection_edge_id", IntProperty(
        name="Previously selected edge Id", default=-1,
        description="Store the id of the previous selected edge"
    )),
    ("previous_selection_vert_id", IntProperty(
        name="Previously selected vert Id", default=-1,
        description="Store the id of the previous selected vertex"
    )),
    ("previous_edge_number", IntProperty(
        name="Previously number of edges", default=-1,
        description="Store the number of edges of the previous selection"
    )),
    
    # ------------------------------
    # Mastro Extras
    # ------------------------------
    ("mastro_attribute_extra_vertex", FloatProperty(
        name="Custom vertex value", 
        default=0, 
        step=100, 
        update=update_extras_vertex,
    )),
    ("mastro_attribute_extra_edge", FloatProperty(
        name="Custom edge value", 
        default=0, 
        step=100, 
        update=update_extras_edge
    )),
    ("mastro_attribute_extra_face", FloatProperty(
        name="Custom face value", 
        default=0, 
        step=100, 
        update=update_extras_face
    )),

    # ------------------------------
    # Mastro Project Data (Collections & EnumProperties)
    # ------------------------------
    ("mastro_block_name_list", CollectionProperty(type=block_name_list)),
    ("mastro_block_name_current", CollectionProperty(type=name_with_id)),
    ("mastro_block_name_list_index", IntProperty(name="Block Name", default=0)),
    ("mastro_block_names", EnumProperty(
        name="Block names", description="Current block name",
        items=lambda self, context: get_names_from_list(context.scene, context, "mastro_block_name_list"),
        update=update_attributes_mastro_block_name_id
    )),

    ("mastro_building_name_list", CollectionProperty(type=building_name_list)),
    ("mastro_building_name_current", CollectionProperty(type=name_with_id)),
    ("mastro_building_name_list_index", IntProperty(name="Building Name", default=0)),
    ("mastro_building_names", EnumProperty(
        name="Building names", description="Current building name",
        items=lambda self, context: get_names_from_list(context.scene, context, "mastro_building_name_list"),
        update=update_attributes_mastro_building_name_id
    )),

    ("mastro_use_name_list", CollectionProperty(type=use_name_list)),

    ("mastro_typology_name_list", CollectionProperty(type=typology_name_list)),
    ("mastro_typology_name_current", CollectionProperty(type=name_with_id)),
    ("mastro_typology_name_list_index", IntProperty(name="Typology Name", default=0)),
    ("mastro_typology_names", EnumProperty(
        name="Typology List",
            items=lambda self, context: get_names_from_list(context.scene, context, "mastro_typology_name_list"),
        update=update_attributes_mastro_mesh_typology
    )),
    ("mastro_typology_uses_name_list", CollectionProperty(type=typology_uses_name_list)),
    ("mastro_typology_uses_name_list_index", IntProperty(name="Typology Use Name", default=0)),
    ("mastro_previous_selected_typology", IntProperty(name="Previous Typology Id", default=-1)),
    ("mastro_typology_uses_name", EnumProperty(
        name="Typology uses drop down menu",
        description="Typology use drop down list in the Typology Uses UI",
        items=lambda self, context: get_names_from_list(context.scene, context, "mastro_use_name_list"),
        update=update_typology_uses_name_label
    )),
    ("mastro_obj_typology_uses_name_list", CollectionProperty(type=obj_typology_uses_name_list)),
    ("mastro_obj_typology_uses_name_list_index", IntProperty(
        name="Typology Use Name of the selected object", default=0
    )),

    ("mastro_street_name_list", CollectionProperty(type=street_name_list)),
    ("mastro_street_name_current", CollectionProperty(type=name_with_id)),
    ("mastro_street_name_list_index", IntProperty(name="Street Name", default=0)),
    ("mastro_street_names", EnumProperty(
        name="Street List", description="",
        items=lambda self, context: get_names_from_list(context.scene, context, "mastro_street_name_list"),
        update=update_attributes_street
    )),

    ("mastro_wall_name_list", CollectionProperty(type=wall_name_list)),
    ("mastro_wall_name_current", CollectionProperty(type=name_with_id)),
    ("mastro_wall_name_list_index", IntProperty(name="Wall Name", default=0)),
    ("mastro_wall_names", EnumProperty(
        name="Wall List", description="",
        items=lambda self, context: get_names_from_list(context.scene, context, "mastro_wall_name_list"),
        update=update_attributes_wall
    )),

    ("mastro_floor_name_list", CollectionProperty(type=floor_name_list)),
    ("mastro_floor_name_current", CollectionProperty(type=name_with_id)),
    ("mastro_floor_name_list_index", IntProperty(name="Floor Name", default=0)),
    ("mastro_floor_names", EnumProperty(
        name="Floor List", description="", 
        items=lambda self, context: get_names_from_list(context.scene, context, "mastro_floor_name_list"),
    )),
]

# =============================================================================
# Object / Node Pointer Properties
# =============================================================================
object_props = [
    ("mastro_props", PointerProperty(type=mastroAddonProperties)),
    ("sticky_note_props", PointerProperty(type=mastro_geometryNodes.StickyNoteProperties)),
]

scene_pointer_props = [
    ("constraint_xy_setting", PointerProperty(type=constraintXYSettings)),
    ("mastroKeyDictionary", CollectionProperty(type=mastro_schedule.MaStro_string_item)),
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


def unregister():
    for name, _ in window_manager_props:
        delattr(bpy.types.WindowManager, name)
    for name, _ in scene_props:
        delattr(bpy.types.Scene, name)
    for name, _ in object_props:
        delattr(bpy.types.Object, name)
    for name, _ in scene_pointer_props:
        delattr(bpy.types.Scene, name)
