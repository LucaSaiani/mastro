import bpy
import math

plan_attribute_set = [
            {
            "attr" :  "mastro_wall_id",
            "attr_type" :  "INT",
            "attr_domain" :  "EDGE",
            "attr_default" : 0
            },
            {
            "attr" :  "mastro_floor_id",
            "attr_type" :  "INT",
            "attr_domain" :  "FACE",
            "attr_default" : 0
            },
            {
            "attr" :  "mastro_inverted_normal",
            "attr_type" :  "BOOLEAN",
            "attr_domain" :  "EDGE",
            "attr_default" : 0
            },
            {
            "attr" : "mastro_custom_vertex",
            "attr_type" :  "FLOAT",
            "attr_domain" :  "POINT",
            "attr_default" : 0
            },
            {
            "attr" : "mastro_custom_edge",
            "attr_type" :  "FLOAT",
            "attr_domain" :  "EDGE",
            "attr_default" : 0
            },
            {
            "attr" : "mastro_custom_face",
            "attr_type" :  "FLOAT",
            "attr_domain" :  "FACE",
            "attr_default" : 0
            }
]


def add_plan_attributes(obj):
    """Initialise all MaStro mesh attributes on `obj` for a plan.

    Creates every attribute in plan_attribute_set, sets the mesh-level and
    object-level MaStro markers, and resets the per-object FFL / floor to
    floor height / bottom level id / lock state fields. These live on
    obj.mastro_props rather than the mesh so that objects sharing the same
    linked mesh data (e.g. duplicated repeated floors) can still each sit
    at a different level with a different height."""

    obj.mastro_props['mastro_ffl'] = 0
    obj.mastro_props['mastro_floor_to_floor_height'] = 0
    obj.mastro_props['mastro_bottom_level_id'] = 0
    # Locked by default: the caller (OBJECT_OT_Add_Mastro_Plan) wires up the
    # FFL/height drivers right after calling this, matching this default.
    obj.mastro_props['mastro_lock_to_level'] = True

    mesh = obj.data
    mesh["MaStro object"] = True
    mesh["MaStro plan"] = True

    for a in plan_attribute_set:
        if a["attr"] not in mesh.attributes:
            mesh.attributes.new(name=a["attr"], type=a["attr_type"], domain=a["attr_domain"])
