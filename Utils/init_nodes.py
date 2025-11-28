import bpy 

def init_nodes():
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
   