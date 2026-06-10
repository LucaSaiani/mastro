import bpy
from bpy.types import Operator
from bpy.props import StringProperty


# ─────────────────────────────────────────────────────────────────────────────

class MASTRO_OT_CameraSetAdd(Operator):
    """Add a new empty camera set"""
    bl_idname  = "mastro.camera_set_add"
    bl_label   = "Add Camera Set"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ssp = context.scene.mastro_projector_props
        s = ssp.camera_sets.add()
        s.name = "Set"
        s.is_default = False
        ssp.active_set_index = len(ssp.camera_sets) - 1
        return {'FINISHED'}


class MASTRO_OT_CameraSetRemove(Operator):
    """Remove the selected camera set"""
    bl_idname  = "mastro.camera_set_remove"
    bl_label   = "Remove Camera Set"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ssp = context.scene.mastro_projector_props
        idx = ssp.active_set_index
        if idx < 0 or idx >= len(ssp.camera_sets):
            return {'CANCELLED'}
        if ssp.camera_sets[idx].is_default:
            self.report({'WARNING'}, "Set 0 cannot be deleted.")
            return {'CANCELLED'}
        ssp.camera_sets.remove(idx)
        ssp.active_set_index = max(0, idx - 1)
        return {'FINISHED'}


class MASTRO_OT_CameraSetDuplicate(Operator):
    """Duplicate the selected camera set"""
    bl_idname  = "mastro.camera_set_duplicate"
    bl_label   = "Duplicate Camera Set"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ssp = context.scene.mastro_projector_props
        idx = ssp.active_set_index
        if idx < 0 or idx >= len(ssp.camera_sets):
            return {'CANCELLED'}
        src = ssp.camera_sets[idx]
        dst = ssp.camera_sets.add()
        dst.name = src.name + " Copy"
        dst.is_default = False
        for item in src.cameras:
            dst.cameras.add().camera_name = item.camera_name
        ssp.active_set_index = len(ssp.camera_sets) - 1
        return {'FINISHED'}


class MASTRO_OT_CameraSetMoveUp(Operator):
    """Move the selected camera set up"""
    bl_idname  = "mastro.camera_set_move_up"
    bl_label   = "Move Camera Set Up"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ssp = context.scene.mastro_projector_props
        idx = ssp.active_set_index
        # Cannot move Set 0, and cannot move a set above Set 0 (index 1 → stays at 1)
        if idx <= 1:
            return {'CANCELLED'}
        ssp.camera_sets.move(idx, idx - 1)
        ssp.active_set_index = idx - 1
        return {'FINISHED'}


class MASTRO_OT_CameraSetMoveDown(Operator):
    """Move the selected camera set down"""
    bl_idname  = "mastro.camera_set_move_down"
    bl_label   = "Move Camera Set Down"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ssp = context.scene.mastro_projector_props
        idx = ssp.active_set_index
        if ssp.camera_sets[idx].is_default:
            return {'CANCELLED'}
        if idx >= len(ssp.camera_sets) - 1:
            return {'CANCELLED'}
        ssp.camera_sets.move(idx, idx + 1)
        ssp.active_set_index = idx + 1
        return {'FINISHED'}


class MASTRO_OT_CameraSetToggleCamera(Operator):
    """Add or remove a camera from the selected set"""
    bl_idname  = "mastro.camera_set_toggle_camera"
    bl_label   = "Toggle Camera in Set"
    bl_options = {'REGISTER', 'UNDO'}

    camera_name: StringProperty()

    def execute(self, context):
        ssp = context.scene.mastro_projector_props
        idx = ssp.active_set_index
        if idx < 0 or idx >= len(ssp.camera_sets):
            return {'CANCELLED'}
        s = ssp.camera_sets[idx]
        if s.is_default:
            self.report({'WARNING'}, "Set 0 membership is managed automatically.")
            return {'CANCELLED'}
        for i, item in enumerate(s.cameras):
            if item.camera_name == self.camera_name:
                s.cameras.remove(i)
                return {'FINISHED'}
        s.cameras.add().camera_name = self.camera_name
        return {'FINISHED'}
