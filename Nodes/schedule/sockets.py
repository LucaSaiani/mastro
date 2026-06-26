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
    # bl_label only - the displayed text, not the class/bl_idname.
    # Used to be "Number Column", to leave room for a future "String
    # Column" socket type - dropped (the user's own call): this same
    # socket already carries text values fine too (e.g. a future "use"
    # Column), so a separate String Column type was never actually
    # needed, and "Number Column" was misleading about that.
    bl_label = "Column"

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
            # placeholder is a text-field concept (greyed-out text
            # filling an otherwise-empty textbox) - it has no effect on
            # a numeric field (Columns/Rows use this same socket type
            # with an IntProperty prop_name; a number field has no
            # "empty" state for placeholder to fill, confirmed live: no
            # label appeared at all). text=text (an external label to
            # the field's left) is what Blender's own numeric fields use
            # for this, so that's what a numeric prop_name gets;
            # placeholder is only used when this socket's prop_name
            # happens to be a StringProperty (Title/String fields - see
            # nodes_column_primitive.py, nodes_header.py - where it
            # matches Geometry Nodes' own "String" inside an empty
            # textbox convention).
            prop_def = node.bl_rna.properties.get(self.prop_name)
            if prop_def is not None and prop_def.type == 'STRING':
                layout.prop(node, self.prop_name, text="", placeholder=text)
            else:
                layout.prop(node, self.prop_name, text=text)
        else:
            layout.label(text=text)

    @classmethod
    def draw_color_simple(cls):
        return (161 / 255, 161 / 255, 161 / 255, 1.0)


# A list of groups, as produced by Group Into List (see
# nodes_groupby_column.py) - each group is {"key": <id key's value for
# this group>, "rows": [...]}, "rows" being a list of ordinary Column
# rows (still carrying every id key except the chosen Id Key, untouched
# - not yet aggregated). A darker shade (0.6x value) of
# MaStroScheduleColumnSocket's own gray (161,161,161) - the user's own
# call, distinct enough to read as "not a plain Column" while still
# visually related, the same relationship MaStroScheduleAttributeRefSocket's
# color already has to String's (0.7x value, same hue).
class MaStroScheduleListSocket(NodeSocket):
    """Socket carrying a list of groups, each holding its own list of
    Column rows"""
    bl_idname = 'MaStroScheduleListSocketType'
    bl_label = "List"

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    @classmethod
    def draw_color_simple(cls):
        return (97 / 255, 97 / 255, 97 / 255, 1.0)


# A reference to one id key (e.g. "_Object", "_Level") on a Column - as
# produced by Get Id Keys (see nodes_id_keys.py) and consumed by
# Aggregate/Flatten Key/Group Into List/Accumulate's own "Id Key" input,
# instead of each of those nodes hardcoding its own search-popup-only
# picker independently. Kept as its own dedicated socket type rather
# than reusing String - the user's own call: a distinct color makes a
# wrong/missing connection here easy to spot at a glance while
# debugging, the same reasoning MaStroScheduleStringSocket itself was
# kept separate from MaStroScheduleColumnSocket's generic prop_name
# mechanism for.
class MaStroScheduleIdKeySocket(NodeSocket):
    """Socket carrying a reference to one id key on a Column (e.g.
    "Object_id", "Level_id")"""
    bl_idname = 'MaStroScheduleIdKeySocketType'
    bl_label = "Id Key"

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    @classmethod
    def draw_color_simple(cls):
        return (214 / 255, 138 / 255, 89 / 255, 1.0)


# A single constant string, as produced by the String node (see
# nodes_string.py) - fed into e.g. a Rename Header node's String input
# (renames a Column's header) or a Table primitive's/Edit
# Header's Title input (nodes_table_primitive.py/
# nodes_table_edit_header.py), kept as its own dedicated socket type
# rather than reusing MaStroScheduleColumnSocket's generic prop_name
# mechanism, so a string value reads unambiguously as text wherever
# it's plugged in.
class MaStroScheduleStringSocket(NodeSocket):
    """Socket carrying a single text value"""
    bl_idname = 'MaStroScheduleStringSocketType'
    bl_label = "String"

    # Same NodeSocket.prop_name mechanism as MaStroScheduleColumnSocket -
    # see that class's docstring - draws an inline editable text field on
    # the socket itself while unlinked.
    prop_name: StringProperty(default="")

    def draw(self, context, layout, node, text):
        if not self.is_output and not self.is_linked and self.prop_name:
            # text="" + placeholder=text - see
            # MaStroScheduleColumnSocket.draw's comment for why, same
            # reasoning here.
            layout.prop(node, self.prop_name, text="", placeholder=text)
        else:
            layout.label(text=text)

    @classmethod
    def draw_color_simple(cls):
        # The full rgb(112, 178, 255) reserved for this when
        # MaStroScheduleAttributeRefSocket's color was chosen as a darker
        # (0.7x) shade of the same hue specifically to leave this value
        # free for String once it existed.
        return (112 / 255, 178 / 255, 255 / 255, 1.0)


# A single color, as produced by the Colour node (see nodes_rgb.py) -
# fed into an Edit Header node's Background Color input. Mirrors
# Sverchok's SvColorSocket (core/sockets.py): a FloatVectorProperty
# (subtype='COLOR') as the inline-field backing value, same
# NodeSocket.prop_name mechanism as every other socket in this file, just
# holding a color instead of a single number/string.
class MaStroScheduleColorSocket(NodeSocket):
    """Socket carrying a single RGB color"""
    bl_idname = 'MaStroScheduleColorSocketType'
    bl_label = "Color"

    prop_name: StringProperty(default="")

    def draw(self, context, layout, node, text):
        # No inline color-wheel field while unlinked, unlike every other
        # socket type's prop_name mechanism in this file - confirmed
        # live that layout.prop(..., expand=True) here draws three flat
        # numeric sliders, not the color wheel a plain layout.prop(self,
        # "value", text="") draws on a node's own draw_buttons (e.g.
        # nodes_rgb.py's Colour node, which has no socket/expand
        # involved at all) - the difference wasn't tracked down, and the
        # user's call was to leave just the socket rather than ship a
        # half-working widget. A constant color still works the same
        # way every other constant does in this tree: wire in a Colour
        # node.
        layout.label(text=text)

    @classmethod
    def draw_color_simple(cls):
        return (199 / 255, 199 / 255, 41 / 255, 1.0)


# A single boolean, as used e.g. by Table's Join Header input (see
# nodes_table_primitive.py) - a plain checkbox as the inline-field
# backing value (NodeSocket.prop_name, same mechanism as every other
# socket in this file), so a flag like Join Header can be driven from
# upstream logic instead of always being a fixed choice on the node
# itself.
class MaStroScheduleBooleanSocket(NodeSocket):
    """Socket carrying a single true/false value"""
    bl_idname = 'MaStroScheduleBooleanSocketType'
    bl_label = "Boolean"

    prop_name: StringProperty(default="")

    def draw(self, context, layout, node, text):
        if not self.is_output and not self.is_linked and self.prop_name:
            layout.prop(node, self.prop_name, text=text)
        else:
            layout.label(text=text)

    @classmethod
    def draw_color_simple(cls):
        return (204 / 255, 166 / 255, 214 / 255, 1.0)


# Table is the purely visual end of the pipeline, deliberately downstream
# of every Column-level operation (Math, future Filter/GroupBy/etc.) - no
# node ever computes anything from a Table's contents, it only displays
# them. A Column's id keys (_Object, _Face/...) exist to let several
# Columns line up into one Table row-for-row by identity; once converted
# to a Table that identity is discarded on purpose (see
# nodes_table_convert.py) - a Table's rows are just positions, free to be
# rearranged (left/right/up/down) by whatever node combines several
# Tables later, with nothing yet guaranteeing row i of one column is "the
# same thing" as row i of another (the user's own call: "nessuna
# garanzia... table è puramente grafico").
#
# Shape: {"columns": [...], "merges": [...]}.
#
# "columns" is a list of columns, each {"header": {"text": str, "bg":
# color or None, "text_color": color or None, "text_align": "LEFT"/
# "CENTER"/"RIGHT"}, "rows": [{"text": str, "bg": color or None,
# "text_align": "LEFT"/"CENTER"/"RIGHT"}, ...]} - a list (not a single
# column) from the start, so a future multi-Table merge only ever
# appends more columns to this same list, no socket/data shape change
# needed when that node exists. "bg"/"text_color" default to None
# (meaning "use the Viewer's own row/header color") until something
# (Edit Header/Table primitive, see nodes_table_edit_header.py/
# nodes_table_primitive.py) sets them - "text_color" exists only on a
# header dict today, since no node edits a row's text color yet; row
# dicts have "bg"/"text_align" (the latter set by Cell Align, see
# nodes_table_align.py), just not "text_color".
#
# "merges" is a list of merged-cell regions, each {"start_row": int,
# "start_col": int, "end_row": int, "end_col": int, "text": str, "bg":
# color, "text_color": color, "text_align": ...} - row/column
# coordinates (inclusive) plus the region's own content, drawn by the
# Viewer LAST, on top of every column's own header/row cells (see
# nodes_viewer.py:_draw_table_overlay) - e.g. Table's own Join Header
# spans one merge across row 0, every column (see
# nodes_table_primitive.py). The same shape a future Excel export would
# feed straight into openpyxl/xlsxwriter's own merge_cells() - row/
# column coordinates, not a special-cased "is this a title row" flag.
class MaStroScheduleTableSocket(NodeSocket):
    """Socket carrying a Table (purely visual - text and per-cell style,
    no further computation happens on this data)"""
    bl_idname = 'MaStroScheduleTableSocketType'
    bl_label = "Table"

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    @classmethod
    def draw_color_simple(cls):
        return (1.0, 1.0, 1.0, 1.0)
