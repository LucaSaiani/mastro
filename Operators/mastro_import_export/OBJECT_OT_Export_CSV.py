from bpy.types import Operator
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty

from ...Utils.import_export.mastro_export_utils import get_visible_mass_data, granularData, write_csv


class OBJECT_OT_Mastro_Export_CSV(Operator, ExportHelper):
    """Export the data of the visible MaStro Objects as a CSV file"""
    bl_idname = "object.mastro_export_csv"
    bl_label = "Export data as CSV"

    filename_ext = ".csv"
    filter_glob: StringProperty(
        default="*.csv",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    filepath: StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        roughData = get_visible_mass_data()
        if not roughData:
            return {'CANCELLED'}

        granularDataDict = granularData(roughData)
        write_csv(self.filepath, granularDataDict)

        print(f"Data saved to {self.filepath}")
        return {'FINISHED'}
