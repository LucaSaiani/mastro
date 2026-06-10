from bpy.props import FloatProperty

from ...Utils.getter_setter import (set_attribute_custom_vert,
                                     set_attribute_custom_edge,
                                     set_attribute_custom_face,
                                     get_attribute_mastro_mesh,
)

# =============================================================================
# Scene Properties - Extras (generic vertex/edge/face attributes)
# =============================================================================
scene_props_extras = [
    ("mastro_attribute_custom_vertex", FloatProperty(
        name="Custom vertex value",
        default=0,
        step=100,
        set = set_attribute_custom_vert,
        get = lambda self: get_attribute_mastro_mesh(self, "mastro_custom_vertex")
    )),
    ("mastro_attribute_custom_edge", FloatProperty(
        name="Custom edge value",
        default=0,
        step=100,
        set = set_attribute_custom_edge,
        get = lambda self: get_attribute_mastro_mesh(self, "mastro_custom_edge")
    )),
    ("mastro_attribute_custom_face", FloatProperty(
        name="Custom face value",
        default=0,
        step=100,
        set = set_attribute_custom_face,
        get = lambda self: get_attribute_mastro_mesh(self, "mastro_custom_face")
    )),
]
