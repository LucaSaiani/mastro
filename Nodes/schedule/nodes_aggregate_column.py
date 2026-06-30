from bpy.types import Node
from bpy.props import EnumProperty, CollectionProperty, IntProperty

from .tree import MaStroScheduleTreeNode, resolve_through_reroutes
from .execution import update_node, get_node_table
from .properties import MaStro_schedule_group_by_item


OPERATION_ITEMS = [
    ('NONE', "-", "Group only - keep any one row's value as-is, with nothing actually aggregated"),
    ('SUM', "Sum", "Sum the column's values within each group"),
    ('COUNT', "Count", "Count the rows in each group"),
    ('AVERAGE', "Average", "Average the column's values within each group"),
    ('MODE', "Mode", "The most frequently occurring value within each group"),
]


def _data_key(row):
    for key in row.keys():
        if not key.startswith("_"):
            return key
    return None


def _resolve_data_key(tree, row, name):
    """The row's own technical data key (some node's own node.name,
    e.g. "Evaluate Attribute.001") whose column_label matches the
    user-facing `name` (e.g. "use") chosen via Named Attribute - NOT
    `name` itself. Confirmed live as a real bug otherwise: a row's own
    data keys are never the readable name directly (see
    nodes_evaluate.py's own evaluate(), "key = self.name" - the exact
    same technical-key-vs-readable-label split nodes_viewer.py's own
    multi-data-key relabeling and nodes_attribute.py's own
    _column_data_keys already had to solve), so `name in row` is only
    ever true by coincidence (a Column with exactly one data key,
    where the upstream node's own column_label happened to already
    equal its own node.name - never true once a Merge List combines
    more than one). Falls back to `name` itself if no row key's own
    column_label matches - keeps the prior (sometimes-correct)
    behavior for whatever single-data-key case might still rely on
    it, rather than going from "wrong value" to "no value at all"."""
    for key in row.keys():
        if key.startswith("_"):
            continue
        source_node = tree.nodes.get(key)
        if source_node is not None and getattr(source_node, "column_label", "") == name:
            return key
    return name


def _link_key(from_node, output_index, link_position):
    """Same stable string identity Join Tables' own _link_key
    (nodes_table_join.py) uses for its own multi-input ordering list -
    see that function's own docstring for why link_position is needed
    alongside from_node.name/output_index."""
    return f"{from_node.name}::{output_index}::{link_position}"


def _values_by_link_key(socket, resolved_values):
    """Maps each of `socket`'s own current links to its own resolved
    value (resolved_values, in execution.py:eval_node's own per-link
    order for a multi-input socket - confirmed against that function's
    own multi_input handling), keyed by the SAME _link_key
    _sync_group_by_items uses to build group_by_items' own link_key -
    so evaluate() can look a value up by WHICH group_by_items entry it
    belongs to, rather than by shared-iterator position. Confirmed
    live as the real fix for a reordering bug: group_by_items' own
    list order is user-controlled and freely reorderable, but
    resolved_values' own order is always socket.links' own fixed link
    order - a shared iterator walked in group_by_items' own order
    silently handed back the WRONG value (still socket.links' own
    next one) whenever the user moved an entry, so reordering the
    UIList never actually changed evaluate()'s own grouping."""
    by_link = {}
    for link_position, (link, value) in enumerate(zip(socket.links, resolved_values)):
        from_node, from_socket = resolve_through_reroutes(link)
        if from_node is None:
            continue
        try:
            output_index = list(from_node.outputs).index(from_socket)
        except ValueError:
            continue
        by_link[_link_key(from_node, output_index, link_position)] = value
    return by_link


def _resolve_linked_value(node, socket, link):
    """The actual value currently flowing through one link into a
    multi-input socket - read straight from the evaluation cache
    (get_node_table), same resolution execution.py's own eval_node
    does for an ordinary input, just done by hand here since
    group_by_items' own ordering (not socket.links' own order) is what
    decides which value lands in which evaluate() slot."""
    if link.is_muted:
        return None
    from_node, from_socket = resolve_through_reroutes(link)
    if from_node is None:
        return None
    table = get_node_table(node.id_data.name, from_node.name)
    if not table:
        return None
    try:
        output_index = list(from_node.outputs).index(from_socket)
    except ValueError:
        return None
    return table[output_index] if output_index < len(table) else None


# Aggregates a Column down to one row per distinct combination of the
# chosen group-by entries (group_by_items, an ordered list mixing Id
# Keys and Attribute Names freely - see this node's own
# _sync_group_by_items docstring), dropping every id key not itself
# part of that combination. "Total per Object" means group by Object's
# own Id Key alone; "total per Object, per Floor, per Use" means group
# by all three together, in whatever order the user listed them in -
# the user's own explicit ask, after finding no way to express that
# combination with only ONE Id Key the way this node used to accept.
# This generalizes (rather than replaces) the prior single-Id-Key
# behavior: with exactly one Id Key entry and nothing else,
# the result is identical to before.
#
# This is the opposite of Flatten Key (nodes_flatten_key.py), which
# instead drops only the chosen key and KEEPS every other one - the
# two cover the two parallel cases the user described: a flat "total
# per Object" (or per Object+Floor+Use) regardless of how many other
# rows feed into each combination (this node), versus a step-by-step
# cascade like Plot -> Block -> Use -> Level where each step needs to
# keep peeling away one key at a time while the others survive to the
# next step (Flatten Key, chained).
#
# TWO separate multi-input sockets, Id Key (MaStroScheduleIdKeySocketType)
# and Attribute Name (MaStroScheduleAttributeRefSocketType) - NOT one
# generic Any-typed multi-input mixing both - the user's own explicit
# call: simpler to validate when each socket only ever carries one real
# type. An Id Key (Get Id Keys' own output, nodes_id_keys.py) is
# already present as a real key on every row (_Object/_Level/...); an
# Attribute Name (Named Attribute's own output, nodes_attribute.py) is
# a DATA key instead (e.g. "Use") - not normally something to group
# by, but the user's own concrete case needs it anyway (grouping by
# Object+Floor+Use, where Use is a data value, not a structural id).
# Converting an Attribute into a real Id Key first (a "promote to Id
# Key" step) was considered and rejected by the user - "non ha senso
# dal punto di vista di come vedo i dati nel viewer", an Attribute
# should stay an Attribute everywhere else in the graph, this node
# alone needs to treat it as groupable.
#
# Both sockets' own links are merged into ONE ordered list
# (group_by_items, a UIList the user can freely reorder/interleave -
# same "order set by this node's own list, not by link order" pattern
# Join Tables' own table_items already follows, see that node's own
# module comment) - the user's own explicit ask: the GROUPING ORDER
# itself matters (Floor then Use nests differently than Use then
# Floor, like a multi-column Excel pivot), and needs to be settable
# independent of which of the two sockets an entry happens to live on.
class MaStroScheduleAggregateColumnNode(MaStroScheduleTreeNode, Node):
    """Aggregate a Column down to one row per distinct combination of
    the chosen group-by entries (Id Keys and/or Attributes, in this
    node's own list order) - e.g. Object+Floor+Use groups by all three
    together, one result row per combination actually present"""
    bl_idname = 'MaStroScheduleAggregateColumn'
    bl_label = 'Aggregate'
    bl_width_default = 180

    operation: EnumProperty(name="Operation", items=OPERATION_ITEMS, default='SUM', update=update_node)

    # See this class's own module comment for why this is a merged,
    # freely-reorderable list spanning both multi-input sockets, rather
    # than either socket's own link order.
    group_by_items: CollectionProperty(type=MaStro_schedule_group_by_item)
    active_group_by_index: IntProperty()

    # Same MaStroScheduleAttributeRefSocketType Named Attribute itself
    # outputs (nodes_attribute.py) - optional, left unwired in the
    # common case (a Column with exactly one data key, found by
    # exclusion via _data_key as always). Added once a Column with
    # MORE than one data key at once became possible (Merge List,
    # nodes_merge_list.py) and confirmed live as a real, silent bug:
    # _data_key always picked the SAME first key by exclusion
    # regardless of which one the user actually wanted, with no way to
    # choose - two separate Aggregate nodes meant to total Area and
    # Use respectively both silently aggregated the same one. Named
    # Attribute's own available_attribute_names (nodes_attribute.py)
    # was extended to recognize this node as a second kind of
    # consumer (reading the Column's own already-present data keys,
    # not a MaStro object's mesh attributes) - one shared picker node
    # covers both cases, the user's own explicit design call, rather
    # than a second dedicated node for this one. This is the VALUE
    # being aggregated (what Sum/Average/... is computed over) -
    # entirely separate from group_by_items above, which instead
    # controls what the result is grouped BY.
    def init(self, context):
        self.inputs.new('MaStroScheduleColumnSocketType', "Column")
        # Right after Column, ahead of the two Group By sockets below -
        # the user's own explicit ordering call: this is the VALUE
        # being aggregated, arguably the single most important choice
        # on this node (Aggregate would still make sense with only
        # Column + Attribute Name wired, the by-exclusion _data_key
        # fallback covering everything else) - reads as more central
        # than where it used to sit, after both Group By sockets.
        self.inputs.new('MaStroScheduleAttributeRefSocketType', "Attribute Name")
        # "Id Key to Group"/"Attribute to Group", not bare "Id Key"/
        # "Group By Attribute" - the user's own explicit naming fix:
        # the original names didn't read as the same kind of thing at
        # a glance ("Id Key" alone gives no hint it's specifically
        # about grouping, "Group By Attribute" buries the shared verb
        # in the middle) - "X to Group" makes both sockets' shared
        # purpose (feeding group_by_items, this node's own merged
        # group-by order) obvious from the socket list alone, distinct
        # only in WHAT they each carry (a structural Id Key vs a data
        # Attribute).
        self.inputs.new('MaStroScheduleIdKeySocketType', "Id Key to Group", use_multi_input=True)
        self.inputs.new('MaStroScheduleAttributeRefSocketType', "Attribute to Group", use_multi_input=True)
        self.outputs.new('MaStroScheduleColumnSocketType', "Column")

    @property
    def column_label(self):
        if "Column" not in self.inputs:
            return ""
        from .tree import upstream_attr
        return upstream_attr(self.inputs["Column"], "column_label")

    def _sync_group_by_items(self):
        """Rebuilds group_by_items to exactly match the Id Key to Group/
        Attribute to Group sockets' own current links, preserving the
        existing ORDER of any link_key already present (new links are
        appended at the end; removed links are dropped from wherever
        they were) - same shape as Join Tables' own _sync_table_items
        (nodes_table_join.py), see that method's own docstring for the
        full reasoning (muted-link handling, why this can't run from
        draw_buttons, etc.), just spanning two sockets merged into one
        list instead of one socket alone. Only ever called from
        tree.py's own polling timer, never from draw_buttons (same
        "Writing to ID classes in this context is not allowed"
        constraint)."""
        current = []
        labels_by_key = {}
        for kind, socket_name in (('KEY', "Id Key to Group"), ('ATTRIBUTE', "Attribute to Group")):
            socket = self.inputs[socket_name]
            for link_position, link in enumerate(socket.links):
                if link.is_muted:
                    continue
                from_node, from_socket = resolve_through_reroutes(link)
                if from_node is None:
                    continue
                try:
                    output_index = list(from_node.outputs).index(from_socket)
                except ValueError:
                    continue
                key = (kind, _link_key(from_node, output_index, link_position))
                current.append(key)
                value = _resolve_linked_value(self, socket, link)
                from .nodes_viewer import _header_text
                if kind == 'ATTRIBUTE':
                    # _header_text's own id-key branch (leading "_"
                    # stripped, "_id" appended) never triggers here -
                    # an Attribute's own chosen Name is never
                    # underscore-prefixed - so this only ever applies
                    # its plain first-letter capitalization, the same
                    # "every group-by label reads consistently
                    # capitalized" fix the user asked for after noticing
                    # Id Key entries (already run through _header_text)
                    # and Attribute entries (previously shown as-is, raw)
                    # looked inconsistent side by side in the same list.
                    raw_name = value[0].get("Name", "") if value else ""
                    label = _header_text(raw_name)
                else:
                    label = _header_text(value) if value else ""
                labels_by_key[key] = label

        existing_keys = [(item.kind, item.link_key) for item in self.group_by_items]
        for index in reversed(range(len(self.group_by_items))):
            if existing_keys[index] not in current:
                self.group_by_items.remove(index)
        tracked_keys = {(item.kind, item.link_key) for item in self.group_by_items}
        for kind, link_key in current:
            if (kind, link_key) not in tracked_keys:
                item = self.group_by_items.add()
                item.kind = kind
                item.link_key = link_key
                tracked_keys.add((kind, link_key))
        for item in self.group_by_items:
            item.label = labels_by_key.get((item.kind, item.link_key), "")

    def draw_buttons(self, context, layout):
        layout.prop(self, "operation", text="")
        row = layout.row()
        row.template_list(
            "MASTRO_UL_schedule_group_by", "", self, "group_by_items", self, "active_group_by_index", rows=4,
        )
        col = row.column(align=True)
        op = col.operator("mastro_schedule.group_by_move", icon='TRIA_UP', text="")
        op.node_name = self.name
        op.direction = 'UP'
        op = col.operator("mastro_schedule.group_by_move", icon='TRIA_DOWN', text="")
        op.node_name = self.name
        op.direction = 'DOWN'

    def evaluate(self, inputs):
        # inputs' own order matches init()'s own socket order: Column,
        # Attribute Name, Id Key to Group, Attribute to Group.
        rows = inputs[0] or []
        attribute_ref = inputs[1] or []
        id_key_values = inputs[2] or []
        attribute_values = inputs[3] or []
        if not rows:
            return [rows]

        # Resolve group_by_items' own order into a list of (kind, key)
        # pairs this evaluate() can actually group by - kind='KEY' means
        # key is an id key STRING (e.g. "_Object", already a real key
        # present on every row, read straight off it). kind='ATTRIBUTE'
        # means the entry only carries a user-facing NAME (e.g. "Use")
        # at this point - resolved to the row's own TECHNICAL data key
        # via _resolve_data_key below, same technical-key-vs-readable-
        # label split nodes_evaluate.py's own evaluate() establishes
        # ("key = self.name", never the chosen attribute's own name) -
        # confirmed live as a real bug otherwise: `row.get("use")`
        # against a row whose own data key is "Evaluate Attribute.001"
        # always returned None, even though group_by_items itself
        # correctly listed "use" as an available, chosen entry.
        # Resolved once against rows[0] (every row sharing the same
        # Column is assumed to share the same key<->label mapping,
        # same assumption chosen_name/data_key below already makes for
        # the aggregated value itself), not per-row - cheaper, and
        # there's no real case where it would differ row to row.
        #
        # Values are matched back to group_by_items by their own
        # link_key, built the SAME way against each socket's own
        # current links as _sync_group_by_items already does - NOT by
        # walking id_key_values/attribute_values with a shared
        # iterator in group_by_items' own (reorderable) order.
        # Confirmed live as a real bug with that iterator approach:
        # reordering the UIList changes which group_by_items ENTRY is
        # visited first, but each socket's own resolved value list
        # (id_key_values/attribute_values) is still in that socket's
        # own FIXED link order, never group_by_items' own order - so
        # `next(attr_iter)` kept handing back the same value regardless
        # of where the user moved that entry to, and the Viewer's own
        # columns/values never actually changed after a reorder.
        tree = self.id_data
        id_key_by_link = _values_by_link_key(self.inputs["Id Key to Group"], id_key_values)
        attribute_by_link = _values_by_link_key(self.inputs["Attribute to Group"], attribute_values)
        plan = []
        for item in self.group_by_items:
            if item.kind == 'KEY':
                value = id_key_by_link.get(item.link_key)
                if value:
                    plan.append(('KEY', value, item.label))
            else:
                value = attribute_by_link.get(item.link_key)
                name = value[0].get("Name") if value else None
                if name:
                    plan.append(('ATTRIBUTE', _resolve_data_key(tree, rows[0], name), None))

        if not plan:
            return [rows]

        # Attribute (the optional explicit choice) wins when wired and
        # actually present in this Column's own rows - falls back to
        # the old by-exclusion behavior otherwise, covering both "left
        # unwired entirely" (the common single-data-key case) and "the
        # chosen name doesn't match anything here" (e.g. picked against
        # a different upstream Column before this one was rewired) -
        # the same "don't silently produce nothing, fall back to
        # something reasonable" spirit Math/Header's own
        # _data_key-style fallbacks already follow. Same
        # name->technical-key resolution as the ATTRIBUTE branch above
        # (_resolve_data_key, not a direct `in rows[0]` check) - the
        # exact same bug applied here too, just unnoticed until now
        # since this path is normally tested with only one data key,
        # where the technical key and chosen name often happen to
        # already match by coincidence.
        chosen_name = attribute_ref[0].get("Name") if attribute_ref else None
        if chosen_name:
            data_key = _resolve_data_key(tree, rows[0], chosen_name)
        else:
            data_key = _data_key(rows[0])

        groups = {}
        order = []
        for row in rows:
            group_values = tuple(row.get(value) for _kind, value, _label in plan)
            if group_values not in groups:
                groups[group_values] = []
                order.append(group_values)
            groups[group_values].append(row.get(data_key))

        # Each KEY entry in plan keeps writing the REAL id key (e.g.
        # "_Object") so the Viewer's own id-column handling (always
        # first, collapsible via show_id_columns - see nodes_viewer.py's
        # own id_column_count) is completely unaffected. Additionally,
        # for KEY entries only, the SAME value is also written under
        # its own readable label (e.g. "Object_id") as an ordinary DATA
        # key - the user's own explicit design call: an Id Key used as
        # a group-by dimension is, in that role, conceptually also an
        # attribute of the result (its own column, freely positionable
        # alongside Use/Floor in group_by_items' own order) - without
        # this, an Id Key used for grouping could never actually
        # appear at the position the user chose in group_by_items, only
        # ever pinned to the Viewer's own fixed "id columns always
        # first" slot regardless of where it sits in the list. The two
        # columns read identically (same label, same value) wherever
        # they both show up in the same Viewer - nodes_viewer.py's own
        # key-glyph marking (added alongside this) ended up applying to
        # every real id column unconditionally rather than singling out
        # ones with a duplicate, so there's nothing further to look up
        # here to tell them apart visually; this comment block is the
        # only place that explains why both columns exist at all.
        result = []
        for group_values in order:
            group_row = {}
            for i, (kind, value, label) in enumerate(plan):
                group_row[value] = group_values[i]
                if kind == 'KEY':
                    group_row[label] = group_values[i]
            group_row[data_key] = self._aggregate(groups[group_values])
            result.append(group_row)
        return [result]

    def _aggregate(self, values):
        if self.operation == 'NONE':
            return values[0] if values else None
        if self.operation == 'COUNT':
            return len(values)
        if self.operation == 'MODE':
            from collections import Counter
            counts = Counter(values)
            return max(counts, key=counts.get) if counts else None
        numbers = []
        for value in values:
            try:
                numbers.append(float(value))
            except (TypeError, ValueError):
                pass
        if self.operation == 'AVERAGE':
            return sum(numbers) / len(numbers) if numbers else 0.0
        return sum(numbers)
