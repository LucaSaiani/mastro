from bpy.types import Operator, UIList
from bpy.props import StringProperty

from .execution import tag_redraw_node_editors
from ...Utils.import_export.mastro_export_utils import clear_mass_data_cache


class MASTRO_UL_schedule_keys(UIList):
    """List of column names used as Group By keys"""
    bl_idname = "MASTRO_UL_schedule_keys"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.prop(item, "name", text="", emboss=False, icon='SORTALPHA')


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
        row.prop(item, "name", text="", emboss=False, icon='BOOKMARKS')
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
