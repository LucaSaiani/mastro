import bpy 

def init_nodes():
    # Maps each filter category to the node types that need a corresponding group:
    # "gn" = Geometry Nodes (filter + separate geometry), "shader" = Shader Nodes (filter by)
    names = {
        "block": ("shader",),
        "building": ("shader",),
        "typology": ("gn", "shader"),
        "use": ("gn", "shader"),
        "wall type": ("gn", "shader"),
        "block side": ("gn",),
        "street type": ("gn", "shader"),
    }
    
    for name in names:
        if "gn" in names[name]:
            bpy.ops.node.mastro_gn_separate_geometry_by(filter_name=name)
            bpy.ops.node.mastro_gn_filter_by(filter_name=name)
        if "shader" in names[name]:
            bpy.ops.node.mastro_shader_filter_by(filter_name=name)
   