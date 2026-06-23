from bpy.types import Node
from bpy.props import StringProperty, EnumProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node, get_available_columns_items


class MaStroScheduleHeaderNode(MaStroScheduleTreeNode, Node):
    """Rename a column of the incoming table. The new name can be a literal
    typed here, or come from a Name input (e.g. a String node), so the same
    name can be reused and changed in one place across several Header nodes"""
    bl_idname = 'MaStroScheduleHeader'
    bl_label = 'Header ?'

    column: EnumProperty(
        name="Column",
        items=lambda self, context: get_available_columns_items(self, 0),
        update=update_node,
    )
    new_name: StringProperty(name="New Name", update=update_node)

    def init(self, context):
        self.inputs.new('MaStroScheduleDataSocketType', "Data")
        self.inputs.new('MaStroScheduleDataSocketType', "Name")
        self.outputs.new('MaStroScheduleDataSocketType', "Data")

    def draw_buttons(self, context, layout):
        layout.prop(self, "column")
        if not self.inputs["Name"].is_linked:
            layout.prop(self, "new_name", text="New Name")

    def evaluate(self, inputs):
        rows = inputs[0] or []
        name_rows = inputs[1] or []
        new_name = name_rows[0].get("Value", "") if name_rows else self.new_name
        new_name = new_name or self.column

        result = []
        for row in rows:
            new_row = dict(row)
            if self.column in new_row:
                new_row[new_name] = new_row.pop(self.column)
            result.append(new_row)
        return [result]
