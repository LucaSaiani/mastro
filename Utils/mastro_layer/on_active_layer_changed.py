def on_active_layer_changed(self, context):
    """Switch the window's active view layer when the user selects a slot in the list."""
    props = self
    if 0 <= props.active_index < len(props.layer_slots):
        name = props.layer_slots[props.active_index].name
        vl = context.scene.view_layers.get(name)
        if vl and context.window.view_layer != vl:
            context.window.view_layer = vl
