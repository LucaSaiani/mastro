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
from ...Utils.getter_setter import *

from .property_classes import ( mastro_CL_addon_properties,
                                mastro_CL_constraint_XY_settings,
                                # mastro_CL_name_with_id,
                                mastro_CL_street_name_list,
                                mastro_CL_floor_name_list,
                                mastro_CL_wall_name_list,
                                mastro_CL_typology_uses_name_list,
                                mastro_CL_use_name_list,
                                mastro_CL_typology_name_list,
                                mastro_CL_building_name_list,
                                mastro_CL_block_name_list,
                                mastro_CL_obj_typology_uses_name_list,
                                mastro_CL_Sticky_Note
                                
)

                                

# from ... import mastro_wall
# from ... import mastro_massing
# from ... import mastro_geometryNodes
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
    ("mastro_toggle_auto_update_mass_data", BoolProperty(name="Auto Update Mass Data", default=True)),
]

# =============================================================================
# Scene Properties
# =============================================================================
scene_props = [
    # ------------------------------
    # Block and building IDs
    # ------------------------------
    # ("mastro_attribute_mass_block_id", IntProperty(name="Block Id", default=0)),
    # ("mastro_attribute_mass_building_id", IntProperty(name="Building Id", default=0)),
    ("mastro_block_name", EnumProperty(
        name="Block name", description="Current block name",
        items=lambda self, context: get_names_from_list(context.scene, context, "mastro_block_name_list"),
        # update=update_attributes_mastro_block_name_id
        set = set_attribute_mastro_object_block,
        get = lambda self: get_attribute_mastro_object(self, "block")
    )),
    ("mastro_building_name", EnumProperty(
        name="Building name", description="Current building name",
        items=lambda self, context: get_names_from_list(context.scene, context, "mastro_building_name_list"),
        # update=update_attributes_mastro_building_name_id
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
        # update=update_attributes_mastro_mesh_storeys
        set = set_attribute_mastro_mesh_storeys,
        get = lambda self: get_attribute_mastro_mesh(self, "mastro_number_of_storeys")
    )),
    # the dropdown menu in the mass VIEW3D panel
    ("mastro_typology_names", EnumProperty(
        name="Typology List",
        items=lambda self, context: get_names_from_list(context.scene, context, "mastro_typology_name_list"),
        # update=update_attributes_mastro_mesh_typology
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
        # update=update_attributes_mastro_block_side_angle
        set = set_attribute_mastro_block_side_angle,
        get = lambda self: get_attribute_mastro_mesh(self, "mastro_side_angle")
        
    )),
    ("mastro_attribute_block_depth", FloatProperty(
        name="The depth of the building",
        min=0,
        default=18,
        precision=3,
        subtype="DISTANCE",
        # update=update_attributes_mastro_block_depth
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
        # update=update_attributes_wall
        set = set_attribute_mastro_wall_id,
        get = lambda self: get_attribute_mastro_mesh(self, "mastro_wall_id")
    )),
    ("mastro_attribute_wall_normal", BoolProperty(
        default=False, 
        # update=update_attributes_mastro_wall_normal
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
    # Mastro Extras
    # ------------------------------
    ("mastro_attribute_custom_vertex", FloatProperty(
        name="Custom vertex value", 
        default=0, 
        step=100, 
        set = set_attribute_custom_vert,
        get = lambda self: get_attribute_mastro_mesh(self, "mastro_custom_vert")
    )),
    ("mastro_attribute_custom_edge", FloatProperty(
        name="Custom edge value", 
        default=0, 
        step=100, 
        set = set_attribute_custom_edge,
        get = lambda self: get_attribute_mastro_mesh(self, "mastro_custom_edge")
    )),
    ("mastro_attribute_custom_face", FloatProperty(
        name="Custom face value", 
        default=0, 
        step=100, 
        set = set_attribute_custom_face,
        get = lambda self: get_attribute_mastro_mesh(self, "mastro_custom_face")
    )),
    
    # ------------------------------
    # Street Properties
    # ------------------------------
    ("mastro_attribute_street_id", IntProperty(name="Street Id", default=0)),
    ("mastro_attribute_street_width", FloatProperty(
        name="Street width", default=8, precision=3, subtype="DISTANCE"
    )),
    ("mastro_attribute_street_radius", FloatProperty(
        name="Street radius", default=18, precision=3, subtype="DISTANCE"
    )),


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
    # ("mastro_previous_selection_vert_id", IntProperty(
    #     name="Previously selected vert Id", default=-1,
    #     description="Store the id of the previous selected vertex"
    # )),
    # ("mastro_previous_edge_number", IntProperty(
    #     name="Previously number of edges", default=-1,
    #     description="Store the number of edges of the previous selection"
    # )),
    
    # ------------------------------
    # Mastro Project Data (Collections & EnumProperties)
    # ------------------------------
    ("mastro_block_name_list", CollectionProperty(type=mastro_CL_block_name_list)),
    # ("mastro_block_name_current", CollectionProperty(type=mastro_CL_name_with_id)),
    ("mastro_block_name_list_index", IntProperty(name="Block Name", default=0)),
    

    ("mastro_building_name_list", CollectionProperty(type=mastro_CL_building_name_list)),
    # ("mastro_building_name_current", CollectionProperty(type=mastro_CL_name_with_id)),
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
    # ("mastro_previous_selected_typology", IntProperty(name="Previous Typology Id", default=-1)),
    ("mastro_typology_uses_name", EnumProperty(
        name="Uses",
        description="Select uses to add to the current typology",
        items=lambda self, context: get_names_from_list(context.scene, context, "mastro_use_name_list"),
        update=update_typology_uses_name_label
    )),
    ("mastro_obj_typology_uses_name_list", CollectionProperty(type=mastro_CL_obj_typology_uses_name_list)),
    ("mastro_obj_typology_uses_name_list_index", IntProperty(
        name="Typology Use Name of the selected object", default=0
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
 
    
    ("mastro_street_name_list", CollectionProperty(type=mastro_CL_street_name_list)),
    ("mastro_street_name_list_index", IntProperty(name="Street Name", default=0)),
    ("mastro_street_names", EnumProperty(
        name="Street List", description="",
        items=lambda self, context: get_names_from_list(context.scene, context, "mastro_street_name_list"),
        update=update_attributes_street
    )),
]

# =============================================================================
# Object / Node Pointer Properties
# =============================================================================
object_props = [
    ("mastro_props", PointerProperty(type=mastro_CL_addon_properties)),
    
]

scene_pointer_props = [
    ("mastro_constraint_xy_setting", PointerProperty(type=mastro_CL_constraint_XY_settings)),
    # ("mastro_key_dictionary", CollectionProperty(type=mastro_schedule.MaStro_string_item)),
]
node_frame_props = [
    ("mastro_sticky_note_props", PointerProperty(type=mastro_CL_Sticky_Note)),
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
        
