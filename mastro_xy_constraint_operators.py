# The source of this document can be found in the autoConstraintsFree addon by SpaghetMeNot

import bpy
import mathutils


def get_view_axis(context):
    """Returns the closest axis to the view vector in a tuple of bools. e.g. X axis = (True, False, False)"""
    
    # Set up view vector based on axis lock settings
    view_vector = mathutils.Vector((0, 0, -1))
    view_rotation = context.space_data.region_3d.view_rotation
    view_vector.rotate(view_rotation)

    # Get transform orientation mode
    transform_orientation_slot = context.scene.transform_orientation_slots[0]
    default_orientations = [i.identifier for i in transform_orientation_slot.bl_rna.properties['type'].enum_items]
    orientation_type = transform_orientation_slot.type

    # Convert view_vector to selected orientation
    orientation_type = transform_orientation_slot.type
    if orientation_type == 'GLOBAL':
        pass
    elif orientation_type == 'LOCAL' or (orientation_type == 'NORMAL' and context.mode == 'OBJECT'):
        inv_mat = context.object.matrix_world.to_euler().to_matrix()
        view_vector = view_vector @ inv_mat
    elif orientation_type == 'CURSOR':
        inv_mat = context.scene.cursor.matrix
        view_vector = view_vector @ inv_mat
    elif orientation_type == 'PARENT':
        obj = context.object
        obj = context.object.parent if context.object.parent != None else obj
        inv_mat = obj.rotation_euler.to_matrix()
        view_vector = view_vector @ inv_mat
    # For unsupported default orientations return all axis (will not apply constraints)
    elif orientation_type in default_orientations:
        return (True, True, True)
    # Custom orientation
    else:
        inv_mat = transform_orientation_slot.custom_orientation.matrix
        view_vector = view_vector @ inv_mat

    # Return closest axis
    abs_vector = [abs(view_vector[0]), abs(view_vector[1]), abs(view_vector[2])]
    if abs_vector[0] > abs_vector[1] and abs_vector[0] > abs_vector[2]:
        return (True, False, False)
    elif abs_vector[1] > abs_vector[0] and abs_vector[1] > abs_vector[2]:
        return (False, True, False)
    elif abs_vector[2] >= abs_vector[0] and abs_vector[2] >= abs_vector[0]:
        return (False, False, True)


def get_view_plane(context):
    """Returns the most perpendicular plane to the view vector in the form of a tuple of bools. e.g. XY plane = (True, True, False)"""
    view_axis = get_view_axis(context)
    return (not view_axis[0], not view_axis[1], not view_axis[2])


def multiple_objects_local(context):
    """Returns True when in local orientation with multiple objects selected"""
    return context.scene.transform_orientation_slots[0].type == 'LOCAL' and context.mode == 'OBJECT' and len(context.selected_objects) > 1


def apply_active_object_space(context) -> bool:
    """
    Creates orientation for active object if multiple objects are selected with 'LOCAL' transform orientation selected.
    Returns whether it has run or not
    """
    use_active_object_space = multiple_objects_local(context) and context.scene.tool_settings.transform_pivot_point != 'INDIVIDUAL_ORIGINS'

    if use_active_object_space:
        # Delete the previously used custom orientation, this should limit the amount of extra orientations in the scene to 1. 
        # This is a workaround because deleting the current orientation here and then trying to lock to an axis while moving crashes blender.
        # There could be a solution if wrapper operators were modal, this would be a big refactor
        last_custom_orientation = context.scene.autoconstraints_free_settings.last_custom_orientation
        if last_custom_orientation != "":
            try:
                context.scene.transform_orientation_slots[0].type = last_custom_orientation
                bpy.ops.transform.delete_orientation()
            except TypeError:
                # Custom transform doesn't exist - likely deleted manually
                pass
        # Create new orientation from selected object
        bpy.ops.transform.create_orientation(use=True)
        context.scene.autoconstraints_free_settings.last_custom_orientation = context.scene.transform_orientation_slots[0].type

    return use_active_object_space


class TRANSFORM_OT_translate_auto_constraint(bpy.types.Operator):
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
        # Run normal translate if auto-constraints are off
        constaint_xy_settings = context.scene.constraint_xy_setting
        if  not constaint_xy_settings.constraint_xy_on or context.mode not in context_modes:
            bpy.ops.transform.translate('INVOKE_DEFAULT')
            return {'FINISHED'}

        # If multiple objects selected with local orientation, use the active objects orientation
        use_active_object_space = apply_active_object_space(context)

        # Invoke translate with constraints
        bpy.ops.transform.translate('INVOKE_DEFAULT',
            constraint_axis = get_view_plane(context)
        )
        
        # Switch back to local orientation after running tool
        if use_active_object_space:
            context.scene.transform_orientation_slots[0].type = 'LOCAL'

        return {'FINISHED'}


class TRANSFORM_OT_rotate_auto_constraint(bpy.types.Operator):
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
        # Run normal rotate if auto_constraints are off
        axis = get_view_axis(context)
        constaint_xy_settings = context.scene.constraint_xy_setting
        if  not constaint_xy_settings.constraint_xy_on or context.mode not in context_modes:
            bpy.ops.transform.rotate('INVOKE_DEFAULT')
            return {'FINISHED'}
        
        # If multiple objects selected with local orientation, use the active objects orientation
        use_active_object_space = apply_active_object_space(context)

        # Invoke rotate with constraints
        bpy.ops.transform.rotate('INVOKE_DEFAULT',
            constraint_axis = axis
        )
        
        # Switch back to local orientation after running tool
        if use_active_object_space:
            context.scene.transform_orientation_slots[0].type = 'LOCAL'

        return {'FINISHED'}


context_modes = ['OBJECT']

# Used for registering and unregistering classes
blender_classes = [
    TRANSFORM_OT_translate_auto_constraint,
    TRANSFORM_OT_rotate_auto_constraint,
]


def register():
    # Register classes
    for blender_class in blender_classes:
        bpy.utils.register_class(blender_class)


def unregister():
    # Unregister classes
    for blender_class in blender_classes:
        bpy.utils.unregister_class(blender_class)