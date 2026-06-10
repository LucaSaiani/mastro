from .PROPERTIES_PT_MaStroCad_Pen import (
    PROPERTIES_OT_MaStroCad_Add_Pen,
    PROPERTIES_OT_MaStroCad_Remove_Pen,
    PROPERTIES_PT_MaStroCad_Drawing,
    PROPERTIES_PT_MaStroCad_Pens,
)
from .PROPERTIES_UL_MaStroCad_Pens import PROPERTIES_UL_MaStroCad_Pens
from .PREFERENCES_MaStroCad_Pens import (
    PREFERENCES_UL_MaStroCad_All_Pens,
    PREFERENCES_OT_MaStroCad_Reset_Pen_Color,
)
from .PROPERTIES_PT_MaStroCad_Line_Types import (
    PROPERTIES_UL_MaStroCad_Scene_Dash_Patterns,
    PROPERTIES_OT_MaStroCad_Add_Scene_Dash,
    PROPERTIES_OT_MaStroCad_Remove_Scene_Dash,
    PROPERTIES_OT_MaStroCad_Move_Scene_Dash,
    PROPERTIES_PT_MaStroCad_Line_Types,
)
from .PROPERTIES_PT_MaStroCad_Camera import register as _register_camera, unregister as _unregister_camera
from .PROPERTIES_PT_MaStroCad_Layers import (
    PROPERTIES_UL_MaStroCad_Layers,
    PROPERTIES_OT_MaStroCad_Add_Layer,
    PROPERTIES_OT_MaStroCad_Remove_Layer,
    PROPERTIES_OT_MaStroCad_Move_Layer,
    PROPERTIES_OT_MaStroCad_Sync_Layers,
    PROPERTIES_OT_MaStroCad_Assign_Layer,
    PROPERTIES_PT_MaStroCad_Layers,
    VIEW3D_UL_MaStroCad_Layers_Sidebar,
    VIEW3D_PT_MaStroCad_Layer_Picker,
    VIEW3D_PT_MaStroCad_Layers,
    register_wm_props as _register_layers_wm,
    unregister_wm_props as _unregister_layers_wm,
)
from .MENUS_MaStroCad import register as _register_cad_menus, unregister as _unregister_cad_menus

classes = (
    PROPERTIES_UL_MaStroCad_Pens,
    PREFERENCES_UL_MaStroCad_All_Pens,
    PREFERENCES_OT_MaStroCad_Reset_Pen_Color,
    PROPERTIES_UL_MaStroCad_Scene_Dash_Patterns,
    PROPERTIES_OT_MaStroCad_Add_Scene_Dash,
    PROPERTIES_OT_MaStroCad_Remove_Scene_Dash,
    PROPERTIES_OT_MaStroCad_Move_Scene_Dash,
    PROPERTIES_UL_MaStroCad_Layers,
    VIEW3D_UL_MaStroCad_Layers_Sidebar,
    PROPERTIES_OT_MaStroCad_Add_Layer,
    PROPERTIES_OT_MaStroCad_Remove_Layer,
    PROPERTIES_OT_MaStroCad_Move_Layer,
    PROPERTIES_OT_MaStroCad_Sync_Layers,
    PROPERTIES_OT_MaStroCad_Assign_Layer,
    PROPERTIES_OT_MaStroCad_Add_Pen,
    PROPERTIES_OT_MaStroCad_Remove_Pen,
    PROPERTIES_PT_MaStroCad_Drawing,
    PROPERTIES_PT_MaStroCad_Pens,
    PROPERTIES_PT_MaStroCad_Line_Types,
    PROPERTIES_PT_MaStroCad_Layers,
    VIEW3D_PT_MaStroCad_Layer_Picker,
    VIEW3D_PT_MaStroCad_Layers,
)


def register():
    _register_layers_wm()
    _register_camera()
    _register_cad_menus()


def unregister():
    _unregister_cad_menus()
    _unregister_camera()
    _unregister_layers_wm()
