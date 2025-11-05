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
    # Iterate over each element in the specified collection
    for el in getattr(scene, collection, []):
        # Create a tuple (id, name, description) for each element
        items.append((el.name, el.name, ""))
    return items
