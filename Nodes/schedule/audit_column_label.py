"""Not a registered module - run manually with `python3 audit_column_label.py`
from this directory whenever a node is added or refactored.

Checks several patterns nodes_template.py's own comments describe as
"every node in this tree is expected to follow", that nothing currently
enforces beyond remembering to re-read that file - this script is the
enforcement that comment alone couldn't be (confirmed missing in
practice: Item from List/Group Into List both shipped without
column_label before this script existed).

Checks, each independently extensible via its own EXEMPT set below:

1. COLUMN_LABEL: every node class (inherits Node, not PropertyGroup/
   Operator) that outputs a Column or List socket
   (MaStroScheduleColumnSocketType/MaStroScheduleListSocketType) should
   define a `column_label` property, so the Viewer (and Get Id Keys/
   Aggregate/etc.'s own pickers) can find a readable header by walking
   through pass-through nodes back to whatever originally produced the
   data.

2. EVALUATE: every node class should define `evaluate()` - one that
   doesn't never produces any output at all, almost certainly a mistake
   for any node that isn't purely a UI/picker helper.

3. PROPERTY_UPDATE: every bpy.props.*Property() assigned directly on a
   node class (not a PropertyGroup/Operator, and not one of the known
   internal-bookkeeping names in PROPERTY_NAME_EXEMPT below, e.g.
   *_value caches) should pass update=... - one that doesn't never
   triggers tree.py's re-evaluation when the user changes it (the
   user's own report behind nodes_math.py's comment: "without update=
   here, changing either property never flags this tree... to
   re-evaluate").

A flagged class/property that turns out to be a deliberate exception
(rare - most should follow the pattern) can be added to the relevant
EXEMPT set below, with a comment explaining why - the user's own
explicit call: start broad, narrow down false positives one at a time
as they're confirmed, rather than under-checking from the start.
"""

import ast
import pathlib

# (filename, class_name) pairs - only add with a comment justifying why
# this specific node is exempt from needing column_label.
COLUMN_LABEL_EXEMPT = {
    # A reference skeleton, never registered (see its own module
    # docstring) - not a real node, exists only to be copy-pasted from.
    ("nodes_template.py", "MaStroScheduleTemplateNode"),
    # A reference-only example for a collapsible-box UI pattern, never
    # registered (see its own module docstring) - not a Schedule node
    # at all, has no init() and so no sockets whatsoever (it only
    # exists to demonstrate draw_buttons' own panel-toggle trick).
    ("reference_collapsible_box_pattern.py", "MyCustomNode"),
}

# (filename, class_name) pairs - only add with a comment justifying why
# this specific node has no evaluate() (e.g. a pure menu/operator
# helper that was mistakenly picked up as a Node subclass).
EVALUATE_EXEMPT = {
    # Same reference-only exemption as COLUMN_LABEL_EXEMPT above.
    ("reference_collapsible_box_pattern.py", "MyCustomNode"),
}

# (filename, class_name, property_name) triples - only add with a
# comment justifying why this specific property deliberately has no
# update= (e.g. it's a read-only cache written from evaluate(), never
# meant to be user-editable in the first place).
PROPERTY_UPDATE_EXEMPT = {
    # panel_1_open/panel_2_open/prop_a/prop_b/prop_c
    # (reference_collapsible_box_pattern.py): a reference-only example,
    # never registered (see its own module docstring) - update= doesn't
    # matter for a node that's never actually instantiated in a real
    # tree.
    ("reference_collapsible_box_pattern.py", "MyCustomNode", "panel_1_open"),
    ("reference_collapsible_box_pattern.py", "MyCustomNode", "panel_2_open"),
    ("reference_collapsible_box_pattern.py", "MyCustomNode", "prop_a"),
    ("reference_collapsible_box_pattern.py", "MyCustomNode", "prop_b"),
    ("reference_collapsible_box_pattern.py", "MyCustomNode", "prop_c"),
    # cached_header_text (nodes_header.py/nodes_column_primitive.py):
    # written from evaluate()/draw_buttons reading the real input, never
    # directly edited by the user - update= would be a no-op (nothing
    # ever sets it through Blender's own UI).
    ("nodes_header.py", "MaStroScheduleHeaderNode", "cached_header_text"),
    ("nodes_column_primitive.py", "MaStroScheduleColumnPrimitiveNode", "cached_header_text"),
    # active_key_index/active_item_index: a UIList's own "which row is
    # selected" index, written by Blender's own template_list click
    # handling, never something the user types in expecting the tree to
    # re-run - changing which row is highlighted doesn't change any
    # actual data.
    ("nodes_groupby.py", "MaStroScheduleGroupByNode", "active_key_index"),
    ("nodes_lookup.py", "MaStroScheduleCategoryLookupNode", "active_item_index"),
    ("nodes_lookup.py", "MaStroScheduleMatrixLookupNode", "active_key_index"),
    ("nodes_table_join.py", "MaStroScheduleTableJoinNode", "active_table_index"),
    ("nodes_sheet_place.py", "MaStroScheduleSheetPlaceNode", "active_table_index"),
    # column_to_add (nodes_groupby.py): still-WIP dynamic-items
    # EnumProperty already flagged in its own TODO comment as a
    # RecursionError risk - left untouched until that node graduates
    # out of WIP (see project_schedule_nodes_roadmap memory), not papered
    # over with an update= that doesn't address the actual risk.
    ("nodes_groupby.py", "MaStroScheduleGroupByNode", "column_to_add"),
    # has_bg/has_text_colour/has_alignment (nodes_table_edit_header.py):
    # hidden bookkeeping flags, only ever flipped True by their own
    # _mark_touched() update= wrapper on the SIBLING property they
    # track (bg_value/text_colour_value/alignment) - never written
    # directly by the user, so they have no independent "user changed
    # this" moment of their own to trigger update= for.
    ("nodes_table_edit_header.py", "MaStroScheduleTableHeaderNode", "has_bg"),
    ("nodes_table_edit_header.py", "MaStroScheduleTableHeaderNode", "has_text_colour"),
    ("nodes_table_edit_header.py", "MaStroScheduleTableHeaderNode", "has_alignment"),
    # Same _mark_touched() pattern, same reasoning, on Edit Cell - a
    # copy of Edit Header's own approach (see this node's own docstring).
    ("nodes_table_edit_cell.py", "MaStroScheduleTableEditCellNode", "has_bg"),
    ("nodes_table_edit_cell.py", "MaStroScheduleTableEditCellNode", "has_text_colour"),
    ("nodes_table_edit_cell.py", "MaStroScheduleTableEditCellNode", "has_alignment"),
    # showing_table/showing_list/id_column_count (nodes_viewer.py):
    # internal cache flags written every evaluate() to record which
    # rendering path/column split is currently in effect - never
    # written by the user directly, same reasoning as cached_header_text
    # above.
    ("nodes_viewer.py", "MaStroScheduleViewerNode", "showing_table"),
    ("nodes_viewer.py", "MaStroScheduleViewerNode", "showing_list"),
    ("nodes_viewer.py", "MaStroScheduleViewerNode", "id_column_count"),
}

OUTPUT_SOCKET_TYPES = {"MaStroScheduleColumnSocketType", "MaStroScheduleListSocketType"}
PROPERTY_FUNC_NAMES = {
    "BoolProperty", "IntProperty", "FloatProperty", "StringProperty",
    "EnumProperty", "FloatVectorProperty", "CollectionProperty", "PointerProperty",
}


def _string_value(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _base_names(class_node):
    names = []
    for base in class_node.bases:
        if isinstance(base, ast.Name):
            names.append(base.id)
        elif isinstance(base, ast.Attribute):
            names.append(base.attr)
    return names


def _is_node_class(class_node):
    """A Node subclass, not a PropertyGroup/Operator/Menu - those have
    their own, different property conventions (e.g. an Operator's
    `option: EnumProperty(items=...)` is a one-shot popup choice, never
    meant to trigger tree re-evaluation the way a node's own property
    does)."""
    bases = _base_names(class_node)
    return "Node" in bases and "PropertyGroup" not in bases


def _outputs_tracked_socket(class_node):
    for node in ast.walk(class_node):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr == "new"):
            continue
        if not (isinstance(func.value, ast.Attribute) and func.value.attr == "outputs"):
            continue
        if not node.args:
            continue
        if _string_value(node.args[0]) in OUTPUT_SOCKET_TYPES:
            return True
    return False


def _has_method(class_node, method_name):
    return any(isinstance(item, ast.FunctionDef) and item.name == method_name for item in class_node.body)


def _bl_idname(class_node):
    for item in class_node.body:
        if isinstance(item, ast.Assign) and len(item.targets) == 1:
            target = item.targets[0]
            if isinstance(target, ast.Name) and target.id == "bl_idname":
                return _string_value(item.value)
    return None


def _property_assignments(class_node):
    """Yields (property_name, call_node) for every `name: SomeProperty(...)`
    annotated assignment directly in this class's body."""
    for item in class_node.body:
        if not isinstance(item, ast.AnnAssign):
            continue
        if not isinstance(item.target, ast.Name):
            continue
        call = item.annotation if isinstance(item.annotation, ast.Call) else None
        # bpy.props.FloatProperty(...) parses as a Call whose func is
        # either Name("FloatProperty") (from `from bpy.props import
        # FloatProperty`) or Attribute(attr="FloatProperty") (from `bpy.
        # props.FloatProperty`) - both forms appear across this codebase.
        if call is None:
            continue
        func = call.func
        func_name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
        if func_name in PROPERTY_FUNC_NAMES:
            yield item.target.id, call, func_name


def _has_update_kwarg(call_node):
    return any(kw.arg == "update" for kw in call_node.keywords)


def main():
    here = pathlib.Path(__file__).parent
    missing_column_label = []
    missing_evaluate = []
    missing_update = []

    for path in sorted(here.glob("*.py")):
        if path.name == "audit_column_label.py":
            continue
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            bl_idname = _bl_idname(node) or node.name

            if _outputs_tracked_socket(node) and (path.name, node.name) not in COLUMN_LABEL_EXEMPT:
                if not _has_method(node, "column_label"):
                    missing_column_label.append((path.name, node.name, bl_idname))

            if _is_node_class(node) and (path.name, node.name) not in EVALUATE_EXEMPT:
                if not _has_method(node, "evaluate"):
                    missing_evaluate.append((path.name, node.name, bl_idname))

            if _is_node_class(node):
                for prop_name, call_node, func_name in _property_assignments(node):
                    # Collection/Pointer properties have no single
                    # "user changed this" moment the way a scalar
                    # property does (the user edits an ITEM inside the
                    # collection, not the collection itself) - update=
                    # genuinely doesn't apply to these the way it does
                    # to Bool/Int/Float/String/Enum/FloatVector.
                    if func_name in ("CollectionProperty", "PointerProperty"):
                        continue
                    if (path.name, node.name, prop_name) in PROPERTY_UPDATE_EXEMPT:
                        continue
                    if not _has_update_kwarg(call_node):
                        missing_update.append((path.name, node.name, bl_idname, prop_name))

    def _report(title, items, formatter):
        print(f"=== {title}: {len(items)} ===")
        for item in items:
            print(f"  {formatter(item)}")
        print()

    _report(
        "Missing column_label", missing_column_label,
        lambda item: f"{item[0]}: {item[1]} (bl_idname={item[2]!r})",
    )
    _report(
        "Missing evaluate()", missing_evaluate,
        lambda item: f"{item[0]}: {item[1]} (bl_idname={item[2]!r})",
    )
    _report(
        "Property missing update=", missing_update,
        lambda item: f"{item[0]}: {item[1]}.{item[3]} (bl_idname={item[2]!r})",
    )

    if not (missing_column_label or missing_evaluate or missing_update):
        print("OK - no issues found.")


if __name__ == "__main__":
    main()
