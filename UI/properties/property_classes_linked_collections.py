from bpy.types import PropertyGroup
from bpy.props import (StringProperty,
                       EnumProperty,
                       FloatVectorProperty,
                       IntProperty,
                       CollectionProperty,
)


class mastro_CL_linked_collection_entry(PropertyGroup):
    """One collection imported through the mastro Linked Collections manager."""

    collection_name: StringProperty()
    filepath: StringProperty(subtype='FILE_PATH')
    instance_object_name: StringProperty()

    status: EnumProperty(
        items=(
            ('LOADED', "Loaded", "The collection is linked and instanced in the scene"),
            ('UNLOADED', "Unloaded", "The collection has been removed from memory; the entry can be reloaded"),
            ('BROKEN', "Broken", "The collection name could not be found in the source file on reload"),
        ),
        default='LOADED',
    )

    instance_location: FloatVectorProperty(size=3, default=(0.0, 0.0, 0.0))
    instance_rotation_euler: FloatVectorProperty(size=3, default=(0.0, 0.0, 0.0))
    instance_scale: FloatVectorProperty(size=3, default=(1.0, 1.0, 1.0))


class mastro_CL_linked_collections_props(PropertyGroup):
    """Scene-level container for the Linked Collections registry."""

    entries: CollectionProperty(type=mastro_CL_linked_collection_entry)
    active_index: IntProperty(default=0)
