from .menus import (

    MASTRO_MT_add_gn_menu,
    append_menus, 
    remove_menus,

    )

# from .panels import (

#     NODEBOOSTER_PT_tool_search,
#     NODEBOOSTER_PT_tool_color_palette,
#     NODEBOOSTER_PT_tool_frame,
#     NODEBOOSTER_PT_shortcuts_memo,
#     NODEBOOSTER_PT_active_node,

#     )


classes = (
    MASTRO_MT_add_gn_menu,
    )


def register():
    append_menus()
    return None


def unregister():
    remove_menus()
    return None