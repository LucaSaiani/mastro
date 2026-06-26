from bpy.types import Node

from .tree import MaStroScheduleTreeNode
from .nodes_viewer import _cell_text


# The boundary between Multi Column (Pivot's own output, see
# nodes_pivot.py/sockets.py:MaStroScheduleMultiColumnSocket) and Table
# (purely visual text) - mirrors Column to Table's own role
# (nodes_table_convert.py), one column per Multi Column's own id_keys
# THEN one column per its own data_keys, in that order. Discards
# nothing the way Column to Table discards Column's own id keys -
# every id_key and every data_key becomes its own Table column, since
# (unlike a plain Column's id keys) a Multi Column's own id_keys/
# data_keys ARE the meaningful labeled axes of the pivot, not internal
# bookkeeping to throw away.
class MaStroScheduleMultiColumnToTableNode(MaStroScheduleTreeNode, Node):
    """Convert a Multi Column into a Table, ready for display - one
    column per id key, then one column per data key"""
    bl_idname = 'MaStroScheduleMultiColumnToTable'
    bl_label = 'Multi Column to Table'

    def init(self, context):
        self.inputs.new('MaStroScheduleMultiColumnSocketType', "Multi Column")
        self.outputs.new('MaStroScheduleTableSocketType', "Table")

    def evaluate(self, inputs):
        multi_column = inputs[0] or {"id_keys": [], "data_keys": [], "rows": []}
        id_keys = multi_column.get("id_keys", [])
        data_keys = multi_column.get("data_keys", [])
        rows = multi_column.get("rows", [])

        columns = []
        for key in id_keys + data_keys:
            table_rows = [{"text": _cell_text(row.get(key, "")), "bg": None} for row in rows]
            columns.append({"header": {"text": key, "bg": None}, "rows": table_rows})

        return [{"columns": columns, "merges": []}]
