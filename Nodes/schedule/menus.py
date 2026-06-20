from nodeitems_utils import NodeCategory, NodeItem


class MaStroScheduleNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return (context.space_data.type == 'NODE_EDITOR'
                and context.space_data.tree_type == 'MaStroScheduleTreeType')


schedule_node_categories = [
    MaStroScheduleNodeCategory('MASTRO_SCHEDULE_INPUT', "Input", items=[
        NodeItem("MaStroScheduleInputAll"),
        NodeItem("MaStroScheduleInputSelected"),
    ]),
    MaStroScheduleNodeCategory('MASTRO_SCHEDULE_ATTRIBUTE', "Attribute", items=[
        NodeItem("MaStroScheduleGetCustomAttribute"),
    ]),
    MaStroScheduleNodeCategory('MASTRO_SCHEDULE_FILTER', "Filter", items=[
        NodeItem("MaStroScheduleFilter"),
    ]),
    MaStroScheduleNodeCategory('MASTRO_SCHEDULE_GROUP', "Group", items=[
        NodeItem("MaStroScheduleGroupBy"),
        NodeItem("MaStroScheduleAggregate"),
    ]),
    MaStroScheduleNodeCategory('MASTRO_SCHEDULE_MATH', "Math", items=[
        NodeItem("MaStroScheduleMath"),
    ]),
    MaStroScheduleNodeCategory('MASTRO_SCHEDULE_LOOKUP', "Lookup", items=[
        NodeItem("MaStroScheduleCategoryLookup"),
        NodeItem("MaStroScheduleMatrixLookup"),
    ]),
    MaStroScheduleNodeCategory('MASTRO_SCHEDULE_OUTPUT', "Output", items=[
        NodeItem("MaStroScheduleTableData"),
        NodeItem("MaStroScheduleFlatten"),
        NodeItem("MaStroScheduleViewer"),
    ]),
]
