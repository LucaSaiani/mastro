import os

import bpy
from bpy.types import Operator


class OBJECT_OT_Linked_Collection_Reload(Operator):
    """Re-link an unloaded collection from its source file and restore its instance"""
    bl_idname = "mastro_linked_collections.reload"
    bl_label = "Reload Collection"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        props = context.scene.mastro_linked_collections_props
        index = props.active_index
        if not (0 <= index < len(props.entries)):
            return False
        return props.entries[index].status in {'UNLOADED', 'BROKEN'}

    def execute(self, context):
        props = context.scene.mastro_linked_collections_props
        entry = props.entries[props.active_index]

        with bpy.data.libraries.load(entry.filepath, link=True) as (data_from, data_to):
            if entry.collection_name not in data_from.collections:
                entry.status = 'BROKEN'
                self.report(
                    {'ERROR'},
                    f"Collection '{entry.collection_name}' not found in {entry.filepath}",
                )
                return {'CANCELLED'}
            data_to.collections = [entry.collection_name]

        collection = data_to.collections[0]
        if collection is None:
            entry.status = 'BROKEN'
            self.report({'ERROR'}, f"Collection '{entry.collection_name}' could not be loaded")
            return {'CANCELLED'}

        instance = bpy.data.objects.new(f"Instance_{collection.name}", None)
        instance.instance_type = 'COLLECTION'
        instance.instance_collection = collection
        instance.location = entry.instance_location
        instance.rotation_euler = entry.instance_rotation_euler
        instance.scale = entry.instance_scale
        context.collection.objects.link(instance)

        entry.instance_object_name = instance.name
        entry.status = 'LOADED'
        entry.source_mtime = str(os.path.getmtime(entry.filepath))
        entry.source_changed = False

        return {'FINISHED'}
