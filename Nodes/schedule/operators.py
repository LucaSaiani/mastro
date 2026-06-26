from bpy.types import Operator, UIList
from bpy.props import StringProperty, EnumProperty

from .execution import tag_redraw_node_editors
from ...Utils.import_export.mastro_export_utils import clear_mass_data_cache


class MASTRO_UL_schedule_keys(UIList):
    """List of column names used as Group By keys"""
    bl_idname = "MASTRO_UL_schedule_keys"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.prop(item, "name", text="", emboss=False)


class MASTRO_OT_Schedule_GroupBy_Key_Add(Operator):
    """Add a column to the Group By keys list"""
    bl_idname = "mastro_schedule.groupby_key_add"
    bl_label = "Add Key"

    node_name: StringProperty()

    def execute(self, context):
        node = context.space_data.edit_tree.nodes[self.node_name]
        item = node.keys.add()
        item.name = node.column_to_add or "Column"
        node.active_key_index = len(node.keys) - 1
        node.id_data.execute()
        return {'FINISHED'}


class MASTRO_OT_Schedule_GroupBy_Key_Remove(Operator):
    """Remove the active column from the Group By keys list"""
    bl_idname = "mastro_schedule.groupby_key_remove"
    bl_label = "Remove Key"

    node_name: StringProperty()

    def execute(self, context):
        node = context.space_data.edit_tree.nodes[self.node_name]
        if node.keys:
            node.keys.remove(node.active_key_index)
            node.active_key_index = max(0, node.active_key_index - 1)
        node.id_data.execute()
        return {'FINISHED'}


class MASTRO_UL_schedule_category_lookup(UIList):
    """List of category -> value pairs used by the Category Lookup node"""
    bl_idname = "MASTRO_UL_schedule_category_lookup"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        row.prop(item, "name", text="", emboss=False)
        row.prop(item, "value", text="", emboss=False)


class MASTRO_OT_Schedule_Category_Lookup_Add(Operator):
    """Add a category -> value pair to the Category Lookup node"""
    bl_idname = "mastro_schedule.category_lookup_add"
    bl_label = "Add Category"

    node_name: StringProperty()

    def execute(self, context):
        node = context.space_data.edit_tree.nodes[self.node_name]
        item = node.items.add()
        item.name = "Category"
        item.value = "0"
        node.active_item_index = len(node.items) - 1
        node.id_data.execute()
        return {'FINISHED'}


class MASTRO_OT_Schedule_Category_Lookup_Remove(Operator):
    """Remove the active category -> value pair from the Category Lookup node"""
    bl_idname = "mastro_schedule.category_lookup_remove"
    bl_label = "Remove Category"

    node_name: StringProperty()

    def execute(self, context):
        node = context.space_data.edit_tree.nodes[self.node_name]
        if node.items:
            node.items.remove(node.active_item_index)
            node.active_item_index = max(0, node.active_item_index - 1)
        node.id_data.execute()
        return {'FINISHED'}


class MASTRO_UL_schedule_join_tables(UIList):
    """List of linked Tables for Join Tables (nodes_table_join.py),
    showing each one's own first header text - read-only labels, the
    list only exists here to let the user REORDER them (the join order
    comes from this list's own order, not from link/connection order -
    the user's own explicit call)"""
    bl_idname = "MASTRO_UL_schedule_join_tables"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.label(text=item.label or "(empty)")


class MASTRO_OT_Schedule_Join_Tables_Move(Operator):
    """Move the active Table up or down in Join Tables' own join order"""
    bl_idname = "mastro_schedule.join_tables_move"
    bl_label = "Move Table"

    node_name: StringProperty()
    direction: EnumProperty(items=[('UP', "Up", ""), ('DOWN', "Down", "")])

    def execute(self, context):
        node = context.space_data.edit_tree.nodes[self.node_name]
        index = node.active_table_index
        new_index = index + (-1 if self.direction == 'UP' else 1)
        if 0 <= new_index < len(node.table_items):
            node.table_items.move(index, new_index)
            node.active_table_index = new_index
            node.id_data.execute()
        return {'FINISHED'}


class MASTRO_UL_schedule_export_sheets(UIList):
    """List of linked Sheets for Export Excel (nodes_excel_export.py) -
    unlike Join Tables/Join Sheets' own read-only list, every row here
    has editable fields (update_mode/start_cell) alongside the
    read-only label, since each linked Sheet needs its own export
    settings, not just a position in the join order.

    No editable sheet_name field here anymore - the user's own
    explicit removal, once Table to Sheet/Join Tables/Join Sheets all
    gained their own table_or_sheet_name (a single shared property
    name, see resolve_named_origin's own docstring in tree.py):
    renaming a sheet now happens once, upstream, at whichever node
    actually produced/combined it - not a second time here too. The
    label shown (item.label) already reflects that name automatically
    (see nodes_excel_export.py's own _origin_label)."""
    bl_idname = "MASTRO_UL_schedule_export_sheets"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        from ... import Icons as icons

        # layout.split(factor=...) for exact percentages (confirmed
        # against native examples like properties_data_curve.py's own
        # repeated split(factor=0.25) calls) - 70% the read-only label
        # (no name field to compete with anymore), 15% the update_mode
        # toggle, 15% start_cell.
        split1 = layout.split(factor=0.7, align=True)
        split1.label(text=item.label or "(empty)")
        split2 = split1.split(factor=0.5, align=True)
        # update_mode as a custom-icon toggle (Icons/excel_update_mode.svg
        # - a placeholder copy of an existing icon, the user's own call,
        # to be redrawn into something that actually communicates
        # "update" once this exists) rather than the EnumProperty
        # dropdown this used to be - the user's own explicit rework.
        update_icon = icons.icon_id("excel_update_mode")
        split2.prop(item, "update_mode", text="", icon_value=update_icon)
        start_cell_field = split2.row(align=True)
        start_cell_field.enabled = item.update_mode
        start_cell_field.prop(item, "start_cell", text="")


class MASTRO_OT_Schedule_Export_Sheets_Move(Operator):
    """Move the active Sheet up or down in Export Excel's own sheet order"""
    bl_idname = "mastro_schedule.export_sheets_move"
    bl_label = "Move Sheet"

    node_name: StringProperty()
    direction: EnumProperty(items=[('UP', "Up", ""), ('DOWN', "Down", "")])

    def execute(self, context):
        node = context.space_data.edit_tree.nodes[self.node_name]
        index = node.active_sheet_index
        new_index = index + (-1 if self.direction == 'UP' else 1)
        if 0 <= new_index < len(node.sheet_items):
            node.sheet_items.move(index, new_index)
            node.active_sheet_index = new_index
            node.id_data.execute()
        return {'FINISHED'}


class MASTRO_OT_Schedule_Excel_Export(Operator):
    """Write Export Excel's own linked Sheets to its filepath right
    now, on demand - the only way this node ever writes (see that
    node's own module comment for why an auto-export option was tried
    and removed)"""
    bl_idname = "mastro_schedule.excel_export"
    bl_label = "Export"
    bl_icon = 'EXPORT'

    node_name: StringProperty()

    def execute(self, context):
        import bpy

        node = context.space_data.edit_tree.nodes[self.node_name]
        # Same check the button's own draw_buttons already disables
        # on, repeated here as a second line of defense (e.g. if this
        # were ever invoked some other way than that button, ".node_name"
        # search, a keymap, ...) - never silently write to a folder-only
        # or empty path.
        if not node._has_valid_filepath():
            self.report({'ERROR'}, "Set a valid file name in Path first")
            return {'CANCELLED'}
        node.id_data.execute()
        try:
            node.export_sheets()
        except Exception as exc:
            self.report({'ERROR'}, f"Excel export failed: {exc}")
            return {'CANCELLED'}
        # The user's own explicit ask: a footer INFO message confirming
        # success, not just silence on the happy path (the ERROR report
        # above already covered failure) - bpy.path.abspath so a "//"-
        # relative path reads as the real location it was written to.
        self.report({'INFO'}, f"Exported to {bpy.path.abspath(node.filepath)}")
        return {'FINISHED'}


class MASTRO_OT_Schedule_Force_Refresh(Operator):
    """Re-evaluate the schedule tree. The tree only re-runs automatically
    when the tree itself changes (a node/link added or a property edited);
    it does not react to changes made outside the graph (e.g. editing a
    mesh attribute or a custom property directly in the 3D viewport), so
    this lets the user force a refresh on demand"""
    bl_idname = "mastro_schedule.force_refresh"
    bl_label = "Refresh"
    bl_icon = 'FILE_REFRESH'

    def execute(self, context):
        clear_mass_data_cache()
        context.space_data.edit_tree.execute()
        tag_redraw_node_editors()
        return {'FINISHED'}
