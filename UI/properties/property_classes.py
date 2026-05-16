import bpy
from bpy.types import PropertyGroup
from bpy.props import (IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       BoolProperty,
                       StringProperty,
                       CollectionProperty,
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