import bpy

from ..operators import classes as MASTROCUSTOMCLASSES


# ── helpers ───────────────────────────────────────────────────────────────────

def _local_gn_groups(prefix):
    """Return local (non-linked) Geometry node groups whose name starts with prefix.

    Note: ng.type == 'GEOMETRY' is the runtime value for GeometryNodeTree groups.
    This is different from space_data.tree_type which uses 'GeometryNodeTree'."""
    return sorted(
        (ng for ng in bpy.data.node_groups
         if ng.name.startswith(prefix)
         and ng.library is None
         and ng.type == 'GEOMETRY'),
        key=lambda ng: ng.name,
    )

def _local_shader_groups(prefix):
    """Return local (non-linked) Shader node groups whose name starts with prefix."""
    return sorted(
        (ng for ng in bpy.data.node_groups
         if ng.name.startswith(prefix)
         and ng.library is None
         and ng.type == 'SHADER'),
        key=lambda ng: ng.name,
    )

def _add_group_items(layout, groups):
    """Add one menu entry per group, each invoking node.mastro_add_group."""
    for ng in groups:
        op = layout.operator("node.mastro_add_group", text=ng.name)
        op.group_name = ng.name


# ── GN submenus ───────────────────────────────────────────────────────────────

class MASTRO_MT_gn_filter_by(bpy.types.Menu):
    """Submenu listing local GN Filter By node groups (created by init_nodes)."""
    bl_idname = "MASTRO_MT_gn_filter_by"
    bl_label  = "Filter By"

    def draw(self, context):
        _add_group_items(self.layout, _local_gn_groups("MaStro Filter by"))


class MASTRO_MT_gn_separate_by(bpy.types.Menu):
    """Submenu listing local GN Separate Geometry By node groups (created by init_nodes)."""
    bl_idname = "MASTRO_MT_gn_separate_by"
    bl_label  = "Separate By"

    def draw(self, context):
        _add_group_items(self.layout, _local_gn_groups("MaStro Separate Geometry by"))


# ── GN top-level menu ─────────────────────────────────────────────────────────

class MASTRO_MT_add_gn_menu(bpy.types.Menu):
    """'MaStro Local' entry in Add → Geometry Nodes.

    Shows three sections:
      - Filter By / Separate By submenus (dynamic groups from init_nodes)
      - Custom GN node types registered as Python classes (bl_idname has no dot)
      - All other local MaStro GN groups (appended from mastro.blend)"""
    bl_idname = "MASTRO_MT_add_gn_menu"
    bl_label  = "MaStro Local"

    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'GeometryNodeTree'

    def draw(self, context):
        layout = self.layout

        layout.menu("MASTRO_MT_gn_filter_by",  text="Filter By")
        layout.menu("MASTRO_MT_gn_separate_by", text="Separate By")

        # Custom GN node types: true Blender node classes registered via Python.
        # Operators have "node." in their bl_idname; node types do not.
        custom_nodes = [
            cls for cls in MASTROCUSTOMCLASSES
            if hasattr(cls, 'bl_idname')
            and '.' not in cls.bl_idname
            and '_GN_' in cls.__name__.upper()
        ]
        if custom_nodes:
            layout.separator()
            for cls in custom_nodes:
                op = layout.operator("node.add_node", text=cls.bl_label)
                op.type = cls.bl_idname
                op.use_transform = True

        # Local GN groups appended from mastro.blend, excluding the ones
        # already covered by the Filter By and Separate By submenus.
        other_groups = [
            ng for ng in _local_gn_groups("MaStro")
            if not ng.name.startswith("MaStro Filter by")
            and not ng.name.startswith("MaStro Separate Geometry by")
        ]
        if other_groups:
            layout.separator()
            _add_group_items(layout, other_groups)


# ── Shader submenus ───────────────────────────────────────────────────────────

class MASTRO_MT_shader_filter_by(bpy.types.Menu):
    """Submenu listing local Shader Filter By node groups (created by init_nodes).

    Note: shader filter groups use lowercase 'f' — 'MaStro filter by …'."""
    bl_idname = "MASTRO_MT_shader_filter_by"
    bl_label  = "Filter By"

    def draw(self, context):
        _add_group_items(self.layout, _local_shader_groups("MaStro filter by"))


# ── Shader top-level menu ─────────────────────────────────────────────────────

class MASTRO_MT_add_shader_menu(bpy.types.Menu):
    """'MaStro Local' entry in Add → Shader Editor."""
    bl_idname = "MASTRO_MT_add_shader_menu"
    bl_label  = "MaStro Local"

    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'ShaderNodeTree'

    def draw(self, context):
        layout = self.layout
        layout.menu("MASTRO_MT_shader_filter_by", text="Filter By")

        other_groups = [
            ng for ng in _local_shader_groups("MaStro")
            if not ng.name.startswith("MaStro filter by")
        ]
        if other_groups:
            layout.separator()
            _add_group_items(layout, other_groups)


# ── append / remove ───────────────────────────────────────────────────────────

def _gn_menu_draw(self, context):
    if context.space_data.tree_type == 'GeometryNodeTree':
        self.layout.menu("MASTRO_MT_add_gn_menu", text="MaStro Local")

def _shader_menu_draw(self, context):
    if context.space_data.tree_type == 'ShaderNodeTree':
        self.layout.menu("MASTRO_MT_add_shader_menu", text="MaStro Local")

def _nodemenu_append(self, context):
    self.layout.separator()
    self.layout.operator("mastro.node_purge_unused", text="Purge Unused Nodes")


def append_menus():
    bpy.types.NODE_MT_add.append(_gn_menu_draw)
    bpy.types.NODE_MT_add.append(_shader_menu_draw)
    bpy.types.NODE_MT_node.append(_nodemenu_append)

def remove_menus():
    for fn in (_gn_menu_draw, _shader_menu_draw, _nodemenu_append):
        for menu in (bpy.types.NODE_MT_add, bpy.types.NODE_MT_node):
            try:
                menu.remove(fn)
            except Exception:
                pass
