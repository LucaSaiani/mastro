import bpy
from bpy.types import Node
from bpy.props import BoolProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node


def _id_key_signature(row):
    """A hashable signature built from EVERY id key present on `row`
    (every key starting with "_" - same convention _data_key/_id_keys
    already use elsewhere, e.g. nodes_aggregate_column.py/
    nodes_id_keys.py), sorted by key name so the same combination of
    id keys always produces the same signature regardless of dict
    insertion order. Duplicated from nodes_merge_list.py's own
    identical helper rather than imported - same reasoning as
    nodes_id_keys.py's own _id_keys duplication, avoiding an import
    cycle between sibling node modules."""
    return tuple(sorted((k, row[k]) for k in row if k.startswith("_")))


# Combines several Columns (already sharing the same outer identity -
# e.g. all already filtered/grouped down to one Object, the common
# case right after Item from List/inside a For Each List body) into
# one Column whose own rows carry every input's own data attributes
# together. Merge List's own (nodes_merge_list.py) "outer key, inner
# rows" two-level merge, with the outer level dropped - that level
# only ever mattered for combining whole LISTS (multiple Group Into
# List outputs, one group per Object); once already down to a single
# Object's own Column, there's nothing left to group by at the outer
# level, only the SAME inner-row merge Merge List's own inner loop
# already does (_id_key_signature below, unchanged from there).
#
# The user's own design call, after noticing Aggregate's own "Id Key
# to Group" input was redundant inside a loop already grouped by
# Object (every row already shares the same _Object, so re-passing
# Object_id to Aggregate just to group by it again added nothing) -
# rather than extending Aggregate itself to accept multiple Columns
# directly (considered and rejected: Aggregate would then be doing two
# jobs, merging AND aggregating, instead of one), a separate node
# mirrors Merge List's own "one node, one job" shape: Merge Column
# merges, an ordinary Aggregate (unchanged, still a single Column
# input) aggregates whatever Merge Column hands it - composable, same
# as Merge List -> For Each List already is.
#
# Two DISTINCT, equally legitimate merge strategies, chosen explicitly
# via match_one_to_one (default on) rather than auto-detected or
# silently falling back from one to the other - the user's own
# explicit call, after finding that an earlier auto-detecting version
# (try positional first, silently fall back to id-key-signature
# whenever row counts/positions didn't line up) masked a REAL error in
# one case (Separate Columns' own Selection/Inverted outputs collapsed
# from 50 rows down to 1, because Floor/Use had become ordinary
# attributes rather than real id keys once Aggregate produced them -
# id-key-signature alone, _Object only, couldn't tell the 50 rows
# apart, and silently merged them instead of failing loudly):
#
# - match_one_to_one=True (default, "strict"): every input MUST have
#   the same row count, and each one's own id keys must agree at every
#   position - row i of every input is assumed to already be the SAME
#   entity, already in the same order (e.g. Separate Columns' own
#   Selection/Inverted, both still 1:1 with their shared original
#   Column). A mismatch here is treated as a real error (raised, same
#   as Math's own A/B length-mismatch check, nodes_math.py) rather than
#   silently working around it - a Column that's supposed to already
#   be row-aligned but isn't is exactly the kind of mistake this
#   should surface, not paper over.
#
# - match_one_to_one=False ("by id key", the ORIGINAL behavior this
#   node shipped with): rows are matched by their own FULL id-key
#   signature (_id_key_signature above) instead - the right choice when
#   inputs genuinely don't share the same row count (e.g. one
#   Evaluate Attribute branch produced fewer rows than another for a
#   real reason), with a row present in one input but missing from
#   another padded with None for whatever attributes it never had -
#   never dropped, mirroring Merge List's own identical rule (itself
#   mirroring Join Tables/Join Sheets' own "missing data is padded,
#   not discarded" rule, nodes_table_join.py). Still requires every id
#   key actually present (e.g. _Object alone, once Floor/Use have
#   become ordinary attributes) to be enough to tell rows apart on its
#   own - not a safety net for the Separate Columns case above, which
#   needs the strict positional mode instead.
class MaStroScheduleMergeColumnNode(MaStroScheduleTreeNode, Node):
    """Combine several Columns (already sharing the same outer
    identity, e.g. one Object's own rows) into one - by matching row
    position (default, the common Separate Columns round-trip case) or
    by id key (for inputs that genuinely have different row counts)"""
    bl_idname = 'MaStroScheduleMergeColumn'
    bl_label = 'Merge Column'

    # GN-style optional "clip"-style boolean, default ON (the strict/
    # positional behavior, the safe default - the user's own explicit
    # naming/default call after the auto-detecting version's own live
    # bug, see this class's own module comment).
    match_one_to_one: BoolProperty(
        name="1:1 Match",
        description=(
            "Every input must already share the same row count/order - "
            "row i of every input is treated as the same entity, raising "
            "an error otherwise. Turn off to instead match rows by id "
            "key, padding any row missing from one input with None"
        ),
        default=True,
        update=update_node,
    )

    def init(self, context):
        # use_multi_input is a constructor-only argument - see Join
        # Tables' own init() (nodes_table_join.py) for the confirmed
        # RNA source detail.
        self.inputs.new('MaStroScheduleColumnSocketType', "Column", use_multi_input=True)
        self.outputs.new('MaStroScheduleColumnSocketType', "Column")

    def draw_buttons(self, context, layout):
        layout.prop(self, "match_one_to_one")

    @property
    def column_label(self):
        # Mirrors Merge List's own column_label (nodes_merge_list.py) -
        # delegates to the FIRST linked Column input, since every input
        # is assumed to share the same outer identity already.
        socket = self.inputs["Column"]
        if not socket.links:
            return ""
        from .tree import upstream_attr
        return upstream_attr(socket.links[0].from_socket, "column_label")

    def evaluate(self, inputs):
        columns = [column or [] for column in (inputs[0] or [])]
        if not columns:
            return [[]]

        if not self.match_one_to_one:
            # By id key - rows matched by their own FULL id-key
            # signature (_id_key_signature above), same as Merge
            # List's own inner-row matching (nodes_merge_list.py, with
            # the outer "key" level dropped - see this module's own
            # header comment). A row present in one input but missing
            # from another is simply never updated with that input's
            # own keys - same as Merge List's own "missing data is
            # padded, not discarded" rule.
            merged_by_match = {}
            order = []
            for column in columns:
                for row in column:
                    match_key = _id_key_signature(row)
                    if match_key not in merged_by_match:
                        merged_by_match[match_key] = {}
                        order.append(match_key)
                    merged_by_match[match_key].update(row)
            return [[merged_by_match[match_key] for match_key in order]]

        # Positional (default/strict) - row i of every input MUST
        # already be the same entity, already in the same order (e.g.
        # Separate Columns' own Selection/Inverted, both still 1:1
        # with their shared original Column) - same row count AND
        # matching id keys at every position, checked explicitly and
        # raised as a real error otherwise (same shape as Math's own
        # A/B length-mismatch check, nodes_math.py) rather than
        # silently working around it - see this class's own module
        # comment for the live bug an earlier auto-detecting version
        # masked.
        row_counts = {len(column) for column in columns}
        if len(row_counts) != 1:
            error = ValueError(
                f"Inputs have different row counts ({sorted(row_counts)}) - "
                f"disable 1:1 Match to merge by id key instead"
            )
            error.short_message = "Column row count mismatch"
            raise error

        result = []
        for position, rows_at_position in enumerate(zip(*columns)):
            ids = [{k: v for k, v in row.items() if k.startswith("_")} for row in rows_at_position]
            if any(id_set != ids[0] for id_set in ids[1:]):
                error = ValueError(
                    f"Row {position} doesn't refer to the same entity across "
                    f"every input ({ids}) - disable 1:1 Match to merge by "
                    f"id key instead"
                )
                error.short_message = "Column rows don't match"
                raise error
            merged_row = {}
            for row in rows_at_position:
                merged_row.update(row)
            result.append(merged_row)
        return [result]


classes = (
    MaStroScheduleMergeColumnNode,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
