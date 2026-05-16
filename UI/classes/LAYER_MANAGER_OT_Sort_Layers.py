import bpy
from bpy.types import Operator
from bpy.props import EnumProperty


class LAYER_MANAGER_OT_SortLayers(Operator):
    """Sort view-layer slots alphabetically (A→Z or Z→A)."""
    bl_idname = "layer_manager.sort_layers"
    bl_label = "Sort View Layers"
    bl_options = {'REGISTER', 'UNDO'}

    direction: EnumProperty(
        items=[
            ('AZ', "A → Z", "Sort ascending"),
            ('ZA', "Z → A", "Sort descending"),
        ],
        default='AZ',
    )

    def execute(self, context):
        props = context.scene.mastro_layer_manager_props
        slots = props.layer_slots
        reverse = self.direction == 'ZA'

        sorted_names = sorted(
            (s.name for s in slots),
            key=str.casefold,
            reverse=reverse,
        )

        # Reorder slots in-place using CollectionProperty.move()
        for i, target_name in enumerate(sorted_names):
            for j in range(i, len(slots)):
                if slots[j].name == target_name:
                    if j != i:
                        slots.move(j, i)
                    break

        # Keep active_index on the current window view layer
        active_name = context.window.view_layer.name
        for i, slot in enumerate(slots):
            if slot.name == active_name:
                props.active_index = i
                break

        return {'FINISHED'}
