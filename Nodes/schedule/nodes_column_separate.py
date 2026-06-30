import bpy
from bpy.types import Node

from .tree import MaStroScheduleTreeNode


def _resolve_data_key(tree, row, name):
    """Same name->technical-key resolution as Aggregate's own
    _resolve_data_key (nodes_aggregate_column.py) - a row's own data
    keys are some node's own node.name (see nodes_evaluate.py's own
    evaluate(), "key = self.name"), never the chosen attribute's own
    readable name (e.g. "use") directly. Duplicated rather than
    imported - same reasoning as nodes_id_keys.py's own _id_keys
    duplication, avoiding an import cycle between sibling node
    modules. Falls back to `name` itself if no row key's own
    column_label matches."""
    for key in row.keys():
        if key.startswith("_"):
            continue
        source_node = tree.nodes.get(key)
        if source_node is not None and getattr(source_node, "column_label", "") == name:
            return key
    return name


# Splits a Column's own data keys into two: Selection (only the chosen
# attribute) and Inverted (every OTHER attribute) - both keep every id
# key (_Object, _Face/...) unchanged, only the DATA keys differ between
# the two outputs. Mirrors Geometry Nodes' own Separate Geometry in
# spirit (a single chosen criterion splits one input into two
# complementary outputs) - the user's own explicit naming/shape
# reference - but splits which ATTRIBUTES a row carries, not which
# ROWS pass a boolean test (Separate Geometry's own criterion is a
# per-element boolean; this one is a single chosen Attribute Name, the
# same MaStroScheduleAttributeRefSocketType Named Attribute already
# outputs, picking ONE data key out of however many a Column carries
# at once since Merge Column (nodes_merge_column.py) and Aggregate's
# own multi-key group-by (nodes_aggregate_column.py) made more than
# one possible in the first place).
#
# Built for the user's own concrete need: after Aggregate produces a
# Column carrying Object_id/Use/Floor/Area together, Math's own
# operation now applies to EVERY attribute a row carries at once (the
# user's own explicit design from earlier the same session) - there
# was no way to apply Math to JUST Area without it also touching
# Use/Floor. Separate Columns isolates Area into its own Column
# first (Selection), Math runs on that alone, and Inverted (still
# carrying Use/Floor) is recombined afterward with Merge Column if
# needed.
class MaStroScheduleColumnSeparateNode(MaStroScheduleTreeNode, Node):
    """Split a Column's own data keys into Selection (the chosen
    Attribute Name only) and Inverted (every other attribute) - both
    keep every id key unchanged"""
    bl_idname = 'MaStroScheduleColumnSeparate'
    bl_label = 'Separate Columns'

    def init(self, context):
        self.inputs.new('MaStroScheduleColumnSocketType', "Column")
        self.inputs.new('MaStroScheduleAttributeRefSocketType', "Attribute Name")
        self.outputs.new('MaStroScheduleColumnSocketType', "Selection")
        self.outputs.new('MaStroScheduleColumnSocketType', "Inverted")

    @property
    def column_label(self):
        # The chosen Attribute Name itself (e.g. "floor"), NOT the
        # upstream Column's own column_label (which only ever
        # describes ONE attribute - typically whichever one happens to
        # be _data_key's own first-found pick - and reads as wrong/
        # misleading once Selection has isolated a DIFFERENT attribute
        # entirely). Confirmed live as a real bug otherwise: Selection
        # carrying Floor's own values showed up in the Viewer labeled
        # "Area" (whatever the upstream Column's own first attribute
        # happened to be), since the Viewer's own single-data-key
        # relabeling path (nodes_viewer.py) reads straight off
        # column_label with no awareness of WHICH output socket
        # (Selection vs Inverted) it's actually looking at - column_label
        # is one property per NODE, not per output socket, the same
        # structural limit every other column_label in this codebase
        # already has (see tree.py's own upstream_attr, which discards
        # from_socket entirely). Inverted (potentially several
        # attributes at once) still falls back to whatever this
        # reports when the Viewer's own multi-data-key path can't use
        # it anyway - not a perfect label for that case, but no worse
        # than before, and the common single-attribute-left-in-Inverted
        # case still reads correctly.
        if "Attribute Name" not in self.inputs:
            return ""
        from .tree import upstream_attr
        attribute_ref = upstream_attr(self.inputs["Attribute Name"], "name_value")
        return attribute_ref or upstream_attr(self.inputs["Column"], "column_label")

    def evaluate(self, inputs):
        rows = inputs[0] or []
        attribute_ref = inputs[1] or []
        if not rows:
            return [rows, rows]

        chosen_name = attribute_ref[0].get("Name") if attribute_ref else None
        if not chosen_name:
            # Nothing chosen - Selection has no data to isolate, every
            # attribute stays in Inverted (the same "don't silently
            # produce something plausible-but-wrong, make the gap
            # visible" spirit as the rest of this picker's own
            # fallbacks, here meaning an empty Selection rather than
            # guessing which attribute was meant).
            return [[{k: v for k, v in row.items() if k.startswith("_")} for row in rows], rows]

        tree = self.id_data
        data_key = _resolve_data_key(tree, rows[0], chosen_name)

        selection = []
        inverted = []
        for row in rows:
            id_items = {k: v for k, v in row.items() if k.startswith("_")}
            selection_row = dict(id_items)
            if data_key in row:
                selection_row[data_key] = row[data_key]
            selection.append(selection_row)
            inverted_row = dict(id_items)
            for key, value in row.items():
                if key.startswith("_") or key == data_key:
                    continue
                inverted_row[key] = value
            inverted.append(inverted_row)

        return [selection, inverted]


classes = (
    MaStroScheduleColumnSeparateNode,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
