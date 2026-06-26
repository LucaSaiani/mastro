from bpy.types import Node
from bpy.props import IntProperty, EnumProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node
from .table_text_edit_shared import resolve_index, map_table_rows


# UPPER/lower/Capitalize ("First upper" - only the string's own first
# letter)/Title Case ("First Upper" - every word's first letter) - the
# user's own explicit distinction between the latter two, confirmed:
# Capitalize is Python's own str.capitalize() (which also lowercases
# everything else, same as Python's own behavior - not assumed, that's
# what capitalize() actually does), Title Case is str.title().
CASE_ITEMS = [
    ('UPPER', "UPPERCASE", "Convert to all upper case"),
    ('LOWER', "lowercase", "Convert to all lower case"),
    ('CAPITALIZE', "Capitalize", "Capitalize only the first letter of the whole text"),
    ('TITLE', "Title Case", "Capitalize the first letter of every word"),
]


class MaStroScheduleTableCaseNode(MaStroScheduleTreeNode, Node):
    """Change the letter case of one or more columns of a Table"""
    bl_idname = 'MaStroScheduleTableCase'
    bl_label = 'Cell Case'

    case: EnumProperty(name="Case", items=CASE_ITEMS, default='UPPER', update=update_node)
    start_index: IntProperty(name="Start Index", default=0, min=0, update=update_node)
    end_index: IntProperty(name="End Index", default=0, min=0, update=update_node)

    def init(self, context):
        self.inputs.new('MaStroScheduleTableSocketType', "Table")
        self.inputs.new('MaStroScheduleColumnSocketType', "Start Index").prop_name = "start_index"
        self.inputs.new('MaStroScheduleColumnSocketType', "End Index").prop_name = "end_index"
        self.outputs.new('MaStroScheduleTableSocketType', "Table")

    def draw_buttons(self, context, layout):
        layout.prop(self, "case", text="")

    def _transform(self, text):
        if self.case == 'UPPER':
            return text.upper()
        if self.case == 'LOWER':
            return text.lower()
        if self.case == 'CAPITALIZE':
            return text.capitalize()
        return text.title()

    def evaluate(self, inputs):
        table = inputs[0] or {"columns": [], "merges": []}
        start_index = resolve_index(self.inputs["Start Index"], inputs[1], self.start_index)
        end_index = resolve_index(self.inputs["End Index"], inputs[2], self.end_index)
        return [map_table_rows(table, start_index, end_index, self._transform)]
