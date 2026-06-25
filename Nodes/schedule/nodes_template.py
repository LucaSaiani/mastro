# NOT REGISTERED - not imported/added to __init__.py's classes tuple,
# not in any Add menu. A reference skeleton only, kept here so writing a
# new Column-producing node starts from a checklist of the patterns
# every node in this tree is expected to follow - found, one at a time,
# by forgetting them on a real node first (Header/Column to Table missed
# mute support; A's copy-paste race was found on Math, then needed again
# elsewhere). Centralizing each pattern into a shared function (tree.py,
# execution.py) means most nodes need ZERO code for it - mute, for
# instance, needs nothing here at all anymore, see the note below. What
# remains is the handful of patterns that still require a node to call a
# specific helper or shape its init()/evaluate() a specific way - this
# file exists so that's a checklist, not something to remember from
# scratch each time.
#
# Copy this file's class body as a starting point, then delete whatever
# doesn't apply (e.g. a node with one input doesn't need the
# "momentarily absent after copy-paste" guards at all).

from bpy.types import Node
from bpy.props import FloatProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node


class MaStroScheduleTemplateNode(MaStroScheduleTreeNode, Node):
    """One-line, user-facing description - shown as this node's tooltip,
    so keep it short and about WHAT the node does, not HOW (see
    nodes_attribute.py's MASTRO_OT_Schedule_Pick_Attribute_Name for an
    example of a docstring that grew into a multi-paragraph technical
    essay and ended up as the literal in-editor tooltip - move that kind
    of reasoning into a comment above the class instead, like this one)."""
    bl_idname = 'MaStroScheduleTemplate'
    bl_label = 'Template'

    # === MUTE ===
    # Nothing to do here. tree.py:resolve_through_reroutes already walks
    # straight through a muted node via its first input, for every node
    # in this tree, with no per-node code at all - this used to require
    # a `mastro_internal_links` override (removed) because
    # bpy.types.Node.internal_links is only ever populated for built-in
    # C nodes, never for scripted ones, and silently producing no output
    # was the result of forgetting to override it on every node that
    # needed it. If THIS node has more than one input and the "obviously
    # correct" one to pass through when muted isn't simply "the first
    # one" (Math's A vs B was never actually a problem - both share the
    # same socket type, so first-input-found is already A), then mute
    # may need rethinking for this node specifically - that hasn't come
    # up yet, so there's no established pattern for it to follow here.

    # === INLINE CONSTANT INPUT (optional - only if this node takes a
    # Column/String/etc. that should also work as a typed-in constant
    # with nothing wired in, e.g. Math's A/B) ===
    # 1. A plain property backing the inline field:
    value_a: FloatProperty(name="A", update=update_node)
    # 2. In init(), set prop_name on the socket so it draws that field
    #    while unlinked (NodeSocket.prop_name, see sockets.py - native
    #    Blender mechanism, not specific to this addon):
    #        self.inputs.new('MaStroScheduleColumnSocketType', "A").prop_name = "value_a"
    # 3. In evaluate(), eval_node does NOT read prop_name automatically -
    #    an unlinked socket's input value always comes through as None,
    #    so check self.inputs["A"].is_linked explicitly and fall back to
    #    self.value_a yourself (see nodes_math.py's evaluate() or
    #    nodes_header.py's for two real examples of this exact check).

    # === "SOCKET MOMENTARILY ABSENT" GUARD (only needed if you read
    # self.inputs["SomeName"] from inside a property like column_label,
    # which Blender can invoke before init() has rebuilt sockets on a
    # freshly pasted copy - confirmed live, a real
    # 'bpy_prop_collection[key]: key "X" not found' warning) ===
    # Guard every such lookup:
    #     if "A" not in self.inputs:
    #         return ""  # or whatever this property's safe default is

    # === column_label (only if this node outputs a Number Column) ===
    # Every Column-producing node exposes a `column_label` @property -
    # not a method named `label`, which collides with bpy.types.Node's
    # own native `label` attribute (a same-named Python @property
    # doesn't reliably override it). If this node passes a Column
    # through unchanged (like Header, or Math), mirror the upstream
    # node's label via tree.py:upstream_attr instead of inventing a new
    # one - see nodes_math.py's column_label for the pattern.

    def init(self, context):
        self.inputs.new('MaStroScheduleColumnSocketType', "A").prop_name = "value_a"
        self.outputs.new('MaStroScheduleColumnSocketType', "Number Column")

    def evaluate(self, inputs):
        a_linked = self.inputs["A"].is_linked
        rows_a = inputs[0] if a_linked else [{self.name: self.value_a}]
        return [rows_a or []]
