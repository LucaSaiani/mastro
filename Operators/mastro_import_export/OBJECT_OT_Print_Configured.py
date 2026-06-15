from bpy.types import Operator

from ...Utils.import_export.print_configured import build_print_table


class OBJECT_OT_Mastro_Print_Configured(Operator):
    """Print the data of the MaStro mass/block objects using the active print set"""
    bl_idname = "object.mastro_print_configured"
    bl_label = "Print"

    def execute(self, context):
        pp = context.scene.mastro_print_props
        idx = pp.active_set_index
        if idx < 0 or idx >= len(pp.print_sets):
            self.report({'WARNING'}, "No active print set")
            return {'CANCELLED'}

        print_set = pp.print_sets[idx]
        if not print_set.params:
            self.report({'WARNING'}, "Print set has no columns")
            return {'CANCELLED'}

        build_print_table(context, print_set.name, print_set.params, pp.scan_scope)
        return {'FINISHED'}
