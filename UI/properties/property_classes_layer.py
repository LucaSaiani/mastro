from bpy.types import PropertyGroup
from bpy.props import (IntProperty,
                       StringProperty,
                       CollectionProperty,
)

from ...Utils.mastro_layer.on_active_layer_changed import on_active_layer_changed


class mastro_CL_layer_slot(PropertyGroup):
    """One entry in the view-layer shadow list — stores the layer name and its previous name for rename detection."""

    def _on_slot_name_changed(self, context):
        """Propagate a user rename of a shadow slot to the actual Blender view layer."""
        scene = context.scene
        if scene.view_layers.get(self.name):
            self.prev_name = self.name
            return
        old_vl = scene.view_layers.get(self.prev_name)
        if old_vl:
            old_vl.name = self.name
            self.prev_name = self.name

    name: StringProperty(update=_on_slot_name_changed)
    prev_name: StringProperty()


class mastro_CL_layer_manager_props(PropertyGroup):
    """Scene-level container for the view-layer shadow list and its active index."""
    layer_slots: CollectionProperty(type=mastro_CL_layer_slot)
    active_index: IntProperty(
        default=0,
        update=on_active_layer_changed,
    )
