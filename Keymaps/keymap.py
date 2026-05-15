import bpy
 
from ..Operators.MESH_OT_Move_Active_Vertex import MESH_OT_Move_Active_Vertex
from ..Operators.TRANSFORM_OT_Set_Orientation import TRANSFORM_OT_Mastro_Set_Orientation
from ..Operators.TRANSFORM_OT_XY_Constraint import TRANSFORM_OT_Mastro_Translate_XY_Constraint, TRANSFORM_OT_Mastro_Rotate_XY_Constraint

from ..Nodes.operators.NODE_OT_Rename_Reroute import NODE_OT_Mastro_Rename_Reroute



addon_keymaps = []

def register():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if not kc:
        return

    # Object mode
    km = kc.keymaps.new(name='Object Mode', space_type='EMPTY')
    addon_keymaps.extend([
        (km, km.keymap_items.new(TRANSFORM_OT_Mastro_Translate_XY_Constraint.bl_idname, 'G', 'PRESS')),
        (km, km.keymap_items.new(TRANSFORM_OT_Mastro_Rotate_XY_Constraint.bl_idname, 'R', 'PRESS')),
    ])

    # Mesh mode
    km = kc.keymaps.new(name='Mesh', space_type='EMPTY')
    addon_keymaps.extend([
        (km, km.keymap_items.new(TRANSFORM_OT_Mastro_Translate_XY_Constraint.bl_idname, 'G', 'PRESS')),
        (km, km.keymap_items.new(TRANSFORM_OT_Mastro_Rotate_XY_Constraint.bl_idname, 'R', 'PRESS')),
        (km, km.keymap_items.new(MESH_OT_Move_Active_Vertex.bl_idname, 'G', 'PRESS', alt=True)),
        (km, km.keymap_items.new(TRANSFORM_OT_Mastro_Set_Orientation.bl_idname, 'COMMA', 'PRESS', alt=True)),
    ])
    
    # Rename Reroute node
    km = kc.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')
    addon_keymaps.extend([
        (km, km.keymap_items.new(NODE_OT_Mastro_Rename_Reroute.bl_idname, 'F2', 'PRESS', shift=True, ctrl=True)),
    ])
        
def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    