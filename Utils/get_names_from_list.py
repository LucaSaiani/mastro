_enum_cache = {}

def get_names_from_list(scene, context, collection):
    """
    Generate a list of tuples for EnumProperty from a Blender CollectionProperty.
    The result is stored in a module-level dict so Python does not garbage-collect
    the strings while Blender still holds raw C pointers to them.
    """
    items = []
    for el in sorted(getattr(scene, collection, []), key=lambda e: e.name):
        items.append((f"id_{el.id}", el.name, f"Id. {el.id} - {el.name}", 0, el.id))
    _enum_cache[collection] = items
    return items

