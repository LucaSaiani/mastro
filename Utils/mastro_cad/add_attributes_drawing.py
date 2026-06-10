drawing_attribute_set = [
    {
        "attr":    "mastro_drawing_layer",
        "attr_type":   "INT",
        "attr_domain": "EDGE",
        "attr_default": 0,
    },
    {"attr": "mastro_drawing_style_l1", "attr_type": "FLOAT", "attr_domain": "EDGE", "attr_default": 1.0},
    {"attr": "mastro_drawing_style_g1", "attr_type": "FLOAT", "attr_domain": "EDGE", "attr_default": 0.0},
    {"attr": "mastro_drawing_style_l2", "attr_type": "FLOAT", "attr_domain": "EDGE", "attr_default": 0.0},
    {"attr": "mastro_drawing_style_g2", "attr_type": "FLOAT", "attr_domain": "EDGE", "attr_default": 0.0},
    {"attr": "mastro_drawing_style_l3", "attr_type": "FLOAT", "attr_domain": "EDGE", "attr_default": 0.0},
    {"attr": "mastro_drawing_style_g3", "attr_type": "FLOAT", "attr_domain": "EDGE", "attr_default": 0.0},
    {
        "attr":    "mastro_drawing_thickness",
        "attr_type":   "FLOAT",
        "attr_domain": "EDGE",
        "attr_default": 0.2,
    },
    {
        "attr":    "mastro_drawing_black",
        "attr_type":   "BOOLEAN",
        "attr_domain": "EDGE",
        "attr_default": False,
    },
    {
        "attr":    "mastro_drawing_black_switch",
        "attr_type":   "BOOLEAN",
        "attr_domain": "EDGE",
        "attr_default": False,
    },
    {
        "attr":    "mastro_drawing_visibile",
        "attr_type":   "BOOLEAN",
        "attr_domain": "EDGE",
        "attr_default": True,
    },
    {
        "attr":    "mastro_drawing_resample",
        "attr_type":   "BOOLEAN",
        "attr_domain": "EDGE",
        "attr_default": False,
    },
]


def add_drawing_attributes(obj):
    mesh = obj.data
    for a in drawing_attribute_set:
        if a["attr"] in mesh.attributes:
            continue
        mesh.attributes.new(name=a["attr"], type=a["attr_type"], domain=a["attr_domain"])
        attr_data = mesh.attributes[a["attr"]].data
        default = a["attr_default"]
        for item in attr_data:
            if a["attr_type"] == "FLOAT_COLOR":
                item.color = default
            elif a["attr_type"] == "BOOLEAN":
                item.value = default
            else:
                item.value = default
