import bpy
from bpy.types import Node, Operator
from bpy.props import EnumProperty, StringProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node, linked_table
from .attribute_naming import FIELD_DOMAINS, to_logical_name, COMPUTED_NAMES

# mastro_props fields exposed as pseudo object-level attributes, alongside
# the object's own custom properties (obj.keys()).
OBJECT_MASTRO_PROPS = ("Block", "Building")


def unique_objects(node):
    """Resolve the distinct MaStro objects referenced by the table feeding
    this node's Data input (typically Input Mesh All/Selected)."""
    objs = []
    table = linked_table(node, 0)
    if table:
        seen = set()
        for row in table:
            name = row.get("_Object")
            if name is None or name in seen:
                continue
            obj = bpy.data.objects.get(name)
            if obj is not None:
                seen.add(name)
                objs.append(obj)
    return objs


def _object_attribute_names(obj, field):
    """Logical attribute names present on a single object for the given
    Field: object custom properties for 'Object', or mesh attributes of
    the matching domain for Vertex/Edge/Face (domain suffix stripped, and
    multi-component groups like use/storey/height collapsed to one
    name). Order preserved, no duplicates."""
    names = []
    if field == 'OBJECT':
        for name in OBJECT_MASTRO_PROPS:
            if name not in names:
                names.append(name)
        for key in obj.keys():
            # "_RNA_UI" is Blender's own internal UI-metadata id-property,
            # not a real custom property - everything else, including
            # mastro's own underscore-prefixed custom properties (see
            # property_classes_custom_properties.py), is real data.
            if key != "_RNA_UI" and key not in names:
                names.append(key)
    else:
        for computed in COMPUTED_NAMES.get(field, ()):
            if computed not in names:
                names.append(computed)
        domain = FIELD_DOMAINS[field]
        from .nodes_evaluate import _resolve_attribute_mesh
        mesh, is_temp_mesh = _resolve_attribute_mesh(obj)
        for attr in mesh.attributes:
            if attr.domain != domain:
                continue
            logical = to_logical_name(attr.name, field)
            if logical not in names:
                names.append(logical)
        if is_temp_mesh:
            bpy.data.meshes.remove(mesh)
    return names


def available_attribute_names(node):
    """List the logical attribute names common to EVERY object feeding
    this node - the intersection, not the union. Input Mesh (All) is
    meant to grow into mixing heterogeneous MaStro categories (Mass,
    Block, Plan, Drawing, Street, generic Mesh), which don't all share
    the same attributes; showing only names every selected object
    actually has means the user is never offered a name that would
    silently come back None for some objects (the None-row fallback in
    nodes_evaluate.py stays in place as a safety net for cases that slip
    through this anyway, e.g. an attribute removed after this list was
    built)."""
    objs = unique_objects(node)
    if not objs:
        return []
    field = node.field
    common = None
    for obj in objs:
        obj_names = set(_object_attribute_names(obj, field))
        common = obj_names if common is None else (common & obj_names)
        if not common:
            return []
    # Preserve the first object's order for a stable, predictable list.
    first_names = _object_attribute_names(objs[0], field)
    return [name for name in first_names if name in common]


def _resolve_node(tree_name, node_name):
    tree = bpy.data.node_groups.get(tree_name)
    if tree is None:
        return None
    return tree.nodes.get(node_name)


def _pick_attribute_name_items(operator_self, context):
    """Module-level function, not a method on the operator class - an
    instance method referenced from an `items=` annotation evaluated at
    class-body time was confirmed (live, in the editor) to raise
    `AttributeError: ... object has no attribute '_get_node'` when Blender
    invokes the callback: by the time `option: EnumProperty(items=...)` is
    evaluated as part of the class body, methods defined later in that same
    body (`execute`, formerly `_get_node`) aren't bound/visible the way a
    plain function reference is. Sverchok's equivalent callbacks
    (`nodes/exchange/FCStd_spreadsheet.py`'s `LabelReader`) are also plain
    functions for the same reason."""
    node = _resolve_node(operator_self.tree_name, operator_self.node_name)
    if node is None:
        return [("", "(node not found)", "")]
    names = available_attribute_names(node)
    return [(name, name, "") for name in names] or [("", "(no attributes)", "")]


# Search popup for Get Attribute Names' Name field, instead of a permanent
# dynamic EnumProperty on the node itself. The node's `name_value` is a
# plain StringProperty - this operator computes the choices once when the
# popup opens and writes the result there, rather than the node owning a
# dynamic-items EnumProperty that Blender would keep re-validating on its
# own schedule (redraws, undo, topology changes). That re-validation,
# while walking this node's input link back to its source table, was
# confirmed (headless Blender isolation) to recurse into a real
# RecursionError - re-entering Blender's own node-update machinery before
# the items callback returns. No node anywhere in Sverchok
# (github.com/nortikin/sverchok, a long-established Blender node addon)
# has a permanent dynamic-items EnumProperty either - it solves "pick from
# a dynamic list" the same way, via a temporary EnumProperty on a
# search-popup operator (e.g. nodes/exchange/FCStd_spreadsheet.py).
class MASTRO_OT_Schedule_Pick_Attribute_Name(Operator):
    """Pick the attribute Name to read"""
    bl_idname = "node.mastro_schedule_pick_attribute_name"
    bl_label = "Pick Attribute Name"
    bl_options = {'INTERNAL', 'REGISTER'}
    bl_property = "option"

    tree_name: StringProperty()
    node_name: StringProperty()
    option: EnumProperty(items=_pick_attribute_name_items)

    def execute(self, context):
        node = _resolve_node(self.tree_name, self.node_name)
        if node is not None:
            node.name_value = self.option
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {'FINISHED'}


def _on_field_changed(node, context):
    """update= callback for Get Attribute Names' Field - a module-level
    function, matching the rest of the codebase's convention for
    update=/items= callbacks (e.g. nodes_viewer.py's
    _on_show_table_changed), not a method on the node class.

    A name_value picked for the previous Field (e.g. "area" under Face)
    is silently wrong under a different Field - Evaluate Attribute
    doesn't error on it, it just produces an empty/bogus value (e.g.
    _evaluate_object falling through to obj.get("area", "") on a
    Field=Object switch, which never has an "area" custom property).
    Clearing it forces the user to pick a name that's actually valid for
    the new Field, instead of leaving a stale one that looks set but
    silently evaluates to nothing."""
    node.name_value = ""
    update_node(node, context)


class MaStroScheduleGetAttributeNamesNode(MaStroScheduleTreeNode, Node):
    """List the attribute names available for the chosen Field (Object
    custom property, or Vertex/Edge/Face mesh attribute) on the objects
    feeding the Data input - names only, no values. Pick one with the Name
    button to feed it to an Evaluate Attribute node, which reads the
    actual values"""
    bl_idname = 'MaStroScheduleGetAttributeNames'
    bl_label = 'Get Attribute Names'

    # field's items are a fixed, static list - this one is safe as a
    # normal EnumProperty (no items callback, nothing reads upstream link
    # data to build it). name_value is a plain StringProperty written by
    # MASTRO_OT_Schedule_Pick_Attribute_Name's search popup - see that
    # operator's docstring for why Name is deliberately NOT a dynamic
    # EnumProperty on the node itself.
    field: EnumProperty(
        name="Field",
        items=[
            ('OBJECT', "Object", "Object custom property"),
            ('FACE', "Face", "Face-domain mesh attribute"),
            ('EDGE', "Edge", "Edge-domain mesh attribute"),
            ('VERTEX', "Vertex", "Vertex-domain mesh attribute"),
        ],
        default='FACE',
        update=_on_field_changed,
    )
    name_value: StringProperty(name="Name", update=update_node)

    def init(self, context):
        self.inputs.new('MaStroScheduleDataSocketType', "Data")
        self.outputs.new('MaStroScheduleAttributeRefSocketType', "Attribute Name")

    def draw_buttons(self, context, layout):
        layout.prop(self, "field")
        if self.is_valid:
            op = layout.operator(
                "node.mastro_schedule_pick_attribute_name",
                text=self.name_value or "(pick a name)",
            )
            op.tree_name = self.id_data.name
            op.node_name = self.name
        else:
            layout.label(text="Connect Data to a Viewer", icon='INFO')

    def evaluate(self, inputs):
        name_ref = [{"Field": self.field, "Name": self.name_value}] if self.name_value else []
        return [name_ref]
