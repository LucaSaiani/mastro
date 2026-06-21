def sync_children_display(album):
    """Rebuild album.mastro_album_settings.children_display from album.children.

    Must be called from an operator, not from a panel's draw() — Blender
    forbids writing to ID data (including this CollectionProperty) while
    the UI is being redrawn."""
    settings = album.mastro_album_settings
    settings.children_display.clear()
    for child in album.children:
        settings.children_display.add().object = child
