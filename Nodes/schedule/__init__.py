from .sockets import (
    MaStroScheduleDataSocket,
    MaStroScheduleAttributeRefSocket,
    MaStroScheduleColumnSocket,
    MaStroScheduleAnySocket,
    MaStroScheduleTableSocket,
    MaStroScheduleStringSocket,
    MaStroScheduleColorSocket,
    MaStroScheduleBooleanSocket,
    MaStroScheduleListSocket,
    MaStroScheduleIdKeySocket,
)
from .tree import MaStroScheduleTree, start_polling, stop_polling
from .properties import (
    MaStro_schedule_key_item,
    MaStro_schedule_cell,
    MaStro_schedule_row,
    MaStro_schedule_table_cell,
    MaStro_schedule_table_column,
    MaStro_schedule_table_merge,
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
from .nodes_integer import MaStroScheduleIntegerNode
from .nodes_column_primitive import MaStroScheduleColumnPrimitiveNode
from .nodes_table_primitive import MaStroScheduleTablePrimitiveNode
from .nodes_string import MaStroScheduleStringNode
from .nodes_rgb import MaStroScheduleColourNode
from .nodes_boolean import MaStroScheduleBooleanNode
from .nodes_header import MaStroScheduleHeaderNode
from .nodes_table_edit_header import MaStroScheduleTableHeaderNode
from .nodes_lookup import MaStroScheduleCategoryLookupNode, MaStroScheduleMatrixLookupNode
from .nodes_table import MaStroScheduleTableDataNode, MaStroScheduleFlattenNode
from .nodes_table_convert import MaStroScheduleConvertColumnToTableNode
from .nodes_table_hide_zero import MaStroScheduleTableHideZeroNode
from .nodes_table_prefix_suffix import MaStroScheduleTablePrefixSuffixNode
from .nodes_table_case import MaStroScheduleTableCaseNode
from .nodes_table_align import MaStroScheduleTableAlignNode
from .nodes_id_keys import MaStroScheduleGetIdKeysNode, MASTRO_OT_Schedule_Pick_Id_Key
from .nodes_aggregate_column import MaStroScheduleAggregateColumnNode
from .nodes_flatten_key import MaStroScheduleFlattenKeyNode
from .nodes_groupby_column import (
    MaStroScheduleGroupByColumnNode,
    MaStroScheduleItemFromListNode,
    MaStroScheduleListLengthNode,
)
from .nodes_accumulate import MaStroScheduleAccumulateNode
from .nodes_viewer import (
    MaStroScheduleViewerNode,
    register_viewer_draw_handler,
    unregister_viewer_draw_handler,
)
from . import menus
from . import nodes_math


classes = (
    MaStro_schedule_key_item,
    MaStro_schedule_cell,
    MaStro_schedule_row,
    MaStro_schedule_table_cell,
    MaStro_schedule_table_column,
    MaStro_schedule_table_merge,
    MaStroScheduleDataSocket,
    MaStroScheduleAttributeRefSocket,
    MaStroScheduleColumnSocket,
    MaStroScheduleAnySocket,
    MaStroScheduleTableSocket,
    MaStroScheduleStringSocket,
    MaStroScheduleColorSocket,
    MaStroScheduleBooleanSocket,
    MaStroScheduleListSocket,
    MaStroScheduleIdKeySocket,
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
    MaStroScheduleIntegerNode,
    MaStroScheduleColumnPrimitiveNode,
    MaStroScheduleTablePrimitiveNode,
    MaStroScheduleStringNode,
    MaStroScheduleColourNode,
    MaStroScheduleBooleanNode,
    MaStroScheduleHeaderNode,
    MaStroScheduleTableHeaderNode,
    MaStroScheduleCategoryLookupNode,
    MaStroScheduleMatrixLookupNode,
    MaStroScheduleTableDataNode,
    MaStroScheduleFlattenNode,
    MaStroScheduleConvertColumnToTableNode,
    MaStroScheduleTableHideZeroNode,
    MaStroScheduleTablePrefixSuffixNode,
    MaStroScheduleTableCaseNode,
    MaStroScheduleTableAlignNode,
    MaStroScheduleGetIdKeysNode,
    MASTRO_OT_Schedule_Pick_Id_Key,
    MaStroScheduleAggregateColumnNode,
    MaStroScheduleFlattenKeyNode,
    MaStroScheduleGroupByColumnNode,
    MaStroScheduleItemFromListNode,
    MaStroScheduleListLengthNode,
    MaStroScheduleAccumulateNode,
    MaStroScheduleViewerNode,
)


def register():
    nodes_math.register()
    menus.register()
    register_viewer_draw_handler()
    start_polling()


def unregister():
    stop_polling()
    unregister_viewer_draw_handler()
    menus.unregister()
    nodes_math.unregister()
