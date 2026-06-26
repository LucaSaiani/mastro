from bpy.types import Node

from .tree import MaStroScheduleTreeNode
from .nodes_viewer import _cell_text


def _data_key(row):
    """Same elimination logic as Math/Evaluate Attribute - a Column row
    has exactly one key that isn't an id key (doesn't start with "_")."""
    for key in row.keys():
        if not key.startswith("_"):
            return key
    return None


# The boundary between the Column model (id keys + one data key per row,
# everything downstream computable) and Table (purely visual text, see
# sockets.py:MaStroScheduleTableSocket) - this is where a Column's id
# keys (_Object, _Face/...) are deliberately thrown away, since Table
# rows carry no identity of their own past this point.
class MaStroScheduleConvertColumnToTableNode(MaStroScheduleTreeNode, Node):
    """Convert a Column into a one-column Table, ready for display -
    discards the Column's id keys, keeping only its values as text"""
    bl_idname = 'MaStroScheduleConvertColumnToTable'
    bl_label = 'Column to Table'

    def init(self, context):
        self.inputs.new('MaStroScheduleColumnSocketType', "Column")
        self.outputs.new('MaStroScheduleTableSocketType', "Table")

    def evaluate(self, inputs):
        rows = inputs[0] or []
        # No "or self.name" fallback - same correction as the Viewer's
        # own column_label lookup (nodes_viewer.py): an invalid/mismatched
        # link (e.g. Column plugged with something that isn't a Column,
        # confirmed live as a real case - eval_node already gates that
        # input to None, see execution.py's mismatch check) must never
        # fall back to showing this node's own internal name
        # ("Column to Table", "Column to Table.001", ...) as if it were
        # real header text.
        from .tree import upstream_attr
        header_text = upstream_attr(self.inputs["Column"], "column_label")

        table_rows = []
        for row in rows:
            key = _data_key(row)
            # _cell_text, not a plain str() - same "0.00 vs blank"
            # convention as the Viewer's own Column rendering
            # (nodes_viewer.py), confirmed live as a real inconsistency
            # otherwise: a Column showing blank for a zeroed value (e.g.
            # an undercroft floor's area) still showed "0.0" once
            # converted to a Table through this node. is_id_key isn't
            # passed - `key` here is already _data_key's result, never
            # an id key (those were discarded above, see this class's
            # own docstring).
            text = _cell_text(row.get(key, "")) if key is not None else ""
            table_rows.append({"text": text, "bg": None})

        return [{
            "columns": [{
                "header": {"text": header_text, "bg": None},
                "rows": table_rows,
            }],
            "merges": [],
        }]
