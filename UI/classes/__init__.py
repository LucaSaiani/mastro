
import bpy 
from bpy.utils import register_class, unregister_class

from .PROPERTIES_UL_List import PROPERTIES_UL_List, PROPERTIES_UL_Typology_Uses
from .PROPERTIES_OT_New_Item import PROPERTIES_OT_New_Item, PROPERTIES_OT_Typology_Uses_List_New_Item, PROPERTIES_OT_Use_List_New_Item
from .PROPERTIES_OT_Move_Item import PROPERTIES_OT_Move_Item, PROPERTIES_OT_Typology_Uses_List_Move_Item
from .PROPERTIES_OT_Delete_Item import PROPERTIES_OT_Typology_Uses_List_Delete_Item
from .PROPERTIES_OT_Duplicate_Item import PROPERTIES_OT_Typology_List_Duplicate_Item
from .PROPERTIES_OT_Update_List import PROPERTIES_OT_Update_Use_List
from .VIEW3D_UL_Typology_Uses import VIEW3D_UL_Typology_Uses
from ..properties.class_properties import obj_typology_uses_name_list
from .PREFERENCES_Mastro_Preferences import PREFERENCES_Mastro_Preferences
from .PROPERTIES_PT_Mastro_Project_Data import PROPERTIES_PT_Mastro_Project_Data
from .PROPERTIES_PT_Mastro_Overlays import PROPERTIES_PT_Mastro_Overlay
from .PROPERTIES_PT_Mastro_Mass import PROPERTIES_PT_Mastro_Mass
from .PROPERTIES_PT_Mastro_Block import PROPERTIES_PT_Mastro_Block
from .PROPERTIES_PT_Mastro_Building import PROPERTIES_PT_Mastro_Building
from .PROPERTIES_PT_Mastro_Typology import PROPERTIES_PT_Mastro_Typology
from .PROPERTIES_PT_Mastro_Architecture import PROPERTIES_PT_Mastro_Architecture
from .PROPERTIES_PT_Mastro_Wall import PROPERTIES_PT_Mastro_Wall
from .PROPERTIES_PT_Mastro_Floor import PROPERTIES_PT_Mastro_Floor
from .PROPERTIES_PT_Mastro_Street import PROPERTIES_PT_Mastro_Street
from .VIEW3D_PT_Mastro_Panel import VIEW3D_PT_Mastro_Panel
from .VIEW3D_PT_Mastro_Architecture import VIEW3D_PT_Mastro_Architecture
from .VIEW3D_PT_Mastro_Block import VIEW3D_PT_Mastro_Block  
from .VIEW3D_PT_Mastro_Extras import VIEW3D_PT_Mastro_Extras
from .VIEW3D_PT_Mastro_Mass import VIEW3D_PT_Mastro_Mass
from .VIEW3D_PT_Mastro_Street import VIEW3D_PT_Mastro_Street
from .VIEW3D_PT_Set_Orientation import VIEW3D_PT_set_orientation


classes = (
    PROPERTIES_OT_New_Item, 
    PROPERTIES_OT_Typology_Uses_List_New_Item,
    PROPERTIES_OT_Use_List_New_Item,
    PROPERTIES_OT_Move_Item, 
    PROPERTIES_OT_Typology_Uses_List_Move_Item,
    PROPERTIES_OT_Typology_Uses_List_Delete_Item,
    PROPERTIES_UL_List,
    PROPERTIES_UL_Typology_Uses,
    PROPERTIES_OT_Typology_List_Duplicate_Item,
    PROPERTIES_OT_Update_Use_List,
    VIEW3D_UL_Typology_Uses,
    obj_typology_uses_name_list,
    PREFERENCES_Mastro_Preferences,
    PROPERTIES_PT_Mastro_Project_Data,
    PROPERTIES_PT_Mastro_Overlay,
    PROPERTIES_PT_Mastro_Mass,
    PROPERTIES_PT_Mastro_Block,
    PROPERTIES_PT_Mastro_Building,
    PROPERTIES_PT_Mastro_Typology,
    PROPERTIES_PT_Mastro_Architecture,
    PROPERTIES_PT_Mastro_Wall,
    PROPERTIES_PT_Mastro_Floor,
    PROPERTIES_PT_Mastro_Street,
    VIEW3D_PT_Mastro_Panel,
    VIEW3D_PT_Mastro_Architecture,
    VIEW3D_PT_Mastro_Block,
    VIEW3D_PT_Mastro_Extras,
    VIEW3D_PT_Mastro_Mass,
    VIEW3D_PT_Mastro_Street,
    VIEW3D_PT_set_orientation,
    )

MASTRO_LISTS = [
    # name,               icon,             color_attr,           filter_name
    ("block",    "MOD_BOOLEAN",     None,                  "block"),
    ("building", "HOME",            None,                  "building"),
    ("typology", "ASSET_MANAGER",   "typologyEdgeColor",   "typology"),
    ("wall",     "NODE_TEXTURE",    "wallEdgeColor",       "wall type"),
    ("floor",    "VIEW_PERSPECTIVE", None,                 None),
    ("street",   "NODE_TEXTURE",    "streetEdgeColor",     "street type"),
]

# ============================================================
#  DYNAMIC CLASS GENERATION
# ============================================================

_dynamic_classes = []
def dynamic_list_classes():
    dynamicClasses = []
    """Dynamically create and register UIList, NewItem, MoveItem for each type."""
    for name, icon, color_attr, filter_name in MASTRO_LISTS:
        list_name = f"mastro_{name}_name_list"
        index_name = f"mastro_{name}_name_list_index"

        # --- UIList ---
        ui_class = type(
            f"PROPERTIES_UL_{name.capitalize()}",
            (PROPERTIES_UL_List,),
            {
                "bl_idname": f"PROPERTIES_UL_{name.capitalize()}",
                "list_name": list_name,
                "icon": icon,
            }
        )
        dynamicClasses.append(ui_class)
        # bpy.utils.register_class(ui_class)

        # --- New Item Operator ---
        op_new = type(
            f"{name.upper()}_LIST_OT_NewItem",
            (PROPERTIES_OT_New_Item,),
            {
                "bl_idname": f"{list_name}.new_item",
                "bl_label": f"Add new {name}",
                "list_name": list_name,
                "color_attr": color_attr,
                "filter_name": filter_name,
            }
        )
        dynamicClasses.append(op_new)
        # bpy.utils.register_class(op_new)

        # --- Move Item Operator ---
        op_move = type(
            f"{name.upper()}_LIST_OT_MoveItem",
            (PROPERTIES_OT_Move_Item,),
            {
                "bl_idname": f"{list_name}.move_item",
                "bl_label": f"Move {name} in list",
                "list_name": list_name,
                "index_name": index_name,
            }
        )
        dynamicClasses.append(op_move)
        # bpy.utils.register_class(op_move)
    return(dynamicClasses)
        
def register():
    global _dynamic_classes
    _dynamic_classes = dynamic_list_classes()

    for cls in _dynamic_classes:
        register_class(cls)

def unregister():
    global _dynamic_classes
    if "_dynamic_classes" in globals() and _dynamic_classes:
        for cls in reversed(_dynamic_classes):
            unregister_class(cls)