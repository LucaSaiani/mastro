import bpy
from bpy.types import Operator

from .OBJECT_OT_Linked_Collection_Unload import _has_pending_override


class OBJECT_OT_Linked_Collection_Remove(Operator):
    """Remove the registry entry for the active collection, unloading it first if still loaded"""
    bl_idname = "mastro_linked_collections.remove"
    bl_label = "Remove Collection Entry"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        props = context.scene.mastro_linked_collections_props
        return 0 <= props.active_index < len(props.entries)

    def execute(self, context):
        props = context.scene.mastro_linked_collections_props
        index = props.active_index
        entry = props.entries[index]

        if entry.status == 'LOADED':
            instance = bpy.data.objects.get(entry.instance_object_name)
            if instance is not None:
                collection = instance.instance_collection
                if collection is not None and _has_pending_override(collection):
                    self.report(
                        {'ERROR'},
                        f"'{collection.name}' has pending Library Overrides — resolve or apply them before removing",
                    )
                    return {'CANCELLED'}
                bpy.data.objects.remove(instance, do_unlink=True)
                bpy.data.orphans_purge(do_recursive=True)

        props.entries.remove(index)
        props.active_index = max(0, index - 1)

        return {'FINISHED'}
