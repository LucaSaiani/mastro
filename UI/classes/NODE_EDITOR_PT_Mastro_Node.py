import bpy 
from bpy.types import Panel

class NODE_EDITOR_PT_Mastro_Node(Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = "UI"
    bl_category = "Node"
    bl_label = "MaStro Note"
  
    # @classmethod
    # def poll(cls, context):
    #     return context.space_data.tree_type == 'GeometryNodeTree'    
    
    def draw(self, context):
        # scene = context.scene
        layout = self.layout
        node_tree = bpy.context.space_data.edit_tree
        if node_tree:
            activeNode = node_tree.nodes.active
            is_custom_note = False
            if activeNode and hasattr(activeNode, "mastro_sticky_note_props"):
                is_custom_note = activeNode.mastro_sticky_note_props.customNote
            # activeNode = get_active_node(self)
            if activeNode and activeNode.select and is_custom_note:
                layout.operator("node.sticky_note", text="Edit the Sticky Note")
            else:
                layout.operator("node.sticky_note", text="Add a Sticky Note")