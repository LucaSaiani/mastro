from .menus import (
    MASTRO_MT_add_gn_menu,
    MASTRO_MT_gn_filter_by,
    MASTRO_MT_gn_separate_by,
    MASTRO_MT_add_shader_menu,
    MASTRO_MT_shader_filter_by,
    append_menus,
    remove_menus,
)

classes = (
    MASTRO_MT_gn_filter_by,
    MASTRO_MT_gn_separate_by,
    MASTRO_MT_add_gn_menu,
    MASTRO_MT_shader_filter_by,
    MASTRO_MT_add_shader_menu,
)


def register():
    append_menus()
    return None


def unregister():
    remove_menus()
    return None
