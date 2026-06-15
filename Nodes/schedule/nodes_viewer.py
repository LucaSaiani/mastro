from bpy.types import Node
from bpy.props import CollectionProperty

from .tree import MaStroScheduleTreeNode
from .properties import MaStro_schedule_key_item, MaStro_schedule_row


class MaStroScheduleViewerNode(MaStroScheduleTreeNode, Node):
    """Display the incoming table as a grid in the node's side panel"""
    bl_idname = 'MaStroScheduleViewer'
    bl_label = 'Viewer'

    columns: CollectionProperty(type=MaStro_schedule_key_item)
    rows: CollectionProperty(type=MaStro_schedule_row)

    def init(self, context):
        self.inputs.new('MaStroScheduleDataSocketType', "Data")

    def evaluate(self, inputs):
        rows = inputs[0] or []

        column_names = []
        for row in rows:
            for key in row.keys():
                if key.startswith("_"):
                    continue
                if key not in column_names:
                    column_names.append(key)

        self.columns.clear()
        for name in column_names:
            self.columns.add().name = name

        self.rows.clear()
        for row in rows:
            row_item = self.rows.add()
            for name in column_names:
                cell = row_item.cells.add()
                cell.name = name
                cell.value = str(row.get(name, ""))

        return []

    def draw_buttons_ext(self, context, layout):
        col = layout.column()

        header = col.row()
        for column in self.columns:
            header.label(text=column.name)

        for row in self.rows:
            row_layout = col.row()
            for cell in row.cells:
                row_layout.label(text=cell.value)
