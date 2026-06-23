import bpy
from bpy.types import Node
from bpy.props import EnumProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node, linked_table
from .attribute_naming import FIELD_DOMAINS, to_logical_name, COMPUTED_NAMES

# mastro_props fields exposed as pseudo object-level attributes, alongside
# the object's own custom properties (obj.keys()).
OBJECT_MASTRO_PROPS = ("Block", "Building")


def unique_objects(node):
    """Resolve the distinct MaStro objects referenced by the table feeding
    this node's Data input (typically Input Mesh All/Selected)."""
    objs = []
    table = linked_table(node, 0)
    if table:
        seen = set()
        for row in table:
            name = row.get("_Object")
            if name is None or name in seen:
                continue
            obj = bpy.data.objects.get(name)
            if obj is not None:
                seen.add(name)
                objs.append(obj)
    return objs


def get_attribute_name_items(node, context):
    """List the logical attribute names available for the current Field:
    object custom properties for 'Object', or mesh attributes of the
    matching domain for Vertex/Edge/Face (domain suffix stripped, and
    multi-component groups like use/storey/height collapsed to one name)."""
    names = []
    for obj in unique_objects(node):
        if node.field == 'OBJECT':
            for name in OBJECT_MASTRO_PROPS:
                if name not in names:
                    names.append(name)
            for key in obj.keys():
                # "_RNA_UI" is Blender's own internal UI-metadata id-property,
                # not a real custom property - everything else, including
                # mastro's own underscore-prefixed custom properties (see
                # property_classes_custom_properties.py), is real data.
                if key != "_RNA_UI" and key not in names:
                    names.append(key)
        else:
            for computed in COMPUTED_NAMES.get(node.field, ()):
                if computed not in names:
                    names.append(computed)
            domain = FIELD_DOMAINS[node.field]
            for attr in obj.data.attributes:
                if attr.domain != domain:
                    continue
                logical = to_logical_name(attr.name, node.field)
                if logical not in names:
                    names.append(logical)

    items = [(name, name, "") for name in names] or [("", "(no attributes)", "")]
    return items


class MaStroScheduleGetAttributeNamesNode(MaStroScheduleTreeNode, Node):
    """List the attribute names available for the chosen Field (Object
    custom property, or Vertex/Edge/Face mesh attribute) on the objects
    feeding the Data input - names only, no values. Pick one with the Name
    dropdown to feed it to an Evaluate Attribute node, which reads the
    actual values"""
    bl_idname = 'MaStroScheduleGetAttributeNames'
    bl_label = 'Get Attribute Names'

    field: EnumProperty(
        name="Field",
        items=[
            ('OBJECT', "Object", "Object custom property"),
            ('FACE', "Face", "Face-domain mesh attribute"),
            ('EDGE', "Edge", "Edge-domain mesh attribute"),
            ('VERTEX', "Vertex", "Vertex-domain mesh attribute"),
        ],
        default='FACE',
        update=update_node,
    )
    name: EnumProperty(
        name="Name",
        items=get_attribute_name_items,
        update=update_node,
    )

    def init(self, context):
        self.inputs.new('MaStroScheduleDataSocketType', "Data")
        self.outputs.new('MaStroScheduleAttributeRefSocketType', "Name")

    def draw_buttons(self, context, layout):
        layout.prop(self, "field")
        layout.prop(self, "name")

    def evaluate(self, inputs):
        name_ref = [{"Field": self.field, "Name": self.name}] if self.name else []
        return [name_ref]
