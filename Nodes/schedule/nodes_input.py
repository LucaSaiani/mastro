import bpy
from bpy.types import Node

from .tree import MaStroScheduleTreeNode
from .execution import extract_mesh_rows


def _mass_objects(objs):
    return [obj for obj in objs
            if obj.type == 'MESH' and obj.data is not None and "MaStro mass" in obj.data]


class MaStroScheduleInputAllNode(MaStroScheduleTreeNode, Node):
    """Build the schedule table from every MaStro mass object in the scene"""
    bl_idname = 'MaStroScheduleInputAll'
    bl_label = 'Input Mesh (All)'

    def init(self, context):
        self.outputs.new('MaStroScheduleDataSocketType', "Data")

    def evaluate(self, inputs):
        return [extract_mesh_rows(_mass_objects(bpy.context.scene.objects))]


class MaStroScheduleInputSelectedNode(MaStroScheduleTreeNode, Node):
    """Build the schedule table from the currently selected MaStro mass objects"""
    bl_idname = 'MaStroScheduleInputSelected'
    bl_label = 'Input Mesh (Selected)'

    def init(self, context):
        self.outputs.new('MaStroScheduleDataSocketType', "Data")

    def evaluate(self, inputs):
        return [extract_mesh_rows(_mass_objects(bpy.context.selected_objects))]
