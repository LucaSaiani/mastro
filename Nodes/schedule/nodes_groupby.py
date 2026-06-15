from bpy.types import Node
from bpy.props import CollectionProperty, IntProperty

from .tree import MaStroScheduleTreeNode
from .properties import MaStro_schedule_key_item


class MaStroScheduleGroupByNode(MaStroScheduleTreeNode, Node):
    """Group rows by one or more key columns, producing one output row per
    unique combination of key values (equivalent to the VBA getUnique /
    getUniqueOfSelection helpers)"""
    bl_idname = 'MaStroScheduleGroupBy'
    bl_label = 'Group By'

    keys: CollectionProperty(type=MaStro_schedule_key_item)
    active_key_index: IntProperty()

    def init(self, context):
        self.inputs.new('MaStroScheduleDataSocketType', "Data")
        self.outputs.new('MaStroScheduleDataSocketType', "Data")

    def draw_buttons(self, context, layout):
        layout.template_list("MASTRO_UL_schedule_keys", "", self, "keys", self, "active_key_index", rows=3)
        row = layout.row(align=True)
        row.operator("mastro_schedule.groupby_key_add", text="Add").node_name = self.name
        row.operator("mastro_schedule.groupby_key_remove", text="Remove").node_name = self.name

    def evaluate(self, inputs):
        rows = inputs[0] or []
        key_names = [k.name for k in self.keys if k.name]

        groups = {}
        order = []
        for row in rows:
            key_tuple = tuple(row.get(k, "") for k in key_names)
            if key_tuple not in groups:
                group = {k: row.get(k, "") for k in key_names}
                group["_members"] = []
                groups[key_tuple] = group
                order.append(key_tuple)
            groups[key_tuple]["_members"].append(row)

        return [[groups[k] for k in order]]
