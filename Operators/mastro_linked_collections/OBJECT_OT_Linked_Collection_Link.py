import os

import bpy
from bpy.types import Operator
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper


def _create_linked_collection_instance(context, filepath, collection_name):
    """Link a collection from filepath, instance it in the scene, and register it in the mastro Linked Collections registry."""
    with bpy.data.libraries.load(filepath, link=True) as (data_from, data_to):
        if collection_name not in data_from.collections:
            return None
        data_to.collections = [collection_name]

    collection = data_to.collections[0]

    instance = bpy.data.objects.new(f"Instance_{collection.name}", None)
    instance.instance_type = 'COLLECTION'
    instance.instance_collection = collection
    context.collection.objects.link(instance)

    props = context.scene.mastro_linked_collections_props
    entry = props.entries.add()
    entry.collection_name = collection.name
    entry.filepath = filepath
    entry.instance_object_name = instance.name
    entry.status = 'LOADED'
    entry.instance_location = instance.location
    entry.instance_rotation_euler = instance.rotation_euler
    entry.instance_scale = instance.scale

    props.active_index = len(props.entries) - 1

    return instance


class OBJECT_OT_Linked_Collection_Choose_Collection(Operator):
    """Pick which collection from the chosen file to link and register"""
    bl_idname = "mastro_linked_collections.choose_collection"
    bl_label = "Choose Collection to Link"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(subtype='FILE_PATH')
    collection_name: StringProperty()

    def execute(self, context):
        instance = _create_linked_collection_instance(context, self.filepath, self.collection_name)
        if instance is None:
            self.report({'ERROR'}, f"Collection '{self.collection_name}' not found in {self.filepath}")
            return {'CANCELLED'}
        return {'FINISHED'}


class OBJECT_OT_Linked_Collection_Link(Operator, ImportHelper):
    """Link a collection from a .blend file and register it in the mastro Linked Collections manager"""
    bl_idname = "mastro_linked_collections.link"
    bl_label = "Link Collection"
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = ".blend"
    filter_glob: StringProperty(default="*.blend", options={'HIDDEN'})

    def execute(self, context):
        if not os.path.isfile(self.filepath):
            self.report({'ERROR'}, f"File not found: {self.filepath}")
            return {'CANCELLED'}

        with bpy.data.libraries.load(self.filepath, link=False) as (data_from, _data_to):
            collection_names = list(data_from.collections)

        if not collection_names:
            self.report({'ERROR'}, "No collections found in the selected file")
            return {'CANCELLED'}

        context.window_manager.popup_menu(
            lambda popup_self, popup_context: self._draw_collection_menu(popup_self, collection_names),
            title="Choose Collection",
        )
        return {'FINISHED'}

    def _draw_collection_menu(self, popup_self, collection_names):
        layout = popup_self.layout
        for name in collection_names:
            op = layout.operator(
                OBJECT_OT_Linked_Collection_Choose_Collection.bl_idname,
                text=name,
            )
            op.filepath = self.filepath
            op.collection_name = name
