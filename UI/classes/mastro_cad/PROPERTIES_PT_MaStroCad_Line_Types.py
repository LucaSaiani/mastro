import bpy
from bpy.types import Panel, Operator, UIList
from ...properties.property_classes_cad import ensure_default_patterns, _next_pattern_id
from ....Icons import get_wide_icon_id


class PROPERTIES_UL_MaStroCad_Scene_Dash_Patterns(UIList):
    """Scene UIList — line types."""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            split = layout.split(factor=0.12)
            split.label(text="Id: %d" % index)
            row = split.row(align=True)
            if item.locked:
                row.label(text=item.name)
            else:
                row.prop(item, "name", text="", emboss=False)
            row.label(text="", icon='LOCKED' if item.locked else 'BLANK1')
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text=item.name)

    def draw_filter(self, context, layout):
        pass

    def filter_items(self, context, data, propname):
        items = getattr(data, propname)
        return [self.bitflag_filter_item] * len(items), []


class PROPERTIES_OT_MaStroCad_Add_Scene_Dash(Operator):
    """Add a new line type to this scene."""
    bl_idname = "mastrocad.scene_add_dash_pattern"
    bl_label  = "Add Line Type"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        patterns = context.scene.mastro_cad_dash_patterns
        p = patterns.add()
        p.pattern_id = _next_pattern_id(patterns)
        p.name = "Pattern"
        p.l1 = 1.0
        context.scene.mastro_cad_line_type_index = len(patterns) - 1
        return {'FINISHED'}


class PROPERTIES_OT_MaStroCad_Remove_Scene_Dash(Operator):
    """Remove the selected line type (locked patterns cannot be removed)."""
    bl_idname = "mastrocad.scene_remove_dash_pattern"
    bl_label  = "Remove Line Type"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene    = context.scene
        patterns = scene.mastro_cad_dash_patterns
        idx      = scene.mastro_cad_line_type_index
        if not (0 <= idx < len(patterns)):
            return {'CANCELLED'}
        if patterns[idx].locked:
            self.report({'WARNING'}, "This pattern cannot be removed")
            return {'CANCELLED'}
        removed_id = patterns[idx].pattern_id
        patterns.remove(idx)
        scene.mastro_cad_line_type_index = max(0, idx - 1)
        # Reassign layers that referenced the removed pattern to the smallest available one.
        valid_ids = {p.pattern_id for p in patterns}
        if valid_ids:
            fallback = min(valid_ids)
            for layer in scene.mastro_cad_layers:
                if layer.pattern_id == removed_id:
                    layer.pattern_id = fallback
        return {'FINISHED'}


class PROPERTIES_OT_MaStroCad_Move_Scene_Dash(Operator):
    """Move the selected line type up or down."""
    bl_idname = "mastrocad.scene_move_dash_pattern"
    bl_label  = "Move Line Type"
    bl_options = {'REGISTER', 'UNDO'}

    direction: bpy.props.EnumProperty(items=[('UP', "Up", ""), ('DOWN', "Down", "")])

    def execute(self, context):
        patterns = context.scene.mastro_cad_dash_patterns
        idx = context.scene.mastro_cad_line_type_index
        new_idx = idx - 1 if self.direction == 'UP' else idx + 1
        if not (0 <= new_idx < len(patterns)):
            return {'CANCELLED'}
        patterns.move(idx, new_idx)
        context.scene.mastro_cad_line_type_index = new_idx
        return {'FINISHED'}


class PROPERTIES_PT_MaStroCad_Line_Types(Panel):
    """Scene → MaStro → Drawing → Line Types."""
    bl_space_type  = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_label       = "Line Types"
    bl_parent_id   = "PROPERTIES_PT_MaStroCad_Drawing"
    bl_options     = {'DEFAULT_CLOSED'}
    bl_context     = "scene"

    def draw(self, context):
        scene  = context.scene
        layout = self.layout


        idx = scene.mastro_cad_line_type_index
        pat = scene.mastro_cad_dash_patterns[idx] if 0 <= idx < len(scene.mastro_cad_dash_patterns) else None

        split = layout.split(factor=0.7)

        # Left column (70%): list + buttons.
        left = split.column()
        list_row = left.row()
        list_row.template_list(
            "PROPERTIES_UL_MaStroCad_Scene_Dash_Patterns", "",
            scene, "mastro_cad_dash_patterns",
            scene, "mastro_cad_line_type_index",
            rows=4,
        )
        btn_col = list_row.column(align=True)
        btn_col.operator("mastrocad.scene_add_dash_pattern",    icon='ADD',    text="")
        btn_col.operator("mastrocad.scene_remove_dash_pattern", icon='REMOVE', text="")
        btn_col.separator()
        btn_col.operator("mastrocad.scene_move_dash_pattern", icon='TRIA_UP',   text="").direction = 'UP'
        btn_col.operator("mastrocad.scene_move_dash_pattern", icon='TRIA_DOWN', text="").direction = 'DOWN'

        # Right column (30%): icon preview.
        right = split.column()
        if pat is not None:
            right.template_icon(icon_value=get_wide_icon_id(pat), scale=6)

        # Full-width numeric fields below.
        if pat is not None:
            sub = layout.column(align=True)
            sub.enabled = not pat.locked
            fld = sub.grid_flow(row_major=True, columns=6, even_columns=True, align=True)
            fld.prop(pat, "l1", text="")
            fld.prop(pat, "g1", text="")
            fld.prop(pat, "l2", text="")
            fld.prop(pat, "g2", text="")
            fld.prop(pat, "l3", text="")
            fld.prop(pat, "g3", text="")
            layout.prop(pat, "use_custom_pattern")
