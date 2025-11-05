import bpy 

from .. import PREFS_KEY
def get_prefs():
    # return bpy.context.preferences.addons[__package__].preferences
    return bpy.context.preferences.addons[PREFS_KEY].preferences