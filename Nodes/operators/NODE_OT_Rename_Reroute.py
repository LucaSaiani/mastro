import bpy
from bpy.types import Operator 

class NODE_OT_Mastro_Rename_Reroute(Operator):
    '''Rename the selected reroute node and any unlabelled reroutes upstream, based on the source socket'''
    bl_idname = "node.rename_reroute_from_source_socket"
    bl_label = "Rename Reroute from Source Socket"
    bl_options = {'REGISTER', 'UNDO'}
    
    def find_source_socket(self, socket):
        current_socket = socket
        visited_reroutes = []

        while True:
            node = current_socket.node

            # If not reroute, this is the origin
            if node.type != 'REROUTE':
                source_name = current_socket.name
                break

            # If reroute is already labelled, stop here and reuse its label
            if node.label:
                source_name = node.label
                break

            in_socket = node.inputs[0]
            if not in_socket.is_linked:
                source_name = current_socket.name
                break

            # keep walking upstream through unlabelled reroutes
            visited_reroutes.append(node)
            current_socket = in_socket.links[0].from_socket

        # backfill every unlabelled reroute crossed on the way to the source
        for reroute in visited_reroutes:
            reroute.label = source_name
            reroute.name = f"Reroute_{source_name}"

        return source_name

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



