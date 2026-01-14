import bpy 
from bpy.types import Panel

class NODE_EDITOR_PT_Mastro_Panel(Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = "UI"
    bl_category = "Node"
    bl_label = "MaStro"
    
    
    def draw(self, context):
        layout = self.layout
        node_tree = context.space_data.edit_tree
        if node_tree:
            activeNode = node_tree.nodes.active
        
            # Rename Reroute
            if not activeNode:
                return
            if not activeNode.select:
                return
            
            if activeNode.type == "REROUTE":
                layout.operator("node.rename_reroute_from_source_socket", text="Rename Reroute")
            
            valid_types = {'JOIN_GEOMETRY', 
                           'GEOMETRY_TO_INSTANCE',
                           }

            if activeNode.type in valid_types:
                layout.operator("node.sort_multiple_input", text="Sort Join")