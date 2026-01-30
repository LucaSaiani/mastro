import bpy 
from bpy.types import Operator 
import math

class NODE_OT_sort_multiple_input(Operator):
    bl_idname = "node.sort_multiple_input"
    bl_label = "Sort Join / Geometry to Instance"
    bl_description = "Sort Multiple Geometry Inputs by Position"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        tree = context.space_data.edit_tree
        
        if not tree:
            return {'CANCELLED'}
        
        type_mapping = {
            'JOIN_GEOMETRY': 'GeometryNodeJoinGeometry',
            'GEOMETRY_TO_INSTANCE': 'GeometryNodeGeometryToInstance',
        }

        # Filter selected nodes that match the mapping
        target_nodes = [n for n in tree.nodes if n.select and n.type in type_mapping]
        
        if not target_nodes:
            return {'CANCELLED'}

        for old_node in target_nodes:
            incoming = []
            cx, cy = old_node.location.x, old_node.location.y
            
            # Store all incoming links with their spatial angle
            for socket in old_node.inputs:
                for link in socket.links:
                    src_node = link.from_node
                    src_socket = link.from_socket

                    # Calculate angle relative to the target node center
                    dx = src_node.location.x - cx
                    dy = src_node.location.y - cy
                    angle = math.atan2(dy, dx)  
                    if angle < 0:
                        angle += 2 * math.pi

                    incoming.append((src_node, src_socket, angle))
                    
            if not incoming:
                continue # Skip if node has no inputs
            
            # Sort inputs (usually top-to-bottom or circular)
            incoming_sorted = sorted(incoming, key=lambda x: x[2], reverse=True)
            
            # Create a replacement node in the same tree
            new_node_type = type_mapping[old_node.type]
            new_node = tree.nodes.new(type=new_node_type)
            new_node.location = old_node.location
            
            # Transfer basic visual properties
            new_node.label = old_node.label
            new_node.use_custom_color = old_node.use_custom_color
            if new_node.use_custom_color:
                new_node.color = old_node.color
            
            # Re-link inputs in the new sorted order
            # [-1] targets the dynamic multi-input socket
            for src_node, src_socket, angle in incoming_sorted: 
                tree.links.new(src_socket, new_node.inputs[-1])
                
            # Re-link original outputs to the new node
            if old_node.outputs and old_node.outputs[0].links:
                for out_link in list(old_node.outputs[0].links):
                    tree.links.new(new_node.outputs[0], out_link.to_socket)

            # Clean up: remove the old unsorted node
            tree.nodes.remove(old_node)
                
        self.report({'INFO'}, "Node inputs sorted.")
        return {'FINISHED'}