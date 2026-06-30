import bpy
from bpy.types import Operator
from bpy.props import IntProperty, EnumProperty
from bpy_extras.object_utils import AddObjectHelper, object_data_add

from .frame_formats import FORMAT_SIZES

FRAME_IMAGE_NAME = "MaStro frame paper"


def _get_frame_image():
    """Return the shared white "paper" image used by all frame empties,
    generating it once if it doesn't exist yet in this .blend file.

    A single 2x2 white image is reused by every frame instead of creating
    one per object: actual paper proportions come from obj.scale, not from
    the image's own pixel aspect, so there is nothing format-specific to
    bake into the image itself."""
    img = bpy.data.images.get(FRAME_IMAGE_NAME)
    if img is None:
        img = bpy.data.images.new(FRAME_IMAGE_NAME, width=2, height=2, alpha=False)
        img.pixels = [1.0, 1.0, 1.0, 1.0] * 4
        img.pack()
    return img


def update_format(self, context):
    if self.format in FORMAT_SIZES:
        w, h = FORMAT_SIZES[self.format]
        if self.orientation == 'LANDSCAPE':
            self.width, self.height = max(w, h), min(w, h)
        else:
            self.width, self.height = min(w, h), max(w, h)


def update_orientation(self, _context):
    self.width, self.height = self.height, self.width


class OBJECT_OT_Add_Mastro_Frame(Operator, AddObjectHelper):
    """Add a MaStro frame"""
    bl_idname = "object.mastro_add_mastro_frame"
    bl_label = "Frame"
    bl_options = {'REGISTER', 'UNDO'}

    width: IntProperty(
        name="Width",
        description="Frame width in mm",
        min=1,
        default=297,
    )

    height: IntProperty(
        name="Height",
        description="Frame height in mm",
        min=1,
        default=210,
    )

    orientation: EnumProperty(
        name="Orientation",
        description="Frame orientation: landscape or portrait",
        items=[
            ('LANDSCAPE', "Landscape", ""),
            ('PORTRAIT',  "Portrait",  ""),
        ],
        default='LANDSCAPE',
        update=update_orientation,
    )

    format: EnumProperty(
        name="Format",
        description="ISO 216 international paper size",
        items=[
            ('A0', "A0", ""),
            ('A1', "A1", ""),
            ('A2', "A2", ""),
            ('A3', "A3", ""),
            ('A4', "A4", ""),
            ('CUSTOM', 'Custom', ""),
        ],
        default="A4",
        update=update_format,
    )
    
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "format")
        layout.prop(self, "orientation")
        if self.format == 'CUSTOM':
            layout.prop(self, "width")
            layout.prop(self, "height")
    
    def execute(self, context):
        obj = object_data_add(context, None, operator=self, name="MaStro frame")
        obj.empty_display_type = 'IMAGE'
        obj.data = _get_frame_image()
        obj.empty_image_depth = 'BACK'
        obj.empty_display_size = 0.5
        obj.scale = (self.width / 1000, self.height / 1000, 0.0)

        obj["MaStro object"] = True
        obj["MaStro frame"] = True

        # Mirror the operator's values onto the Object Data panel's PropertyGroup.
        # format/orientation go through the [] override to skip their own update
        # callbacks (which would recompute width/height from FORMAT_SIZES and
        # discard the values this operator already resolved for CUSTOM sizes).
        settings = obj.mastro_frame_settings
        settings["format"] = self.format
        settings["orientation"] = self.orientation
        settings.width = self.width
        settings.height = self.height

        return {'FINISHED'}
    