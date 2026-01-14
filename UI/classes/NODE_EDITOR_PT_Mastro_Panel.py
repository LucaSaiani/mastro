import bpy 
from bpy.types import Panel

class NODE_EDITOR_PT_Mastro_Panel(Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = "UI"
    bl_category = "Node"
    bl_label = "MaStro"
    
    
    def draw(self, context):
        layout = self.layout
        node_tree = bpy.context.space_data.edit_tree
        if node_tree:
            activeNode = node_tree.nodes.active
        
            # Rename Reroute
            if activeNode.select and activeNode.type == "REROUTE":
                layout.operator("node.rename_reroute_from_source_socket", text="Rename Reroute")