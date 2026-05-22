import bpy
from bpy.types import Operator
from bpy.props import StringProperty

from ..Utils.projection.shadow_silhouette import _CACHE_PREFIX


class OBJECT_OT_ClearShadowCache(Operator):
    """Remove the cached shadow footprint object for this light configuration"""
    bl_idname  = "object.mastro_clear_shadow_cache"
    bl_label   = "Clear Shadow Cache"
    bl_options = {'REGISTER', 'UNDO'}

    cache_name: StringProperty()

    def execute(self, context):
        obj = bpy.data.objects.get(self.cache_name)
        if obj is None:
            self.report({'WARNING'}, f"Cache object '{self.cache_name}' not found.")
            return {'CANCELLED'}
        bpy.data.meshes.remove(obj.data, do_unlink=True)
        self.report({'INFO'}, f"Shadow cache '{self.cache_name}' cleared.")
        return {'FINISHED'}
