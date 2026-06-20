import bpy
from bpy.types import Operator
from bpy.props import IntProperty, EnumProperty
from bpy_extras.object_utils import AddObjectHelper, object_data_add


FORMAT_SIZES = {
    'A0': (1189, 841),
    'A1': (841, 594),
    'A2': (594, 420),
    'A3': (420, 297),
    'A4': (297, 210),
}


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
        obj.empty_display_type = 'CUBE'
        obj.empty_display_size = 0.5
        obj.scale = (self.width / 1000, self.height / 1000, 0.0)

        obj["MaStro object"] = True
        obj["MaStro frame"] = True

        return {'FINISHED'}
    