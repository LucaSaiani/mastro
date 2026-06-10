import bpy
from bpy.types import Operator
from bpy.props import EnumProperty, IntProperty, StringProperty


def _active_prop(context):
    idx = context.scene.mastro_custom_property_name_list_index
    lst = context.scene.mastro_custom_property_name_list
    if 0 <= idx < len(lst):
        return lst[idx]
    return None


class OBJECT_OT_Mastro_String_Option_New(Operator):
    bl_idname = "mastro_string_options.new_item"
    bl_label  = "Add String Option"

    def execute(self, context):
        prop = _active_prop(context)
        if prop is None:
            return {'CANCELLED'}
        opts = prop.string_options
        item = opts.add()
        ids = [o.id for o in opts]
        item.id = max(ids) + 1 if len(ids) > 1 else 1
        prop.string_options_index = len(opts) - 1
        return {'FINISHED'}


class OBJECT_OT_Mastro_String_Option_Remove(Operator):
    bl_idname = "mastro_string_options.remove_item"
    bl_label  = "Remove String Option"

    def execute(self, context):
        prop = _active_prop(context)
        if prop is None:
            return {'CANCELLED'}
        opts = prop.string_options
        idx  = prop.string_options_index
        if 0 <= idx < len(opts):
            opts.remove(idx)
            prop.string_options_index = max(0, idx - 1)
        return {'FINISHED'}


class OBJECT_OT_Mastro_String_Option_Move(Operator):
    bl_idname = "mastro_string_options.move_item"
    bl_label  = "Move String Option"

    direction: EnumProperty(items=(('UP', 'Up', ''), ('DOWN', 'Down', '')))

    def execute(self, context):
        prop = _active_prop(context)
        if prop is None:
            return {'CANCELLED'}
        opts      = prop.string_options
        idx       = prop.string_options_index
        neighbor  = idx + (-1 if self.direction == 'UP' else 1)
        if 0 <= neighbor < len(opts):
            opts.move(neighbor, idx)
            prop.string_options_index = neighbor
        return {'FINISHED'}


class OBJECT_OT_Mastro_Set_String_Property(Operator):
    """Set the string value for a STRING custom property on the active object"""
    bl_idname  = "object.mastro_set_string_property"
    bl_label   = "Set String Property"
    bl_options = {'INTERNAL', 'UNDO'}

    property_id: IntProperty()
    string_id:   IntProperty()

    def execute(self, context):
        obj = context.object
        if obj is None:
            return {'CANCELLED'}
        prop = next((p for p in context.scene.mastro_custom_property_name_list
                     if p.id == self.property_id), None)
        if prop is None:
            return {'CANCELLED'}
        key = f"_{prop.name}"
        if key in obj:
            obj[key] = self.string_id
        return {'FINISHED'}


class OBJECT_OT_Mastro_Set_String_Property_Menu(Operator):
    """Open a popup to pick a string value for a STRING custom property"""
    bl_idname  = "object.mastro_set_string_property_menu"
    bl_label   = "Set String"
    bl_options = {'INTERNAL'}

    property_id: IntProperty()

    def invoke(self, context, event):
        prop = next((p for p in context.scene.mastro_custom_property_name_list
                     if p.id == self.property_id), None)
        if prop is None:
            return {'CANCELLED'}

        options = sorted(prop.string_options, key=lambda o: o.name)
        pid = self.property_id

        def draw_menu(menu, context):
            for opt in options:
                op = menu.layout.operator(
                    "object.mastro_set_string_property",
                    text=opt.name,
                )
                op.property_id = pid
                op.string_id   = opt.id

        context.window_manager.popup_menu(draw_menu, title=prop.name)
        return {'FINISHED'}

    def execute(self, context):
        return {'FINISHED'}
