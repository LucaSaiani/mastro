import bpy


# ── Rectangle submenu ─────────────────────────────────────────────────────────

class VIEW3D_MT_mastrocad_rectangle(bpy.types.Menu):
    bl_label  = "Rectangle"
    bl_idname = "VIEW3D_MT_mastrocad_rectangle"

    def draw(self, context):
        layout = self.layout
        layout.operator("mastrocad.rectangle_diagonal",
                        text="Diagonal",     icon='MESH_PLANE')
        layout.operator("mastrocad.rectangle_baseline",
                        text="Base Line",    icon='MESH_PLANE')
        layout.operator("mastrocad.rectangle_center",
                        text="Center",       icon='MESH_PLANE')
        layout.operator("mastrocad.rectangle_centerline",
                        text="Center Line",  icon='MESH_PLANE')


# ── Circle submenu ────────────────────────────────────────────────────────────

class VIEW3D_MT_mastrocad_circle(bpy.types.Menu):
    bl_label  = "Circle"
    bl_idname = "VIEW3D_MT_mastrocad_circle"

    def draw(self, context):
        layout = self.layout
        layout.operator("mastrocad.circle",
                        text="Center + Radius", icon='MESH_CIRCLE')
        layout.operator("mastrocad.circle3",
                        text="3 Inputs",        icon='MESH_CIRCLE')


# ── Append functions ──────────────────────────────────────────────────────────

def _draw_add_mesh(self, context):
    """Appended to Add > Mesh (object and edit mode)."""
    self.layout.menu("VIEW3D_MT_mastrocad_rectangle", icon='MESH_PLANE')
    self.layout.menu("VIEW3D_MT_mastrocad_circle",    icon='MESH_CIRCLE')


def _draw_edge_menu(self, context):
    """Appended to the Edge menu in edit mode."""
    layout = self.layout
    layout.separator()
    layout.operator("mastrocad.offset", text="Offset")
    layout.operator("mastrocad.fillet", text="Fillet")
    layout.operator("mastrocad.trim",           text="Trim / Extend")
    layout.operator("mastrocad.delete_segment", text="Delete Segment")


# ── Register / unregister ─────────────────────────────────────────────────────

def register():
    bpy.utils.register_class(VIEW3D_MT_mastrocad_rectangle)
    bpy.utils.register_class(VIEW3D_MT_mastrocad_circle)
    bpy.types.VIEW3D_MT_mesh_add.append(_draw_add_mesh)
    bpy.types.VIEW3D_MT_edit_mesh_edges.append(_draw_edge_menu)


def unregister():
    bpy.types.VIEW3D_MT_edit_mesh_edges.remove(_draw_edge_menu)
    bpy.types.VIEW3D_MT_mesh_add.remove(_draw_add_mesh)
    bpy.utils.unregister_class(VIEW3D_MT_mastrocad_circle)
    bpy.utils.unregister_class(VIEW3D_MT_mastrocad_rectangle)
