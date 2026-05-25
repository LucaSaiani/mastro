from .MESH_OT_Move_Active_Vertex import MESH_OT_Move_Active_Vertex

from .OBJECT_OT_Add_Mastro_Block import OBJECT_OT_Add_Mastro_Block
from .OBJECT_OT_Add_Mastro_Dimension import OBJECT_OT_Add_Mastro_Dimension
from .OBJECT_OT_Add_Mastro_Mass import OBJECT_OT_Add_Mastro_Mass
from .OBJECT_OT_Add_Mastro_Street import OBJECT_OT_Add_Mastro_Street
from .OBJECT_OT_Convert_to_Mastro import OBJECT_OT_Convert_to_Mastro_Mass, OBJECT_OT_Convert_to_Mastro_Street
from .OBJECT_OT_Set_Street_Id import OBJECT_OT_Set_Street_Id
from .OBJECT_OT_Update_Mastro_Mesh_Attributes import OBJECT_OT_Update_Mastro_Mesh_Attributes
from .OBJECT_OT_Update_Street_Attributes import OBJECT_OT_Mastro_Update_Street_Attributes
from .OBJECT_OT_Update_Mastro_Custom_Properties import OBJECT_OT_Update_Mastro_Custom_Properties, OBJECT_OT_Remove_Mastro_Custom_Property, OBJECT_OT_Mastro_Activate_String_Property
from .OBJECT_OT_Export_Data import OBJECT_OT_Mastro_Export_CSV, OBJECT_OT_Mastro_Print_Data

from .TRANSFORM_OT_Set_Orientation import TRANSFORM_OT_Mastro_Set_Orientation
from .TRANSFORM_OT_XY_Constraint import TRANSFORM_OT_Mastro_Rotate_XY_Constraint, TRANSFORM_OT_Mastro_Translate_XY_Constraint

from .LAYER_MANAGER_OT_Set_Active import LAYER_MANAGER_OT_SetActive
from .LAYER_MANAGER_OT_Add_Layer import LAYER_MANAGER_OT_AddLayer
from .LAYER_MANAGER_OT_Add_Layer_Popup import LAYER_MANAGER_OT_AddLayer_Popup

from .OBJECT_OT_run_all import OBJECT_OT_RunAll, OBJECT_OT_CancelAll
from .OBJECT_OT_run_batch import OBJECT_OT_RunBatch
from .OBJECT_OT_bidimensional_Lines_Projection import OBJECT_OT_bidimensional_Lines_Projection
from .OBJECT_OT_clear_shadow_cache import OBJECT_OT_ClearShadowCache
from .OBJECT_OT_camera_sets import (
    MASTRO_OT_CameraSetAdd,
    MASTRO_OT_CameraSetRemove,
    MASTRO_OT_CameraSetDuplicate,
    MASTRO_OT_CameraSetMoveUp,
    MASTRO_OT_CameraSetMoveDown,
    MASTRO_OT_CameraSetToggleCamera,
)
from ..Utils.projection.shadow_render import MASTRO_OT_RenderShadowModal
from .OBJECT_OT_import_mastro_objects import (MASTRO_PG_ImportObject,
                                               MASTRO_PG_ImportCollection,
                                               MASTRO_UL_ImportObjects,
                                               MASTRO_UL_ImportCollections,
                                               MASTRO_MT_ImportSpecials,
                                               OBJECT_OT_Import_Mastro_Toggle_All,
                                               OBJECT_OT_Import_Mastro_Select,
                                               OBJECT_OT_Import_Mastro_Objects)


classes = (
    MESH_OT_Move_Active_Vertex,

    OBJECT_OT_Add_Mastro_Block,
    OBJECT_OT_Add_Mastro_Dimension,
    OBJECT_OT_Add_Mastro_Mass,
    OBJECT_OT_Add_Mastro_Street,
    OBJECT_OT_Convert_to_Mastro_Mass,
    OBJECT_OT_Convert_to_Mastro_Street,
    OBJECT_OT_Set_Street_Id,
    OBJECT_OT_Update_Mastro_Mesh_Attributes,
    OBJECT_OT_Mastro_Update_Street_Attributes,
    OBJECT_OT_Update_Mastro_Custom_Properties,
    OBJECT_OT_Mastro_Export_CSV,
    OBJECT_OT_Mastro_Print_Data,

    TRANSFORM_OT_Mastro_Set_Orientation,
    TRANSFORM_OT_Mastro_Translate_XY_Constraint,
    TRANSFORM_OT_Mastro_Rotate_XY_Constraint,

    LAYER_MANAGER_OT_SetActive,
    LAYER_MANAGER_OT_AddLayer,
    LAYER_MANAGER_OT_AddLayer_Popup,

    OBJECT_OT_RunAll,
    OBJECT_OT_CancelAll,
    OBJECT_OT_RunBatch,
    OBJECT_OT_bidimensional_Lines_Projection,
    OBJECT_OT_ClearShadowCache,
    MASTRO_OT_CameraSetAdd,
    MASTRO_OT_CameraSetRemove,
    MASTRO_OT_CameraSetDuplicate,
    MASTRO_OT_CameraSetMoveUp,
    MASTRO_OT_CameraSetMoveDown,
    MASTRO_OT_CameraSetToggleCamera,
    MASTRO_OT_RenderShadowModal,
    OBJECT_OT_Remove_Mastro_Custom_Property,
    OBJECT_OT_Mastro_Activate_String_Property,

    MASTRO_PG_ImportObject,
    MASTRO_PG_ImportCollection,
    MASTRO_UL_ImportObjects,
    MASTRO_UL_ImportCollections,
    MASTRO_MT_ImportSpecials,
    OBJECT_OT_Import_Mastro_Toggle_All,
    OBJECT_OT_Import_Mastro_Select,
    OBJECT_OT_Import_Mastro_Objects,
    )