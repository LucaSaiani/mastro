from bpy.types import Node
from bpy.props import StringProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node, is_socket_active


# Renames a Column's header independently of the node that produced it -
# the same separation of concerns as Math (transforms a Column's value
# without taking over its identity): this transforms a Column's label
# without touching its rows or data key. The new header comes from a
# String input rather than a property on this node itself, so the same
# name can be typed once (on a String node) and reused across several
# Header nodes.
class MaStroScheduleHeaderNode(MaStroScheduleTreeNode, Node):
    """Rename a column header, on a Column"""
    bl_idname = 'MaStroScheduleHeader'
    bl_label = 'Rename Header'

    # Cache of the String input's last resolved value, written by
    # evaluate() below - a plain Python attribute wouldn't reliably
    # persist on a bpy.types.Node instance, this needs to be a real
    # property. No leading underscore - untested whether Blender's RNA
    # system treats that specially, and no existing property in this
    # codebase does it, so there's no established precedent to rely on.
    cached_header_text: StringProperty(default="")
    # Backing value for the String socket's inline text field
    # (NodeSocket.prop_name, see sockets.py:MaStroScheduleStringSocket) -
    # same mechanism as Math's value_a/value_b: editable directly on the
    # socket while unlinked, read from the actual linked node's output
    # instead once a String node is plugged in.
    string_value: StringProperty(name="String", update=update_node)

    def init(self, context):
        self.inputs.new('MaStroScheduleColumnSocketType', "Column")
        self.inputs.new('MaStroScheduleStringSocketType', "String").prop_name = "string_value"
        self.outputs.new('MaStroScheduleColumnSocketType', "Column")

    @property
    def column_label(self):
        # No String value at all (unlinked AND the inline field left
        # empty) means "don't rename" - the user's explicit call, to
        # stop a Rename Header with nothing typed into String from
        # turning the Column's existing label into an empty one. Falls
        # through to the upstream Column's own label instead, the same
        # way a muted node would (see tree.py:resolve_through_reroutes) -
        # this node is meant to act as if it weren't there at all in
        # that case.
        if not self.cached_header_text:
            from .tree import upstream_attr
            return upstream_attr(self.inputs["Column"], "column_label")
        return self.cached_header_text

    def evaluate(self, inputs):
        # Stashed on self rather than recomputed in column_label - that
        # property has no access to eval_node's resolved input_values,
        # only to this node's own properties/links, and the String
        # input's actual value (typed locally or fed from an upstream
        # String node) is only available here.
        #
        # An unlinked socket always comes through as None (eval_node
        # doesn't read prop_name on its own - confirmed in
        # execution.py:eval_node, same as Math's value_a/value_b), so
        # string_value (the inline field's own backing property) is read
        # explicitly for that case rather than assuming inputs[1] holds
        # it.
        if is_socket_active(self.inputs["String"]):
            self.cached_header_text = inputs[1] or ""
        else:
            self.cached_header_text = self.string_value
        return [inputs[0] or []]
