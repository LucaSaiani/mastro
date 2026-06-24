import nodeitems_utils

from .sockets import (
    MaStroScheduleDataSocket,
    MaStroScheduleAttributeRefSocket,
    MaStroScheduleColumnSocket,
    MaStroScheduleAnySocket,
)
from .tree import MaStroScheduleTree, start_polling, stop_polling
from .properties import (
    MaStro_schedule_key_item,
    MaStro_schedule_cell,
    MaStro_schedule_row,
)
from .operators import (
    MASTRO_UL_schedule_keys,
    MASTRO_OT_Schedule_GroupBy_Key_Add,
    MASTRO_OT_Schedule_GroupBy_Key_Remove,
    MASTRO_UL_schedule_category_lookup,
    MASTRO_OT_Schedule_Category_Lookup_Add,
    MASTRO_OT_Schedule_Category_Lookup_Remove,
    MASTRO_OT_Schedule_Force_Refresh,
)
from .panel import MASTRO_PT_Schedule_Tools
from .nodes_input import MaStroScheduleInputAllNode, MaStroScheduleInputSelectedNode
from .nodes_attribute import MaStroScheduleGetAttributeNamesNode, MASTRO_OT_Schedule_Pick_Attribute_Name
from .nodes_evaluate import MaStroScheduleEvaluateAttributeNode
from .nodes_filter import MaStroScheduleFilterNode
from .nodes_groupby import MaStroScheduleGroupByNode
from .nodes_aggregate import MaStroScheduleAggregateNode
from .nodes_math import MaStroScheduleMathNode
from .nodes_value import MaStroScheduleValueNode
from .nodes_string import MaStroScheduleStringNode
from .nodes_header import MaStroScheduleHeaderNode
from .nodes_lookup import MaStroScheduleCategoryLookupNode, MaStroScheduleMatrixLookupNode
from .nodes_table import MaStroScheduleTableDataNode, MaStroScheduleFlattenNode
from .nodes_viewer import (
    MaStroScheduleViewerNode,
    register_viewer_draw_handler,
    unregister_viewer_draw_handler,
)
from .menus import schedule_node_categories


classes = (
    MaStro_schedule_key_item,
    MaStro_schedule_cell,
    MaStro_schedule_row,
    MaStroScheduleDataSocket,
    MaStroScheduleAttributeRefSocket,
    MaStroScheduleColumnSocket,
    MaStroScheduleAnySocket,
    MaStroScheduleTree,
    MASTRO_UL_schedule_keys,
    MASTRO_OT_Schedule_GroupBy_Key_Add,
    MASTRO_OT_Schedule_GroupBy_Key_Remove,
    MASTRO_UL_schedule_category_lookup,
    MASTRO_OT_Schedule_Category_Lookup_Add,
    MASTRO_OT_Schedule_Category_Lookup_Remove,
    MASTRO_OT_Schedule_Force_Refresh,
    MASTRO_PT_Schedule_Tools,
    MaStroScheduleInputAllNode,
    MaStroScheduleInputSelectedNode,
    MaStroScheduleGetAttributeNamesNode,
    MASTRO_OT_Schedule_Pick_Attribute_Name,
    MaStroScheduleEvaluateAttributeNode,
    MaStroScheduleFilterNode,
    MaStroScheduleGroupByNode,
    MaStroScheduleAggregateNode,
    MaStroScheduleMathNode,
    MaStroScheduleValueNode,
    MaStroScheduleStringNode,
    MaStroScheduleHeaderNode,
    MaStroScheduleCategoryLookupNode,
    MaStroScheduleMatrixLookupNode,
    MaStroScheduleTableDataNode,
    MaStroScheduleFlattenNode,
    MaStroScheduleViewerNode,
)


def register():
    nodeitems_utils.register_node_categories('MASTRO_SCHEDULE_NODES', schedule_node_categories)
    register_viewer_draw_handler()
    start_polling()


def unregister():
    stop_polling()
    unregister_viewer_draw_handler()
    nodeitems_utils.unregister_node_categories('MASTRO_SCHEDULE_NODES')
