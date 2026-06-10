import bpy
import bpy.utils.previews
from pathlib import Path

from .mastro_cad_line_type_icons import (register as _register_cad_icons,
                                         unregister as _unregister_cad_icons,
                                         get_wide_icon_id,
                                         get_wide_icon_id_colored,
                                         get_color_swatch_icon_id,
                                         get_custom_pattern_icon_id,
                                         invalidate_icon,
)

pcoll = None


def register():
    global pcoll
    pcoll = bpy.utils.previews.new()
    dir = Path(__file__).parent
    for img_file in dir.glob("*.svg"):
        pcoll.load(img_file.stem, str(img_file), 'IMAGE')
    _register_cad_icons()


def unregister():
    global pcoll
    _unregister_cad_icons()
    bpy.utils.previews.remove(pcoll)


def icon_id(name:str):
    global pcoll
    return pcoll[name].icon_id



