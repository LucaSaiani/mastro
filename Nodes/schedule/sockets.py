from bpy.types import NodeSocket


class MaStroScheduleDataSocket(NodeSocket):
    """Socket carrying a MaStro schedule table (a list of row dicts)"""
    bl_idname = 'MaStroScheduleDataSocketType'
    bl_label = "Data"

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    @classmethod
    def draw_color_simple(cls):
        return (0.4, 0.7, 1.0, 1.0)


class MaStroScheduleAttributeRefSocket(NodeSocket):
    """Socket carrying a reference to one attribute (Field + Name), as
    produced by Get Attribute Names - not a table of rows, so it gets its
    own color to keep it visually distinct from a MaStroScheduleDataSocket
    and prevent miswiring (e.g. plugging Objects where Name is expected)"""
    bl_idname = 'MaStroScheduleAttributeRefSocketType'
    bl_label = "Attribute"

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    @classmethod
    def draw_color_simple(cls):
        return (1.0, 0.6, 0.2, 1.0)


class MaStroScheduleAnySocket(NodeSocket):
    """Socket that accepts a link from any other MaStro Schedule socket
    type (Data/Column/Attribute) without being flagged as a mismatch -
    used only by the Viewer's input, so it works for debugging whatever
    a node happens to output, instead of being limited to one specific
    shape. tree.py's mark_mismatched_links() skips this socket's links
    entirely (matching by from_socket.bl_idname would otherwise flag
    every link into it). evaluate() on the receiving node inspects the
    actual row shape at runtime (one data key vs several, or no rows at
    all) to decide how to interpret it - this socket itself carries no
    structural guarantee, unlike Data/Column."""
    bl_idname = 'MaStroScheduleAnySocketType'
    bl_label = "Any"

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    @classmethod
    def draw_color_simple(cls):
        return (0.8, 0.8, 0.8, 1.0)


class MaStroScheduleColumnSocket(NodeSocket):
    """Socket carrying a single Column: a list of row dicts each holding
    only id keys (_Object, and one of _Face/_Edge/_Vertex/_Level
    depending on Field) plus exactly one data key. That data key is the
    producing node's own node.name - stable and guaranteed unique by
    Blender, used as the Column's identity for joining several Columns
    into a Table later on (matching rows by their shared id keys), never
    by its user-facing label (read separately, e.g. from the Name chosen
    on Get Attribute Names) - two Columns can have the same label
    (e.g. both "area") without colliding, since they're still different
    node.names.

    Distinct color from Data (a multi-column Table) and Attribute (a
    Field+Name reference, not row data at all) to keep the three from
    being miswired into each other."""
    bl_idname = 'MaStroScheduleColumnSocketType'
    bl_label = "Column"

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    @classmethod
    def draw_color_simple(cls):
        return (0.6, 0.9, 0.3, 1.0)
