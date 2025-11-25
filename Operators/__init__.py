from .MESH_OT_Move_Active_Vertex import MESH_OT_Move_Active_Vertex
from .OBJECT_OT_Add_Mastro_Block import OBJECT_OT_Add_Mastro_Block
from .OBJECT_OT_Add_Mastro_Dimension import OBJECT_OT_Add_Mastro_Dimension
from .OBJECT_OT_Add_Mastro_Mass import OBJECT_OT_Add_Mastro_Mass
from .OBJECT_OT_Add_Mastro_Street import OBJECT_OT_Add_Mastro_Street
from .OBJECT_OT_Convert_to_Mastro import OBJECT_OT_Convert_to_Mastro_Mass, OBJECT_OT_Convert_to_Mastro_Street
from .OBJECT_OT_Set_Edge_Attribute_Angle import OBJECT_OT_Set_Edge_Attribute_Angle
from .OBJECT_OT_Set_Edge_Attribute_Depth import OBJECT_OT_Set_Edge_Attribute_Depth
from .OBJECT_OT_Set_Edge_Attribute_Normal import OBJECT_OT_Set_Edge_Attribute_Normal
# from .ss_OBJECT_OT_Set_Edge_Attribute_Storeys import OBJECT_OT_Set_Edge_Attribute_Storeys
# from .ss_OBJECT_OT_Set_Edge_Attribute_Uses import OBJECT_OT_Set_Edge_Attribute_Uses
from .OBJECT_OT_Set_Extras import OBJECT_OT_Set_Vertex_Extra, OBJECT_OT_Set_Edge_Extra, OBJECT_OT_Set_Face_Extra
# from .ss_OBJECT_OT_Set_Face_Attribute_Storeys import OBJECT_OT_Set_Face_Attribute_Storeys
# from .ss_OBJECT_OT_Set_Face_Attribute_Uses import OBJECT_OT_Set_Face_Attribute_Uses
from .OBJECT_OT_Set_Floor_Id import OBJECT_OT_Set_Floor_Id
from .OBJECT_OT_Set_Street_Id import OBJECT_OT_Set_Street_Id
from .OBJECT_OT_Set_Wall_Id import OBJECT_OT_Set_Wall_Id
from .OBJECT_OT_Update_Mastro_Mesh_Attributes import OBJECT_OT_Update_Mastro_Mesh_Attributes
from .OBJECT_OT_Update_Street_Attributes import OBJECT_OT_update_all_MaStro_street_attributes
from .TRANSFORM_OT_Set_Orientation import TRANSFORM_OT_Mastro_Set_Orientation


classes = (
    MESH_OT_Move_Active_Vertex,
    OBJECT_OT_Add_Mastro_Block,
    OBJECT_OT_Add_Mastro_Dimension,
    OBJECT_OT_Add_Mastro_Mass,
    OBJECT_OT_Add_Mastro_Street,
    OBJECT_OT_Convert_to_Mastro_Mass, 
    OBJECT_OT_Convert_to_Mastro_Street,
    OBJECT_OT_Set_Edge_Attribute_Angle,
    OBJECT_OT_Set_Edge_Attribute_Depth,
    OBJECT_OT_Set_Vertex_Extra, 
    OBJECT_OT_Set_Edge_Extra, 
    OBJECT_OT_Set_Face_Extra,
    OBJECT_OT_Set_Edge_Attribute_Normal,
    # ss_OBJECT_OT_Set_Edge_Attribute_Storeys,
    # ss_OBJECT_OT_Set_Edge_Attribute_Uses,
    # ss_OBJECT_OT_Set_Face_Attribute_Storeys,
    # ss_OBJECT_OT_Set_Face_Attribute_Uses,
    OBJECT_OT_Set_Floor_Id,
    OBJECT_OT_Set_Street_Id,
    OBJECT_OT_Set_Wall_Id,
    OBJECT_OT_Update_Mastro_Mesh_Attributes,
    OBJECT_OT_update_all_MaStro_street_attributes,
    TRANSFORM_OT_Mastro_Set_Orientation,
    )