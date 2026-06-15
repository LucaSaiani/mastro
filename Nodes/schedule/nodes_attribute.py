import bpy
from bpy.types import Node
from bpy.props import StringProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node


class MaStroScheduleGetCustomAttributeNode(MaStroScheduleTreeNode, Node):
    """Read a per-object custom property (e.g. a user-defined 'Phase') and add it
    as a new column, broadcasting its value to every row of that object"""
    bl_idname = 'MaStroScheduleGetCustomAttribute'
    bl_label = 'Get Custom Attribute'

    property_name: StringProperty(name="Property", default="Phase", update=update_node)
    output_name: StringProperty(name="Output Name", default="Phase", update=update_node)

    def init(self, context):
        self.inputs.new('MaStroScheduleDataSocketType', "Data")
        self.outputs.new('MaStroScheduleDataSocketType', "Data")

    def draw_buttons(self, context, layout):
        layout.prop(self, "property_name")
        layout.prop(self, "output_name")

    def evaluate(self, inputs):
        rows = inputs[0] or []
        out_key = self.output_name or self.property_name

        result = []
        for row in rows:
            new_row = dict(row)
            obj = bpy.data.objects.get(row.get("Object"))
            new_row[out_key] = obj.get(self.property_name, "") if obj else ""
            result.append(new_row)
        return [result]
