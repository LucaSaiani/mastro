from bpy.types import Node
from bpy.props import IntProperty, StringProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node, is_socket_active


# A Column with no upstream at all - rows of empty values, ready to be
# filled in or used as a placeholder while building a tree (the same role
# Mesh > Add > Cube/Plane plays for geometry: a primitive to start from,
# not a real data source). header is the ONLY source for this Column's
# label, there being no upstream to inherit one from - a Rename Header
# node (nodes_header.py) can still override it afterwards, the same way
# it overrides any other Column's label.
class MaStroScheduleColumnPrimitiveNode(MaStroScheduleTreeNode, Node):
    """Create an empty Column with the given number of rows"""
    bl_idname = 'MaStroScheduleColumnPrimitive'
    bl_label = 'Column'

    # Backing values for Header/Rows' inline fields (NodeSocket.prop_name,
    # same mechanism as Math's value_a/value_b) - editable directly on
    # the socket while unlinked, read from the actual linked node's
    # output instead once something is plugged in (a String node for
    # Header, an Integer/Value/another Column for Rows).
    row_count: IntProperty(name="Rows", default=1, min=1, update=update_node)
    # Default "" not "Column" - the placeholder text shown inside the
    # empty field (see sockets.py:MaStroScheduleStringSocket.draw) is
    # "Title" (the socket's own name), which already tells the user
    # what to type without needing a fake starting value here too.
    header: StringProperty(name="Title", default="", update=update_node)
    # Cache of the Header input's last resolved value, written by
    # evaluate() below - column_label has no access to eval_node's
    # resolved input_values, only this node's own properties/links, same
    # reasoning as Rename Header's cached_header_text.
    cached_header_text: StringProperty(default="")

    def init(self, context):
        # Rows first, then Title - matches the user's explicit ordering
        # call (the numeric field that defines the Column's shape comes
        # before the cosmetic one that just labels it).
        self.inputs.new('MaStroScheduleColumnSocketType', "Rows").prop_name = "row_count"
        self.inputs.new('MaStroScheduleStringSocketType', "Title").prop_name = "header"
        self.outputs.new('MaStroScheduleColumnSocketType', "Column")

    @property
    def column_label(self):
        return self.cached_header_text

    def evaluate(self, inputs):
        # Same "unlinked socket always comes through as None" handling
        # as Rename Header/Math - read the inline field's own backing
        # property explicitly when unlinked, rather than assuming
        # inputs[...] holds it. Rows is inputs[0], Title is inputs[1] -
        # matches init()'s socket order above.
        if is_socket_active(self.inputs["Rows"]):
            rows_in = inputs[0] or []
            row_count = 0
            if rows_in:
                row_key = next((k for k in rows_in[0] if not k.startswith("_")), None)
                row_count = int(rows_in[0].get(row_key, 0)) if row_key else 0
        else:
            row_count = self.row_count

        if is_socket_active(self.inputs["Title"]):
            self.cached_header_text = inputs[1] or ""
        else:
            self.cached_header_text = self.header

        # _Object as the id key, numbered positionally (Row 0, Row 1,
        # ...) - there's no real object behind these rows, but every
        # other Column shares the same id-key shape (see sockets.py:
        # MaStroScheduleColumnSocket's docstring), so this stays
        # consistent with that rather than inventing a Column with no id
        # key at all.
        key = self.name
        # No clamping here - min=1 on row_count only constrains the
        # inline field's UI slider (the user's call: if a linked socket
        # provides 0 or a negative value on purpose, that's what's used,
        # not silently forced up to 1). range() already returns nothing
        # for a value <= 0, no special-casing needed.
        return [[{"_Object": f"Row {i}", key: 0.0} for i in range(row_count)]]
