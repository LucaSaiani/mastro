from bpy.types import Node
from bpy.props import CollectionProperty, IntProperty, EnumProperty

from .tree import MaStroScheduleTreeNode
from .properties import MaStro_schedule_key_item
from .execution import get_available_columns_items


class MaStroScheduleGroupByNode(MaStroScheduleTreeNode, Node):
    """Group rows by one or more key columns, producing one output row per
    unique combination of key values (equivalent to the VBA getUnique /
    getUniqueOfSelection helpers)"""
    bl_idname = 'MaStroScheduleGroupBy'
    bl_label = 'Group By'

    keys: CollectionProperty(type=MaStro_schedule_key_item)
    active_key_index: IntProperty()
    column_to_add: EnumProperty(name="Column", items=lambda self, context: get_available_columns_items(self))

    def init(self, context):
        self.inputs.new('MaStroScheduleDataSocketType', "Data")
        self.outputs.new('MaStroScheduleDataSocketType', "Data")

    def draw_buttons(self, context, layout):
        layout.template_list("MASTRO_UL_schedule_keys", "", self, "keys", self, "active_key_index", rows=3)
        row = layout.row(align=True)
        row.prop(self, "column_to_add", text="")
        row.operator("mastro_schedule.groupby_key_add", text="Add").node_name = self.name
        row.operator("mastro_schedule.groupby_key_remove", text="Remove").node_name = self.name

    def evaluate(self, inputs):
        rows = inputs[0] or []
        key_names = [k.name for k in self.keys if k.name]
        return [self._group(rows, key_names)]

    def _group(self, items, key_names):
        """Group `items` by `key_names`. If `items` are already groups
        (i.e. carry "_members" from a previous Group By), descend into each
        group's "_members" and group those instead - chaining Group By nodes
        nests an additional level, with the first one applied becoming the
        outermost grouping."""
        if items and "_members" in items[0]:
            return [
                {**group, "_members": self._group(group["_members"], key_names)}
                for group in items
            ]

        groups = {}
        order = []
        for row in items:
            key_tuple = tuple(row.get(k, "") for k in key_names)
            if key_tuple not in groups:
                group = {k: row.get(k, "") for k in key_names}
                group["_members"] = []
                groups[key_tuple] = group
                order.append(key_tuple)
            groups[key_tuple]["_members"].append(row)

        return [groups[k] for k in order]
