import bpy
from bpy.types import Operator


class LAYER_MANAGER_OT_AddLayer_Popup(Operator):
    """Open a popup menu to choose the type of new view layer to add."""
    bl_idname = "layer_manager.add_layer_popup"
    bl_label = "New View Layer"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        context.window_manager.popup_menu(self.draw_menu, title="New Layer")
        return {'FINISHED'}

    def draw_menu(self, menu, context):
        layout = menu.layout
        layout.operator("layer_manager.add_layer", text="New").action   = 'NEW'
        layout.operator("layer_manager.add_layer", text="Copy").action  = 'COPY'
        layout.operator("layer_manager.add_layer", text="Blank").action = 'EMPTY'
