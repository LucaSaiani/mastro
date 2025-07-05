import bpy
import bpy.utils.previews
from pathlib import Path

pcoll = None


def register():
    global pcoll
    pcoll = bpy.utils.previews.new()
    dir = Path(__file__).parent
    for img_file in dir.glob("*.svg"):
        pcoll.load(img_file.stem, str(img_file), 'IMAGE')


def unregister():
    global pcoll
    bpy.utils.previews.remove(pcoll)


def icon_id(name:str):
    global pcoll
    return pcoll[name].icon_id

