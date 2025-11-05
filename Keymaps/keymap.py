import bpy
 
from ..Operators.MESH_OT_move_active_vertex_modal import MESH_OT_move_active_vertex_modal
from ..mastro_xy_constraint_operators import TRANSFORM_OT_rotate_xy_constraint, TRANSFORM_OT_translate_xy_constraint

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
        (km, km.keymap_items.new(MESH_OT_move_active_vertex_modal.bl_idname, 'G', 'PRESS', alt=True)),
    ])
        
def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    