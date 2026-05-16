import bpy
from bpy.types import Operator
from bpy.props import EnumProperty

from ..Utils.sync_layer_slots import sync_layer_slots


class LAYER_MANAGER_OT_AddLayer(Operator):
    """Add a new view layer to the scene."""
    bl_idname = "layer_manager.add_layer"
    bl_label = "New View Layer"
    bl_options = {'REGISTER', 'UNDO'}

    action: EnumProperty(
        items=[
            ("NEW",   "New",           "Add a new view layer",                       "", 0),
            ("COPY",  "Copy Settings", "Copy settings of current view layer",        "", 1),
            ("EMPTY", "Blank",         "Add a new layer with all collections disabled", "", 2),
        ]
    )

    @classmethod
    def description(cls, context, properties):
        descriptions = {
            "NEW":   "Add a new view layer",
            "COPY":  "Copy settings of current view layer",
            "EMPTY": "Add a new layer with all collections disabled",
        }
        return descriptions.get(properties.action, "Add view layer")

    def execute(self, context):
        bpy.ops.scene.view_layer_add(type=self.action)
        sync_layer_slots(context.scene)
        for area in context.screen.areas:
            area.tag_redraw()
        return {'FINISHED'}
