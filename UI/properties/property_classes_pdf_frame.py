import bpy
from bpy.types import PropertyGroup
from bpy.props import IntProperty, EnumProperty

from ...Operators.mastro_pdf.frame_formats import FORMAT_SIZES


def _apply_frame_size(obj, width, height):
    """Write width/height (mm) onto a MaStro frame empty's scale."""
    obj.scale = (width / 1000, height / 1000, 0.0)


def _on_frame_format_changed(self, context):
    if self.format == 'CUSTOM':
        return
    w, h = FORMAT_SIZES[self.format]
    if self.orientation == 'LANDSCAPE':
        w, h = max(w, h), min(w, h)
    else:
        w, h = min(w, h), max(w, h)
    self.width, self.height = w, h


def _on_frame_orientation_changed(self, context):
    self.width, self.height = self.height, self.width


def _on_frame_dimension_changed(self, context):
    obj = context.object
    if obj is not None:
        _apply_frame_size(obj, self.width, self.height)


class mastro_CL_frame_settings(PropertyGroup):
    """Lives on a MaStro frame Empty as obj.mastro_frame_settings.

    width/height are mirrored onto obj.scale.x/y (in metres) by the update
    callbacks below — this is the only place that does so, so the empty's
    scale always reflects the paper size chosen here."""
    width: IntProperty(
        name="Width",
        description="Frame width in mm",
        min=1,
        default=297,
        update=_on_frame_dimension_changed,
    )

    height: IntProperty(
        name="Height",
        description="Frame height in mm",
        min=1,
        default=210,
        update=_on_frame_dimension_changed,
    )

    orientation: EnumProperty(
        name="Orientation",
        description="Frame orientation: landscape or portrait",
        items=[
            ('LANDSCAPE', "Landscape", ""),
            ('PORTRAIT',  "Portrait",  ""),
        ],
        default='LANDSCAPE',
        update=_on_frame_orientation_changed,
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
        update=_on_frame_format_changed,
    )
