import re

from bpy.types import Node
from bpy.props import IntProperty, StringProperty, FloatVectorProperty, EnumProperty, BoolProperty

from .nodes_table_edit_header import ALIGNMENT_ITEMS

from .tree import MaStroScheduleTreeNode
from .execution import update_node, is_socket_active


# Set on BOTH the property's own description= AND the Title socket's
# own .description in init() below - a NodeSocket has its own
# "description" ("Socket tooltip"), separate from the description of
# whatever property is drawn inside it via prop_name, and the socket's
# own tooltip is what Blender actually shows while hovering the field
# drawn on a socket (confirmed: the property's description alone wasn't
# showing up there) - so both need the same text, not just one.
TITLE_TOOLTIP = (
    "Header text. Accepts a \"{...}\" wildcard when Join Header is off, "
    "expanded into one label per column: \"{5}\" or \"{f}\"/\"{F}\" inside the "
    "text starts a numeric or alphabetic (lower/upper-case) sequence, one step "
    "per column - e.g. \"text_{5}\" with 6 columns gives text_5, text_6, ..., "
    "text_10"
)


def _column_letter(index):
    """Same base-26 letter numbering as nodes_viewer.py's _column_letter
    (0, 1, 2, ... -> "A", "B", ..., "Z", "AA", ...) - duplicated rather
    than imported, since nodes_viewer.py's version is local to that
    module's drawing code and this has nothing to do with drawing."""
    letters = ""
    index += 1
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        letters = chr(ord('A') + remainder) + letters
    return letters


# Per-column header labels, parsed from a "text_{N}" pattern typed into
# Title - the user's own shorthand: "test_{5}" with 6 columns means
# test_5, test_6, test_7, test_8, test_9, test_10 (a numeric sequence
# starting at 5, one label per column, always derived straight from
# Title - never edited per column individually). "test_{f}"/"test_{F}"
# means an alphabetic sequence starting at f/F instead, case-matched to
# the token. Anything not matching this pattern (including an empty
# Title) leaves every column's header blank - this used to fall back to
# an automatic "A0"/"B0"/... label, removed (the user's own correction):
# it was both semantically wrong (numbering should start at 1, not 0,
# if numbering at all) and entirely redundant - the exact same sequence
# is already obtainable on purpose by typing "{A}0" into Title, so a
# silent default doing the same thing behind an EMPTY Title just hid
# what "no Title" actually means (nothing typed = no header text, not
# "some flavor of auto-numbering").
_PATTERN_RE = re.compile(r"^(.*)\{([0-9]+|[a-zA-Z])\}(.*)$")


def _per_column_labels(pattern, count):
    """Generate `count` per-column header labels from a "{...}" pattern
    (see _PATTERN_RE above) - or a blank header for every column if
    `pattern` doesn't match that shape at all (including an empty
    Title)."""
    match = _PATTERN_RE.match(pattern) if pattern else None
    if not match:
        return ["" for _ in range(count)]

    prefix, token, suffix = match.groups()
    if token.isdigit():
        start = int(token)
        return [f"{prefix}{start + i}{suffix}" for i in range(count)]

    # Alphabetic - same base-26 letter sequence as _column_letter, just
    # not necessarily starting at A, and case-matched to the token
    # (lowercase "f" -> lowercase sequence, uppercase "F" -> uppercase).
    is_upper = token.isupper()
    start_index = ord(token.upper()) - ord('A')
    labels = []
    for i in range(count):
        letters = _column_letter(start_index + i)
        labels.append(f"{prefix}{letters if is_upper else letters.lower()}{suffix}")
    return labels


# A Table with no upstream at all - the same primitive role
# nodes_column_primitive.py's Column plays, just for Table (see that
# file's docstring). Columns/Rows come first (the fields that define
# this Table's shape), then a separate Header section (Title, Alignment,
# Text Colour, Background Colour) - the cosmetic fields that label/style it.
#
# Rows has min=1, same as Column's primitive - a column's header is
# itself row 0 of the grid (confirmed elsewhere - cell_corners(0,
# col_idx) draws it through the exact same function/coordinate system
# as every other row, just with a different default color), so a Table
# never actually has "0 rows" - row_count here only ever meant "how many
# DATA rows below the header", never the Table's total row count.
#
# Join Header (a bool socket, default False) decides only whether the
# header row is ONE merged cell spanning every column or N independent
# per-column cells - Title is ALWAYS the single source for the text
# either way (never something edited per column on this node), and
# Alignment/Background Colour/Text Colour ALWAYS apply too, regardless of Join
# Header - the user's explicit correction: an earlier version of this
# only applied them while merged, which was wrong; they're meant to
# style the header row whether it's one merged cell or N separate ones.
# - On: Title's literal text becomes a single merge spanning row 0
#   across every column (table["merges"], see
#   sockets.py:MaStroScheduleTableSocket's docstring) - even with Title
#   left empty (an empty-text merge still gets its own background/
#   alignment). The "merges" shape is the same one a future Excel
#   export would feed straight into openpyxl/xlsxwriter's own
#   merge_cells().
# - Off: no merge - Title is parsed as a "{...}" pattern instead (see
#   _per_column_labels above) and expanded into one header label per
#   column (test_{5} with 6 columns -> test_5, test_6, ..., test_10),
#   each column keeping its own independent header cell, all sharing
#   the same Alignment/Background Colour/Text Colour.
class MaStroScheduleTablePrimitiveNode(MaStroScheduleTreeNode, Node):
    """Create an empty Table with the given number of columns and rows,
    with control over the header row's text, alignment and color"""
    bl_idname = 'MaStroScheduleTablePrimitive'
    bl_label = 'Table'

    # Backing values for every inline field below (NodeSocket.prop_name,
    # same mechanism as Math's value_a/value_b) - editable directly on
    # the socket while unlinked, read from the actual linked node's
    # output instead once something is plugged in.
    column_count: IntProperty(name="Columns", default=3, min=1, update=update_node)
    row_count: IntProperty(name="Rows", default=2, min=1, update=update_node)
    title_value: StringProperty(name="Title", description=TITLE_TOOLTIP, update=update_node)
    bg_value: FloatVectorProperty(name="Background Colour", subtype='COLOR', size=3,
                                   min=0.0, max=1.0, default=(0.18, 0.18, 0.18), update=update_node)
    text_colour_value: FloatVectorProperty(name="Text Colour", subtype='COLOR', size=3,
                                            min=0.0, max=1.0, default=(1.0, 1.0, 1.0), update=update_node)
    # Not collectable from a socket - a choice of three fixed options
    # has no meaningful "upstream node" equivalent to mirror (see
    # nodes_table_edit_header.py's identical alignment property). Named
    # "Alignment", not "Header" - the dropdown's own items (Left/Center/
    # Right) already make clear what it's choosing, "Header" above it
    # read as a second, redundant label for the same thing.
    alignment: EnumProperty(name="Alignment", items=ALIGNMENT_ITEMS, default='LEFT', update=update_node)
    # Default False - most Tables don't want a merged title row by
    # default, Join Header is something to opt into.
    join_header: BoolProperty(name="Join Header", default=False, update=update_node)

    def init(self, context):
        self.inputs.new('MaStroScheduleColumnSocketType', "Columns").prop_name = "column_count"
        self.inputs.new('MaStroScheduleColumnSocketType', "Rows").prop_name = "row_count"
        title_socket = self.inputs.new('MaStroScheduleStringSocketType', "Title")
        title_socket.prop_name = "title_value"
        title_socket.description = TITLE_TOOLTIP
        self.inputs.new('MaStroScheduleBooleanSocketType', "Join Header").prop_name = "join_header"
        self.inputs.new('MaStroScheduleColorSocketType', "Background Colour").prop_name = "bg_value"
        self.inputs.new('MaStroScheduleColorSocketType', "Text Colour").prop_name = "text_colour_value"
        self.outputs.new('MaStroScheduleTableSocketType', "Table")

    def draw_buttons(self, context, layout):
        # Always shown, same as Background Colour/Text Colour (the sockets
        # right below it) - Alignment/the colors always apply to the
        # header row, whether it's one merged cell (Join Header on) or
        # N separate per-column cells (off).
        layout.prop(self, "alignment", text="")

    @staticmethod
    def _resolve_count(socket, rows_in, fallback):
        if not is_socket_active(socket):
            return fallback
        rows_in = rows_in or []
        if not rows_in:
            return 0
        row_key = next((k for k in rows_in[0] if not k.startswith("_")), None)
        return int(rows_in[0].get(row_key, 0)) if row_key else 0

    @staticmethod
    def _resolve_text(socket, value_in, fallback):
        if not is_socket_active(socket):
            return fallback
        return value_in if isinstance(value_in, str) else fallback

    @staticmethod
    def _resolve_color(socket, value_in, fallback):
        if not is_socket_active(socket):
            return tuple(fallback)
        return tuple(value_in) if value_in else tuple(fallback)

    @staticmethod
    def _resolve_bool(socket, value_in, fallback):
        if not is_socket_active(socket):
            return fallback
        if isinstance(value_in, bool):
            return value_in
        rows_in = value_in or []
        if not rows_in:
            return fallback
        row_key = next((k for k in rows_in[0] if not k.startswith("_")), None)
        return bool(rows_in[0].get(row_key, fallback)) if row_key else fallback

    def evaluate(self, inputs):
        # Same "unlinked socket always comes through as None" handling
        # as Rename Header/Math - fall back to the inline field's own
        # backing property explicitly when unlinked.
        column_count = self._resolve_count(self.inputs["Columns"], inputs[0], self.column_count)
        row_count = self._resolve_count(self.inputs["Rows"], inputs[1], self.row_count)
        title_text = self._resolve_text(self.inputs["Title"], inputs[2], self.title_value)
        join_header = self._resolve_bool(self.inputs["Join Header"], inputs[3], self.join_header)
        bg = self._resolve_color(self.inputs["Background Colour"], inputs[4], self.bg_value)
        text_colour = self._resolve_color(self.inputs["Text Colour"], inputs[5], self.text_colour_value)

        # No clamping on column_count/row_count - min=1 on the
        # properties only constrains the inline fields' UI sliders (the
        # user's call: if a linked socket provides a different value on
        # purpose, that's what's used, not silently forced). range()
        # already returns nothing for a value <= 0, no special-casing
        # needed.
        if join_header:
            # Always covered by the merge built below (which draws
            # Title's own text on top, see sockets.py:
            # MaStroScheduleTableSocket's docstring - merges are drawn
            # LAST, over every column's own header cell) - blank rather
            # than some auto-numbered placeholder for the same reason
            # _per_column_labels' own fallback was removed: data that's
            # never actually seen shouldn't carry a misleading value
            # either, even if invisible today.
            header_texts = ["" for _ in range(column_count)]
        else:
            header_texts = _per_column_labels(title_text, column_count)

        # Alignment/Background Colour/Text Colour always apply to every
        # column's own header cell - the user's explicit correction:
        # they're not gated on Join Header, they style the header row
        # either way (whether it ends up as one merged cell below, or
        # stays N separate per-column cells when Join Header is off).
        columns = []
        for col_idx in range(column_count):
            rows = [{"text": "", "bg": None} for _ in range(row_count)]
            columns.append({
                "header": {
                    "text": header_texts[col_idx], "bg": bg, "text_color": text_colour,
                    "text_align": self.alignment,
                },
                "rows": rows,
            })

        merges = []
        if join_header:
            # Always builds the merge, even with an empty Title - an
            # empty-text merge still gets its own background/alignment.
            # The "merges" shape is the same one a future Excel export
            # would feed straight into openpyxl/xlsxwriter's own
            # merge_cells().
            merges.append({
                "start_row": 0, "start_col": 0,
                "end_row": 0, "end_col": max(column_count - 1, 0),
                "text": title_text, "bg": bg, "text_color": text_colour,
                "text_align": self.alignment,
            })

        return [{"columns": columns, "merges": merges}]
