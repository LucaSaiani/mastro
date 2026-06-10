import sys
import bpy
from bpy.types import Panel, Operator, UIList
from ...properties.property_classes_cad import _next_layer_id
from ....Icons import get_wide_icon_id_colored, get_color_swatch_icon_id, get_custom_pattern_icon_id



class PROPERTIES_UL_MaStroCad_Layers(UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=False)
            row.label(text="Id: %d" % item.layer_id)
            name_col = row.column()
            name_col.prop(item, "name", text="", emboss=False)
            row.prop(item, "visible", text="",
                     icon='HIDE_OFF' if item.visible else 'HIDE_ON')
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text=item.name)

    def draw_filter(self, context, layout):
        pass

    def filter_items(self, context, data, propname):
        items = getattr(data, propname)
        return [self.bitflag_filter_item] * len(items), []



class PROPERTIES_OT_MaStroCad_Add_Layer(Operator):
    """Add a new layer."""
    bl_idname = "mastrocad.add_layer"
    bl_label  = "Add Layer"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from ....Utils.mastro_cad.sync_layer_groups import maybe_sync

        layers = context.scene.mastro_cad_layers
        l = layers.add()
        l.layer_id = _next_layer_id(layers)
        l.name     = "Layer"
        context.scene.mastro_cad_layer_index = len(layers) - 1
        maybe_sync(context)
        return {'FINISHED'}


class PROPERTIES_OT_MaStroCad_Remove_Layer(Operator):
    """Remove the selected layer."""
    bl_idname = "mastrocad.remove_layer"
    bl_label  = "Remove Layer"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from ....Utils.mastro_cad.sync_layer_groups import maybe_sync

        layers = context.scene.mastro_cad_layers
        idx    = context.scene.mastro_cad_layer_index
        if not (0 <= idx < len(layers)):
            return {'CANCELLED'}
        if layers[idx].locked:
            return {'CANCELLED'}
        layers.remove(idx)
        context.scene.mastro_cad_layer_index = max(0, idx - 1)
        maybe_sync(context)
        return {'FINISHED'}


class PROPERTIES_OT_MaStroCad_Sync_Layers(Operator):
    """Sync vertex groups of all MaStro drawing objects to match scene layers."""
    bl_idname = "mastrocad.sync_layer_groups"
    bl_label  = "Update"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from ....Utils.mastro_cad.sync_layer_groups import sync_layer_groups

        sync_layer_groups(context)
        return {'FINISHED'}


class PROPERTIES_OT_MaStroCad_Assign_Layer(Operator):
    """Assign the active layer to all selected edges of the active MaStro drawing mesh."""
    bl_idname = "mastrocad.assign_layer_to_edges"
    bl_label  = "Assign Layer to Selected Edges"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (context.mode == 'EDIT_MESH' and
                obj is not None and
                obj.data is not None and
                bool(obj.data.get("MaStro drawing mesh")))

    layer_index: bpy.props.IntProperty(default=-1, options={'HIDDEN'})

    def execute(self, context):
        import bmesh
        from ....Utils.mastro_cad.update_bmesh_drawing_attributes import update_bmesh_drawing_attributes

        scene  = context.scene
        layers = scene.mastro_cad_layers
        idx    = self.layer_index if self.layer_index >= 0 else scene.mastro_cad_layer_index
        if not (0 <= idx < len(layers)):
            return {'CANCELLED'}
        layer_id = layers[idx].layer_id

        for obj in context.objects_in_mode:
            if obj.type != 'MESH':
                continue
            if not obj.data.get("MaStro drawing mesh"):
                continue

            bm = bmesh.from_edit_mesh(obj.data)
            bm.edges.ensure_lookup_table()

            layer_attr = bm.edges.layers.int.get("mastro_drawing_layer")
            if layer_attr is None:
                continue

            for edge in bm.edges:
                if edge.select:
                    edge[layer_attr] = layer_id

            bmesh.update_edit_mesh(obj.data)

        update_bmesh_drawing_attributes(context, {layer_id})
        return {'FINISHED'}


class PROPERTIES_OT_MaStroCad_Move_Layer(Operator):
    """Move the selected layer up or down."""
    bl_idname = "mastrocad.move_layer"
    bl_label  = "Move Layer"
    bl_options = {'REGISTER', 'UNDO'}

    direction: bpy.props.EnumProperty(items=[('UP', "Up", ""), ('DOWN', "Down", "")])

    def execute(self, context):
        layers  = context.scene.mastro_cad_layers
        idx     = context.scene.mastro_cad_layer_index
        new_idx = idx - 1 if self.direction == 'UP' else idx + 1
        if not (0 <= new_idx < len(layers)):
            return {'CANCELLED'}
        layers.move(idx, new_idx)
        context.scene.mastro_cad_layer_index = new_idx
        return {'FINISHED'}


def _draw_layers_panel(layout, context):
    scene = context.scene
    idx   = scene.mastro_cad_layer_index

    row = layout.row()
    row.template_list(
        "PROPERTIES_UL_MaStroCad_Layers", "",
        scene, "mastro_cad_layers",
        scene, "mastro_cad_layer_index",
        rows=4,
    )
    col = row.column(align=True)
    col.operator("mastrocad.add_layer", icon='ADD', text="")
    rm_row = col.row()
    rm_row.enabled = not (0 <= idx < len(scene.mastro_cad_layers) and scene.mastro_cad_layers[idx].locked)
    rm_row.operator("mastrocad.remove_layer", icon='REMOVE', text="")
    col.separator()
    col.operator("mastrocad.move_layer", icon='TRIA_UP',   text="").direction = 'UP'
    col.operator("mastrocad.move_layer", icon='TRIA_DOWN', text="").direction = 'DOWN'

    row = layout.row(align=True)
    row.operator("mastrocad.sync_layer_groups")
    row.prop(context.window_manager, "mastro_cad_auto_update_layers", text="", icon='FILE_REFRESH')
    row.prop(scene, "mastro_cad_drawing_black_mode", text="", icon='SHADING_SOLID', toggle=True)

    if not (0 <= idx < len(scene.mastro_cad_layers)):
        return
    layer = scene.mastro_cad_layers[idx]
    box   = layout.box()
    split = box.split(factor=0.6)

    props = split.column()
    props.use_property_split    = True
    props.use_property_decorate = False
    props.prop(layer, "pen_enum",     text="Pen")
    props.prop(layer, "pattern_enum", text="Line Type")
    colour_row = props.row(align=True)
    colour_row.prop(layer, "color", text="Colour")
    link_icon = 'LINKED' if layer.use_pen_color else 'LOOP_BACK'
    colour_row.prop(layer, "use_pen_color", text="", icon=link_icon, toggle=True)
    props.prop(layer, "black")
    desc_col = box.column()
    desc_col.scale_y = 1.0
    desc_col.textbox(layer, "description", placeholder="Description")

    pat = next((p for p in scene.mastro_cad_dash_patterns if p.pattern_id == layer.pattern_id), None)
    if pat is not None:
        pen       = next((p for p in scene.mastro_cad_pens if p.pen_id == layer.pen_id), None)
        color_rgb = tuple(int(c * 255) for c in layer.color[:3])
        thickness = pen.thickness if pen else 0.5
        split.column().template_icon(
            icon_value=get_wide_icon_id_colored(pat, color_rgb, thickness),
            scale=5,
        )


class PROPERTIES_PT_MaStroCad_Layers(Panel):
    """Scene → MaStro → Drawing → Layers."""
    bl_space_type  = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_label       = "Layers"
    bl_parent_id   = "PROPERTIES_PT_MaStroCad_Drawing"
    bl_options     = {'DEFAULT_CLOSED'}
    bl_context     = "scene"

    def draw(self, context):
        _draw_layers_panel(self.layout, context)


def _layer_icon_id(scene, layer):
    """Return the custom icon id for a layer, or 0 if not available.

    Layers whose pattern has use_custom_pattern=True get the static X icon
    instead of the generated line-type preview.
    """
    pat = next((p for p in scene.mastro_cad_dash_patterns
                if p.pattern_id == layer.pattern_id), None)
    if pat is None:
        return 0
    if pat.use_custom_pattern:
        return get_custom_pattern_icon_id()
    pen = next((p for p in scene.mastro_cad_pens
                if p.pen_id == layer.pen_id), None)
    color_rgb = tuple(int(c * 255) for c in layer.color[:3])
    thickness = pen.thickness if pen else 0.5
    return get_wide_icon_id_colored(pat, color_rgb, thickness)


class VIEW3D_UL_MaStroCad_Layers_Sidebar(UIList):
    """Layer list for the N-panel button: icon + name per row."""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        icon_id = _layer_icon_id(context.scene, item)
        if icon_id:
            layout.label(text=item.name, icon_value=icon_id)
        else:
            layout.label(text=item.name, icon='RENDERLAYERS')

    def draw_filter(self, context, layout):
        pass

    def filter_items(self, context, data, propname):
        items = getattr(data, propname)
        return [self.bitflag_filter_item] * len(items), []


# Single cache: refreshed each callback so icon IDs are always from the current
# _preview_coll. sys.intern() keeps the name strings alive in Python's intern
# table, preventing GC between the callback return and Blender's C-side read.
_layer_enum_cache = []


def _layer_enum_items(self, context):
    global _layer_enum_cache
    if context is None:
        return _layer_enum_cache or [("0", "No Layers", "", 0, 0)]
    scene = context.scene
    items = []
    for i, layer in enumerate(scene.mastro_cad_layers):
        icon_id = _layer_icon_id(scene, layer)
        ident   = sys.intern(str(i))
        name    = sys.intern(str(layer.name))
        items.append((ident, name, name, icon_id, i))
    _layer_enum_cache = items if items else [("0", "No Layers", "", 0, 0)]
    return _layer_enum_cache


def _layer_enum_get(self):
    return self.mastro_cad_viewport_layer_index


def _layer_enum_set(self, value):
    self.mastro_cad_viewport_layer_index = value


class VIEW3D_PT_MaStroCad_Layer_Picker(Panel):
    """Popover: icon_view grid for layer selection."""
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label       = "Choose Layer"
    bl_ui_units_x  = 10

    def draw(self, context):
        self.layout.template_icon_view(
            context.window_manager, "mastro_cad_layer_enum",
            show_labels=True, scale=5.0, scale_popup=5.0,
        )


class VIEW3D_PT_MaStroCad_Layers(Panel):
    """MaStro Drawing Layers — N-panel sidebar tab."""
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'MaStro'
    bl_label       = "Drawing Layers"
    bl_order       = 10

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (context.mode == 'EDIT_MESH' and
                obj is not None and
                obj.data is not None and
                bool(obj.data.get("MaStro drawing mesh")))

    def draw(self, context):
        layout = self.layout
        scene  = context.scene

        idx   = context.window_manager.mastro_cad_viewport_layer_index
        layer = scene.mastro_cad_layers[idx] if 0 <= idx < len(scene.mastro_cad_layers) else None
        if layer is not None:
            layout.label(text=layer.name, icon='RENDERLAYERS')

        layout.template_icon_view(
            context.window_manager, "mastro_cad_layer_enum",
            show_labels=True, scale=5.0, scale_popup=5.0,
        )

        if layer is None:
            return

        pen = next((p for p in scene.mastro_cad_pens
                    if p.pen_id == layer.pen_id), None)
        pat = next((p for p in scene.mastro_cad_dash_patterns
                    if p.pattern_id == layer.pattern_id), None)

        color_rgb = tuple(int(c * 255) for c in layer.color[:3])
        swatch_id = get_color_swatch_icon_id(color_rgb)
        pen_text  = f"{pen.name}  {pen.thickness:.2f} mm" if pen else "—"
        pat_text  = pat.name if pat else "—"

        box = layout.box()
        row = box.row(align=False)
        row.label(text=pen_text)
        row.label(text=pat_text)
        if swatch_id:
            row.label(text="", icon_value=swatch_id)
        else:
            row.label(text="", icon='COLOR')

        op = layout.operator("mastrocad.assign_layer_to_edges", icon='LAYER_ACTIVE')
        op.layer_index = idx


def register_wm_props():
    _layer_enum_cache.clear()
    bpy.types.WindowManager.mastro_cad_viewport_layer_index = bpy.props.IntProperty(
        name="Viewport Layer Index", default=0, min=0,
    )
    bpy.types.WindowManager.mastro_cad_layer_enum = bpy.props.EnumProperty(
        items=_layer_enum_items,
        get=_layer_enum_get,
        set=_layer_enum_set,
    )


def unregister_wm_props():
    _layer_enum_cache.clear()
    del bpy.types.WindowManager.mastro_cad_layer_enum
    del bpy.types.WindowManager.mastro_cad_viewport_layer_index
