import bpy 
from bpy.types import Operator

context_modes = ['OBJECT', 'EDIT_MESH']

class TRANSFORM_OT_translate_xy_constraint(Operator):
    """Wrapper for transform.translate operator with automatic axis constraints"""
    bl_idname = "transform.translate_xy_constraint"
    bl_label = "Translate XY Constraint"
    bl_description = "Invokes the move tool with automatic constraints"
    bl_options = {'REGISTER'}

    # Only available in view_3d
    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D' and context.region.type == 'WINDOW'

    def execute(self, context):
        constaint_xy_settings = context.scene.constraint_xy_setting
        if  not constaint_xy_settings.constraint_xy_on or context.mode not in context_modes:
            bpy.ops.transform.translate('INVOKE_DEFAULT')
            return {'FINISHED'}

        bpy.ops.transform.translate('INVOKE_DEFAULT',
            constraint_axis =  (True, True, False)
        )
        return {'FINISHED'}


class TRANSFORM_OT_rotate_xy_constraint(Operator):
    """Wrapper for transform.rotate operator with automatic axis constraints"""
    bl_idname = "transform.rotate_xy_constraint"
    bl_label = "Rotate XY Constraint"
    bl_description = "Invokes the rotate tool with automatic constraints"
    bl_options = {'REGISTER'}

    # Only available in view_3d
    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D' and context.region.type == 'WINDOW'

    def execute(self, context):
        constaint_xy_settings = context.scene.constraint_xy_setting
        if  not constaint_xy_settings.constraint_xy_on or context.mode not in context_modes:
            bpy.ops.transform.rotate('INVOKE_DEFAULT')
            return {'FINISHED'}
        
        bpy.ops.transform.rotate('INVOKE_DEFAULT',
            constraint_axis = (False, False, True)
        )
        
        return {'FINISHED'}