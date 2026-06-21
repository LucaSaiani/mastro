def set_modifier_input(mod, socket_name, value):
    """Set a Geometry Nodes modifier input by its interface socket name.

    Blender 5.0 replaced the old IDProperty paths (mod[identifier] = value)
    with real RNA properties under mod.properties.inputs.<identifier>.value."""
    for item in mod.node_group.interface.items_tree:
        if getattr(item, "in_out", None) == 'INPUT' and item.name == socket_name:
            getattr(mod.properties.inputs, item.identifier).value = value
            return
