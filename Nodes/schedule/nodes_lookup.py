from bpy.types import Node
from bpy.props import StringProperty, IntProperty, CollectionProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node
from .properties import MaStro_schedule_cell, MaStro_schedule_key_item


def _as_number_if_possible(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return value


class MaStroScheduleCategoryLookupNode(MaStroScheduleTreeNode, Node):
    """Look up a value for each row from an inline category -> value table,
    matched on a single column (equivalent to the VBA plotColor-style helpers:
    a fixed mapping from a category name to a value)"""
    bl_idname = 'MaStroScheduleCategoryLookup'
    bl_label = 'Category Lookup'

    key_column: StringProperty(name="Key Column", update=update_node)

    items: CollectionProperty(type=MaStro_schedule_cell)
    active_item_index: IntProperty()

    def init(self, context):
        self.inputs.new('MaStroScheduleDataSocketType', "Data")
        self.outputs.new('MaStroScheduleDataSocketType', "Data")

    def draw_buttons(self, context, layout):
        layout.prop(self, "key_column")
        layout.template_list("MASTRO_UL_schedule_category_lookup", "", self, "items", self, "active_item_index", rows=3)
        row = layout.row(align=True)
        row.operator("mastro_schedule.category_lookup_add", text="Add").node_name = self.name
        row.operator("mastro_schedule.category_lookup_remove", text="Remove").node_name = self.name

    def evaluate(self, inputs):
        rows = inputs[0] or []
        out_key = "Lookup"

        mapping = {item.name: _as_number_if_possible(item.value) for item in self.items}

        result = []
        for row in rows:
            new_row = dict(row)
            new_row[out_key] = mapping.get(str(row.get(self.key_column, "")), "")
            result.append(new_row)
        return [result]


class MaStroScheduleMatrixLookupNode(MaStroScheduleTreeNode, Node):
    """Look up a value for each row of "Data" from a "Reference" table,
    matching on one or more key columns (equivalent to the VBA MultiLookup
    helper, e.g. MultiLookup(massFloors, [Phase, Use], [phase, use], Area))"""
    bl_idname = 'MaStroScheduleMatrixLookup'
    bl_label = 'Matrix Lookup'

    return_column: StringProperty(name="Return Column", update=update_node)

    keys: CollectionProperty(type=MaStro_schedule_key_item)
    active_key_index: IntProperty()

    def init(self, context):
        self.inputs.new('MaStroScheduleDataSocketType', "Data")
        self.inputs.new('MaStroScheduleDataSocketType', "Reference")
        self.outputs.new('MaStroScheduleDataSocketType', "Data")

    def draw_buttons(self, context, layout):
        layout.template_list("MASTRO_UL_schedule_keys", "", self, "keys", self, "active_key_index", rows=3)
        row = layout.row(align=True)
        row.operator("mastro_schedule.groupby_key_add", text="Add").node_name = self.name
        row.operator("mastro_schedule.groupby_key_remove", text="Remove").node_name = self.name
        layout.prop(self, "return_column")

    def evaluate(self, inputs):
        rows = inputs[0] or []
        reference = inputs[1] or []
        out_key = "Lookup"
        key_names = [k.name for k in self.keys if k.name]

        result = []
        for row in rows:
            new_row = dict(row)
            value = ""
            for ref_row in reference:
                if all(str(row.get(k, "")) == str(ref_row.get(k, "")) for k in key_names):
                    value = ref_row.get(self.return_column, "")
                    break
            new_row[out_key] = value
            result.append(new_row)
        return [result]
