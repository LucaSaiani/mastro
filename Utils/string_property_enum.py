import bpy
from bpy.props import EnumProperty


def _prop_name(property_id):
    return f"mastro_string_enum_{property_id}"


def _make_items(property_id):
    def items(self, context):
        prop = next(
            (p for p in context.scene.mastro_custom_property_name_list
             if p.id == property_id),
            None,
        )
        if prop is None:
            return [("0", "—", "", 0)]
        result = sorted(
            [(str(o.id), o.name, o.name, o.id) for o in prop.string_options],
            key=lambda t: t[1],
        )
        return result or [("0", "—", "No options defined", 0)]
    return items


def _make_get(property_id):
    def get(self):
        prop = next(
            (p for p in bpy.context.scene.mastro_custom_property_name_list
             if p.id == property_id),
            None,
        )
        if prop is None:
            return 0
        obj = bpy.context.object
        if obj is None:
            return 0
        return obj.get(f"_{prop.name}", 0)
    return get


def _make_set(property_id):
    def set(self, value):
        prop = next(
            (p for p in bpy.context.scene.mastro_custom_property_name_list
             if p.id == property_id),
            None,
        )
        if prop is None:
            return
        obj = bpy.context.object
        if obj is None:
            return
        key = f"_{prop.name}"
        if key in obj:
            obj[key] = value
    return set


def register_string_enum(property_id):
    name = _prop_name(property_id)
    if hasattr(bpy.types.Scene, name):
        return
    setattr(
        bpy.types.Scene,
        name,
        EnumProperty(
            name="String Value",
            items=_make_items(property_id),
            get=_make_get(property_id),
            set=_make_set(property_id),
        ),
    )


def unregister_string_enum(property_id):
    name = _prop_name(property_id)
    if hasattr(bpy.types.Scene, name):
        delattr(bpy.types.Scene, name)


def sync_string_enums():
    """Re-register enums for all committed STRING properties (called on load)."""
    for scene in bpy.data.scenes:
        for prop in scene.mastro_custom_property_name_list:
            if prop.committed and prop.property_type == 'STRING':
                register_string_enum(prop.id)
