from bpy.types import Node
from bpy.props import StringProperty, EnumProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node


class MaStroScheduleAggregateNode(MaStroScheduleTreeNode, Node):
    """Aggregate a value column over each group's members (equivalent to the
    VBA SumByCriteria helper, generalized to Sum/Count/Average)"""
    bl_idname = 'MaStroScheduleAggregate'
    bl_label = 'Aggregate'

    column: StringProperty(name="Column", update=update_node)
    operation: EnumProperty(
        name="Operation",
        items=[
            ('SUM', "Sum", "Sum the column values"),
            ('COUNT', "Count", "Count the rows in each group"),
            ('AVERAGE', "Average", "Average the column values"),
        ],
        default='SUM',
        update=update_node,
    )
    output_name: StringProperty(name="Output Name", default="Result", update=update_node)

    def init(self, context):
        self.inputs.new('MaStroScheduleDataSocketType', "Data")
        self.outputs.new('MaStroScheduleDataSocketType', "Data")

    def draw_buttons(self, context, layout):
        layout.prop(self, "column")
        layout.prop(self, "operation")
        layout.prop(self, "output_name")

    def evaluate(self, inputs):
        rows = inputs[0] or []
        out_key = self.output_name or "Result"

        result = []
        for row in rows:
            new_row = {k: v for k, v in row.items() if k != "_members"}
            members = row.get("_members", [row])

            if self.operation == 'COUNT':
                aggregate = len(members)
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

            new_row[out_key] = aggregate
            result.append(new_row)

        return [result]
