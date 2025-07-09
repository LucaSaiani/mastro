# The source of this document can be found in the autoConstraintsFree addon by SpaghetMeNot

import bpy
# from pathlib import Path
# import json
# from pathlib import Path
# import addon_utils

# store keymaps here to access after registration
addon_keymaps = []

keymap_names = ['Object Mode', 'Mesh']

# # Dict of default operator names and their auto-contstraint counterparts to replace them with
# replacement_operators = {
#     'transform.translate': 'transform.translate_xy_constraint',
#     'transform.rotate': 'transform.rotate_xy_constraint',
# }


# def new_kmi_from_reference(keymap, idname, reference_kmi) -> bpy.types.KeyMapItem:
#     """Creates a copy of a KeyMapItem into a new keymap and adds it to addon_keymaps"""
#     new_kmi = keymap.keymap_items.new(idname,
#         type = reference_kmi.type,
#         value = reference_kmi.value,
#         ctrl = reference_kmi.ctrl,
#         shift = reference_kmi.shift,
#         alt = reference_kmi.alt)
#     new_kmi.active = True

#     addon_keymaps.append((keymap, new_kmi))
#     print(keymap, new_kmi)
#     return new_kmi


# # def find_keymap_items(user_config_keymaps, idname, keymap_names=[]) -> tuple[bpy.types.KeyMapItem]:
# #     """
# #     Find all KeyMapItems with idname in the given keyconfig.
# #     Will return a tuple of (keymap, keymap_item)
# #     """
# #     kmis = []
# #     for keymap in user_config_keymaps:
# #         if keymap.name not in keymap_names and len(keymap_names) > 0:
# #             continue

# #         for kmi in keymap.keymap_items:
# #             if kmi.idname == idname:
# #                 kmis.append(kmi)
# #     return tuple(kmis)


# def replace_keymap_items(old_keyconfig_keymaps, old_idname, keymap_names, new_keymap, new_idname) -> list[bpy.types.KeyMapItem]:
#     """
#     Find and disable all keymap_items with old_idname in old_keymap.
#     For each one, create a new keymap_item with new_idname in new_keymap
#     """
#     user_kmis = find_keymap_items(old_keyconfig_keymaps, old_idname, keymap_names)
#     # filter out specific shortut that breaks cursor behaviour
#     user_kmis = tuple([kmi for kmi in user_kmis if not ( kmi.value=="CLICK_DRAG" and kmi.idname == "transform.translate" and kmi.type == "RIGHTMOUSE") ])
    
#     new_kmis = []
#     if len(user_kmis) == 0:
#         print(f'Could not find a keymap for {old_idname}')
#     for kmi in user_kmis:
#         kmi.active = False
#         new_kmis.append(new_kmi_from_reference(new_keymap, new_idname, kmi))
#     return new_kmis


# def kmi_to_dict(kmi) -> dict:
#     """Turn a KeyMapItem into a dictionary — used to save keymaps to a json file"""
#     return {
#         'idname': kmi.idname,
#         'type': kmi.type,
#         'value': kmi.value,
#         'ctrl': kmi.ctrl,
#         'shift': kmi.shift,
#         'alt': kmi.alt,
#     }


# def kmi_from_dict(keymap, kmi_dict) -> bpy.types.KeyMapItem:
#     """Create a KeyMapItem from a dictionary — used to load keymaps from a json file"""
#     new_kmi = keymap.keymap_items.new(kmi_dict['idname'],
#             type = kmi_dict['type'],
#             value = kmi_dict['value'],
#             ctrl = kmi_dict['ctrl'],
#             shift = kmi_dict['shift'],
#             alt = kmi_dict['alt'])
    
#     addon_keymaps.append((keymap, new_kmi))
#     new_kmi.active = True
#     return new_kmi


# def keymaps_to_json(keymaps):
#     """Create a dictionary for every keymap and every kmi in it"""
#     keymaps_dict = {}

#     for keymap, kmi in keymaps:
#         if keymap.name not in keymaps_dict:
#             keymaps_dict[keymap.name] = []
#         keymaps_dict[keymap.name].append(kmi_to_dict(kmi))

#     return keymaps_dict


# def keymaps_from_json(keymap: bpy.types.KeyMap, keymap_dict: dict):
#     """Create Keymaps populates with KeyMapItems from a dictionary. Used to load keymap from json file"""
#     kmi_list = keymap_dict.get(keymap.name)
#     if kmi_list == None:
#         print('Keymap not found in dictionary')
#     for kmi in kmi_list:
#         kmi_from_dict(keymap, kmi)


# def get_keymap_filepath() -> Path:
#     """Returns path to addon's keymap json file"""
#     addon_path = None
#     # filename = f'mastro_keymap_{bpy.app.version[0]}_{bpy.app.version[1]}.json'
#     filename = f'mastro_keymap.json'

#     for mod in addon_utils.modules():
#         if mod.bl_info['name'] == 'MaStro':
#             addon_path = Path(mod.__file__).parent.resolve()
#             break
#     if not addon_path:
#         return None
#     return Path(addon_path, filename)


# def ensure_keymaps():
#     """Reload keymaps. Useful for when Blender doesn't have access to user keymaps when starting"""
#     unregister()
#     register()




# def find_keymap_items(user_config_keymaps, idname, keymap_names=[]) -> tuple[bpy.types.KeyMapItem]:
#     """
#     Find all KeyMapItems with idname in the given keyconfig.
#     Will return a tuple of (keymap, keymap_item)
#     """
#     kmis = []
#     for keymap in user_config_keymaps:
#         if keymap.name not in keymap_names and len(keymap_names) > 0:
#             continue

#         for kmi in keymap.keymap_items:
#             if kmi.idname == idname:
#                 kmis.append(kmi)
#     return tuple(kmis)


def register():
    # handle the keymap
    wm = bpy.context.window_manager

    # user_config_keymaps = wm.keyconfigs.user.keymaps
    # user_kmis = find_keymap_items(user_config_keymaps, "transform.translate", keymap_names)
    # # filter out specific shortut that breaks cursor behaviour
    # user_kmis = tuple([
    #     kmi for kmi in user_kmis
    #     if not (kmi.value == "CLICK_DRAG" and kmi.idname == "transform.translate" and kmi.type == "RIGHTMOUSE")
    # ])
    # for k in user_kmis:
    #     k.active = False
    # print()
    user_config_keymaps = wm.keyconfigs.user.keymaps
    for keymap in user_config_keymaps:
        if keymap.name in keymap_names:
            for kmi in keymap.keymap_items:
                if kmi.idname == "transform.translate" and kmi.type == "G":
                    kmi.active = False
                    # print(keymap.name, kmi.idname, kmi.type, kmi.active)
                elif kmi.idname == "transform.rotate" and kmi.type == "R":
                    kmi.active = False
                    # print(keymap.name, kmi.idname, kmi.type, kmi.active)
                
    # Note that in background mode (no GUI available), keyconfigs are not available either,
    # so we have to check this to avoid nasty errors in background case.
    kc = wm.keyconfigs.addon
    if kc:
        # keyconfigs = wm.keyconfigs
        # for k in user_kmis:
            # k.active = False
            # print(km.name, km.space_type)

        km = wm.keyconfigs.addon.keymaps.new(name='Mesh', space_type='EMPTY')
        kmi = km.keymap_items.new("transform.translate_xy_constraint", 'G', 'PRESS')
        addon_keymaps.append((km, kmi))
        km = wm.keyconfigs.addon.keymaps.new(name='Object Mode', space_type='EMPTY')
        kmi = km.keymap_items.new("transform.translate_xy_constraint", 'G', 'PRESS')
        addon_keymaps.append((km, kmi))
        
        km = wm.keyconfigs.addon.keymaps.new(name='Mesh', space_type='EMPTY')
        kmi = km.keymap_items.new("transform.rotate_xy_constraint", 'R', 'PRESS')
        addon_keymaps.append((km, kmi))
        km = wm.keyconfigs.addon.keymaps.new(name='Object Mode', space_type='EMPTY')
        kmi = km.keymap_items.new("transform.rotate_xy_constraint", 'R', 'PRESS')
        addon_keymaps.append((km, kmi))
        
    # print()
    # print()
    # user_config_keymaps = wm.keyconfigs.user.keymaps
    # for keymap in user_config_keymaps:
    #     if keymap.name in keymap_names:
    #         for kmi in keymap.keymap_items:
    #             if (kmi.idname == "transform.translate" or kmi.idname == "transform.translate_xy_constraint") and kmi.type == "G":
    #                 print("post", keymap.name, kmi.idname, kmi.type, kmi.active)    
    #             if (kmi.idname == "transform.rotate" or kmi.idname == "transform.rotate_xy_constraint") and kmi.type == "R":
    #                 print("post", keymap.name, kmi.idname, kmi.type, kmi.active)    
    # for keymap in addon_keymaps:
    #     for kmi in keymap.kmi:
    #         print("post", kmi.name)
        
       
        
        
    
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
                    
    
    
# def register():
#     """
#     Set up keymaps for auto-constraint operators.
#     Find, disable and copy user keymaps for translate/rotate/duplicate/extrude operations
#     Sometimes when Blender starts it doesn't have access to user keymaps. There are two fallbacks:
#     1. We call 'ensure_keymaps' on a 2 second timer
#     2. We save keymap to a json file every time it's enabled and load from this when we can't find user keymaps
#     """
#     wm = bpy.context.window_manager
#     keyconfigs = wm.keyconfigs

#     addon_keyconfig = keyconfigs.addon
#     # For running in headless - skip adding keymaps
#     if not addon_keyconfig:
#         return
    
#     # Create addon keymap
#     # addon_keymap = addon_keyconfig.keymaps.new(name='3D View Generic', space_type='VIEW_3D', region_type='WINDOW')
#     addon_keymap_3dview = addon_keyconfig.keymaps.new(name='3D View Generic', space_type='VIEW_3D', region_type='WINDOW')
#     # addon_keymap_mesh = addon_keyconfig.keymaps.new(name='Mesh', space_type='EMPTY', region_type='WINDOW')

#     # Get user keymaps
#     user_config_keymaps = keyconfigs.user.keymaps

#     # If there isn't access to user keymaps when starting. Load from file instead
#     if len(user_config_keymaps) == 0:
#         # Create keymap for toolbar popup. Apparently doesn't work with addon keymap
#         user_toolbar_keymap = user_config_keymaps.new('Toolbar Popup')

#         with open(get_keymap_filepath(), 'r') as f:
#             keymap_dict = json.load(f)
#         # keymaps_from_json(addon_keymap, keymap_dict)
#         keymaps_from_json(addon_keymap_3dview, keymap_dict)
#         # keymaps_from_json(addon_keymap_mesh, keymap_dict)
#         keymaps_from_json(user_toolbar_keymap, keymap_dict)
#         return

#     # Replace default operator keymaps with addon operators
#     # for key, item in replacement_operators.items():
#     #     replace_keymap_items(user_config_keymaps, key, keymap_names, addon_keymap, item)
        
#     for old_op, new_op in replacement_operators.items():
#         replace_keymap_items(user_config_keymaps, old_op, ['3D View', 'Object Mode'], addon_keymap_3dview, new_op)
#         # replace_keymap_items(user_config_keymaps, old_op, ['Mesh'], addon_keymap_mesh, new_op)
        

#     # Re-add tool menu shortcuts, for some reason this doesn't work when added to addon keymaps so we'll just use the user keymaps
#     user_toolbar_keymap = keyconfigs.user.keymaps.new('Toolbar Popup')
#     try:
#         move_kmi = [kmi for kmi in find_keymap_items(user_config_keymaps, 'transform.translate', keymap_names) if kmi.map_type == 'KEYBOARD'][0]
#     except IndexError:
#         move_kmi = None
#     try:
#         rotate_kmi = [kmi for kmi in find_keymap_items(user_config_keymaps, 'transform.rotate', keymap_names) if kmi.map_type == 'KEYBOARD'][0]
#     except IndexError:
#         rotate_kmi = None

#     if move_kmi:
#     # tool menu move
#         move_kmi = user_toolbar_keymap.keymap_items.new('wm.tool_set_by_id',
#             type = move_kmi.type,
#             value = 'PRESS',
#             head = True
#             )
#         move_kmi.properties.get('name')
#         move_kmi.properties.name = 'builtin.move'
#         addon_keymaps.append((user_toolbar_keymap, move_kmi))

#     if rotate_kmi:
#         # tool menu rotate
#         rotate_kmi = user_toolbar_keymap.keymap_items.new('wm.tool_set_by_id',
#             type = rotate_kmi.type,
#             value = 'PRESS',
#             head = True
#             )
#         rotate_kmi.properties.get('name')
#         rotate_kmi.properties.name = 'builtin.rotate'
#         addon_keymaps.append((user_toolbar_keymap, rotate_kmi))

#     # Dump keymap dictionary to json file
#     # The Blender Keymap is not always available on startup, this file will be used as a second fallback to load user hotkeys
#     keymap_dict = keymaps_to_json(addon_keymaps)
#     file_path = get_keymap_filepath()
#     with open(file_path, 'w') as f:
#         json.dump(keymap_dict, f)


# def unregister():
#     """Re-enable previous hotkeys. Remove all addon hotkeys"""
#     wm = bpy.context.window_manager
#     user_config_keymaps = wm.keyconfigs.user.keymaps

#     # Find and re-enable previous keymaps
#     kmis = []
#     for idname in replacement_operators:
#         kmis += find_keymap_items(user_config_keymaps, idname, keymap_names)
#     for kmi in kmis:
#         kmi.active = True

#     # Remove addon keymaps
#     for km, kmi in addon_keymaps:
#         if kmi.idname in km.keymap_items:
#             km.keymap_items.remove(kmi)
#     addon_keymaps.clear()