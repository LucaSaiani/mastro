import bpy
from bpy.types import Operator


class LAYER_MANAGER_OT_SetActive(Operator):
    """Set the Blender active view layer to match the selected shadow slot."""
    bl_idname = "layer_manager.set_active"
    bl_label = "Set Active View Layer"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        props = scene.mastro_layer_manager_props

        active_slot = (
            props.layer_slots[props.active_index]
            if 0 <= props.active_index < len(props.layer_slots)
            else None
        )

        if active_slot:
            context.window.view_layer = scene.view_layers[active_slot.name]
            return {'FINISHED'}
        return {'CANCELLED'}
