def sort_level_list(scene):
    """Sort mastro_level_list by descending level, then by name, keeping the
    active index pointed at the same item.

    Levels are never reordered manually (no move up/down in the UI): the
    order is always derived from `level`/`name`, so this is called instead
    of a move operator whenever those fields change.
    """
    collection = scene.mastro_level_list
    if len(collection) < 2:
        return

    # Remember which item was selected by id (not by index), since the
    # index is about to become stale as items are moved around below.
    active_id = collection[scene.mastro_level_list_index].id

    order = sorted(range(len(collection)), key=lambda i: (-collection[i].level, collection[i].name))
    # CollectionProperty only exposes move(from, to); simulate the target
    # permutation with a sequence of moves while tracking where each
    # original index currently lives in `pos`.
    pos = list(range(len(collection)))
    for target_pos, source_pos in enumerate(order):
        current_pos = pos.index(source_pos)
        collection.move(current_pos, target_pos)
        pos.insert(target_pos, pos.pop(current_pos))

    for i, item in enumerate(collection):
        if item.id == active_id:
            scene.mastro_level_list_index = i
            break
