import bpy

def init_lists(scene=None):
    """Initialize all MaStro name lists with default values if empty."""
    s = bpy.data.scenes[scene] if scene else bpy.context.scene

    # --- Internal helper: ensures a list has an item with id=0 ---
    def ensure_item(collection, defaults):
        """Ensure the collection has an element with id=0, setting default values if needed."""
        if not any(el.id == 0 for el in collection):
            item = collection.add()
            item.id = 0
            for attr, value in defaults.items():
                setattr(item, attr, value)
        elif len(collection) == 0:
            item = collection.add()
            item.id = 0
            for attr, value in defaults.items():
                setattr(item, attr, value)

    # --- Internal helper: ensures the 'current' collection mirrors the first element ---
    def ensure_current(current_collection, name):
        """Ensure the 'current' collection exists and mirrors the first name from the base list."""
        if len(current_collection) == 0:
            item = current_collection.add()
            item.id = 0
            item.name = name

    # --- Configuration of all list types ---
    configs = [
        ("mastro_block_name_list", "mastro_block_name_current", {"name": "Block type... "}),
        ("mastro_building_name_list", "mastro_building_name_current", {"name": "Building name... "}),
        ("mastro_use_name_list", None, {"name": "Use name... ", "storeys": 3, "liquid": True}),
        ("mastro_typology_name_list", "mastro_typology_name_current", {"name": "Typology name... ", "useList": "0"}),
        ("mastro_typology_uses_name_list", None, {"name": "Use name... "}),
        ("mastro_street_name_list", "mastro_street_name_current", {"name": "Street type... "}),
        ("mastro_wall_name_list", "mastro_wall_name_current", {"name": "Wall type... ", "normal": 0}),
        ("mastro_floor_name_list", "mastro_floor_name_current", {"name": "Floor type... "}),
    ]

    # --- Apply initialization logic for all configured collections ---
    for main_name, current_name, defaults in configs:
        main_list = getattr(s, main_name)
        ensure_item(main_list, defaults)

        if current_name:
            current_list = getattr(s, current_name)
            ensure_current(current_list, main_list[0].name)
