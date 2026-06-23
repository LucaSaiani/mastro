import bpy
from bpy.types import Node
from bpy.props import EnumProperty

from .tree import MaStroScheduleTreeNode
from .execution import update_node, get_node_table

FIELD_DOMAINS = {
    'VERTEX': 'POINT',
    'EDGE': 'EDGE',
    'FACE': 'FACE',
}

# bpy attribute data items expose the stored value under different property
# names depending on the attribute's data type (int/float/bool vs vector vs
# color vs string).
VALUE_PROPERTY_BY_TYPE = {
    'FLOAT': 'value',
    'INT': 'value',
    'BOOLEAN': 'value',
    'INT8': 'value',
    'FLOAT2': 'vector',
    'FLOAT_VECTOR': 'vector',
    'FLOAT_COLOR': 'color',
    'BYTE_COLOR': 'color',
    'STRING': 'value',
    'QUATERNION': 'value',
    'FLOAT4X4': 'value',
}


def _read_attribute_value(attr, index):
    prop_name = VALUE_PROPERTY_BY_TYPE.get(attr.data_type, 'value')
    item = attr.data[index]
    value = getattr(item, prop_name)
    return tuple(value) if prop_name in ('vector', 'color') else value


# mastro_props fields exposed as pseudo object-level attributes, alongside
# the object's own custom properties (obj.keys()). Stored as raw ids (e.g.
# mastro_block_attribute), not resolved to names - that is a separate node's
# job (id -> name lookup against mastro_block_name_list/mastro_building_name_list).
OBJECT_MASTRO_PROPS = ("Block", "Building")
OBJECT_MASTRO_PROPS_SOURCE = {
    "Block": "mastro_block_attribute",
    "Building": "mastro_building_attribute",
}


def _unique_objects(node):
    """Resolve the distinct MaStro objects referenced by the table feeding
    this node's Objects input (typically Input Mesh All/Selected)."""
    objs = []
    socket = node.inputs[0]
    if socket.is_linked:
        link = socket.links[0]
        table = get_node_table(node.id_data.name, link.from_node.name)
        if table:
            output_index = list(link.from_node.outputs).index(link.from_socket)
            seen = set()
            for row in table[output_index] or []:
                name = row.get("Object")
                obj = bpy.data.objects.get(name)
                if obj is not None and name not in seen:
                    seen.add(name)
                    objs.append(obj)
    return objs


def get_attribute_items(node, context):
    """List the attributes available for the current Field: object custom
    properties for 'Object', or mesh attributes of the matching domain for
    Vertex/Edge/Face."""
    names = []
    for obj in _unique_objects(node):
        if node.field == 'OBJECT':
            for name in OBJECT_MASTRO_PROPS:
                if name not in names:
                    names.append(name)
            for key in obj.keys():
                if not key.startswith("_") and key not in names:
                    names.append(key)
        else:
            domain = FIELD_DOMAINS[node.field]
            for attr in obj.data.attributes:
                if attr.domain == domain and attr.name not in names:
                    names.append(attr.name)

    items = [(name, name, "") for name in names] or [("", "(no attributes)", "")]
    return items


class MaStroScheduleGetAttributeNode(MaStroScheduleTreeNode, Node):
    """Read an attribute for the chosen Field (Object custom property, or
    Vertex/Edge/Face mesh attribute) from the objects feeding the Objects
    input. Produces a fresh table with one row per element of that Field's
    domain - Object custom properties give one row per object, Face/Edge/
    Vertex attributes give one row per face/edge/vertex. Combining rows
    from different Fields (e.g. matching a Face row to its Object's Phase)
    is the job of a future Join node, not of this one"""
    bl_idname = 'MaStroScheduleGetAttribute'
    bl_label = 'Get Attribute ?'

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
    attribute_name: EnumProperty(
        name="Attribute",
        items=get_attribute_items,
        update=update_node,
    )

    def init(self, context):
        self.inputs.new('MaStroScheduleDataSocketType', "Objects")
        self.outputs.new('MaStroScheduleDataSocketType', "Data")

    def draw_buttons(self, context, layout):
        layout.prop(self, "field")
        layout.prop(self, "attribute_name")

    def evaluate(self, inputs):
        out_key = self.attribute_name or "Attribute"
        result = []

        for obj in _unique_objects(self):
            if self.field == 'OBJECT':
                if self.attribute_name in OBJECT_MASTRO_PROPS_SOURCE:
                    value = getattr(obj.mastro_props, OBJECT_MASTRO_PROPS_SOURCE[self.attribute_name], "")
                else:
                    value = obj.get(self.attribute_name, "")
                result.append({
                    "Object": obj.name,
                    out_key: value,
                })
            else:
                domain = FIELD_DOMAINS[self.field]
                if self.attribute_name not in obj.data.attributes:
                    continue
                attr = obj.data.attributes[self.attribute_name]
                if attr.domain != domain:
                    continue
                index_key = {'POINT': "Vertex", 'EDGE': "Edge", 'FACE': "Face"}[domain]
                for i in range(len(attr.data)):
                    result.append({
                        "Object": obj.name,
                        index_key: i,
                        out_key: _read_attribute_value(attr, i),
                    })

        return [result]
