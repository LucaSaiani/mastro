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


def _resolve_attribute_mesh(obj):
    """The mesh whose .attributes actually has the mastro_* layers for
    this object - mirrors mastro_export_utils.py:get_mass_data's own
    "mass" vs "block" distinction exactly, not just "has a Nodes
    modifier or not":

    - A MaStro "mass" must always read obj.data directly, regardless of
      whether it has any Geometry Nodes modifiers of its own. The user's
      explicit requirement: mass data has to come from the mass itself,
      independent of GN, the same way the CSV export and on-screen print
      already work - basing it on the GN-evaluated mesh would mean that
      adding GN-driven detail to a mass (a purely visual/detail layer)
      changes the numbers that feed the masterplan-level schedule, which
      makes no sense at that level.
    - A MaStro "block" always goes through evaluate_mastro_obj() (which
      evaluates only the *first* Nodes modifier - the one that turns the
      block into a mass-equivalent shape - temporarily disabling any
      later ones), same as the CSV export.
    - Anything else (a generic "Mesh" category object, Plan, Drawing,
      Street) falls back to "has a Nodes modifier or not": there's no
      mass/block-specific rule for these yet, so evaluating when a
      modifier is present is the closest match to what the object
      actually looks like.

    Returns (mesh, is_temporary) - is_temporary meshes must be removed
    with bpy.data.meshes.remove() by the caller once done."""
    if "MaStro mass" in obj.data:
        return obj.data, False
    from ...Utils.import_export.mastro_export_utils import evaluate_mastro_obj
    if "MaStro block" in obj.data:
        return evaluate_mastro_obj(obj), True
    if not any(mod.type == 'NODES' for mod in obj.modifiers):
        return obj.data, False
    return evaluate_mastro_obj(obj), True

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


# Outputs a Column: rows with only id keys (_Object, and one of _Face/
# _Edge/_Vertex/_Level depending on Field) plus exactly one data key -
# this node's own node.name, not the chosen attribute's name. node.name
# is the Column's stable, Blender-guaranteed-unique identity, used to
# join several Columns into a Table later without colliding even if two
# Columns happen to have the same user-facing label (e.g. both "area").
# `column_label` mirrors the chosen Name for now (read-only) - a
# dedicated Rename Header node (nodes_header.py) renames a Column
# independently of this, the same way a Math node transforms a Column's
# value without taking over its identity. Not called `label` -
# bpy.types.Node already has a native `label` attribute (the node's own
# custom display label, unrelated to this), and a same-named Python
# @property doesn't reliably override it.
#
# For Field=Face, every face of a MaStro mass/block stands for
# `mastro_number_of_storeys` stacked floors, so this always expands one
# row per face into one row per (face, level); multi-component groups
# (use/storey/height) are decoded per level the same way the legacy
# Input Mesh node does. For Object/Edge/Vertex there is no such
# expansion - one row per element.
class MaStroScheduleEvaluateAttributeNode(MaStroScheduleTreeNode, Node):
    """Read the chosen attribute's values for the objects in Data, as a Column"""
    bl_idname = 'MaStroScheduleEvaluateAttribute'
    bl_label = 'Evaluate Attribute'

    def init(self, context):
        self.inputs.new('MaStroScheduleDataSocketType', "Data")
        self.inputs.new('MaStroScheduleAttributeRefSocketType', "Attribute Name")
        self.outputs.new('MaStroScheduleColumnSocketType', "Column")

    @property
    def column_label(self):
        """User-facing name for this Column - for now just mirrors the
        chosen attribute Name, read straight from the upstream Get
        Attribute Names node (if linked) rather than cached on this
        node, so there's nothing here that can fall out of sync with the
        actual link."""
        # "Attribute Name" can be momentarily absent right after a
        # copy/paste - Blender restores this node's properties before
        # init() has necessarily finished rebuilding its sockets on the
        # pasted copy (confirmed live, same shape as nodes_math.py's
        # "A"/"B" case).
        if "Attribute Name" not in self.inputs:
            return ""
        from .tree import upstream_attr
        return upstream_attr(self.inputs["Attribute Name"], "name_value")

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
        key = self.name

        if field == 'OBJECT':
            return [self._evaluate_object(objs, name, key)]

        domain = FIELD_DOMAINS[field]
        if name == "area":
            raw_names = ()
        elif name in ATTRIBUTE_GROUPS:
            raw_names = ATTRIBUTE_GROUPS[name]
        else:
            raw_names = (domain_raw_name(name, field),)

        if field == 'FACE':
            return [self._evaluate_face_expanded(objs, name, raw_names, domain, key)]
        return [self._evaluate_simple(objs, name, raw_names, domain, key)]

    def _evaluate_object(self, objs, name, key):
        result = []
        for obj in objs:
            if name in OBJECT_MASTRO_PROPS_SOURCE:
                value = getattr(obj.mastro_props, OBJECT_MASTRO_PROPS_SOURCE[name], "")
            else:
                value = obj.get(name, "")
            result.append({"_Object": obj.name, key: value})
        return result

    def _evaluate_simple(self, objs, name, raw_names, domain, key):
        """One row per element (Edge/Vertex), no per-level expansion."""
        index_key = {'POINT': "_Vertex", 'EDGE': "_Edge", 'FACE': "_Face"}[domain]
        result = []
        for obj in objs:
            mesh, is_temp_mesh = _resolve_attribute_mesh(obj)
            attrs = [mesh.attributes.get(raw) for raw in raw_names]
            missing = any(a is None or a.domain != domain for a in attrs)
            if missing:
                count = {
                    'POINT': len(mesh.vertices),
                    'EDGE': len(mesh.edges),
                    'FACE': len(mesh.polygons),
                }[domain]
            else:
                count = len(attrs[0].data)
            for i in range(count):
                if missing:
                    # The attribute doesn't exist on this object's mesh
                    # at all (e.g. one mass/block was created before
                    # this attribute existed, or with a different set of
                    # edge attributes than another) - every element this
                    # object actually has still gets its own row, with
                    # this column as None, instead of dropping the
                    # object (losing its other columns/rows entirely) or
                    # collapsing it to one row (which would misrepresent
                    # a multi-edge object as having just one edge).
                    value = None
                else:
                    values = [_read_attribute_value(a, i) for a in attrs]
                    value = values[0] if len(values) == 1 else tuple(values)
                result.append({"_Object": obj.name, index_key: i, key: value})
            if is_temp_mesh:
                bpy.data.meshes.remove(mesh)
        return result

    def _evaluate_face_plain_area(self, obj, mesh, is_temp_mesh, key):
        """One row per face, real geometric BMFace.calc_area() - used for
        "area" on objects with no mastro_number_of_storeys (e.g. a plain
        Cube, or any non-mass/block "Mesh" category object). "area" on a
        mass/block instead goes through _evaluate_face_expanded's
        multi-storey unwrap - that's mastro's own made-up per-floor area
        (one row per (face, level), all sharing the face's full
        geometric area), a different, mass/block-specific concept from
        "the real area of this face", which is what a generic mesh with
        no storey concept actually has."""
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bm.faces.ensure_lookup_table()
        result = [
            {"_Object": obj.name, "_Face": face.index, key: face.calc_area()}
            for face in bm.faces
        ]
        bm.free()
        if is_temp_mesh:
            bpy.data.meshes.remove(mesh)
        return result

    def _evaluate_face_expanded(self, objs, name, raw_names, domain, key):
        """One row per (face, level): every face of a mass/block stands for
        mastro_number_of_storeys stacked floors. Mirrors execution.py's
        extract_mesh_rows decoding loop, generalized to any attribute name."""
        result = []
        is_area = name == "area"
        for obj in objs:
            mesh, is_temp_mesh = _resolve_attribute_mesh(obj)
            attrs = mesh.attributes
            if "mastro_number_of_storeys" not in attrs:
                if is_area:
                    result.extend(self._evaluate_face_plain_area(obj, mesh, is_temp_mesh, key))
                elif is_temp_mesh:
                    bpy.data.meshes.remove(mesh)
                continue
            storeys_attr = attrs["mastro_number_of_storeys"]

            value_attrs = [attrs.get(raw) for raw in raw_names]
            # The attribute doesn't exist on this object's mesh at all
            # (e.g. one mass/block was created before this attribute
            # existed, or with a different set of attributes than
            # another) - mastro_number_of_storeys (checked above) still
            # tells us exactly how many (face, level) rows this object
            # should have, so every one of them gets its own row with
            # this column as None, instead of dropping the object
            # (losing its other rows entirely) or collapsing it to one
            # placeholder row (misrepresenting how many faces/levels it
            # actually has).
            missing = any(a is None or a.domain != domain for a in value_attrs)

            bm = None
            # mastro_undercroft is read independently of raw_names (which
            # for "area" holds nothing - area is a BMFace.calc_area() call,
            # not a stored attribute) - the user's own explicit call:
            # "mastro area" should already mean "area minus the undercroft
            # floors", not the raw full geometric area every level
            # (undercroft or not) used to get. Read once per face below,
            # regardless of `name`, since every attribute - not just area -
            # benefits from knowing which of its levels are undercroft (a
            # future name could need the same zeroing this gives "area").
            undercroft_attr = attrs.get("mastro_undercroft")
            if is_area and not missing:
                # area is computed from the face's geometry
                # (BMFace.calc_area()), not a stored mesh attribute - the
                # FULL geometric area is still what's computed per face
                # (area_undercroft_count, read below, decides per LEVEL
                # whether to zero it out, not the geometry itself).
                bm = bmesh.new()
                bm.from_mesh(mesh)
                bm.faces.ensure_lookup_table()

            # storey_A/_B are always needed to know when a face's storey
            # group advances by one level, same as extract_mesh_rows
            storey_a = attrs.get("mastro_list_storey_A")
            storey_b = attrs.get("mastro_list_storey_B")

            is_digit_group = name in ATTRIBUTE_GROUPS

            for face_index in range(len(storeys_attr.data)):
                storeys = storeys_attr.data[face_index].value

                if not missing:
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
                # Read independently of the name=="undercroft" branch
                # above (which only fires when undercroft IS the
                # requested attribute) - "area" needs this value too, to
                # zero out undercroft levels, without the caller having
                # to separately request "undercroft" itself.
                area_undercroft_count = undercroft_attr.data[face_index].value if undercroft_attr else 0
                if storey_a is not None:
                    storey_a_digits = _digits(storey_a.data[face_index].value)
                    storey_b_digits = _digits(storey_b.data[face_index].value) if storey_b else None

                # Decoding (group_index/storey_group below) must still
                # walk level 0 (ground floor) upward - the digit strings
                # (storey_a_digits/etc.) are encoded in that order, and
                # group_index only knows how to advance forward. The
                # rows THIS FACE contributes are collected here, then
                # appended to `result` reversed (top floor first, ground
                # floor last) - the user's own explicit call: a Table/
                # Viewer reads top-to-bottom, and a real elevation has
                # the ground floor at the bottom, the top floor at the
                # top, with any basement level (a negative _Level, not
                # produced yet but anticipated) ending up visually
                # lowest of all once this convention is in place.
                face_rows = []
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
                    if missing:
                        value = None
                    elif is_area:
                        # "mastro area" deliberately excludes undercroft
                        # floors by default - the user's own explicit
                        # call: undercroft levels never contribute to an
                        # area total unless the caller goes out of their
                        # way to ask for the raw geometric area instead
                        # (no such opt-in exists yet - add one if a real
                        # case for the full area ever comes up).
                        value = 0.0 if level < area_undercroft_count else plain_value
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

                    face_rows.append({
                        "_Object": obj.name,
                        "_Face": face_index,
                        "_Level": level,
                        key: value,
                    })

                    if storey_a is not None:
                        s_a = int(storey_a_digits[group_index])
                        s_b = int(storey_b_digits[group_index]) if storey_b_digits else 0
                        storey_group_new = s_a * 10 + s_b + storey_group
                        if storey_group_new == level + 1:
                            storey_group = storey_group_new
                            group_index += 1

                result.extend(reversed(face_rows))

            if bm is not None:
                bm.free()
            if is_temp_mesh:
                bpy.data.meshes.remove(mesh)
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
