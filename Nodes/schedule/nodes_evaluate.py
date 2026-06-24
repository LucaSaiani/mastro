import bpy
import bmesh
from bpy.types import Node

from .tree import MaStroScheduleTreeNode
from .attribute_naming import FIELD_DOMAINS, ATTRIBUTE_GROUPS, domain_raw_name
from .nodes_attribute import OBJECT_MASTRO_PROPS, unique_objects

OBJECT_MASTRO_PROPS_SOURCE = {
    "Block": "mastro_block_attribute",
    "Building": "mastro_building_attribute",
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

# the parallel-digit-string place value of each raw suffix within its group,
# used to recombine the per-level digit into the final decoded value
# (mirrors extract_mesh_rows: height = A*10 + B + C*0.1 + D*0.01 + E*0.001)
RAW_SUFFIX_WEIGHT = {
    "mastro_list_use_id_A": 10, "mastro_list_use_id_B": 1,
    "mastro_list_storey_A": 10, "mastro_list_storey_B": 1,
    "mastro_list_height_A": 10, "mastro_list_height_B": 1,
    "mastro_list_height_C": 0.1, "mastro_list_height_D": 0.01, "mastro_list_height_E": 0.001,
}


def _read_attribute_value(attr, index):
    prop_name = VALUE_PROPERTY_BY_TYPE.get(attr.data_type, 'value')
    item = attr.data[index]
    value = getattr(item, prop_name)
    return tuple(value) if prop_name in ('vector', 'color') else value


def _digits(raw_value):
    """Parallel-digit-string encoding: the int holds one digit per
    storey-group across the whole face, prefixed with "1" to avoid leading
    zeros being dropped (see add_attributes_mass.py). Stripping that "1"
    gives one character per group, indexed by group_index - simpler in
    plain Python than the log10/power-of-ten digit extraction used on the
    Geometry Nodes side, where strings aren't practical to slice."""
    return str(raw_value)[1:]


class MaStroScheduleEvaluateAttributeNode(MaStroScheduleTreeNode, Node):
    """Read the actual values of the attribute named by the Name input (from
    a Get Attribute Names node) for the objects in the Data input.
    For Field=Face, every face of a MaStro mass/block stands for
    `mastro_number_of_storeys` stacked floors, so this always expands one
    row per face into one row per (face, level); multi-component groups
    (use/storey/height) are decoded per level the same way the legacy
    Input Mesh node does. For Object/Edge/Vertex there is no such
    expansion - one row per element"""
    bl_idname = 'MaStroScheduleEvaluateAttribute'
    bl_label = 'Evaluate Attribute'

    def init(self, context):
        self.inputs.new('MaStroScheduleDataSocketType', "Data")
        self.inputs.new('MaStroScheduleAttributeRefSocketType', "Name")
        self.outputs.new('MaStroScheduleDataSocketType', "Data")

    def evaluate(self, inputs):
        objects_table = inputs[0] or []
        name_ref = inputs[1] or []
        if not name_ref:
            return [[]]

        field = name_ref[0].get("Field", "FACE")
        name = name_ref[0].get("Name", "")
        if not name:
            return [[]]

        objs = unique_objects_from_table(objects_table)

        if field == 'OBJECT':
            return [self._evaluate_object(objs, name)]

        domain = FIELD_DOMAINS[field]
        if name == "area":
            raw_names = ()
        elif name in ATTRIBUTE_GROUPS:
            raw_names = ATTRIBUTE_GROUPS[name]
        else:
            raw_names = (domain_raw_name(name, field),)

        if field == 'FACE':
            return [self._evaluate_face_expanded(objs, name, raw_names, domain)]
        return [self._evaluate_simple(objs, name, raw_names, domain)]

    def _evaluate_object(self, objs, name):
        result = []
        for obj in objs:
            if name in OBJECT_MASTRO_PROPS_SOURCE:
                value = getattr(obj.mastro_props, OBJECT_MASTRO_PROPS_SOURCE[name], "")
            else:
                value = obj.get(name, "")
            result.append({"_Object": obj.name, name: value})
        return result

    def _evaluate_simple(self, objs, name, raw_names, domain):
        """One row per element (Edge/Vertex), no per-level expansion."""
        index_key = {'POINT': "_Vertex", 'EDGE': "_Edge", 'FACE': "_Face"}[domain]
        result = []
        for obj in objs:
            attrs = [obj.data.attributes.get(raw) for raw in raw_names]
            if any(a is None or a.domain != domain for a in attrs):
                continue
            count = len(attrs[0].data)
            for i in range(count):
                values = [_read_attribute_value(a, i) for a in attrs]
                value = values[0] if len(values) == 1 else tuple(values)
                result.append({"_Object": obj.name, index_key: i, name: value})
        return result

    def _evaluate_face_expanded(self, objs, name, raw_names, domain):
        """One row per (face, level): every face of a mass/block stands for
        mastro_number_of_storeys stacked floors. Mirrors execution.py's
        extract_mesh_rows decoding loop, generalized to any attribute name."""
        result = []
        is_area = name == "area"
        for obj in objs:
            attrs = obj.data.attributes
            if "mastro_number_of_storeys" not in attrs:
                continue
            storeys_attr = attrs["mastro_number_of_storeys"]

            value_attrs = [attrs.get(raw) for raw in raw_names]
            if any(a is None or a.domain != domain for a in value_attrs):
                continue

            bm = None
            if is_area:
                # area is computed from the face's geometry (BMFace.calc_area()),
                # not a stored mesh attribute - always the full geometric area,
                # undercroft or not, so footprint-style sums at level 0 don't
                # silently lose area. Subtracting undercroft area is the job of
                # a separate node combining this with an "undercroft" Evaluate.
                bm = bmesh.new()
                bm.from_mesh(obj.data)
                bm.faces.ensure_lookup_table()

            # storey_A/_B are always needed to know when a face's storey
            # group advances by one level, same as extract_mesh_rows
            storey_a = attrs.get("mastro_list_storey_A")
            storey_b = attrs.get("mastro_list_storey_B")

            is_digit_group = name in ATTRIBUTE_GROUPS

            for face_index in range(len(storeys_attr.data)):
                storeys = storeys_attr.data[face_index].value

                if is_area:
                    plain_value = bm.faces[face_index].calc_area()
                elif name == "undercroft":
                    undercroft_count = value_attrs[0].data[face_index].value
                elif is_digit_group:
                    digit_strings = [_digits(attr.data[face_index].value) for attr in value_attrs]
                else:
                    # A plain (non digit-encoded) attribute like typology_id,
                    # floor_id or overlay_top: one value per face, repeated
                    # on every level row.
                    plain_value = value_attrs[0].data[face_index].value
                if storey_a is not None:
                    storey_a_digits = _digits(storey_a.data[face_index].value)
                    storey_b_digits = _digits(storey_b.data[face_index].value) if storey_b else None

                storey_group = 0
                group_index = 0
                for level in range(storeys):
                    # Read this level's value at the CURRENT group_index
                    # before deciding whether group_index advances for the
                    # *next* level - mirrors execution.py:extract_mesh_rows,
                    # where storey_A/use_A/height_A are all read at the same
                    # group_index, and group_index only advances after. Doing
                    # the read after advancing (as an earlier version of this
                    # function did) is an off-by-one: on a face's last level,
                    # group_index would already point past the end of the
                    # digit string, raising IndexError - confirmed live.
                    if is_area:
                        value = plain_value
                    elif name == "undercroft":
                        # mastro_undercroft stores a plain count of floors
                        # from the bottom that are undercroft (e.g. 3 means
                        # levels 0,1,2 are undercroft) - not a per-level
                        # digit like use/storey/height, so it's compared
                        # against the current level and reduced to a bool.
                        value = level < undercroft_count
                    elif is_digit_group:
                        values = []
                        for raw, digits in zip(raw_names, digit_strings):
                            weight = RAW_SUFFIX_WEIGHT.get(raw)
                            digit = int(digits[group_index])
                            values.append(digit * weight if weight is not None else digit)
                        value = sum(values) if len(values) > 1 else values[0]
                    else:
                        value = plain_value

                    result.append({
                        "_Object": obj.name,
                        "_Face": face_index,
                        "_Level": level,
                        name: value,
                    })

                    if storey_a is not None:
                        s_a = int(storey_a_digits[group_index])
                        s_b = int(storey_b_digits[group_index]) if storey_b_digits else 0
                        storey_group_new = s_a * 10 + s_b + storey_group
                        if storey_group_new == level + 1:
                            storey_group = storey_group_new
                            group_index += 1

            if bm is not None:
                bm.free()
        return result


def unique_objects_from_table(table):
    """Resolve the distinct MaStro objects referenced by an already-
    evaluated table (_Object column), without needing the node-graph lookup
    that nodes_attribute.unique_objects relies on - used here because Name
    and Objects are independent inputs, each already evaluated."""
    objs = []
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
