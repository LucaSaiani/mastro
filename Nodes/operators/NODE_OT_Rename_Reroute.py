import bpy
from bpy.types import Operator 

class NODE_OT_mastro_rename_reroute(Operator):
    '''Rename the selected reroute node based on its source socket'''
    bl_idname = "node.rename_reroute_from_source_socket"
    bl_label = "Rename Reroute from Source Socket"
    bl_options = {'REGISTER', 'UNDO'}
    
    def find_source_socket(self, socket):
        current_socket = socket

        while True:
            node = current_socket.node

            # If not reroute, this is the oring
            if node.type != 'REROUTE':
                return current_socket.name

            # If reroute is already labelled, this label is returned
            if node.label:
                return node.label

            in_socket = node.inputs[0]
            if not in_socket.is_linked:
                return current_socket.name

            # recursive research
            current_socket = in_socket.links[0].from_socket

    def execute(self, context):
        tree = context.active_node.id_data if context.active_node else context.space_data.edit_tree
        
        if not tree:
            return {'CANCELLED'}
        
        selected_reroutes = [n for n in tree.nodes if n.select and n.type == 'REROUTE']
        
        if not selected_reroutes:
            return {'FINISHED'}

        for node in selected_reroutes:
            in_socket = node.inputs[0]

            if in_socket.is_linked:
                source_name = self.find_source_socket(
                    in_socket.links[0].from_socket
                )
                
                node.label = source_name
                node.name = f"Reroute_{source_name}"

        return {'FINISHED'}



