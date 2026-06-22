import bpy
from bpy.types import PropertyGroup
from bpy.props import (IntProperty,
                       BoolProperty,
                       StringProperty,
                       CollectionProperty,
)


def _get_pdf_active_set(context):
    pp = context.scene.mastro_pdf_props
    idx = pp.active_set_index
    return pp.pdf_sets[idx] if 0 <= idx < len(pp.pdf_sets) else None


def _get_in_active_pdf_set(self):
    # Blender's BoolProperty get/set callbacks only receive self, never
    # context, so the active scene must be read from bpy.context here.
    active_set = _get_pdf_active_set(bpy.context)
    if active_set is None:
        return False
    return any(it.frame_name == self.frame_name for it in active_set.frames)


def _set_in_active_pdf_set(self, value):
    active_set = _get_pdf_active_set(bpy.context)
    if active_set is None:
        return

    for i, it in enumerate(active_set.frames):
        if it.frame_name == self.frame_name:
            if not value:
                active_set.frames.remove(i)
            return
    if value:
        active_set.frames.add().frame_name = self.frame_name


class mastro_CL_pdf_frame_item(PropertyGroup):
    frame_name: StringProperty()
    # Backed by the active PDF set's `frames` collection (see get/set
    # above). A real toggle prop (instead of an operator button) lets
    # Blender's native click-drag over several UIList rows assign/unassign
    # multiple frames in one gesture.
    in_active_set: BoolProperty(
        name="In Active Set",
        get=_get_in_active_pdf_set,
        set=_set_in_active_pdf_set,
    )


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
