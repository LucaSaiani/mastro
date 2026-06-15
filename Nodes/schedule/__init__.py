import nodeitems_utils

from .sockets import MaStroScheduleDataSocket
from .tree import MaStroScheduleTree
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
)
from .nodes_input import MaStroScheduleInputAllNode, MaStroScheduleInputSelectedNode
from .nodes_attribute import MaStroScheduleGetCustomAttributeNode
from .nodes_filter import MaStroScheduleFilterNode
from .nodes_groupby import MaStroScheduleGroupByNode
from .nodes_aggregate import MaStroScheduleAggregateNode
from .nodes_math import MaStroScheduleMathNode
from .nodes_lookup import MaStroScheduleCategoryLookupNode, MaStroScheduleMatrixLookupNode
from .nodes_table import MaStroScheduleTableDataNode
from .nodes_viewer import MaStroScheduleViewerNode
from .menus import schedule_node_categories


classes = (
    MaStro_schedule_key_item,
    MaStro_schedule_cell,
    MaStro_schedule_row,
    MaStroScheduleDataSocket,
    MaStroScheduleTree,
    MASTRO_UL_schedule_keys,
    MASTRO_OT_Schedule_GroupBy_Key_Add,
    MASTRO_OT_Schedule_GroupBy_Key_Remove,
    MASTRO_UL_schedule_category_lookup,
    MASTRO_OT_Schedule_Category_Lookup_Add,
    MASTRO_OT_Schedule_Category_Lookup_Remove,
    MaStroScheduleInputAllNode,
    MaStroScheduleInputSelectedNode,
    MaStroScheduleGetCustomAttributeNode,
    MaStroScheduleFilterNode,
    MaStroScheduleGroupByNode,
    MaStroScheduleAggregateNode,
    MaStroScheduleMathNode,
    MaStroScheduleCategoryLookupNode,
    MaStroScheduleMatrixLookupNode,
    MaStroScheduleTableDataNode,
    MaStroScheduleViewerNode,
)


def register():
    nodeitems_utils.register_node_categories('MASTRO_SCHEDULE_NODES', schedule_node_categories)


def unregister():
    nodeitems_utils.unregister_node_categories('MASTRO_SCHEDULE_NODES')
