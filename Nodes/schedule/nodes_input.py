import bpy
from bpy.types import Node

from .tree import MaStroScheduleTreeNode
from ...Utils.import_export.mastro_export_utils import (
    get_mass_data_for_scope,
    granularData,
)


class MaStroScheduleInputAllNode(MaStroScheduleTreeNode, Node):
    """Build the schedule table from every MaStro mass object in the scene,
    using the same granularData logic as the CSV export and print schedule
    (multi-storey unwrapping, per-floor use and height)"""
    bl_idname = 'MaStroScheduleInputAll'
    bl_label = 'Input Mesh (All)'

    def init(self, context):
        self.outputs.new('MaStroScheduleDataSocketType', "Data")

    def evaluate(self, inputs):
        rough = get_mass_data_for_scope(bpy.context, 'ALL')
        return [granularData(rough) if rough else []]


class MaStroScheduleInputSelectedNode(MaStroScheduleTreeNode, Node):
    """Build the schedule table from the currently selected MaStro mass objects,
    using the same granularData logic as the CSV export and print schedule"""
    bl_idname = 'MaStroScheduleInputSelected'
    bl_label = 'Input Mesh (Selected)'

    def init(self, context):
        self.outputs.new('MaStroScheduleDataSocketType', "Data")

    def evaluate(self, inputs):
        rough = get_mass_data_for_scope(bpy.context, 'SELECTED')
        return [granularData(rough) if rough else []]
