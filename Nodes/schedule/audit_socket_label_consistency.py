"""Not a registered module - run manually with `python3
audit_socket_label_consistency.py` from this directory whenever a
socket-carrying input/output is added or renamed on any node.

Enforces [[feedback_socket_label_consistency]] (a memory note, not
previously backed by a script): a socket type's own `bl_label`
(sockets.py) and the instance name given to every real
`inputs.new(...)`/`outputs.new(...)` call across nodes_*.py should
read the same thing - Blender does not derive one from the other, so
nothing stops them drifting apart (confirmed live as a real bug once:
MaStroScheduleAnySocket, the Viewer's generic input, shows the
*connected* socket's own bl_label when linked, not whatever instance
name the producing node happened to give it - a renamed instance name
left out of sync with bl_label showed stale/inconsistent text in the
Viewer even though the node's own socket looked right).

A flagged instance that turns out to be a deliberate, more specific
name (e.g. Pivot's "Row Key"/"Column Key" instead of the generic "Id
Key" - two DIFFERENT id keys on the same node, where the generic name
would be ambiguous) can be added to LABEL_EXEMPT below, with a comment
justifying why - same "start broad, narrow down confirmed exceptions"
approach as audit_column_label.py's own EXEMPT sets.
"""

import ast
import pathlib

# (filename, class_name, instance_name) triples - only add with a
# comment justifying why this specific instance name deliberately
# differs from its socket type's own bl_label.
#
# Confirmed legitimate (2026-06-29): every entry below names a MORE
# SPECIFIC role for a socket that carries the same underlying TYPE as
# several others on the same node, or as the generic type name itself
# (e.g. a node with two Column inputs called "A"/"B" rather than both
# being ambiguously called "Column"; "Background Colour"/"Text Colour"
# instead of two identical "Color" sockets the user couldn't tell
# apart) - the generic bl_label would be actively LESS clear here, not
# more consistent. Reviewed and accepted as a batch rather than one at
# a time, since the pattern is the same throughout: a real ambiguity
# this audit is right to flag in general, just not a bug in any of
# these specific cases.
LABEL_EXEMPT = {
    # Pivot's own Row Key/Column Key (nodes_pivot.py): two DIFFERENT id
    # keys on the same node (which becomes the row identity, which
    # becomes the pivoted column identity) - "Id Key" twice on the
    # same node would be genuinely ambiguous, not just less specific.
    ("nodes_pivot.py", "MaStroSchedulePivotNode", "Row Key"),
    ("nodes_pivot.py", "MaStroSchedulePivotNode", "Column Key"),
    ("nodes_accumulate.py", "MaStroScheduleAccumulateNode", "Leading"),
    ("nodes_accumulate.py", "MaStroScheduleAccumulateNode", "Trailing"),
    ("nodes_accumulate.py", "MaStroScheduleAccumulateNode", "Total"),
    ("nodes_column_primitive.py", "MaStroScheduleColumnPrimitiveNode", "Rows"),
    ("nodes_column_primitive.py", "MaStroScheduleColumnPrimitiveNode", "Title"),
    ("nodes_groupby_column.py", "MaStroScheduleItemFromListNode", "Index"),
    # Separate Columns' own Selection/Inverted (nodes_column_separate.py):
    # mirrors Geometry Nodes' own Separate Geometry naming - two
    # DIFFERENT Column outputs (the chosen attribute alone vs every
    # other one), "Column" twice on the same node would say nothing
    # about which is which.
    ("nodes_column_separate.py", "MaStroScheduleColumnSeparateNode", "Selection"),
    ("nodes_column_separate.py", "MaStroScheduleColumnSeparateNode", "Inverted"),
    # Aggregate's own Attribute to Group/Attribute Name
    # (nodes_aggregate_column.py): two DIFFERENT
    # MaStroScheduleAttributeRefSocketType inputs on the same node -
    # one says WHAT to group by (alongside Id Key to Group, freely
    # interleaved via group_by_items), the other says WHICH attribute's
    # values to aggregate (Sum/Average/...) - "Attribute Name" twice on
    # the same node would be genuinely ambiguous, same reasoning as
    # Pivot's own Row Key/Column Key above. "X to Group" on both this
    # one and Id Key to Group below - the user's own explicit naming
    # fix, replacing "Id Key"/"Group By Attribute" (which didn't read
    # as the same kind of thing at a glance) with names that share the
    # same "to Group" suffix, making their shared purpose (feeding
    # group_by_items together) obvious from the socket list alone.
    ("nodes_aggregate_column.py", "MaStroScheduleAggregateColumnNode", "Attribute to Group"),
    ("nodes_aggregate_column.py", "MaStroScheduleAggregateColumnNode", "Id Key to Group"),
    ("nodes_lookup.py", "MaStroScheduleMatrixLookupNode", "Reference"),
    ("nodes_math.py", "MaStroScheduleMathNode", "A"),
    ("nodes_math.py", "MaStroScheduleMathNode", "B"),
    ("nodes_math_superseded.py", "MaStroScheduleMathSupersededNode", "A"),
    ("nodes_math_superseded.py", "MaStroScheduleMathSupersededNode", "B"),
    ("nodes_sheet_background.py", "MaStroScheduleSheetBackgroundNode", "Background Colour"),
    ("nodes_sheet_move.py", "MaStroScheduleSheetMoveNode", "Row Offset"),
    ("nodes_sheet_move.py", "MaStroScheduleSheetMoveNode", "Column Offset"),
    ("nodes_sheet_place.py", "MaStroScheduleSheetPlaceNode", "Sheet Name"),
    ("nodes_sheet_primitive.py", "MaStroScheduleSheetPrimitiveNode", "Columns"),
    ("nodes_sheet_primitive.py", "MaStroScheduleSheetPrimitiveNode", "Rows"),
    ("nodes_sheet_primitive.py", "MaStroScheduleSheetPrimitiveNode", "Background Colour"),
    ("nodes_sheet_primitive.py", "MaStroScheduleSheetPrimitiveNode", "Text Colour"),
    ("nodes_sheet_remove_row.py", "MaStroScheduleSheetRemoveRowNode", "Row Index"),
    ("nodes_table_align.py", "MaStroScheduleTableAlignNode", "Start Column Index"),
    ("nodes_table_align.py", "MaStroScheduleTableAlignNode", "End Column Index"),
    ("nodes_table_case.py", "MaStroScheduleTableCaseNode", "Start Column Index"),
    ("nodes_table_case.py", "MaStroScheduleTableCaseNode", "End Column Index"),
    ("nodes_table_edit_cell.py", "MaStroScheduleTableEditCellNode", "Row Index"),
    ("nodes_table_edit_cell.py", "MaStroScheduleTableEditCellNode", "Column Index"),
    ("nodes_table_edit_cell.py", "MaStroScheduleTableEditCellNode", "Background Colour"),
    ("nodes_table_edit_cell.py", "MaStroScheduleTableEditCellNode", "Text Colour"),
    ("nodes_table_edit_header.py", "MaStroScheduleTableHeaderNode", "Column Index"),
    ("nodes_table_edit_header.py", "MaStroScheduleTableHeaderNode", "Unjoin"),
    ("nodes_table_edit_header.py", "MaStroScheduleTableHeaderNode", "Background Colour"),
    ("nodes_table_edit_header.py", "MaStroScheduleTableHeaderNode", "Text Colour"),
    ("nodes_table_hide_zero.py", "MaStroScheduleTableHideZeroNode", "Start Column Index"),
    ("nodes_table_hide_zero.py", "MaStroScheduleTableHideZeroNode", "End Column Index"),
    ("nodes_table_join.py", "MaStroScheduleTableJoinNode", "Table Name"),
    ("nodes_table_prefix_suffix.py", "MaStroScheduleTablePrefixSuffixNode", "Start Column Index"),
    ("nodes_table_prefix_suffix.py", "MaStroScheduleTablePrefixSuffixNode", "End Column Index"),
    ("nodes_table_prefix_suffix.py", "MaStroScheduleTablePrefixSuffixNode", "Prefix"),
    ("nodes_table_prefix_suffix.py", "MaStroScheduleTablePrefixSuffixNode", "Suffix"),
    ("nodes_table_primitive.py", "MaStroScheduleTablePrimitiveNode", "Title"),
    ("nodes_table_primitive.py", "MaStroScheduleTablePrimitiveNode", "Columns"),
    ("nodes_table_primitive.py", "MaStroScheduleTablePrimitiveNode", "Rows"),
    ("nodes_table_primitive.py", "MaStroScheduleTablePrimitiveNode", "Join Header"),
    ("nodes_table_primitive.py", "MaStroScheduleTablePrimitiveNode", "Background Colour"),
    ("nodes_table_primitive.py", "MaStroScheduleTablePrimitiveNode", "Text Colour"),
    ("nodes_table_row_colour.py", "MaStroScheduleTableRowColourNode", "Row Index"),
    ("nodes_table_row_colour.py", "MaStroScheduleTableRowColourNode", "Background Colour"),
    ("nodes_table_row_colour.py", "MaStroScheduleTableRowColourNode", "Text Colour"),
    ("nodes_table_row_pattern.py", "MaStroScheduleTableRowPatternNode", "Start Column Index"),
    ("nodes_table_row_pattern.py", "MaStroScheduleTableRowPatternNode", "End Column Index"),
    ("nodes_table_row_pattern.py", "MaStroScheduleTableRowPatternNode", "Background Colour A"),
    ("nodes_table_row_pattern.py", "MaStroScheduleTableRowPatternNode", "Text Colour A"),
    ("nodes_table_row_pattern.py", "MaStroScheduleTableRowPatternNode", "Background Colour B"),
    ("nodes_table_row_pattern.py", "MaStroScheduleTableRowPatternNode", "Text Colour B"),
    ("nodes_table_sheet.py", "MaStroScheduleTableSheetNode", "Sheet Name"),
    # A reference skeleton, never registered (see its own module
    # docstring) - not a real node, exists only to be copy-pasted from.
    ("nodes_template.py", "MaStroScheduleTemplateNode", "A"),
}


def _string_value(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _bl_idname(class_node):
    for item in class_node.body:
        if isinstance(item, ast.Assign) and len(item.targets) == 1:
            target = item.targets[0]
            if isinstance(target, ast.Name) and target.id == "bl_idname":
                return _string_value(item.value)
    return None


def _bl_label(class_node):
    for item in class_node.body:
        if isinstance(item, ast.Assign) and len(item.targets) == 1:
            target = item.targets[0]
            if isinstance(target, ast.Name) and target.id == "bl_label":
                return _string_value(item.value)
    return None


def _socket_labels(here):
    """{socket bl_idname: bl_label} for every NodeSocket subclass found
    in sockets.py."""
    labels = {}
    tree = ast.parse((here / "sockets.py").read_text())
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        bl_idname = _bl_idname(node)
        bl_label = _bl_label(node)
        if bl_idname and bl_label:
            labels[bl_idname] = bl_label
    return labels


def _socket_new_calls(tree):
    """Yields (socket_bl_idname, instance_name) for every
    `self.inputs.new(...)`/`self.outputs.new(...)` call found anywhere
    in `tree` (an entire module's own AST) - not scoped per-class,
    since a few nodes build sockets inside a shared helper rather than
    directly in their own init()."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr == "new"):
            continue
        if not (isinstance(func.value, ast.Attribute) and func.value.attr in ("inputs", "outputs")):
            continue
        if len(node.args) < 2:
            continue
        socket_type = _string_value(node.args[0])
        instance_name = _string_value(node.args[1])
        if socket_type and instance_name:
            yield socket_type, instance_name


def main():
    here = pathlib.Path(__file__).parent
    socket_labels = _socket_labels(here)
    mismatches = []

    for path in sorted(here.glob("nodes_*.py")):
        tree = ast.parse(path.read_text())
        # Figure out which class each socket.new() call sits inside, by
        # walking class-by-class rather than the whole module at once -
        # gives a useful (filename, class_name) pair in the report.
        for class_node in ast.walk(tree):
            if not isinstance(class_node, ast.ClassDef):
                continue
            for socket_type, instance_name in _socket_new_calls(class_node):
                bl_label = socket_labels.get(socket_type)
                if bl_label is None:
                    continue
                if instance_name == bl_label:
                    continue
                if (path.name, class_node.name, instance_name) in LABEL_EXEMPT:
                    continue
                mismatches.append((path.name, class_node.name, socket_type, instance_name, bl_label))

    print(f"=== Socket instance names diverging from their type's own bl_label: {len(mismatches)} ===")
    for filename, class_name, socket_type, instance_name, bl_label in mismatches:
        print(f"  {filename}: {class_name} - {socket_type!r} instance {instance_name!r} != bl_label {bl_label!r}")
    print()

    if not mismatches:
        print("OK - no issues found.")


if __name__ == "__main__":
    main()
