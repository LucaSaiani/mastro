import bpy
 
from ..Operators.mastro_2D.MESH_OT_Move_Active_Vertex import MESH_OT_Move_Active_Vertex
from ..Operators.mastro_2D.TRANSFORM_OT_Set_Orientation import TRANSFORM_OT_Mastro_Set_Orientation
from ..Operators.mastro_constraints.TRANSFORM_OT_XY_Constraint import TRANSFORM_OT_Mastro_Translate_XY_Constraint, TRANSFORM_OT_Mastro_Rotate_XY_Constraint

from ..Nodes.operators.NODE_OT_Rename_Reroute import NODE_OT_Mastro_Rename_Reroute

from ..Operators.mastro_cad.MESH_OT_EditCAD import MESH_OT_MaStroCad_EditCAD



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
    kmi_pie = km.keymap_items.new('wm.call_menu_pie', 'C', 'PRESS', alt=True)
    kmi_pie.properties.name = 'MESH_MT_MaStroCad_Pie'
    addon_keymaps.extend([
        # MaStroCad EditCAD is registered first: its poll() only returns True
        # when a valid CAD rectangle/circle is the active element, so
        # Move_Active_Vertex's Alt+G keeps working in all other cases.
        (km, km.keymap_items.new(MESH_OT_MaStroCad_EditCAD.bl_idname, 'G', 'PRESS', alt=True)),
        (km, km.keymap_items.new(TRANSFORM_OT_Mastro_Translate_XY_Constraint.bl_idname, 'G', 'PRESS')),
        (km, km.keymap_items.new(TRANSFORM_OT_Mastro_Rotate_XY_Constraint.bl_idname, 'R', 'PRESS')),
        (km, km.keymap_items.new(MESH_OT_Move_Active_Vertex.bl_idname, 'G', 'PRESS', alt=True)),
        (km, km.keymap_items.new(TRANSFORM_OT_Mastro_Set_Orientation.bl_idname, 'COMMA', 'PRESS', alt=True)),
        (km, kmi_pie),
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
    