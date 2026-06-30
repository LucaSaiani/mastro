from bpy.types import Node

from .tree import MaStroScheduleTreeNode
from .nodes_viewer import _cell_text


def _data_keys(rows):
    """Every distinct non-id key (doesn't start with "_") present on
    ANY of `rows`, in first-appearance order - NOT just the first key
    of the first row (the old _data_key elimination logic Math/
    Evaluate Attribute still use for their own single-attribute case).
    A Column can carry more than one data key at once since Merge
    Column (nodes_merge_column.py) and Aggregate's own multi-key
    group-by (nodes_aggregate_column.py, including an Id Key
    duplicated as an ordinary attribute at its own chosen position) -
    confirmed live as a real bug otherwise: Column to Table only ever
    produced ONE column, silently dropping every other attribute a
    Column might carry, the exact same single-data-key assumption
    already found and fixed in the Viewer/Aggregate themselves."""
    keys = []
    for row in rows:
        for key in row.keys():
            if not key.startswith("_") and key not in keys:
                keys.append(key)
    return keys


# The boundary between the Column model (id keys + one or more data
# keys per row, everything downstream computable) and Table (purely
# visual text, see sockets.py:MaStroScheduleTableSocket) - this is
# where a Column's id keys (_Object, _Face/...) are deliberately
# thrown away, since Table rows carry no identity of their own past
# this point. One Table column per distinct data key found
# (_data_keys above), not just the first - see that function's own
# docstring for why a Column can carry more than one at once.
class MaStroScheduleConvertColumnToTableNode(MaStroScheduleTreeNode, Node):
    """Convert a Column into a Table, ready for display - one Table
    column per distinct data key the Column carries, discarding only
    its id keys"""
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
        upstream_label = upstream_attr(self.inputs["Column"], "column_label")

        keys = _data_keys(rows)
        tree = self.id_data
        table_columns = []
        for key in keys:
            # The upstream Column's own column_label only ever
            # describes ONE attribute (its own single original data
            # key) - meaningless as a shared header once there's more
            # than one column to label distinctly. With exactly one
            # key (the common, pre-existing case), this falls back to
            # upstream_label exactly as before; with more than one,
            # each column is labeled by resolving ITS OWN key back to
            # whichever node produced it (same tree.nodes.get(key)
            # lookup nodes_viewer.py's own multi-data-key relabeling
            # already does) - falling back to the raw key itself if no
            # node matches (e.g. an Id Key's own readable label, e.g.
            # "Object_id", which was never a node.name to begin with).
            if len(keys) == 1:
                header_text = upstream_label
            else:
                source_node = tree.nodes.get(key)
                header_text = getattr(source_node, "column_label", "") if source_node else ""
                header_text = header_text or key
            table_rows = []
            for row in rows:
                # _cell_text, not a plain str() - same float-formatting
                # convention as the Viewer's own Column rendering
                # (nodes_viewer.py): 2 decimal places, avoiding
                # IEEE754's own binary-representation noise. Hiding a
                # zero for a specific column, if wanted, is Hide Zero's
                # job (nodes_table_hide_zero.py), applied after this
                # node, not this one's concern.
                table_rows.append({"text": _cell_text(row.get(key, "")), "bg": None})
            table_columns.append({
                "header": {"text": header_text, "bg": None},
                "rows": table_rows,
            })

        return [{"columns": table_columns, "merges": []}]
