from bpy.types import Node
from bpy.props import EnumProperty, FloatVectorProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node, is_socket_active


# Sets a uniform border (style, color) on every cell of a Sheet - the
# user's own framing: "preparerei un nodo, al momento un nodo che
# imposta colore, spessore e tipo a livello globale". A real Excel
# grid (visible gridlines even over a colored cell, see
# excel_export_shared.write_sheet's own showGridLines comment for why
# Excel/Gnumeric's own gridlines alone don't show through a filled
# cell's background) needs explicit borders drawn on every cell, not
# just the sheet-wide showGridLines flag this node has nothing to do
# with.
#
# Stores its border setting in the SAME shared cell shape every other
# Sheet/Table cell already uses ("border": {"style": str, "color":
# (r, g, b)} or None, see sockets.py:MaStroScheduleSheetSocket's own
# docstring) rather than only inside the export path - meaningful only
# to Export Excel today (the Viewer never reads it, has no border
# concept of its own), but living in the shared shape means this node
# can sit anywhere in a chain, not necessarily right before Export
# Excel. GitHub issue filed to revisit/expand this once the Viewer's
# own preview needs to show the same border the export would produce
# (which means this eventually needs a Table-level equivalent too, not
# just Sheet).
BORDER_STYLE_ITEMS = [
    ('thin', "Thin", "A thin solid line"),
    ('medium', "Medium", "A medium solid line"),
    ('thick', "Thick", "A thick solid line"),
    ('dashed', "Dashed", "A dashed line"),
    ('dotted', "Dotted", "A dotted line"),
    ('double', "Double", "A double line"),
]


class MaStroScheduleSheetGridNode(MaStroScheduleTreeNode, Node):
    """Set a uniform border (style and color) on every cell of a Sheet
    - the only way to keep a visible grid over colored cells once
    exported to Excel"""
    bl_idname = 'MaStroScheduleSheetGrid'
    bl_label = 'Sheet Grid'

    style: EnumProperty(name="Style", items=BORDER_STYLE_ITEMS, default='thin', update=update_node)
    color_value: FloatVectorProperty(name="Color", subtype='COLOR', size=3, min=0.0, max=1.0,
                                      default=(0.0, 0.0, 0.0), update=update_node)

    def init(self, context):
        self.inputs.new('MaStroScheduleSheetSocketType', "Sheet")
        self.inputs.new('MaStroScheduleColorSocketType', "Color").prop_name = "color_value"
        self.outputs.new('MaStroScheduleSheetSocketType', "Sheet")

    @staticmethod
    def _resolve_color(socket, value_in, fallback):
        if not is_socket_active(socket):
            return tuple(fallback)
        return tuple(value_in) if value_in else tuple(fallback)

    def evaluate(self, inputs):
        sheet = inputs[0] or {"columns": [], "merges": []}
        color = self._resolve_color(self.inputs["Color"], inputs[1], self.color_value)
        border = {"style": self.style, "color": color}

        columns = []
        for column in sheet.get("columns", []):
            cells = [{**cell, "border": border} for cell in column.get("cells", [])]
            columns.append({"cells": cells})

        return [{"columns": columns, "merges": sheet.get("merges", [])}]
