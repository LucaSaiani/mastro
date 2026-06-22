from .mastro_2D.MESH_OT_Move_Active_Vertex import MESH_OT_Move_Active_Vertex

from .mastro_arch.OBJECT_OT_Add_Mastro_Block import OBJECT_OT_Add_Mastro_Block
from .mastro_2D.OBJECT_OT_Add_Mastro_Dimension import OBJECT_OT_Add_Mastro_Dimension
from .mastro_arch.OBJECT_OT_Add_Mastro_Mass import OBJECT_OT_Add_Mastro_Mass
from .mastro_street.OBJECT_OT_Add_Mastro_Street import OBJECT_OT_Add_Mastro_Street
from .mastro_pdf.OBJECT_OT_Add_Mastro_Frame import OBJECT_OT_Add_Mastro_Frame
from .mastro_album.OBJECT_OT_Add_Mastro_Album import OBJECT_OT_Add_Mastro_Album
from .mastro_album.OBJECT_OT_Parent_to_Mastro_Album import OBJECT_OT_Parent_to_Mastro_Album
from .mastro_album.OBJECT_OT_Unparent_from_Mastro_Album import OBJECT_OT_Unparent_from_Mastro_Album
from .mastro_album.OBJECT_OT_Mastro_Album_Remove_Child import OBJECT_OT_Mastro_Album_Remove_Child
from .mastro_arch.OBJECT_OT_Convert_to_Mastro_Mass import OBJECT_OT_Convert_to_Mastro_Mass
from .mastro_street.OBJECT_OT_Convert_to_Mastro_Street import OBJECT_OT_Convert_to_Mastro_Street
from .mastro_cad.OBJECT_OT_Convert_to_Mastro_Cad import OBJECT_OT_Convert_to_Mastro_Cad
from .mastro_street.OBJECT_OT_Set_Street_Id import OBJECT_OT_Set_Street_Id
from .mastro_arch.OBJECT_OT_Update_Mastro_Mesh_Attributes import OBJECT_OT_Update_Mastro_Mesh_Attributes
from .mastro_street.OBJECT_OT_Update_Street_Attributes import OBJECT_OT_Mastro_Update_Street_Attributes
from .mastro_custom_properties.OBJECT_OT_Update_Mastro_Custom_Properties import OBJECT_OT_Update_Mastro_Custom_Properties, OBJECT_OT_Remove_Mastro_Custom_Property
from .mastro_custom_properties.OBJECT_OT_Mastro_String_Options import (
    OBJECT_OT_Mastro_String_Option_New,
    OBJECT_OT_Mastro_String_Option_Remove,
    OBJECT_OT_Mastro_String_Option_Move,
    OBJECT_OT_Mastro_Set_String_Property,
    OBJECT_OT_Mastro_Set_String_Property_Menu,
)
from .mastro_import_export.OBJECT_OT_Export_CSV import OBJECT_OT_Mastro_Export_CSV
from .mastro_import_export.OBJECT_OT_Print_Configured import OBJECT_OT_Mastro_Print_Configured
from .mastro_import_export.OBJECT_OT_Print_Config import (
    MASTRO_OT_PrintSetAdd,
    MASTRO_OT_PrintSetRemove,
    MASTRO_OT_PrintSetMoveUp,
    MASTRO_OT_PrintSetMoveDown,
    MASTRO_OT_PrintSetParamAdd,
    MASTRO_OT_PrintSetParamRemove,
    MASTRO_OT_PrintSetParamMove,
    OBJECT_OT_Mastro_Print_Config,
)
from .mastro_pdf.OBJECT_OT_Export_Mastro_Frame_PDF import OBJECT_OT_Export_Mastro_Frame_PDF

from .mastro_2D.TRANSFORM_OT_Set_Orientation import TRANSFORM_OT_Mastro_Set_Orientation
from .mastro_constraints.TRANSFORM_OT_XY_Constraint import TRANSFORM_OT_Mastro_Rotate_XY_Constraint, TRANSFORM_OT_Mastro_Translate_XY_Constraint, MESH_OT_Mastro_Extrude_XY_Constraint

from .mastro_layer.LAYER_MANAGER_OT_Set_Active import LAYER_MANAGER_OT_SetActive
from .mastro_layer.LAYER_MANAGER_OT_Add_Layer import LAYER_MANAGER_OT_AddLayer
from .mastro_layer.LAYER_MANAGER_OT_Add_Layer_Popup import LAYER_MANAGER_OT_AddLayer_Popup

from .mastro_projector.OBJECT_OT_run_all import OBJECT_OT_RunAll, OBJECT_OT_CancelAll
from .mastro_projector.OBJECT_OT_run_batch import OBJECT_OT_RunBatch
from .mastro_projector.OBJECT_OT_bidimensional_Lines_Projection import OBJECT_OT_bidimensional_Lines_Projection
from .mastro_projector.OBJECT_OT_camera_sets import (
    MASTRO_OT_CameraSetAdd,
    MASTRO_OT_CameraSetRemove,
    MASTRO_OT_CameraSetDuplicate,
    MASTRO_OT_CameraSetMoveUp,
    MASTRO_OT_CameraSetMoveDown,
)
from .mastro_pdf.OBJECT_OT_pdf_sets import (
    MASTRO_OT_PdfSetAdd,
    MASTRO_OT_PdfSetRemove,
    MASTRO_OT_PdfSetDuplicate,
    MASTRO_OT_PdfSetMoveUp,
    MASTRO_OT_PdfSetMoveDown,
    MASTRO_OT_PdfSetExport,
)
from ..Utils.mastro_projector.shadow_render import MASTRO_OT_RenderShadowModal
from .mastro_cad.MESH_OT_Offset import MESH_OT_MaStroCad_Offset
from .mastro_cad.MESH_OT_Fillet import MESH_OT_MaStroCad_Fillet
from .mastro_cad.MESH_OT_Trim import MESH_OT_MaStroCad_Trim
from .mastro_cad.MESH_OT_DeleteSegment import MESH_OT_MaStroCad_DeleteSegment
from .mastro_cad.MESH_OT_RectangleDiagonal import MESH_OT_MaStroCad_RectangleDiagonal
from .mastro_cad.MESH_OT_RectangleBaseLine import MESH_OT_MaStroCad_RectangleBaseLine
from .mastro_cad.MESH_OT_RectangleCenter import MESH_OT_MaStroCad_RectangleCenter
from .mastro_cad.MESH_OT_RectangleCenterLine import MESH_OT_MaStroCad_RectangleCenterLine
from .mastro_cad.MESH_OT_EditRectangle import MESH_OT_MaStroCad_EditRectangle
from .mastro_cad.MESH_OT_Circle import MESH_OT_MaStroCad_Circle
from .mastro_cad.MESH_OT_Circle3 import MESH_OT_MaStroCad_Circle3
from .mastro_cad.MESH_OT_EditCircle import MESH_OT_MaStroCad_EditCircle
from .mastro_cad.MESH_OT_EditCAD import MESH_OT_MaStroCad_EditCAD
from .mastro_cad.MESH_MT_MaStroCad_Pie import MESH_MT_MaStroCad_Pie
from .mastro_cad.OBJECT_OT_Add_MaStroCad_Drawing_Mesh import OBJECT_OT_MaStroCad_Add_Drawing_Mesh

from .mastro_gis.VIEW3D_OT_MastroGIS_Basemap_Import import (
    VIEW3D_OT_map_viewer,
    VIEW3D_OT_MastroGIS_Basemap_Import,
    VIEW3D_OT_MastroGIS_Unlock_Origin,
    VIEW3D_OT_MastroGIS_3DTiles_Import,
)

from .mastro_import_export.OBJECT_OT_import_mastro_objects import (MASTRO_PG_ImportObject,
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
    OBJECT_OT_Add_Mastro_Frame,
    OBJECT_OT_Add_Mastro_Album,
    OBJECT_OT_Parent_to_Mastro_Album,
    OBJECT_OT_Unparent_from_Mastro_Album,
    OBJECT_OT_Mastro_Album_Remove_Child,
    OBJECT_OT_Convert_to_Mastro_Mass,
    OBJECT_OT_Convert_to_Mastro_Street,
    OBJECT_OT_Convert_to_Mastro_Cad,
    OBJECT_OT_Set_Street_Id,
    OBJECT_OT_Update_Mastro_Mesh_Attributes,
    OBJECT_OT_Mastro_Update_Street_Attributes,
    OBJECT_OT_Update_Mastro_Custom_Properties,
    OBJECT_OT_Mastro_Export_CSV,
    OBJECT_OT_Mastro_Print_Configured,
    MASTRO_OT_PrintSetAdd,
    MASTRO_OT_PrintSetRemove,
    MASTRO_OT_PrintSetMoveUp,
    MASTRO_OT_PrintSetMoveDown,
    MASTRO_OT_PrintSetParamAdd,
    MASTRO_OT_PrintSetParamRemove,
    MASTRO_OT_PrintSetParamMove,
    OBJECT_OT_Mastro_Print_Config,
    OBJECT_OT_Export_Mastro_Frame_PDF,

    TRANSFORM_OT_Mastro_Set_Orientation,
    TRANSFORM_OT_Mastro_Translate_XY_Constraint,
    TRANSFORM_OT_Mastro_Rotate_XY_Constraint,
    MESH_OT_Mastro_Extrude_XY_Constraint,

    LAYER_MANAGER_OT_SetActive,
    LAYER_MANAGER_OT_AddLayer,
    LAYER_MANAGER_OT_AddLayer_Popup,

    OBJECT_OT_RunAll,
    OBJECT_OT_CancelAll,
    OBJECT_OT_RunBatch,
    OBJECT_OT_bidimensional_Lines_Projection,
    MASTRO_OT_CameraSetAdd,
    MASTRO_OT_CameraSetRemove,
    MASTRO_OT_CameraSetDuplicate,
    MASTRO_OT_CameraSetMoveUp,
    MASTRO_OT_CameraSetMoveDown,
    MASTRO_OT_PdfSetAdd,
    MASTRO_OT_PdfSetRemove,
    MASTRO_OT_PdfSetDuplicate,
    MASTRO_OT_PdfSetMoveUp,
    MASTRO_OT_PdfSetMoveDown,
    MASTRO_OT_PdfSetExport,
    MASTRO_OT_RenderShadowModal,
    OBJECT_OT_Remove_Mastro_Custom_Property,
    OBJECT_OT_Mastro_String_Option_New,
    OBJECT_OT_Mastro_String_Option_Remove,
    OBJECT_OT_Mastro_String_Option_Move,
    OBJECT_OT_Mastro_Set_String_Property,
    OBJECT_OT_Mastro_Set_String_Property_Menu,

    MASTRO_PG_ImportObject,
    MASTRO_PG_ImportCollection,
    MASTRO_UL_ImportObjects,
    MASTRO_UL_ImportCollections,
    MASTRO_MT_ImportSpecials,
    OBJECT_OT_Import_Mastro_Toggle_All,
    OBJECT_OT_Import_Mastro_Select,
    OBJECT_OT_Import_Mastro_Objects,

    MESH_MT_MaStroCad_Pie,
    MESH_OT_MaStroCad_Offset,
    MESH_OT_MaStroCad_Fillet,
    MESH_OT_MaStroCad_Trim,
    MESH_OT_MaStroCad_DeleteSegment,
    MESH_OT_MaStroCad_RectangleDiagonal,
    MESH_OT_MaStroCad_EditRectangle,
    MESH_OT_MaStroCad_EditCircle,
    MESH_OT_MaStroCad_EditCAD,
    MESH_OT_MaStroCad_RectangleBaseLine,
    MESH_OT_MaStroCad_RectangleCenter,
    MESH_OT_MaStroCad_RectangleCenterLine,
    MESH_OT_MaStroCad_Circle,
    MESH_OT_MaStroCad_Circle3,
    OBJECT_OT_MaStroCad_Add_Drawing_Mesh,

    VIEW3D_OT_map_viewer,
    VIEW3D_OT_MastroGIS_Basemap_Import,
    VIEW3D_OT_MastroGIS_Unlock_Origin,
    VIEW3D_OT_MastroGIS_3DTiles_Import,
    )