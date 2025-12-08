def get_names_from_list(scene, context, collection):
    """
    Generate a list of tuples (identifier, name, description) for EnumProperty
    from a Blender CollectionProperty.

    :param scene: Blender scene
    :param context: Blender context (required by EnumProperty)
    :param collection: the name of the CollectionProperty as a string
    :return: list of tuples suitable for EnumProperty items
    """
    items = []
    for el in getattr(scene, collection, []):
        items.append((el.name, el.name, "", el.id))
        
    return items

