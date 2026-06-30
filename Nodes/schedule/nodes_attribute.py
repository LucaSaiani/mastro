import bpy
from bpy.types import Node, Operator
from bpy.props import EnumProperty, StringProperty

from .tree import MaStroScheduleTreeNode, downstream_main_inputs
from .execution import update_node, linked_table
from .attribute_naming import FIELD_DOMAINS, to_logical_name, COMPUTED_NAMES, HIDDEN_NAMES

# mastro_props fields exposed as pseudo object-level attributes, alongside
# the object's own custom properties (obj.keys()).
OBJECT_MASTRO_PROPS = ("Block", "Building")


def unique_objects(node, input_index=0):
    """Resolve the distinct MaStro objects referenced by the table feeding
    `node`'s input at `input_index` (typically Input Mesh All/Selected)."""
    objs = []
    table = linked_table(node, input_index)
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
            if logical not in names and logical not in HIDDEN_NAMES:
                names.append(logical)
        if is_temp_mesh:
            bpy.data.meshes.remove(mesh)
    return names


def _column_data_keys(node, socket):
    """(technical_key, readable_label) pairs for every distinct non-id
    (data) key present on whatever Column/List feeds `socket` on
    `node` - e.g. [("Evaluate Attribute", "area"), ("Evaluate
    Attribute.001", "use")] after a Merge List combined two Evaluate
    Attribute branches (nodes_merge_list.py). Mirrors
    nodes_id_keys.py's own _id_keys_for_socket (same multi-link/
    List-vs-Column handling), collecting keys that DON'T start with
    "_" instead of ones that do.

    A row's own data key is always some node's own node.name (NOT a
    readable name - see nodes_evaluate.py's own evaluate(), "key =
    self.name", and that module's own comment for why: a stable,
    Blender-guaranteed-unique identity, so two Columns that happen to
    share the same user-facing label - e.g. both "area" - never
    collide once merged) - resolved here back to THAT node's own
    column_label for display, the same lookup-by-name nodes_viewer.py's
    own multi-data-key relabeling does (confirmed live as the matching
    bug otherwise: this function originally returned the raw technical
    keys themselves, so Aggregate's own picker showed "Evaluate
    Attribute"/"Evaluate Attribute.001" instead of "area"/"use")."""
    from .tree import resolve_through_reroutes
    from .execution import get_node_table

    tree = node.id_data
    pairs = []
    seen = set()
    if not socket.is_linked:
        return pairs
    is_list_socket = socket.bl_idname == 'MaStroScheduleListSocketType'
    for link in socket.links:
        if link.is_muted:
            continue
        from_node, from_socket = resolve_through_reroutes(link)
        if from_node is None or from_socket.bl_idname != socket.bl_idname:
            continue
        table = get_node_table(tree.name, from_node.name)
        if not table:
            continue
        try:
            output_index = list(from_node.outputs).index(from_socket)
        except ValueError:
            continue
        value = table[output_index] or []
        rows = [row for group in value for row in group.get("rows", [])] if is_list_socket else value
        for row in rows:
            for key in row.keys():
                if key.startswith("_") or key in seen:
                    continue
                seen.add(key)
                source_node = tree.nodes.get(key)
                label = getattr(source_node, "column_label", "") if source_node else ""
                pairs.append((key, label or key))
    return pairs


def available_attribute_names(get_attribute_names_node):
    """(value, label) pairs for every attribute name available to pick
    from this Named Attribute node's own output, found by walking
    FORWARD (downstream_main_inputs, tree.py) to whatever real node(s)
    consume it - NOT a Data input this node carries itself (removed -
    a second, independently-wired input here was a real, silent
    mismatch risk, same reasoning as Id Keys' own redesign,
    nodes_id_keys.py).

    value is what actually gets stored in name_value/sent downstream;
    label is what the picker popup shows. For the Evaluate Attribute
    case these are the same string (the chosen attribute's own
    already-readable name, e.g. "area"). For the Aggregate case they
    differ - value is the Column's own technical data key (some node's
    own node.name, e.g. "Evaluate Attribute.001" - the actual dict key
    Aggregate's own evaluate() needs to look a row up by), label is
    that SAME node's own column_label ("use") - see _column_data_keys'
    own docstring for why those two are different at all.

    Two different kinds of consumer are handled, intersected together
    when both are wired at once (rare, but not disallowed - the same
    "only offer what's safe for every consumer" rule Id Keys' own
    available_id_keys already follows for multiple consumers of the
    same kind):

    - Evaluate Attribute's own Data input - logical attribute names
      read off the real MaStro objects feeding it (mesh attributes/
      object custom properties), the ORIGINAL and still most common
      use of this node.

    - Aggregate's own Column input (or any other Column/List-consuming
      node sharing this node's column_label-blind "which data key do
      you mean" problem) - the COLUMN'S OWN already-present data keys
      (e.g. "Area"/"Use" after a Merge List, nodes_merge_list.py) -
      added once Aggregate was confirmed live to always silently pick
      the FIRST data key by exclusion (_data_key,
      nodes_aggregate_column.py) whenever a Column carried more than
      one, with no way to choose - this is the picker for that choice.
      The user's own explicit design call: ONE node covers both cases
      automatically (which one applies is read straight off whichever
      real node this one happens to be wired into), rather than a
      second, separate node the user would otherwise need to know to
      reach for - simpler to discover, at the cost of this function
      having to branch on what kind of consumer it found.

    Still the intersection, not the union, across every object/Column
    AND every consumer found - Input Mesh (All) is meant to grow into
    mixing heterogeneous MaStro categories (Mass, Block, Plan, Drawing,
    Street, generic Mesh), which don't all share the same attributes;
    showing only names available everywhere means the user is never
    offered a name that would silently come back None/missing for some
    of them (the None-row fallback in nodes_evaluate.py stays in place
    as a safety net for cases that slip through this anyway, e.g. an
    attribute removed after this list was built).

    Same KNOWN LIMITATION as Id Keys' own available_id_keys
    (nodes_id_keys.py): only reads one level upstream of each consumer -
    if a consumer's own input is itself fed by another node that needs
    something from this node to produce anything, that chain isn't
    resolved here."""
    pairs = downstream_main_inputs(get_attribute_names_node.outputs["Attribute Name"], 'MaStroScheduleAttributeRefSocketType')
    if not pairs:
        return []
    field = get_attribute_names_node.field
    common = None
    first_values = None
    label_by_value = {}
    for consumer, socket in pairs:
        if socket.bl_idname == 'MaStroScheduleDataSocketType':
            try:
                input_index = list(consumer.inputs).index(socket)
            except ValueError:
                continue
            objs = unique_objects(consumer, input_index)
            if not objs:
                return []
            for obj in objs:
                obj_names = _object_attribute_names(obj, field)
                for name in obj_names:
                    label_by_value[name] = name
                obj_name_set = set(obj_names)
                common = obj_name_set if common is None else (common & obj_name_set)
                if not common:
                    return []
                if first_values is None:
                    first_values = obj_names
        else:
            # A Column/List consumer (e.g. Aggregate's own "Column"
            # input) - read the data keys already present on it
            # directly, rather than treating it as a MaStro
            # object/Field lookup at all.
            key_label_pairs = _column_data_keys(consumer, socket)
            if not key_label_pairs:
                return []
            for value, label in key_label_pairs:
                label_by_value[value] = label
            value_set = {value for value, _label in key_label_pairs}
            common = value_set if common is None else (common & value_set)
            if not common:
                return []
            if first_values is None:
                first_values = [value for value, _label in key_label_pairs]
    if not common or first_values is None:
        return []
    # Preserve the first match's own order for a stable, predictable list.
    return [(value, label_by_value.get(value, value)) for value in first_values if value in common]


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
    pairs = available_attribute_names(node)
    # Capitalized for DISPLAY only (Get Id Keys' own picker already
    # does the same via nodes_viewer.py's own _header_text) - value
    # itself (what actually gets stored in name_value, matched against
    # row keys elsewhere - see nodes_aggregate_column.py's own
    # _resolve_data_key) stays exactly as-is, never capitalized, so
    # this is purely cosmetic. The user's own explicit ask, after
    # noticing Id Key entries (already capitalized) and Attribute
    # entries (shown raw) looked inconsistent side by side.
    from .nodes_viewer import _header_text
    return [(value, _header_text(label), "") for value, label in pairs] or [("", "(no attributes)", "")]


# Search popup for Named Attribute's Name field, instead of a permanent
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
    """update= callback for Named Attribute's Field - a module-level
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
    bl_label = 'Named Attribute'

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
        # No Data input of its own (removed - see
        # available_attribute_names' own docstring for why a second,
        # independently-wired input was a real, silent mismatch risk) -
        # this node's own picker now reads Data straight off whatever
        # real node(s) consume its Attribute Name output instead (e.g.
        # Evaluate Attribute's own Data input).
        self.outputs.new('MaStroScheduleAttributeRefSocketType', "Attribute Name")

    def draw_buttons(self, context, layout):
        layout.prop(self, "field")
        # Always shown, no "connect something first" placeholder text -
        # mirrors Id Keys' own draw_buttons (nodes_id_keys.py),
        # which never had one either; the popup itself already says
        # "(no attributes)" when available_attribute_names finds
        # nothing (_pick_attribute_name_items' own fallback below) -
        # no need to say the same thing twice in two different ways.
        # Capitalized for display, same as Id Keys' own draw_buttons
        # (nodes_id_keys.py) - self.name_value itself stays exactly
        # as picked, only the button's own text is run through
        # _header_text.
        from .nodes_viewer import _header_text
        op = layout.operator(
            "node.mastro_schedule_pick_attribute_name",
            text=_header_text(self.name_value) if self.name_value else "(pick a name)",
        )
        op.tree_name = self.id_data.name
        op.node_name = self.name

    def evaluate(self, inputs):
        name_ref = [{"Field": self.field, "Name": self.name_value}] if self.name_value else []
        return [name_ref]
