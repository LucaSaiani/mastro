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
        NodeItem("MaStroScheduleGetAttributeNames"),
        NodeItem("MaStroScheduleEvaluateAttribute"),
    ]),
    MaStroScheduleNodeCategory('MASTRO_SCHEDULE_OUTPUT', "Output", items=[
        NodeItem("MaStroScheduleViewer"),
    ]),
    MaStroScheduleNodeCategory('MASTRO_SCHEDULE_WIP', "WIP", items=[
        NodeItem("MaStroScheduleFilter"),
        NodeItem("MaStroScheduleGroupBy"),
        NodeItem("MaStroScheduleAggregate"),
        NodeItem("MaStroScheduleMath"),
        NodeItem("MaStroScheduleValue"),
        NodeItem("MaStroScheduleString"),
        NodeItem("MaStroScheduleHeader"),
        NodeItem("MaStroScheduleCategoryLookup"),
        NodeItem("MaStroScheduleMatrixLookup"),
        NodeItem("MaStroScheduleTableData"),
        NodeItem("MaStroScheduleFlatten"),
    ]),
]
