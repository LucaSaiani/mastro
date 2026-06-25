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


class NODE_MT_mastro_schedule_input_scene(bpy.types.Menu):
    bl_idname = "NODE_MT_mastro_schedule_input_scene"
    bl_label = "Scene"

    def draw(self, context):
        _add_node(self.layout, "MaStroScheduleInputAll", "Input All")
        _add_node(self.layout, "MaStroScheduleInputSelected", "Input Selected")


class NODE_MT_mastro_schedule_input_constants(bpy.types.Menu):
    bl_idname = "NODE_MT_mastro_schedule_input_constants"
    bl_label = "Constants"

    def draw(self, context):
        _add_node(self.layout, "MaStroScheduleValue", "Value")
        _add_node(self.layout, "MaStroScheduleInteger", "Integer")


class NODE_MT_mastro_schedule_input(bpy.types.Menu):
    bl_idname = "NODE_MT_mastro_schedule_input"
    bl_label = "Input"

    def draw(self, context):
        self.layout.menu(NODE_MT_mastro_schedule_input_scene.bl_idname)
        self.layout.menu(NODE_MT_mastro_schedule_input_constants.bl_idname)


class NODE_MT_mastro_schedule_output(bpy.types.Menu):
    bl_idname = "NODE_MT_mastro_schedule_output"
    bl_label = "Output"

    def draw(self, context):
        _add_node(self.layout, "MaStroScheduleViewer", "Viewer")


class NODE_MT_mastro_schedule_attribute(bpy.types.Menu):
    bl_idname = "NODE_MT_mastro_schedule_attribute"
    bl_label = "Attribute"

    def draw(self, context):
        _add_node(self.layout, "MaStroScheduleGetAttributeNames", "Get Attribute Names")
        _add_node(self.layout, "MaStroScheduleEvaluateAttribute", "Evaluate Attribute")


class NODE_MT_mastro_schedule_utilities_maths(bpy.types.Menu):
    bl_idname = "NODE_MT_mastro_schedule_utilities_maths"
    bl_label = "Maths"

    def draw(self, context):
        _add_node(self.layout, "MaStroScheduleMath", "Math")


class NODE_MT_mastro_schedule_utilities(bpy.types.Menu):
    bl_idname = "NODE_MT_mastro_schedule_utilities"
    bl_label = "Utilities"

    def draw(self, context):
        self.layout.menu(NODE_MT_mastro_schedule_utilities_maths.bl_idname)


class NODE_MT_mastro_schedule_wip(bpy.types.Menu):
    bl_idname = "NODE_MT_mastro_schedule_wip"
    bl_label = "WIP"

    def draw(self, context):
        _add_node(self.layout, "MaStroScheduleFilter", "Filter")
        _add_node(self.layout, "MaStroScheduleGroupBy", "Group By")
        _add_node(self.layout, "MaStroScheduleAggregate", "Aggregate")
        _add_node(self.layout, "MaStroScheduleString", "String")
        _add_node(self.layout, "MaStroScheduleHeader", "Header")
        _add_node(self.layout, "MaStroScheduleCategoryLookup", "Category Lookup")
        _add_node(self.layout, "MaStroScheduleMatrixLookup", "Matrix Lookup")
        _add_node(self.layout, "MaStroScheduleTableData", "Table Data")
        _add_node(self.layout, "MaStroScheduleFlatten", "Flatten")


_menu_classes = (
    NODE_MT_mastro_schedule_input_scene,
    NODE_MT_mastro_schedule_input_constants,
    NODE_MT_mastro_schedule_input,
    NODE_MT_mastro_schedule_output,
    NODE_MT_mastro_schedule_attribute,
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
