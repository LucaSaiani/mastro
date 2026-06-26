from bpy.types import Node
from bpy.props import FloatVectorProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node, is_socket_active


# Colors every cell whose bg is still None - the padding/fit cells
# inserted by Move Sheet or Join Sheets (both of which deliberately
# leave their own inserted Sheet cells transparent, bg=None - the
# user's own explicit call: "se bg None poi lo possiamo facilmente
# individuare e correggere con quel nodo che ho proposto"). Join Tables
# follows the exact same bg=None convention for ITS OWN padding cells,
# but that's in the separate Table world (nodes_table_join.py) - this
# node only ever sees a Sheet, never a Table, so it's mentioned here
# only as the same idea applied on the other side of Table to Sheet's
# own boundary. Cells that already carry their own bg (from Table to
# Sheet, Sheet Primitive, or an earlier Sheet Background) are left
# untouched - this node only fills in the gap, never overwrites an
# existing choice.
#
# No Text Colour input, unlike Edit Cell/Row Colour/Row Pattern - a
# padding cell never has any text in the first place (nothing that
# generates one ever sets it), so there's nothing to color.
class MaStroScheduleSheetBackgroundNode(MaStroScheduleTreeNode, Node):
    """Color every still-uncolored cell in a Sheet (the padding cells
    Move Sheet/Join Sheets/Join Tables leave transparent) - cells
    that already have their own background are left untouched"""
    bl_idname = 'MaStroScheduleSheetBackground'
    bl_label = 'Sheet Background'

    bg_value: FloatVectorProperty(name="Background Colour", subtype='COLOR', size=3,
                                   min=0.0, max=1.0, default=(0.18, 0.18, 0.18), update=update_node)

    def init(self, context):
        self.inputs.new('MaStroScheduleSheetSocketType', "Sheet")
        self.inputs.new('MaStroScheduleColorSocketType', "Background Colour").prop_name = "bg_value"
        self.outputs.new('MaStroScheduleSheetSocketType', "Sheet")

    @staticmethod
    def _resolve_color(socket, value_in, fallback):
        if not is_socket_active(socket):
            return tuple(fallback)
        return tuple(value_in) if value_in else tuple(fallback)

    def evaluate(self, inputs):
        sheet = inputs[0] or {"columns": [], "merges": []}
        bg = self._resolve_color(self.inputs["Background Colour"], inputs[1], self.bg_value)

        columns = []
        for column in sheet.get("columns", []):
            cells = [
                {**cell, "bg": bg} if cell.get("bg") is None else cell
                for cell in column.get("cells", [])
            ]
            columns.append({"cells": cells})

        return [{"columns": columns, "merges": sheet.get("merges", [])}]
