import bpy
 
from ..Operators.MESH_OT_Move_Active_Vertex import MESH_OT_Move_Active_Vertex
from ..Operators.TRANSFORM_OT_Set_Orientation import TRANSFORM_OT_Mastro_Set_Orientation
from ..Nodes.Operators.NODE_OT_Rename_Reroute import NODE_OT_mastro_rename_reroute

from .operators import TRANSFORM_OT_rotate_xy_constraint, TRANSFORM_OT_translate_xy_constraint


addon_keymaps = []

def register():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if not kc:
        return

    # Object mode
    km = kc.keymaps.new(name='Object Mode', space_type='EMPTY')
    addon_keymaps.extend([
        (km, km.keymap_items.new(TRANSFORM_OT_translate_xy_constraint.bl_idname, 'G', 'PRESS')),
        (km, km.keymap_items.new(TRANSFORM_OT_rotate_xy_constraint.bl_idname, 'R', 'PRESS')),
    ])

    # Mesh mode
    km = kc.keymaps.new(name='Mesh', space_type='EMPTY')
    addon_keymaps.extend([
        (km, km.keymap_items.new(TRANSFORM_OT_translate_xy_constraint.bl_idname, 'G', 'PRESS')),
        (km, km.keymap_items.new(TRANSFORM_OT_rotate_xy_constraint.bl_idname, 'R', 'PRESS')),
        (km, km.keymap_items.new(MESH_OT_Move_Active_Vertex.bl_idname, 'G', 'PRESS', alt=True)),
        (km, km.keymap_items.new(TRANSFORM_OT_Mastro_Set_Orientation.bl_idname, 'COMMA', 'PRESS', alt=True)),
    ])
    
    # Rename Reroute node
    km = kc.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')
    addon_keymaps.extend([
        (km, km.keymap_items.new(NODE_OT_mastro_rename_reroute.bl_idname, 'F2', 'PRESS', shift=True, ctrl=True)),
    ])
        
def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    