import bpy
from bpy.types import PropertyGroup
from bpy.props import (IntProperty,
                       BoolProperty,
                       StringProperty,
                       CollectionProperty,
)


class mastro_CL_pdf_frame_item(PropertyGroup):
    frame_name: StringProperty()


class mastro_CL_pdf_set(PropertyGroup):
    name:       StringProperty(name="Name", default="PDF Set")
    bind_pages: BoolProperty(name="Bind Pages", default=False)
    frames:     CollectionProperty(type=mastro_CL_pdf_frame_item)


class mastro_CL_pdf_scene_props(PropertyGroup):
    pdf_sets:                CollectionProperty(type=mastro_CL_pdf_set)
    active_set_index:        IntProperty(default=0, min=0)
    active_frame_index:      IntProperty(default=0, min=0)
    all_frames:              CollectionProperty(type=mastro_CL_pdf_frame_item)
    filter_set_members_only: BoolProperty(
        name        = "Show assigned only",
        default     = False,
        description = "Show only frames assigned to this set",
    )
