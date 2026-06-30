"""Shared naming rules between Get Attribute Names and Evaluate Attribute,
translating mastro's raw mesh.attributes names (constrained by the lack of
array support: parallel-digit-string encoding for multi-component values,
and a domain suffix to avoid name clashes between Face/Edge variants of the
same logical attribute) into the clean logical names shown to the user.
"""

FIELD_DOMAINS = {
    'VERTEX': 'POINT',
    'EDGE': 'EDGE',
    'FACE': 'FACE',
}

# Domain suffix mastro appends to the raw attribute name to avoid a clash
# when the same logical attribute exists on more than one domain (see
# add_attributes_mass.py: block_attribute_set creates both `name` on FACE
# and `name_EDGE` on EDGE). Never shown to the user; stripped/added
# transparently. No clash has ever required a VERTEX-domain suffix.
DOMAIN_SUFFIX = {'EDGE': '_EDGE'}

# Logical name -> ordered list of raw attribute suffixes that together
# encode its value as parallel digit strings (see add_attributes_mass.py
# comment near `height_A += height[0]`). Evaluate reads each one of these
# and recombines them; Get Attribute Names shows only the logical name.
ATTRIBUTE_GROUPS = {
    "use": ("mastro_list_use_id_A", "mastro_list_use_id_B"),
    "storey": ("mastro_list_storey_A", "mastro_list_storey_B"),
    "height": (
        "mastro_list_height_A",
        "mastro_list_height_B",
        "mastro_list_height_C",
        "mastro_list_height_D",
        "mastro_list_height_E",
    ),
}
# raw name -> logical group name, for fast membership checks while scanning
# mesh.attributes
RAW_TO_GROUP = {raw: logical for logical, raws in ATTRIBUTE_GROUPS.items() for raw in raws}

# Logical names that exist (decodable via RAW_TO_GROUP/to_logical_name,
# same as any other ATTRIBUTE_GROUPS entry) but are never offered to the
# user by Get Attribute Names' own picker - internal-only encoding the
# user has no real use for as-is. "storey" specifically: the raw
# mastro_list_storey_A/B digit-pair encodes how the CURRENT typology's
# total floor count is split across its own uses (e.g. "2 floors of
# shops, then 4 of offices, then 4 residential" - see
# read_write_bmesh_storey_attribute.py's own read_bmesh_storey_attribute
# for the encoding/decoding logic), used internally to resolve "use" per
# level - not a number meaningful on its own once decoded raw, confirmed
# by the user: "questa cosa non serve, la nasconderei" (after both of us
# worked out what it actually was, an earlier reply in this same
# conversation wrongly conflated it with mastro_number_of_storeys before
# checking the code).
HIDDEN_NAMES = {"storey"}

# Names that aren't backed by a single stored mesh.attribute at all -
# "area" comes from BMFace.calc_area(), not a layer; "floor" is the
# CURRENT level index itself (0, 1, 2, ... - the same number each row
# already carries as the _Level id key), exposed here as a real DATA
# value usable in Math/Aggregate/etc. instead - the user's own ask:
# "non abbiamo modo di visualizzare / ottenere il numero dei livelli...
# voglio piano 0, 1, 2, 3...", clarified after an earlier attempt
# returned the face's total floor COUNT instead, which already exists
# as mastro_number_of_storeys and wasn't what was wanted. Named "floor",
# not "level"/"storey" - those already mean something else here:
# _Level is the per-row id key (shown as "Level_id", never a value);
# "storey" is the ATTRIBUTE_GROUPS logical name for the per-level
# storey-group digit (mastro_list_storey_A/B) - "floor" reads distinctly
# from both at a glance. Only meaningful for Field=FACE. Always
# available, regardless of what mesh.attributes the object happens to
# have.
COMPUTED_NAMES = {'FACE': ("area", "floor")}


def domain_raw_name(name, field):
    """Add the domain-disambiguation suffix to a raw attribute name, if
    this field uses one."""
    return name + DOMAIN_SUFFIX.get(field, "")


def to_logical_name(raw_name, field):
    """Strip the domain suffix and resolve a raw attribute name to the
    logical name shown to the user (grouping the _A/_B/.../_E siblings of
    the same multi-component attribute into one name)."""
    suffix = DOMAIN_SUFFIX.get(field, "")
    base = raw_name[: -len(suffix)] if suffix and raw_name.endswith(suffix) else raw_name
    return RAW_TO_GROUP.get(base, base)
