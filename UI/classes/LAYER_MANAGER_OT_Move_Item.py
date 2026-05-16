import bpy
from bpy.types import Operator


class LAYER_MANAGER_OT_Move_Item(Operator):
    """Move the selected view-layer slot up, down, to the top, or to the bottom."""
    bl_idname = "layer_manager.move_item"
    bl_label = "Move View Layer Slot"
    bl_options = {'REGISTER', 'UNDO'}

    direction: bpy.props.EnumProperty(
        items=[
            ('UP',     "Up",     "Move one position up"),
            ('DOWN',   "Down",   "Move one position down"),
            ('TOP',    "Top",    "Move to the top of the list"),
            ('BOTTOM', "Bottom", "Move to the bottom of the list"),
        ],
        default='UP',
    )

    def execute(self, context):
        props = context.scene.mastro_layer_manager_props
        slots = props.layer_slots
        index = props.active_index
        count = len(slots)

        if count < 2:
            return {'CANCELLED'}

        if self.direction == 'UP' and index > 0:
            slots.move(index, index - 1)
            props.active_index = index - 1
        elif self.direction == 'DOWN' and index < count - 1:
            slots.move(index, index + 1)
            props.active_index = index + 1
        elif self.direction == 'TOP' and index > 0:
            for i in range(index, 0, -1):
                slots.move(i, i - 1)
            props.active_index = 0
        elif self.direction == 'BOTTOM' and index < count - 1:
            for i in range(index, count - 1):
                slots.move(i, i + 1)
            props.active_index = count - 1
        else:
            return {'CANCELLED'}

        return {'FINISHED'}
