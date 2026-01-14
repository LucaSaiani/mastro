import bpy 
from bpy.types import Operator 
import math

class NODE_OT_sort_multiple_input(Operator):
    bl_idname = "node.sort_multiple_input"
    bl_label = "Sort Join / Geometry to Instance"
    bl_description = "Sort Multiple Geometry Input"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        space = context.space_data
        tree = space.node_tree
        
        type_mapping = {
            'JOIN_GEOMETRY': 'GeometryNodeJoinGeometry',
            'GEOMETRY_TO_INSTANCE': 'GeometryNodeGeometryToInstance',
        }

        target_nodes = [n for n in tree.nodes if n.select and n.type in type_mapping]
        
        if not target_nodes:
            return {'CANCELLED'}

        for old_node in target_nodes:
            incoming = []
            cx, cy = old_node.location.x, old_node.location.y
            
            for socket in old_node.inputs:
                for link in socket.links:
                    src_node = link.from_node
                    src_socket = link.from_socket

                    # angle from center of join node
                    dx = src_node.location.x - cx
                    dy = src_node.location.y - cy
                    angle = math.atan2(dy, dx)  
                    if angle < 0:
                        angle += 2*math.pi

                    incoming.append((src_node, src_socket, angle))
                    
            if not incoming:
                return {'CANCELLED'}
            
            incoming_sorted = sorted(incoming, key=lambda x: x[2], reverse = True)
            
            # create a new join node
            new_node_type = type_mapping[old_node.type]
            new_node = tree.nodes.new(type=new_node_type)
            new_node.location = old_node.location
            
            # copy old node properties
            temp_name = old_node.name
            old_node.name = f"old_{temp_name}"
            new_node.name = temp_name
            new_node.label = old_node.label
            new_node.use_custom_color = old_node.use_custom_color
            if new_node.use_custom_color:
                new_node.color = old_node.color
            
            # link the inputs with the sorted order
            for src_node, src_socket, angle in incoming_sorted: 
                tree.links.new(src_socket, new_node.inputs[-1])
                
            # re-link the original outputs, if any
            for out_link in list(old_node.outputs[0].links):
                tree.links.new(new_node.outputs[0], out_link.to_socket)

            # remove the old node
            tree.nodes.remove(old_node)
                
        return {'FINISHED'}