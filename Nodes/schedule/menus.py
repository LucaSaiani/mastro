import bpy


# nodeitems_utils.NodeCategory only supports a single flat level of items
# (confirmed against Blender's own source,
# scripts/modules/nodeitems_utils.py: register_node_categories builds one
# bpy.types.Menu per category, each just iterating NodeItem - no nesting
# support at all) - too limited for the requested layout (Input > Scene/
# Constants, Utilities > Math as actual sub-menus). This instead hooks
# directly into the node editor's native Add menu
# (bpy.types.NODE_MT_add), the same way Sverchok does
# (ui/nodeview_space_menu.py: `bpy.types.NODE_MT_add.append(sv_draw_menu)`),
# with bpy.types.Menu subclasses calling layout.menu(...) on each other
# for real nesting.
#
# Ordering convention (the user's own explicit call, confirmed against
# Geometry Nodes' own native Add menu - every one of GN's submenus is
# alphabetical): every submenu's own entries (nodes AND nested
# submenus alike) are sorted alphabetically by their own displayed
# label - ONLY the top-level entries directly under Add itself (Input,
# Output, Primitive, Attribute, Utilities, WIP) keep the deliberate,
# non-alphabetical order set here. Any NEW node or submenu added later
# must slot into its own level alphabetically, not just appended at
# the end.
TREE_TYPE = 'MaStroScheduleTreeType'


def _add_node(layout, nodetype, text=None):
    """layout.operator("node.add_node", ...) is the same operator
    nodeitems_utils.NodeItem.draw uses internally (scripts/modules/
    nodeitems_utils.py) - calling it directly here, rather than through
    NodeItem, since this menu structure no longer goes through
    NodeCategory/NodeItem at all."""
    props = layout.operator("node.add_node", text=text or nodetype, text_ctxt='*')
    props.type = nodetype
    props.use_transform = True


class NODE_MT_mastro_schedule_input_constant(bpy.types.Menu):
    bl_idname = "NODE_MT_mastro_schedule_input_constant"
    bl_label = "Constant"

    def draw(self, context):
        _add_node(self.layout, "MaStroScheduleBoolean", "Boolean")
        _add_node(self.layout, "MaStroScheduleColour", "Colour")
        _add_node(self.layout, "MaStroScheduleInteger", "Integer")
        _add_node(self.layout, "MaStroScheduleString", "String")
        _add_node(self.layout, "MaStroScheduleValue", "Value")


class NODE_MT_mastro_schedule_input_scene(bpy.types.Menu):
    bl_idname = "NODE_MT_mastro_schedule_input_scene"
    bl_label = "Scene"

    def draw(self, context):
        _add_node(self.layout, "MaStroScheduleInputAll", "Input All")
        _add_node(self.layout, "MaStroScheduleInputSelected", "Input Selected")


class NODE_MT_mastro_schedule_input(bpy.types.Menu):
    bl_idname = "NODE_MT_mastro_schedule_input"
    bl_label = "Input"

    def draw(self, context):
        self.layout.menu(NODE_MT_mastro_schedule_input_constant.bl_idname)
        self.layout.menu(NODE_MT_mastro_schedule_input_scene.bl_idname)


class NODE_MT_mastro_schedule_primitives_primitives(bpy.types.Menu):
    bl_idname = "NODE_MT_mastro_schedule_primitives_primitives"
    bl_label = "Primitive"

    def draw(self, context):
        _add_node(self.layout, "MaStroScheduleColumnPrimitive", "Column")
        _add_node(self.layout, "MaStroScheduleSheetPrimitive", "Sheet")
        _add_node(self.layout, "MaStroScheduleTablePrimitive", "Table")


class NODE_MT_mastro_schedule_primitives_operations_cells(bpy.types.Menu):
    bl_idname = "NODE_MT_mastro_schedule_primitives_operations_cells"
    bl_label = "Cells"

    def draw(self, context):
        _add_node(self.layout, "MaStroScheduleTableAlign", "Cell Align")
        _add_node(self.layout, "MaStroScheduleTableCase", "Cell Case")
        _add_node(self.layout, "MaStroScheduleTablePrefixSuffix", "Cell Prefix / Suffix")
        _add_node(self.layout, "MaStroScheduleTableEditCell", "Edit Cell")
        _add_node(self.layout, "MaStroScheduleTableHideZero", "Hide Zero")
        _add_node(self.layout, "MaStroScheduleTableRowColour", "Row Colour")
        _add_node(self.layout, "MaStroScheduleTableRowPattern", "Row Pattern")


class NODE_MT_mastro_schedule_primitives_operations_column(bpy.types.Menu):
    bl_idname = "NODE_MT_mastro_schedule_primitives_operations_column"
    bl_label = "Column"

    def draw(self, context):
        _add_node(self.layout, "MaStroScheduleAggregateColumn", "Aggregate")
        _add_node(self.layout, "MaStroScheduleConvertColumnToTable", "Column to Table")


class NODE_MT_mastro_schedule_primitives_operations_header(bpy.types.Menu):
    bl_idname = "NODE_MT_mastro_schedule_primitives_operations_header"
    bl_label = "Header"

    def draw(self, context):
        _add_node(self.layout, "MaStroScheduleTableHeader", "Edit Header")
        _add_node(self.layout, "MaStroScheduleHeader", "Rename Header")


class NODE_MT_mastro_schedule_primitives_operations_sheet(bpy.types.Menu):
    bl_idname = "NODE_MT_mastro_schedule_primitives_operations_sheet"
    bl_label = "Sheet"

    def draw(self, context):
        _add_node(self.layout, "MaStroScheduleSheetMove", "Move Sheet")
        _add_node(self.layout, "MaStroScheduleSheetPlace", "Join Sheets")
        _add_node(self.layout, "MaStroScheduleSheetBackground", "Sheet Background")
        _add_node(self.layout, "MaStroScheduleSheetGrid", "Sheet Grid")


class NODE_MT_mastro_schedule_primitives_operations_table(bpy.types.Menu):
    bl_idname = "NODE_MT_mastro_schedule_primitives_operations_table"
    bl_label = "Table"

    def draw(self, context):
        _add_node(self.layout, "MaStroScheduleTableJoin", "Join Tables")
        _add_node(self.layout, "MaStroScheduleTableToSheet", "Table to Sheet")


class NODE_MT_mastro_schedule_primitives_operations(bpy.types.Menu):
    bl_idname = "NODE_MT_mastro_schedule_primitives_operations"
    bl_label = "Operations"

    def draw(self, context):
        self.layout.menu(NODE_MT_mastro_schedule_primitives_operations_cells.bl_idname)
        self.layout.menu(NODE_MT_mastro_schedule_primitives_operations_column.bl_idname)
        self.layout.menu(NODE_MT_mastro_schedule_primitives_operations_header.bl_idname)
        self.layout.menu(NODE_MT_mastro_schedule_primitives_operations_sheet.bl_idname)
        self.layout.menu(NODE_MT_mastro_schedule_primitives_operations_table.bl_idname)


class NODE_MT_mastro_schedule_primitives(bpy.types.Menu):
    bl_idname = "NODE_MT_mastro_schedule_primitives"
    bl_label = "Primitive"

    def draw(self, context):
        self.layout.menu(NODE_MT_mastro_schedule_primitives_operations.bl_idname)
        self.layout.menu(NODE_MT_mastro_schedule_primitives_primitives.bl_idname)


class NODE_MT_mastro_schedule_output(bpy.types.Menu):
    bl_idname = "NODE_MT_mastro_schedule_output"
    bl_label = "Output"

    def draw(self, context):
        _add_node(self.layout, "MaStroScheduleExcelExport", "Export to Excel")
        _add_node(self.layout, "MaStroScheduleViewer", "Viewer")


class NODE_MT_mastro_schedule_attribute(bpy.types.Menu):
    bl_idname = "NODE_MT_mastro_schedule_attribute"
    bl_label = "Attribute"

    def draw(self, context):
        _add_node(self.layout, "MaStroScheduleEvaluateAttribute", "Evaluate Attribute")
        _add_node(self.layout, "MaStroScheduleGetAttributeNames", "Get Attribute Names")
        _add_node(self.layout, "MaStroScheduleGetIdKeys", "Get Id Keys")


class NODE_MT_mastro_schedule_utilities_list(bpy.types.Menu):
    bl_idname = "NODE_MT_mastro_schedule_utilities_list"
    bl_label = "List"

    def draw(self, context):
        _add_node(self.layout, "MaStroScheduleGroupByColumn", "Group Into List")
        _add_node(self.layout, "MaStroScheduleItemFromList", "Item from List")
        _add_node(self.layout, "MaStroScheduleListLength", "List Length")


class NODE_MT_mastro_schedule_utilities_maths(bpy.types.Menu):
    bl_idname = "NODE_MT_mastro_schedule_utilities_maths"
    bl_label = "Maths"

    def draw(self, context):
        _add_node(self.layout, "MaStroScheduleAccumulate", "Accumulate")
        _add_node(self.layout, "MaStroScheduleMath", "Math")


class NODE_MT_mastro_schedule_utilities(bpy.types.Menu):
    bl_idname = "NODE_MT_mastro_schedule_utilities"
    bl_label = "Utilities"

    def draw(self, context):
        self.layout.menu(NODE_MT_mastro_schedule_utilities_list.bl_idname)
        self.layout.menu(NODE_MT_mastro_schedule_utilities_maths.bl_idname)
        # An empty Group node (no node_tree of its own yet) - useful on
        # its own once a node_tree is assigned manually, but "Group
        # Selected" right below is the normal way to get one with a
        # body already filled in.
        _add_node(self.layout, "MaStroScheduleGroupNodeType", "Group")
        self.layout.operator("mastro_schedule.add_group_from_selected", text="Group Selected")


class NODE_MT_mastro_schedule_wip(bpy.types.Menu):
    bl_idname = "NODE_MT_mastro_schedule_wip"
    bl_label = "WIP"

    def draw(self, context):
        _add_node(self.layout, "MaStroScheduleFlattenKey", "Flatten Key")
        _add_node(self.layout, "MaStroScheduleFilter", "Filter")
        _add_node(self.layout, "MaStroScheduleGroupBy", "Group By")
        _add_node(self.layout, "MaStroScheduleAggregate", "Aggregate")
        _add_node(self.layout, "MaStroScheduleCategoryLookup", "Category Lookup")
        _add_node(self.layout, "MaStroScheduleMatrixLookup", "Matrix Lookup")
        _add_node(self.layout, "MaStroScheduleMultiColumnToTable", "Multi Column to Table")
        _add_node(self.layout, "MaStroSchedulePivot", "Pivot")
        _add_node(self.layout, "MaStroScheduleTableData", "Table Data")
        _add_node(self.layout, "MaStroScheduleFlatten", "Flatten")


_menu_classes = (
    NODE_MT_mastro_schedule_input_constant,
    NODE_MT_mastro_schedule_input_scene,
    NODE_MT_mastro_schedule_input,
    NODE_MT_mastro_schedule_output,
    NODE_MT_mastro_schedule_attribute,
    NODE_MT_mastro_schedule_primitives_primitives,
    NODE_MT_mastro_schedule_primitives_operations_cells,
    NODE_MT_mastro_schedule_primitives_operations_column,
    NODE_MT_mastro_schedule_primitives_operations_header,
    NODE_MT_mastro_schedule_primitives_operations_sheet,
    NODE_MT_mastro_schedule_primitives_operations_table,
    NODE_MT_mastro_schedule_primitives_operations,
    NODE_MT_mastro_schedule_primitives,
    NODE_MT_mastro_schedule_utilities_list,
    NODE_MT_mastro_schedule_utilities_maths,
    NODE_MT_mastro_schedule_utilities,
    NODE_MT_mastro_schedule_wip,
)


def _draw_add_menu(self, context):
    if context.space_data.tree_type != TREE_TYPE:
        return
    layout = self.layout
    layout.menu(NODE_MT_mastro_schedule_input.bl_idname)
    layout.menu(NODE_MT_mastro_schedule_output.bl_idname)
    layout.separator()
    layout.menu(NODE_MT_mastro_schedule_primitives.bl_idname)
    layout.separator()
    layout.menu(NODE_MT_mastro_schedule_attribute.bl_idname)
    layout.separator()
    layout.menu(NODE_MT_mastro_schedule_utilities.bl_idname)
    layout.separator()
    layout.menu(NODE_MT_mastro_schedule_wip.bl_idname)


def register():
    for cls in _menu_classes:
        bpy.utils.register_class(cls)
    bpy.types.NODE_MT_add.append(_draw_add_menu)


def unregister():
    bpy.types.NODE_MT_add.remove(_draw_add_menu)
    for cls in reversed(_menu_classes):
        bpy.utils.unregister_class(cls)
