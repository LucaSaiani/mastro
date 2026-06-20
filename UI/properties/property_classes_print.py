from bpy.types import PropertyGroup
from bpy.props import (IntProperty,
                       BoolProperty,
                       StringProperty,
                       EnumProperty,
                       CollectionProperty,
)

from ...Utils.import_export.print_configured import HARDCODED_PRINT_PARAMS, CALC_ITEMS, scan_custom_param_names

# module-level cache so Python does not garbage-collect the strings while
# Blender still holds raw C pointers to the dynamic EnumProperty items
_enum_cache = {}


def _available_param_names(context, scan_scope):
    return sorted(set(HARDCODED_PRINT_PARAMS) | set(scan_custom_param_names(context, scan_scope)))


def _param_name_items(self, context):
    pp = context.scene.mastro_print_props
    available_names = _available_param_names(context, pp.scan_scope)
    # assign each name a stable numeric id based on its position in the full
    # list, so that the stored enum value doesn't shift when the available
    # names change (e.g. scan scope change)
    items = [(name, name, "", i) for i, name in enumerate(available_names)]
    _enum_cache[self.as_pointer()] = items
    return items


def _on_param_name_change(self, context):
    self.name = self.param_name


class mastro_CL_print_set_param(PropertyGroup):
    """One column inside a print set, in print/grouping order."""
    name: StringProperty(name="Name", default="")
    param_name: EnumProperty(name="Column", items=_param_name_items, update=_on_param_name_change)
    calc: EnumProperty(
        name="Calc",
        description="Aggregation applied to this column in subtotal/grouped rows",
        items=CALC_ITEMS,
        default='NONE',
    )
    group: BoolProperty(
        name="Group",
        description="Collapse rows with the same value of this column into a single row",
        default=False,
    )
    total: BoolProperty(
        name="Total",
        description="Print a subtotal row for this column's groups",
        default=False,
    )
    sort_desc: BoolProperty(
        name="Sort Descending",
        description="Sort order for this column (ascending / descending)",
        default=False,
    )


class mastro_CL_print_set(PropertyGroup):
    """A named, ordered list of columns to print."""
    name: StringProperty(name="Name", default="Schedule")
    params: CollectionProperty(type=mastro_CL_print_set_param)
    active_param_index: IntProperty(default=0)


class mastro_CL_print_scene_props(PropertyGroup):
    print_sets: CollectionProperty(type=mastro_CL_print_set)
    active_set_index: IntProperty(default=0)

    scan_scope: EnumProperty(
        name="Scan",
        description="Which objects to scan for custom properties and to print",
        items=(
            ('VISIBLE', "Visible", "Visible objects in the scene"),
            ('SELECTED', "Selected", "Selected objects"),
            ('ALL', "All", "All objects in the scene"),
        ),
        default='VISIBLE',
    )
