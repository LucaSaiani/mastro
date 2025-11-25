import bpy

###############################################################################    
########## Manage all the required updates fired by depsgraph_update  #########
###############################################################################

# when a new scene is created, it is necessary to initialize the
# variables related to the scene

known_scenes = set()


def check_new_scenes():
    from ...Utils.init_lists import init_lists
    global known_scenes
    current_scenes = set(bpy.data.scenes.keys())
    # print("current:")
    # for s in current_scenes: print(s)
    # print()
    new_scenes = current_scenes - known_scenes
    if new_scenes:
        for sceneName in new_scenes:
            print(f"Nuova scena creata: {sceneName}")
            init_lists(sceneName)
        known_scenes = current_scenes
    return()