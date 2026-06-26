from .sockets import (
    MaStroScheduleDataSocket,
    MaStroScheduleAttributeRefSocket,
    MaStroScheduleColumnSocket,
    MaStroScheduleMultiColumnSocket,
    MaStroScheduleAnySocket,
    MaStroScheduleTableSocket,
    MaStroScheduleSheetSocket,
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
    MaStro_schedule_join_table_item,
    MaStro_schedule_export_sheet_item,
)
from .operators import (
    MASTRO_UL_schedule_keys,
    MASTRO_OT_Schedule_GroupBy_Key_Add,
    MASTRO_OT_Schedule_GroupBy_Key_Remove,
    MASTRO_UL_schedule_category_lookup,
    MASTRO_OT_Schedule_Category_Lookup_Add,
    MASTRO_OT_Schedule_Category_Lookup_Remove,
    MASTRO_UL_schedule_join_tables,
    MASTRO_OT_Schedule_Join_Tables_Move,
    MASTRO_UL_schedule_export_sheets,
    MASTRO_OT_Schedule_Export_Sheets_Move,
    MASTRO_OT_Schedule_Excel_Export,
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
from .nodes_sheet_primitive import MaStroScheduleSheetPrimitiveNode
from .nodes_string import MaStroScheduleStringNode
from .nodes_rgb import MaStroScheduleColourNode
from .nodes_boolean import MaStroScheduleBooleanNode
from .nodes_header import MaStroScheduleHeaderNode
from .nodes_table_edit_header import MaStroScheduleTableHeaderNode
from .nodes_lookup import MaStroScheduleCategoryLookupNode, MaStroScheduleMatrixLookupNode
from .nodes_table import MaStroScheduleTableDataNode, MaStroScheduleFlattenNode
from .nodes_table_convert import MaStroScheduleConvertColumnToTableNode
from .nodes_table_join import MaStroScheduleTableJoinNode
from .nodes_table_sheet import MaStroScheduleTableSheetNode
from .nodes_sheet_move import MaStroScheduleSheetMoveNode
from .nodes_sheet_place import MaStroScheduleSheetPlaceNode
from .nodes_sheet_background import MaStroScheduleSheetBackgroundNode
from .nodes_sheet_grid import MaStroScheduleSheetGridNode
from .nodes_excel_export import MaStroScheduleExcelExportNode
from .nodes_table_hide_zero import MaStroScheduleTableHideZeroNode
from .nodes_table_prefix_suffix import MaStroScheduleTablePrefixSuffixNode
from .nodes_table_case import MaStroScheduleTableCaseNode
from .nodes_table_align import MaStroScheduleTableAlignNode
from .nodes_table_edit_cell import MaStroScheduleTableEditCellNode
from .nodes_table_row_colour import MaStroScheduleTableRowColourNode
from .nodes_table_row_pattern import MaStroScheduleTableRowPatternNode
from .nodes_id_keys import MaStroScheduleGetIdKeysNode, MASTRO_OT_Schedule_Pick_Id_Key
from .nodes_aggregate_column import MaStroScheduleAggregateColumnNode
from .nodes_pivot import MaStroSchedulePivotNode
from .nodes_multicolumn_convert import MaStroScheduleMultiColumnToTableNode
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
    MaStro_schedule_join_table_item,
    MaStro_schedule_export_sheet_item,
    MaStroScheduleDataSocket,
    MaStroScheduleAttributeRefSocket,
    MaStroScheduleColumnSocket,
    MaStroScheduleMultiColumnSocket,
    MaStroScheduleAnySocket,
    MaStroScheduleTableSocket,
    MaStroScheduleSheetSocket,
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
    MASTRO_UL_schedule_join_tables,
    MASTRO_OT_Schedule_Join_Tables_Move,
    MASTRO_UL_schedule_export_sheets,
    MASTRO_OT_Schedule_Export_Sheets_Move,
    MASTRO_OT_Schedule_Excel_Export,
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
    MaStroScheduleSheetPrimitiveNode,
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
    MaStroScheduleTableJoinNode,
    MaStroScheduleTableSheetNode,
    MaStroScheduleSheetMoveNode,
    MaStroScheduleSheetPlaceNode,
    MaStroScheduleSheetBackgroundNode,
    MaStroScheduleSheetGridNode,
    MaStroScheduleExcelExportNode,
    MaStroScheduleTableHideZeroNode,
    MaStroScheduleTablePrefixSuffixNode,
    MaStroScheduleTableCaseNode,
    MaStroScheduleTableAlignNode,
    MaStroScheduleTableEditCellNode,
    MaStroScheduleTableRowColourNode,
    MaStroScheduleTableRowPatternNode,
    MaStroScheduleGetIdKeysNode,
    MASTRO_OT_Schedule_Pick_Id_Key,
    MaStroScheduleAggregateColumnNode,
    MaStroSchedulePivotNode,
    MaStroScheduleMultiColumnToTableNode,
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
