def get_names_from_list(scene, context, collection):
    """
    Generate a list of tuples (identifier, name, description) for EnumProperty
    from a Blender CollectionProperty.
    """
    # items = []
    # coll = getattr(scene, collection, [])
    # for el in coll:  # prendi l’ordine originale
    # # for el in getattr(scene, collection, []):
    #     # items.append((el.name, el.name, "", el.id))
    #     items.append((el.name, el.name, f"Id. {el.id} - {el.name}"))
    # return items

    items = []
    for el in sorted(getattr(scene, collection, []), key=lambda e: e.name):
        items.append((el.name, el.name, f"Id. {el.id} - {el.name}"))
    return items

