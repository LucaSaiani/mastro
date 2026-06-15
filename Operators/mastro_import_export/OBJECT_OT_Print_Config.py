import bpy
from bpy.types import Operator


class MASTRO_OT_PrintSetAdd(Operator):
    bl_idname = "mastro_print.set_add"
    bl_label = "Add Schedule"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        pp = context.scene.mastro_print_props
        print_set = pp.print_sets.add()
        print_set.name = "Schedule"
        pp.active_set_index = len(pp.print_sets) - 1
        return {'FINISHED'}


class MASTRO_OT_PrintSetRemove(Operator):
    bl_idname = "mastro_print.set_remove"
    bl_label = "Remove Schedule"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        pp = context.scene.mastro_print_props
        idx = pp.active_set_index
        if idx < 0 or idx >= len(pp.print_sets):
            return {'CANCELLED'}
        pp.print_sets.remove(idx)
        pp.active_set_index = max(0, idx - 1)
        return {'FINISHED'}


class MASTRO_OT_PrintSetMoveUp(Operator):
    bl_idname = "mastro_print.set_move_up"
    bl_label = "Move Schedule Up"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        pp = context.scene.mastro_print_props
        idx = pp.active_set_index
        if idx <= 0:
            return {'CANCELLED'}
        pp.print_sets.move(idx, idx - 1)
        pp.active_set_index = idx - 1
        return {'FINISHED'}


class MASTRO_OT_PrintSetMoveDown(Operator):
    bl_idname = "mastro_print.set_move_down"
    bl_label = "Move Schedule Down"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        pp = context.scene.mastro_print_props
        idx = pp.active_set_index
        if idx >= len(pp.print_sets) - 1:
            return {'CANCELLED'}
        pp.print_sets.move(idx, idx + 1)
        pp.active_set_index = idx + 1
        return {'FINISHED'}


class MASTRO_OT_PrintSetParamAdd(Operator):
    bl_idname = "mastro_print.set_param_add"
    bl_label = "Add Column to Schedule"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from ...UI.properties.property_classes_print import _available_param_names

        pp = context.scene.mastro_print_props
        idx = pp.active_set_index
        if idx < 0 or idx >= len(pp.print_sets):
            return {'CANCELLED'}
        print_set = pp.print_sets[idx]

        set_names = {param.name for param in print_set.params}
        available_names = _available_param_names(context, pp.scan_scope)
        new_names = [name for name in available_names if name not in set_names]
        if not new_names:
            return {'CANCELLED'}

        param = print_set.params.add()
        param.name = new_names[0]
        param.param_name = new_names[0]
        print_set.active_param_index = len(print_set.params) - 1
        return {'FINISHED'}


class MASTRO_OT_PrintSetParamRemove(Operator):
    bl_idname = "mastro_print.set_param_remove"
    bl_label = "Remove Column from Schedule"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        pp = context.scene.mastro_print_props
        idx = pp.active_set_index
        if idx < 0 or idx >= len(pp.print_sets):
            return {'CANCELLED'}
        print_set = pp.print_sets[idx]

        param_idx = print_set.active_param_index
        if param_idx < 0 or param_idx >= len(print_set.params):
            return {'CANCELLED'}
        print_set.params.remove(param_idx)
        print_set.active_param_index = max(0, param_idx - 1)
        return {'FINISHED'}


class MASTRO_OT_PrintSetParamMove(Operator):
    bl_idname = "mastro_print.set_param_move"
    bl_label = "Move Column in Schedule"
    bl_options = {'REGISTER', 'UNDO'}

    direction: bpy.props.EnumProperty(
        items=(('UP', "Up", ""), ('DOWN', "Down", "")),
        default='UP',
    )

    def execute(self, context):
        pp = context.scene.mastro_print_props
        idx = pp.active_set_index
        if idx < 0 or idx >= len(pp.print_sets):
            return {'CANCELLED'}
        print_set = pp.print_sets[idx]

        param_idx = print_set.active_param_index
        if self.direction == 'UP':
            if param_idx <= 0:
                return {'CANCELLED'}
            print_set.params.move(param_idx, param_idx - 1)
            print_set.active_param_index = param_idx - 1
        else:
            if param_idx >= len(print_set.params) - 1:
                return {'CANCELLED'}
            print_set.params.move(param_idx, param_idx + 1)
            print_set.active_param_index = param_idx + 1

        return {'FINISHED'}


class OBJECT_OT_Mastro_Print_Config(Operator):
    """Configure the columns and grouping used to print MaStro mass/block data"""
    bl_idname = "object.mastro_print_config"
    bl_label = "Configure Print"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.mastro_print_configured()
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=480)

    def draw(self, context):
        layout = self.layout
        pp = context.scene.mastro_print_props

        layout.label(text="Schedules")
        row = layout.row()
        row.template_list(
            "MASTRO_UL_Print_Sets", "",
            pp, "print_sets",
            pp, "active_set_index",
            rows=3,
        )
        col = row.column(align=True)
        col.operator("mastro_print.set_add", text="", icon='ADD')
        col.operator("mastro_print.set_remove", text="", icon='REMOVE')
        col.separator()
        col.operator("mastro_print.set_move_up", text="", icon='TRIA_UP')
        col.operator("mastro_print.set_move_down", text="", icon='TRIA_DOWN')

        idx = pp.active_set_index
        if 0 <= idx < len(pp.print_sets):
            print_set = pp.print_sets[idx]

            layout.label(text="Attributes")
            row = layout.row()
            row.template_list(
                "MASTRO_UL_Print_Set_Params", "",
                print_set, "params",
                print_set, "active_param_index",
                rows=3,
            )
            col = row.column(align=True)
            col.operator("mastro_print.set_param_add", text="", icon='ADD')
            col.operator("mastro_print.set_param_remove", text="", icon='REMOVE')
            col.separator()
            move_up = col.operator("mastro_print.set_param_move", text="", icon='TRIA_UP')
            move_up.direction = 'UP'
            move_down = col.operator("mastro_print.set_param_move", text="", icon='TRIA_DOWN')
            move_down.direction = 'DOWN'
