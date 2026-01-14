import bpy
from bpy.types import Operator 

class NODE_OT_mastro_rename_reroute(Operator):
    '''Rename the selected reroute node using the name of the linked output socket'''
    bl_idname = "node.rename_reroute_from_source_socket"
    bl_label = "Rename Reroute from Source Socket"
    bl_options = {'REGISTER', 'UNDO'}
    
    def find_source_socket(self, socket):
        current_socket = socket

        while True:
            node = current_socket.node

            if node.type != 'REROUTE':
                return current_socket.name

            if node.label:
                return node.label

            in_socket = node.inputs[0]
            if not in_socket.is_linked:
                return current_socket.name

            current_socket = in_socket.links[0].from_socket


    def execute(self, context):
        space = context.space_data
        tree = space.node_tree
        
        for node in tree.nodes:
            if node.select and node.type == 'REROUTE':
                in_socket = node.inputs[0]

                if in_socket.is_linked:
                    source_name = self.find_source_socket(
                        in_socket.links[0].from_socket
                    )
                    
                    # link = in_socket.links[0]
                    # source_socket = link.from_socket

                    # socket_name = source_socket.name
                    node.label = source_name
                    node.name = f"Reroute_{source_name}"

        return {'FINISHED'}



