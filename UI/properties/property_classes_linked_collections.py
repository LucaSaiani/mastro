from bpy.types import PropertyGroup
from bpy.props import (StringProperty,
                       EnumProperty,
                       FloatVectorProperty,
                       BoolProperty,
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

    # Source file mtime at the last link/reload, and whether the optional
    # background check has since seen the file change on disk. Stored as a
    # string because bpy.props has no float64: FloatProperty is float32,
    # which silently loses ~20+ seconds of precision on a Unix timestamp
    # (confirmed live: a timestamp round-tripped through FloatProperty came
    # back 23 seconds off, enough to register a false "source changed").
    source_mtime: StringProperty(default="0.0")
    source_changed: BoolProperty(default=False)


class mastro_CL_linked_collections_props(PropertyGroup):
    """Scene-level container for the Linked Collections registry."""

    entries: CollectionProperty(type=mastro_CL_linked_collection_entry)
    active_index: IntProperty(default=0)
