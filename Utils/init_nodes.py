import bpy 


def init_nodes():
    # nt = bpy.data.node_groups.new("MasterUpdateTMP", "GeometryNodeTree")
    # separateByWallTypeNode = nt.nodes.new("separateByWallType")
    # mastro_GN_separate_by_wall_type.update_all(bpy.context.scene)
    # bpy.data.node_groups.remove(nt) 
    
    # bpy.ops.node.separate_geometry_by_factor()
    
    bpy.ops.node.mastro_gn_separate_by(filter_name="wall type")
    
    bpy.ops.node.mastro_gn_filter_by(filter_name="use")
    bpy.ops.node.mastro_gn_filter_by(filter_name="typology")
    bpy.ops.node.mastro_gn_filter_by(filter_name="wall type")
    bpy.ops.node.mastro_gn_filter_by(filter_name="street type")
    bpy.ops.node.mastro_gn_filter_by(filter_name="block side")
    
    bpy.ops.node.mastro_shader_filter_by(filter_name="block")
    bpy.ops.node.mastro_shader_filter_by(filter_name="building")
    bpy.ops.node.mastro_shader_filter_by(filter_name="use")
    bpy.ops.node.mastro_shader_filter_by(filter_name="typology")