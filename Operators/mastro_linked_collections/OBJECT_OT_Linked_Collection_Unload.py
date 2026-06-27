import bpy
from bpy.types import Operator


def _has_pending_override(collection):
    """Check the collection and everything it contains for a Library Override,
    so unloading never silently discards work the user did on top of a link."""
    if collection.override_library is not None:
        return True
    for obj in collection.all_objects:
        if obj.override_library is not None:
            return True
        if obj.data is not None and getattr(obj.data, "override_library", None) is not None:
            return True
    return False


class OBJECT_OT_Linked_Collection_Unload(Operator):
    """Remove the collection instance and free the linked collection from memory, keeping the registry entry for later reload"""
    bl_idname = "mastro_linked_collections.unload"
    bl_label = "Unload Collection"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        props = context.scene.mastro_linked_collections_props
        index = props.active_index
        if not (0 <= index < len(props.entries)):
            return False
        return props.entries[index].status == 'LOADED'

    def execute(self, context):
        props = context.scene.mastro_linked_collections_props
        entry = props.entries[props.active_index]

        instance = bpy.data.objects.get(entry.instance_object_name)
        if instance is None:
            self.report({'ERROR'}, f"Instance object '{entry.instance_object_name}' not found")
            return {'CANCELLED'}

        collection = instance.instance_collection
        if collection is not None and _has_pending_override(collection):
            self.report(
                {'ERROR'},
                f"'{collection.name}' has pending Library Overrides — resolve or apply them before unloading",
            )
            return {'CANCELLED'}

        entry.instance_location = instance.location
        entry.instance_rotation_euler = instance.rotation_euler
        entry.instance_scale = instance.scale

        bpy.data.objects.remove(instance, do_unlink=True)
        bpy.data.orphans_purge(do_recursive=True)

        entry.status = 'UNLOADED'
        entry.instance_object_name = ""

        return {'FINISHED'}
