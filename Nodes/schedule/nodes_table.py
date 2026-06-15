from bpy.types import Node

from .tree import MaStroScheduleTreeNode


class MaStroScheduleTableDataNode(MaStroScheduleTreeNode, Node):
    """Pass-through node marking the final table of a schedule, so it can be
    picked up by a Viewer (or further processed)"""
    bl_idname = 'MaStroScheduleTableData'
    bl_label = 'Table Data'

    def init(self, context):
        self.inputs.new('MaStroScheduleDataSocketType', "Data")
        self.outputs.new('MaStroScheduleDataSocketType', "Data")

    def evaluate(self, inputs):
        return [inputs[0] or []]
