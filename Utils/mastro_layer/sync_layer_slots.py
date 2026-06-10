def sync_layer_slots(scene):
    """
    Synchronise the shadow list with the real view layers of the given scene.
    Preserves the order of existing slots; appends new ones; removes stale ones.
    Safe to call outside of an operator context.
    """
    props = scene.mastro_layer_manager_props
    slots = props.layer_slots
    real_names = [vl.name for vl in scene.view_layers]
    slot_names = [s.name for s in slots]

    real_set = set(real_names)
    slot_set = set(slot_names)

    added   = real_set - slot_set  # names present in Blender but not in the shadow list
    removed = slot_set - real_set  # names present in the shadow list but no longer in Blender

    # If exactly one name was added and one removed, treat it as a rename.
    # Update the slot name in-place to preserve its position in the list.
    if len(added) == 1 and len(removed) == 1:
        old_name = next(iter(removed))
        new_name = next(iter(added))
        for s in slots:
            if s.name == old_name:
                s.name = new_name
                return

    # Remove stale slots (iterate in reverse to keep indices valid)
    to_remove = [i for i, s in enumerate(slots) if s.name not in real_set]
    for i in reversed(to_remove):
        slots.remove(i)

    # Append slots for layers not yet in the shadow list
    existing = {s.name for s in slots}
    for name in real_names:
        if name not in existing:
            new_slot = slots.add()
            new_slot.prev_name = name  # set before name so the callback finds it
            new_slot.name = name
