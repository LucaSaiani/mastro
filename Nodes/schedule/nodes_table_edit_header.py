from bpy.types import Node
from bpy.props import IntProperty, StringProperty, FloatVectorProperty, EnumProperty, BoolProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node


# Plain text dropdown rather than three custom-icon buttons - the
# user's own call, to sidestep the unconfirmed question of whether
# layout.prop_enum() actually accepts icon_value for a custom preview
# icon the same way layout.prop() does (likely yes, going by Blender's
# own rna_ui_api.cc, but not verified live, and a plain dropdown carries
# zero risk either way). The three custom icon SVGs this would have used
# were removed (the user's call - no point keeping unused assets around)
# rather than left on disk; revisit from scratch if this is ever worth
# trying again.
ALIGNMENT_ITEMS = [
    ('LEFT', "Left", "Align text to the left"),
    ('CENTER', "Center", "Center text"),
    ('RIGHT', "Right", "Align text to the right"),
]


def _mark_touched(flag_name):
    """Returns an update= callback that flips `flag_name` to True
    whenever the property it's attached to is actually edited by the
    user - see has_bg/has_text_colour/has_alignment below for why a
    plain "is this different from the default" check isn't enough (the
    default IS itself a valid choice for a color or an enum, so there's
    no way to tell "never touched" from "set back to the default" by
    value alone)."""
    def _update(self, context):
        setattr(self, flag_name, True)
        update_node(self, context)
    return _update


# Edits one column's header in a Table (text, background, text colour
# and alignment) - the Table equivalent of Rename Header
# (nodes_header.py), kept as a separate node rather than one node that
# branches on whatever's plugged into its first input (Column vs
# Table): Column and Table have stayed two distinct concepts everywhere
# else in this tree, and the code here is small enough that the
# duplication is cheaper than a node whose shape changes depending on
# what's connected. Edits exactly one column at a time, by index - the
# user's explicit call: a future batch/pattern-edit node is deferred
# until a real use case for editing many columns at once actually shows
# up, rather than guessing its shape now. Mirrors Table's own draw_buttons
# layout (Columns count, then a Header section) so the two read
# consistently, minus the Rows field this node has no use for (it never
# adds/removes rows, only edits an existing column's header).
#
# A column index that falls inside an existing merge (e.g. the header
# row when Table's own Join Header is on, see nodes_table_primitive.py)
# is clamped to column 0 instead (see _column_index_in_table), UNLESS
# Unjoin is on (below), in which case that merge is removed entirely -
# the user's own follow-up request, so a Table built with Join Header
# can still be un-merged downstream without having to edit the Table
# primitive itself.
#
# Font/style (bold, italic, a different font family) are NOT implemented
# here - blf (Blender's text-drawing API) requires explicitly loading a
# font file for each variant (blf.load(path)), with no straightforward
# access to system fonts or the UI font's own bold/italic variants from
# Python, so that's a real barrier, not just unimplemented. Text colour,
# unlike font/style, has no such barrier - blf.color() is stateful but
# varies freely between separate blf.draw() calls within the same frame
# (confirmed against nodes_viewer.py's own existing use of two different
# text colours - text_color and ref_label_color - already drawn in the
# same frame), so it's wired through the same way background colour is.
#
# No revert/ignore button for Background Colour/Text Colour - the user's own
# call: deleting this node is already the way to undo an edit it made,
# a dedicated per-property revert wasn't worth the extra UI.
class MaStroScheduleTableHeaderNode(MaStroScheduleTreeNode, Node):
    """Edit one column's header in a Table, by index - text, alignment,
    background and text colour"""
    bl_idname = 'MaStroScheduleTableHeader'
    bl_label = 'Edit Header'

    # Backing values for Column Index/String/Background Colour/Text Colour's
    # inline fields (NodeSocket.prop_name, same mechanism as Math's
    # value_a/value_b) - editable directly on the socket while unlinked,
    # read from the actual linked node's output instead once something
    # is plugged in.
    column_index: IntProperty(name="Column Index", default=0, min=0, update=update_node)
    string_value: StringProperty(name="String", update=update_node)
    bg_value: FloatVectorProperty(name="Background Colour", subtype='COLOR', size=3, min=0.0, max=1.0,
                                   default=(0.18, 0.18, 0.18), update=_mark_touched("has_bg"))
    text_colour_value: FloatVectorProperty(
        name="Text Colour", subtype='COLOR', size=3, min=0.0, max=1.0, default=(1.0, 1.0, 1.0),
        update=_mark_touched("has_text_colour"))
    # Hidden from the UI (never drawn) - flips to True the first time
    # the user actually edits bg_value/text_colour_value (see
    # _mark_touched above), since a FloatVectorProperty's default is
    # itself a valid color choice, with no way to tell "never touched"
    # from "set back to the default" by value alone. While False, this
    # node leaves the column's existing background/text colour
    # untouched - same "no input means no change" rule String already
    # follows (see evaluate()'s has_text), just needing this extra flag
    # here because a color has no natural "empty" value the way a
    # string does.
    has_bg: BoolProperty(default=False)
    has_text_colour: BoolProperty(default=False)
    # Not collectable from a socket, unlike the inline fields above - a
    # choice of three fixed options has no meaningful "upstream node"
    # equivalent to mirror the way Math's A/B or String's value do. Same
    # has_X flag idea as the colors above - LEFT (the default) is
    # itself a valid choice, so there's no way to tell "never touched"
    # from "explicitly set to Left" by value alone either.
    alignment: EnumProperty(name="Alignment", items=ALIGNMENT_ITEMS, default='LEFT',
                             update=_mark_touched("has_alignment"))
    has_alignment: BoolProperty(default=False)
    # See the module-level comment above for what this does - off by
    # default, since the common case is editing a column's header, not
    # removing a merge.
    unjoin: BoolProperty(name="Unjoin", default=False, update=update_node)

    def init(self, context):
        self.inputs.new('MaStroScheduleTableSocketType', "Table")
        self.inputs.new('MaStroScheduleColumnSocketType', "Column Index").prop_name = "column_index"
        self.inputs.new('MaStroScheduleStringSocketType', "String").prop_name = "string_value"
        # Boolean socket, mirroring Table primitive's own Join Header
        # input (nodes_table_primitive.py) - the user's own explicit
        # ask: "table ha join con il socket, ma edit header no.
        # possiamo aggiungerlo?" Placed right after String, matching
        # Edit Cell's own input order (Table, Row/Column Index, String,
        # Background Colour, Text Colour) as closely as Unjoin (which
        # Edit Cell has no use for at all) allows.
        self.inputs.new('MaStroScheduleBooleanSocketType', "Unjoin").prop_name = "unjoin"
        self.inputs.new('MaStroScheduleColorSocketType', "Background Colour").prop_name = "bg_value"
        self.inputs.new('MaStroScheduleColorSocketType', "Text Colour").prop_name = "text_colour_value"
        self.outputs.new('MaStroScheduleTableSocketType', "Table")

    def draw_buttons(self, context, layout):
        # Unjoin no longer drawn here - it's a socket now (see init()),
        # already disabled the same way the disabling here used to be:
        # if there's no merge at all, setting it True simply has no
        # effect (covering_merge would be None regardless) - the user's
        # own call, accepting the loss of the "greyed out when
        # inapplicable" visual cue for a real socket instead.
        #
        # No "Header" section label above Alignment - the user's own
        # call, confirmed never seeing a bare text label used as a
        # section header this way in Geometry Nodes: a custom node's
        # draw_buttons isn't the same kind of grouped-panel UI a Node
        # Group's own interface panels are (see the user's own question
        # about this), so mimicking that look here with a plain label
        # read as out of place rather than as an actual native pattern.
        layout.prop(self, "alignment", text="")

    @staticmethod
    def _resolve_scalar(socket, value_in, fallback, cast):
        # Same "unlinked socket always comes through as None" handling
        # as Rename Header/Math - fall back to the inline field's own
        # backing property explicitly when unlinked, rather than
        # assuming the input holds it.
        if not socket.is_linked:
            return fallback
        if isinstance(value_in, str):
            return cast(value_in) if value_in else fallback
        rows_in = value_in or []
        if not rows_in:
            return fallback
        row_key = next((k for k in rows_in[0] if not k.startswith("_")), None)
        return cast(rows_in[0].get(row_key, fallback)) if row_key else fallback

    @staticmethod
    def _resolve_bool(socket, value_in, fallback):
        # Same shape as Table primitive's own _resolve_bool
        # (nodes_table_primitive.py) - kept separate rather than shared,
        # since both classes already duplicate _resolve_scalar this way
        # too.
        if not socket.is_linked:
            return fallback
        if isinstance(value_in, bool):
            return value_in
        rows_in = value_in or []
        if not rows_in:
            return fallback
        row_key = next((k for k in rows_in[0] if not k.startswith("_")), None)
        return bool(rows_in[0].get(row_key, fallback)) if row_key else fallback

    @staticmethod
    def _find_merge(table, index):
        """The merge region covering column `index`'s row-0 (header)
        cell, or None if it isn't covered by any."""
        for merge in table.get("merges", []):
            if (merge.get("start_row", 0) <= 0 <= merge.get("end_row", 0)
                    and merge.get("start_col", 0) <= index <= merge.get("end_col", 0)):
                return merge
        return None

    def evaluate(self, inputs):
        table = inputs[0] or {"columns": [], "merges": []}
        index = self._resolve_scalar(self.inputs["Column Index"], inputs[1], self.column_index, int)
        unjoin = self._resolve_bool(self.inputs["Unjoin"], inputs[2], self.unjoin)
        merges = table.get("merges", [])

        covering_merge = self._find_merge(table, index)
        # Editing column `index`'s OWN header dict has no visible effect
        # at all while it's covered by a merge - the Viewer draws merge
        # regions LAST, on top of every column's own header cell (see
        # nodes_viewer.py:_draw_table_overlay) - confirmed live as
        # exactly this bug: a Table with Join Header on, edited here
        # with Unjoin off, silently did nothing. The actual fix is to
        # edit the MERGE's own text/bg/text_color dict instead in that
        # case, not the column underneath it.
        edit_merge = covering_merge if (covering_merge is not None and not unjoin) else None
        if covering_merge is not None and unjoin:
            # Remove the covering merge entirely - the columns it used
            # to span go back to having their own independent header
            # cells (whatever text/style they already had - this node
            # still edits column `index` normally below, same as if it
            # had never been merged).
            merges = [m for m in merges if m is not covering_merge]

        # "No input" (unlinked AND the inline field left empty/never
        # edited) means "don't touch this column's existing
        # text/background/text colour" - the user's explicit call, to
        # stop an Edit Header with nothing actually set from silently
        # overwriting whatever the column already had. Linked (even to
        # a node currently producing an empty/default value) counts as
        # an explicit input and does overwrite - only the truly
        # untouched case is special.
        string_socket = self.inputs["String"]
        if string_socket.is_linked:
            new_text = inputs[3] or ""
            has_text = True
        else:
            new_text = self.string_value
            has_text = bool(new_text)

        # Color always comes through as a plain (r, g, b) tuple - both
        # the Colour node's evaluate() and the inline fields' own
        # bg_value/text_colour_value properties are already that shape,
        # no per-row dict/key extraction needed the way scalars above
        # require.
        bg_socket = self.inputs["Background Colour"]
        if bg_socket.is_linked:
            new_bg = inputs[4]
            has_bg = True
        else:
            new_bg = tuple(self.bg_value)
            has_bg = self.has_bg
        text_colour_socket = self.inputs["Text Colour"]
        if text_colour_socket.is_linked:
            new_text_colour = inputs[5]
            has_text_colour = True
        else:
            new_text_colour = tuple(self.text_colour_value)
            has_text_colour = self.has_text_colour

        if edit_merge is not None:
            new_merge = dict(edit_merge)
            if has_text:
                new_merge["text"] = new_text
            if has_bg:
                new_merge["bg"] = new_bg
            if has_text_colour:
                new_merge["text_color"] = new_text_colour
            if self.has_alignment:
                new_merge["text_align"] = self.alignment
            merges = [new_merge if m is edit_merge else m for m in merges]
            return [{"columns": table.get("columns", []), "merges": merges}]

        columns = []
        for col_idx, column in enumerate(table.get("columns", [])):
            if col_idx == index:
                new_header = dict(column["header"])
                if has_text:
                    new_header["text"] = new_text
                if has_bg:
                    new_header["bg"] = new_bg
                if has_text_colour:
                    new_header["text_color"] = new_text_colour
                if self.has_alignment:
                    new_header["text_align"] = self.alignment
                column = {**column, "header": new_header}
            columns.append(column)
        return [{"columns": columns, "merges": merges}]
