from collections import Counter

from bpy.types import Node
from bpy.props import EnumProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node, leaves, get_available_columns_items


class MaStroScheduleAggregateNode(MaStroScheduleTreeNode, Node):
    """Aggregate a value column over each group's members and annotate the
    group with the result (equivalent to the VBA SumByCriteria/GetMostPresent
    helpers, generalized to Sum/Count/Average/Mode). Works at every nesting
    level produced by chained Group By nodes: each group, at whatever depth,
    gets its own subtotal for this column"""
    bl_idname = 'MaStroScheduleAggregate'
    bl_label = 'Aggregate ?'

    column: EnumProperty(
        name="Column",
        items=lambda self, context: get_available_columns_items(self),
        update=update_node,
    )
    operation: EnumProperty(
        name="Operation",
        items=[
            ('SUM', "Sum", "Sum the column values"),
            ('COUNT', "Count", "Count the rows in each group"),
            ('AVERAGE', "Average", "Average the column values"),
            ('MODE', "Mode", "The most frequently occurring value in the column"),
        ],
        default='SUM',
        update=update_node,
    )
    def init(self, context):
        self.inputs.new('MaStroScheduleDataSocketType', "Data")
        self.outputs.new('MaStroScheduleDataSocketType', "Data")

    def draw_buttons(self, context, layout):
        layout.prop(self, "column")
        layout.prop(self, "operation")

    def evaluate(self, inputs):
        rows = inputs[0] or []
        return [self._annotate(rows)]

    def _annotate(self, items):
        out_key = "Result"

        result = []
        for item in items:
            new_item = dict(item)
            if "_members" in item:
                new_item["_members"] = self._annotate(item["_members"])

            members = leaves(item)
            if self.operation == 'COUNT':
                aggregate = len(members)
            elif self.operation == 'MODE':
                counts = Counter(member.get(self.column, "") for member in members)
                aggregate = max(counts, key=counts.get) if counts else ""
            else:
                values = []
                for member in members:
                    try:
                        values.append(float(member.get(self.column, 0)))
                    except (TypeError, ValueError):
                        pass
                if self.operation == 'AVERAGE':
                    aggregate = sum(values) / len(values) if values else 0
                else:
                    aggregate = sum(values)

            new_item[out_key] = aggregate
            result.append(new_item)

        return result
