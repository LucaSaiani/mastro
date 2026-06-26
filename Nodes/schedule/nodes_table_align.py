from bpy.types import Node
from bpy.props import IntProperty, EnumProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node
from .nodes_table_edit_header import ALIGNMENT_ITEMS
from .table_text_edit_shared import resolve_index, column_range


# Sets text_align on one or more columns' ROW cells - the row equivalent
# of Edit Header's own Alignment dropdown, which only ever touches a
# column's header cell. Edit Header/Table primitive already write
# text_align on a header; this is the first node to write it on a row,
# now that nodes_viewer.py's own row-drawing code reads it (previously
# always LEFT, hardcoded - see properties.py:MaStro_schedule_table_cell's
# own text_align comment).
class MaStroScheduleTableAlignNode(MaStroScheduleTreeNode, Node):
    """Set the text alignment of one or more columns' rows in a Table"""
    bl_idname = 'MaStroScheduleTableAlign'
    bl_label = 'Cell Align'

    alignment: EnumProperty(name="Alignment", items=ALIGNMENT_ITEMS, default='LEFT', update=update_node)
    start_index: IntProperty(
        name="Start Column Index", default=0, min=0, update=update_node,
        description="First column to apply this to - equal to End Column Index for just one column",
    )
    end_index: IntProperty(
        name="End Column Index", default=0, min=0, update=update_node,
        description="Last column to apply this to (inclusive) - equal to Start Column Index for just one column",
    )

    def init(self, context):
        self.inputs.new('MaStroScheduleTableSocketType', "Table")
        self.inputs.new('MaStroScheduleColumnSocketType', "Start Column Index").prop_name = "start_index"
        self.inputs.new('MaStroScheduleColumnSocketType', "End Column Index").prop_name = "end_index"
        self.outputs.new('MaStroScheduleTableSocketType', "Table")

    def draw_buttons(self, context, layout):
        layout.prop(self, "alignment", text="")

    def evaluate(self, inputs):
        table = inputs[0] or {"columns": [], "merges": []}
        start_index = resolve_index(self.inputs["Start Column Index"], inputs[1], self.start_index)
        end_index = resolve_index(self.inputs["End Column Index"], inputs[2], self.end_index)

        bounds = column_range(table, start_index, end_index)
        if bounds is None:
            return [table]
        start_index, end_index = bounds

        columns = table.get("columns", [])
        new_columns = list(columns)
        for index in range(start_index, end_index + 1):
            target = columns[index]
            new_rows = [{**row, "text_align": self.alignment} for row in target.get("rows", [])]
            new_columns[index] = {**target, "rows": new_rows}

        return [{"columns": new_columns, "merges": table.get("merges", [])}]
