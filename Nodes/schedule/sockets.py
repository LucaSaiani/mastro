from bpy.types import NodeSocket
from bpy.props import StringProperty


class MaStroScheduleDataSocket(NodeSocket):
    """Socket carrying a MaStro schedule table (a list of row dicts)"""
    bl_idname = 'MaStroScheduleDataSocketType'
    bl_label = "Data"

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    @classmethod
    def draw_color_simple(cls):
        return (0.0, 214 / 255, 163 / 255, 1.0)


class MaStroScheduleAttributeRefSocket(NodeSocket):
    """Socket carrying a reference to one attribute (Field + Name), as
    produced by Get Attribute Names - not a table of rows, so it gets its
    own color to keep it visually distinct from a MaStroScheduleDataSocket
    and prevent miswiring (e.g. plugging Objects where Name is expected)"""
    bl_idname = 'MaStroScheduleAttributeRefSocketType'
    # Matches the instance name used on the actual sockets of this type
    # (Get Attribute Names' output, Evaluate Attribute's input - see
    # nodes_attribute.py/nodes_evaluate.py) - the Viewer's generic input
    # (MaStroScheduleAnySocket.draw) shows THIS bl_label, not the
    # instance name, when something of this type is plugged in, so the
    # two need to read the same to the user or the Viewer's label looks
    # like a typo/mismatch (confirmed live: showed "Attribute" here
    # while the actual socket said "Attribute Name").
    bl_label = "Attribute Name"

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    @classmethod
    def draw_color_simple(cls):
        # A darker shade of rgb(112, 178, 255) (0.7x value, same hue) -
        # that exact color is reserved for the future String socket
        # type, not yet introduced, so this stays visually related
        # (same family) but distinct (darker) rather than colliding once
        # String exists.
        return (112 / 255 * 0.7, 178 / 255 * 0.7, 255 / 255 * 0.7, 1.0)


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
    # No bl_label - draw() below intentionally shows no text at all while
    # unlinked, so a fixed bl_label would never actually appear; it would
    # only mislead anyone reading this class about what the socket
    # displays.

    def _linked_socket(self):
        """The real socket on the other end of this one's link, resolved
        through any native NodeReroute chain (see
        tree.py:resolve_through_reroutes) - or None if unlinked. Shared
        by draw() and draw_color() below, which both need to know what
        this socket is actually connected to."""
        if self.is_output:
            if self.is_linked and self.links:
                return self.links[0].to_socket
            return None
        if self.is_linked and self.links:
            from .tree import resolve_through_reroutes
            _from_node, from_socket = resolve_through_reroutes(self.links[0])
            return from_socket
        return None

    def draw(self, context, layout, node, text):
        # No label while unlinked - this socket carries no structural
        # guarantee of its own (see the module-level comment above), so
        # a fixed name here would claim a meaning the socket doesn't
        # actually have until something is plugged in. Once linked, show
        # the connected socket's own label instead - what the Viewer (or
        # whatever node owns this socket) is actually displaying.
        other = self._linked_socket()
        layout.label(text=other.bl_label if other is not None else "")

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
        other = self._linked_socket()
        if other is not None:
            simple = getattr(type(other), "draw_color_simple", None)
            if simple is not None:
                return simple()
        return self.draw_color_simple()

    @classmethod
    def draw_color_simple(cls):
        return (51 / 255, 51 / 255, 51 / 255, 1.0)


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
    # bl_label only - the displayed text, not the class/bl_idname (kept
    # as "Column" everywhere in code/comments, this is purely the
    # user-facing name). "Number Column" to leave room for a future
    # "String Column" socket type without "Column" alone being ambiguous
    # about what kind of data it carries - applies the same way whether
    # the Column holds one row (e.g. the Value node's constant) or many.
    bl_label = "Number Column"

    # Native Blender mechanism (NodeSocket.prop_name, not Sverchok-
    # specific - Blender's own socket types use the same thing): a node
    # sets e.g. self.inputs["B"].prop_name = "b_value" once, in init(),
    # and this draws a live editable field for that property right on
    # the socket whenever it isn't linked - lets a node like Math take a
    # constant typed directly into the socket, without needing a
    # separate Value node wired in just to provide one number.
    prop_name: StringProperty(default="")

    def draw(self, context, layout, node, text):
        if not self.is_output and not self.is_linked and self.prop_name:
            layout.prop(node, self.prop_name, text=text)
        else:
            layout.label(text=text)

    @classmethod
    def draw_color_simple(cls):
        return (161 / 255, 161 / 255, 161 / 255, 1.0)
