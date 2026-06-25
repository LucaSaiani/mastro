import bpy
from bpy.types import Node
from bpy.props import EnumProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node
from .mass_rows import granular_rows_per_object
from ...Utils.import_export.mastro_export_utils import get_mass_data_for_scope

# Static, hardcoded category list - safe as a normal multi-select
# EnumProperty (ENUM_FLAG): no items callback, nothing dynamic, so this
# doesn't carry the RecursionError risk a dynamic-items EnumProperty did
# (see nodes_attribute.py's history). "Mass" covers both MaStro mass and
# MaStro block objects in one category (a Block already behaves like a
# Mass once its Geometry Nodes modifiers have run, so they share the same
# row schema - see mass_rows.py) - there's no separate "Block" entry.
#
# The CSV/print export (Utils/import_export/mastro_export_utils.py) is
# deliberately scoped to mass/block only - a uniform row shape that's
# manageable in Excel. The node tree's whole point is to go beyond that:
# mixing heterogeneous MaStro categories (mass, plan, drawing, street,
# generic mesh) in one schedule, something a monolithic CSV export can't
# do cleanly once the row shapes diverge this much.
CATEGORY_ITEMS = [
    ('MASS', "Mass", "MaStro mass and block objects"),
    ('PLAN', "Plan", "MaStro plan objects"),
    ('DRAWING', "Drawing", "MaStro CAD drawing objects"),
    ('STREET', "Street", "MaStro street objects"),
    ('MESH', "Mesh", "Any other mesh object, not marked as MaStro"),
]


def _category_objects(category, candidates):
    """Mesh objects among `candidates` matching one of PLAN/DRAWING/
    STREET/MESH (never called with MASS - that goes through
    get_mass_data_for_scope/mass_rows.granular_rows_per_object instead,
    see _evaluate_categories below). These categories have no
    mass-style row schema (no Block Name/Typology/etc. - they're not
    mass/block objects), so they're resolved here as plain object lists;
    their rows are built directly in _evaluate_categories."""
    matched = []
    for obj in candidates:
        if obj.type != 'MESH':
            continue
        is_mastro = "MaStro object" in obj.data
        if category == 'MESH':
            if not is_mastro:
                matched.append(obj)
        elif is_mastro and f"MaStro {category.lower()}" in obj.data:
            matched.append(obj)
    return matched


def _evaluate_categories(categories, scope):
    """Build the combined table for every selected category, over either
    every object in the scene or just the selected ones (`scope`: 'ALL'
    or 'SELECTED').

    Mass rows keep the full mass_rows schema (Block Name, Typology,
    Floor Area, ...); Plan/Drawing/Street/Mesh rows are minimal
    ({_Object: name}) - downstream nodes (Get Attribute Names/Evaluate
    Attribute) read each object's actual attributes from there. Rows
    from different categories can end up with different columns in the
    same table - intentional, not a bug: available_attribute_names
    (nodes_attribute.py) only offers names common to every object
    actually feeding a node, so a mixed-category table never silently
    proposes a column most rows don't have."""
    rows = []
    if 'MASS' in categories:
        rough = get_mass_data_for_scope(bpy.context, scope, use_cache=True)
        rows.extend(granular_rows_per_object(rough) if rough else [])

    other_categories = categories - {'MASS'}
    if other_categories:
        candidates = bpy.context.selected_objects if scope == 'SELECTED' else bpy.context.scene.objects
        for category in ('PLAN', 'DRAWING', 'STREET', 'MESH'):
            if category not in other_categories:
                continue
            for obj in _category_objects(category, candidates):
                rows.append({"_Object": obj.name})
    return rows


class MaStroScheduleInputAllNode(MaStroScheduleTreeNode, Node):
    """Build the schedule table from every matching object of the
    selected categories in the scene"""
    bl_idname = 'MaStroScheduleInputAll'
    bl_label = 'Input All'

    categories: EnumProperty(
        name="Categories",
        items=CATEGORY_ITEMS,
        options={'ENUM_FLAG'},
        default={'MASS'},
        update=update_node,
    )

    def init(self, context):
        self.outputs.new('MaStroScheduleDataSocketType', "Data")

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        for identifier, label, _ in CATEGORY_ITEMS:
            col.prop_enum(self, "categories", identifier, text=label)

    def evaluate(self, inputs):
        return [_evaluate_categories(self.categories, 'ALL')]


class MaStroScheduleInputSelectedNode(MaStroScheduleTreeNode, Node):
    """Build the schedule table from the currently selected matching
    objects of the selected categories"""
    bl_idname = 'MaStroScheduleInputSelected'
    bl_label = 'Input Selected'

    categories: EnumProperty(
        name="Categories",
        items=CATEGORY_ITEMS,
        options={'ENUM_FLAG'},
        default={'MASS'},
        update=update_node,
    )

    def init(self, context):
        self.outputs.new('MaStroScheduleDataSocketType', "Data")

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        for identifier, label, _ in CATEGORY_ITEMS:
            col.prop_enum(self, "categories", identifier, text=label)

    def evaluate(self, inputs):
        return [_evaluate_categories(self.categories, 'SELECTED')]
