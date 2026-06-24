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


# Accepts a link from any other MaStro Schedule socket type without being
# flagged as a mismatch (tree.py:mark_mismatched_links/eval_node skip it
# entirely) - used by the Viewer's input, so it can debug whatever a node
# happens to output, and transparently for links passing through a native
# NodeReroute (Blender always creates that type on Shift+RMB drag, with its
# own native socket type - see tree.py:resolve_through_reroutes). This
# socket carries no structural guarantee, unlike Data/Column - the
# receiving node's evaluate() inspects the actual row shape at runtime.
class MaStroScheduleAnySocket(NodeSocket):
    """Generic socket - accepts any MaStro Schedule connection"""
    bl_idname = 'MaStroScheduleAnySocketType'
    bl_label = "Any"

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        # Blender's C side picks draw_color vs draw_color_simple per
        # socket type internally (node_draw.cc: falls back to
        # draw_color_simple only if draw_color is unset on that type) -
        # that fallback isn't exposed as an ordinary Python method
        # lookup, so calling `.draw_color(...)` on a linked socket whose
        # type only defines draw_color_simple (true for our Data/Column/
        # Attribute sockets) could AttributeError. draw_color_simple()
        # is always present on every socket type in this addon, so reading
        # that classmethod directly is the safe way to mirror the linked
        # socket's color here.
        other = None
        if self.is_output:
            if self.is_linked and self.links:
                other = self.links[0].to_socket
        elif self.is_linked and self.links:
            # Resolve through any native NodeReroute chain (always
            # created by Shift+RMB drag) to the real socket - otherwise
            # a Reroute between this socket and the real one would make
            # `other` the Reroute's own native socket, which has no
            # draw_color_simple, always falling back to plain gray.
            from .tree import resolve_through_reroutes
            _from_node, other = resolve_through_reroutes(self.links[0])
        if other is not None:
            simple = getattr(type(other), "draw_color_simple", None)
            if simple is not None:
                return simple()
        return (0.8, 0.8, 0.8, 1.0)

    @classmethod
    def draw_color_simple(cls):
        return (0.8, 0.8, 0.8, 1.0)


# A Column's rows hold only id keys (_Object, and one of _Face/_Edge/
# _Vertex/_Level depending on Field) plus exactly one data key. That data
# key is the producing node's own node.name - stable and guaranteed
# unique by Blender, used as the Column's identity for joining several
# Columns into a Table later on (matching rows by their shared id keys),
# never by its user-facing label (read separately, e.g. from the Name
# chosen on Get Attribute Names) - two Columns can have the same label
# (e.g. both "area") without colliding, since they're still different
# node.names.
class MaStroScheduleColumnSocket(NodeSocket):
    """Socket carrying a single Column (one attribute's worth of data)"""
    bl_idname = 'MaStroScheduleColumnSocketType'
    bl_label = "Column"

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    @classmethod
    def draw_color_simple(cls):
        return (0.6, 0.9, 0.3, 1.0)
