import bpy

# store keymaps here to access after registration
addon_keymaps = []

keymap_names = ['Object Mode', 'Mesh']


def register():
    # handle the keymap
    wm = bpy.context.window_manager

    user_config_keymaps = wm.keyconfigs.user.keymaps
    for keymap in user_config_keymaps:
        if keymap.name in keymap_names:
            for kmi in keymap.keymap_items:
                if kmi.idname == "transform.translate" and kmi.type == "G":
                    kmi.active = False
                elif kmi.idname == "transform.rotate" and kmi.type == "R":
                    kmi.active = False
                
    # Note that in background mode (no GUI available), keyconfigs are not available either,
    # so we have to check this to avoid nasty errors in background case.
    kc = wm.keyconfigs.addon
    if kc:
        # if keymap doesn't exist, it is added
        def ensure_keymap(name, space_type, idname, key_type, key_value):
            km = kc.keymaps.get(name)
            if not km:
                km = kc.keymaps.new(name=name, space_type=space_type)

            for item in km.keymap_items:
                if (
                    item.idname == idname and
                    item.type == key_type and
                    item.value == key_value
                ):
                   # in case it exists
                    return

            # if not existing, it is added
            kmi = km.keymap_items.new(idname, key_type, key_value)
            addon_keymaps.append((km, kmi))
        
        ensure_keymap('Mesh', 'EMPTY', "transform.translate_xy_constraint", 'G', 'PRESS')
        ensure_keymap('Object Mode', 'EMPTY', "transform.translate_xy_constraint", 'G', 'PRESS')
        ensure_keymap('Mesh', 'EMPTY', "transform.rotate_xy_constraint", 'R', 'PRESS')
        ensure_keymap('Object Mode', 'EMPTY', "transform.rotate_xy_constraint", 'R', 'PRESS')
  
    
def unregister():
    wm = bpy.context.window_manager
    keyconfigs = wm.keyconfigs
    user_config_keymaps = keyconfigs.user.keymaps

    # handle the keymap
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    
    # Find and re-enable previous keymaps
    user_config_keymaps = wm.keyconfigs.user.keymaps
    for keymap in user_config_keymaps:
        if keymap.name in keymap_names:
            for kmi in keymap.keymap_items:
                if kmi.idname == "transform.translate" and kmi.type == "G":
                    kmi.active = True
                elif kmi.idname == "transform.rotate" and kmi.type == "R":
                    kmi.active = True
                    
 