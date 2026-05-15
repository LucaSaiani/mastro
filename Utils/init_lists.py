import bpy

def init_lists(scene=None):
    """Initialize all MaStro name lists with default values if empty."""
    s = bpy.data.scenes[scene] if scene else bpy.context.scene

    def ensure_item(collection, defaults):
        """Ensure the collection has a fallback element with id=0.
        id=0 is the default for all mesh attributes, so a missing entry would
        cause empty labels and broken lookups throughout the addon."""
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
    
    configs = [
        ("mastro_block_name_list", {"name": "Block name"}),
        ("mastro_building_name_list", {"name": "Building name"}),
        ("mastro_use_name_list", {"name": "Use name", "storeys": 3, "liquid": True}),
        ("mastro_typology_name_list", {"name": "Typology name", "useList": "0"}),
        ("mastro_typology_uses_name_list", {"name": "Use name"}),
        ("mastro_street_name_list", {"name": "Street type"}),
        ("mastro_wall_name_list", {"name": "Wall type", "normal": 0}),
        ("mastro_floor_name_list", {"name": "Floor type"}),
    ]

    # --- Apply initialization logic for all configured collections ---
    for main_name, defaults in configs:
        main_list = getattr(s, main_name)
        ensure_item(main_list, defaults)
    
    # Access enum properties to force their internal item cache to refresh,
    # preventing stale or empty strings in the UI dropdowns on first load
    bpy.context.scene.mastro_block_name
    bpy.context.scene.mastro_building_name
    bpy.context.scene.mastro_wall_names
    bpy.context.scene.mastro_floor_names
    bpy.context.scene.mastro_street_names
        
    