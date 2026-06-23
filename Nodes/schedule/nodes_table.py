from bpy.types import Node

from .tree import MaStroScheduleTreeNode


class MaStroScheduleTableDataNode(MaStroScheduleTreeNode, Node):
    """Pass-through node marking the final table of a schedule, so it can be
    picked up by a Viewer (or further processed)"""
    bl_idname = 'MaStroScheduleTableData'
    bl_label = 'Table Data ?'

    def init(self, context):
        self.inputs.new('MaStroScheduleDataSocketType', "Data")
        self.outputs.new('MaStroScheduleDataSocketType', "Data")

    def evaluate(self, inputs):
        return [inputs[0] or []]


class MaStroScheduleFlattenNode(MaStroScheduleTreeNode, Node):
    """Flatten the (possibly nested) output of chained Group By / Aggregate
    nodes into a single ordered list of rows, mirroring the recursive
    control-break used by the print-schedule system: each group's members
    are emitted first, followed by a subtotal row carrying that group's own
    fields (including any aggregates added by Aggregate nodes). Leaf rows
    and subtotal rows are tagged with "_subtotal" and "_level" for the
    Viewer to render"""
    bl_idname = 'MaStroScheduleFlatten'
    bl_label = 'Flatten ?'

    def init(self, context):
        self.inputs.new('MaStroScheduleDataSocketType', "Data")
        self.outputs.new('MaStroScheduleDataSocketType', "Data")

    def evaluate(self, inputs):
        items = inputs[0] or []
        return [self._flatten(items, 0)]

    def _flatten(self, items, level):
        result = []
        for item in items:
            if isinstance(item, dict) and "_members" in item:
                result.extend(self._flatten(item["_members"], level + 1))
                subtotal = {k: v for k, v in item.items() if k != "_members"}
                subtotal["_subtotal"] = True
                subtotal["_level"] = level
                result.append(subtotal)
            else:
                row = dict(item)
                row["_subtotal"] = False
                row["_level"] = level
                result.append(row)
        return result
