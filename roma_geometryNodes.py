import bpy 

from bpy.types import Panel, Operator
from bpy.props import StringProperty

def get_active_node(self):
    space_data = bpy.context.space_data

    if space_data and space_data.tree_type == 'GeometryNodeTree':
        node_tree = space_data.node_tree
        if node_tree:
            if space_data.node_tree.nodes.active:
                return space_data.node_tree.nodes.active
    return None

def updateGroup(self, context):
    bpy.ops.node.separate_geometry_by_factor()

class VIEW_PT_RoMa_GN_Panel(Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = "UI"
    bl_category = "Node"
    bl_label = "RoMa"
    
    
  
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'GeometryNodeTree'
    
    def draw(self, context):
        scene = context.scene
        layout = self.layout
        
        activeNode = get_active_node(self)
        if activeNode and hasattr(activeNode, "node_tree"):
            if activeNode.node_tree.bl_description == "RoMa Geometry By Factor":
                layout.label(text="Subdivision:")
                row = layout.row()
                row.label(text="Subdivide by:")
                row.prop(scene, "geometryMenuSwitch", text="")
                row = layout.row()
                row.label(text="Number of subdivision:")
                row.prop(context.scene, "roma_group_node_number_of_split", text="")
                
       

class separate_geometry_by_factor_OT(Operator):
    '''Separate geometry in geometry node by factor'''
    bl_idname = "node.separate_geometry_by_factor"
    bl_label = "Separate geometry by factor"

    def newGroup (self, groupName):
        group = bpy.data.node_groups.new(groupName,'GeometryNodeTree')
        group.bl_description = "RoMa Geometry By Factor"
        
        group.interface.new_socket(name='Geometry', description='', in_out = 'INPUT', socket_type='NodeSocketGeometry')
        
        group.interface.new_socket(name='Subdivisions', description='The number of subdivisions. This is used only to store data. To plug the socket does nothing. If you want to change the number of subdivisions use the panel Node->RoMa', in_out = 'INPUT', socket_type='NodeSocketInt')
        group.interface.items_tree[1].default_value = bpy.context.scene.roma_group_node_number_of_split
        group.interface.items_tree[1].min_value = 2
        group.interface.items_tree[1].force_non_field = True
        group.interface.items_tree[1].hide_value = True
       
        # group.interface.new_socket(name='ID', description='ID for the random value', in_out = 'INPUT', socket_type='NodeSocketInt')
        # group.interface.items_tree[2].hide_value = True
        
        group.interface.new_socket(name='Seed', description='Seed for the random value', in_out = 'INPUT', socket_type='NodeSocketInt')
        # group.interface.items_tree[2].hide_value = True
        
        group.interface.new_socket(name='Split 0', description='The number of subdivisions', in_out = 'INPUT', socket_type='NodeSocketInt')
        group.interface.items_tree[3].default_value = 0
        group.interface.items_tree[3].min_value = 0
        group.interface.items_tree[3].max_value = 100
        group.interface.items_tree[3].force_non_field = True
        group.interface.items_tree[3].subtype = 'PERCENTAGE'
        
        group.interface.new_socket(name='Geometry less than Split 0', description='', in_out = 'OUTPUT', socket_type='NodeSocketGeometry')
        group.interface.new_socket(name='Geometry more than Split 0', description='', in_out = 'OUTPUT', socket_type='NodeSocketGeometry')
       
        group_input = group.nodes.new('NodeGroupInput')
        group_input.location = (-100, -300)
       
        group_output = group.nodes.new('NodeGroupOutput')
        group_output.location = (600, 0)
        
        split_edges = group.nodes.new(type='GeometryNodeSplitEdges')
        split_edges.location = (150, 0)

        random_value = group.nodes.new(type='FunctionNodeRandomValue')
        random_value.data_type = 'INT'
        random_value.inputs[4].default_value = 0
        random_value.inputs[5].default_value = 100
        random_value.location = (150, -300)
        
        less_than_node = group.nodes.new(type='FunctionNodeCompare')
        less_than_node.name = "Compare 0"
        less_than_node.operation = 'LESS_EQUAL'
        less_than_node.location = (400, 0)

        separate_geometry_node = group.nodes.new(type='GeometryNodeSeparateGeometry')
        separate_geometry_node.name = "Separate 0"
        separate_geometry_node.domain = 'EDGE'
        separate_geometry_node.location = (400, 200)
        
        group.links.new(group_input.outputs['Geometry'], split_edges.inputs['Mesh'])
        # group.links.new(group_input.outputs['ID'], random_value.inputs['ID'])
        group.links.new(group_input.outputs['Seed'], random_value.inputs[8])
        group.links.new(group_input.outputs['Split 0'], less_than_node.inputs[1])
        
        group.links.new(split_edges.outputs['Mesh'], separate_geometry_node.inputs['Geometry'])
        
        group.links.new(random_value.outputs['Value'], less_than_node.inputs[0])
        
        group.links.new(less_than_node.outputs[0], separate_geometry_node.inputs[1])
        
        group.links.new(separate_geometry_node.outputs[0], group_output.inputs[0])
        group.links.new(separate_geometry_node.outputs[1], group_output.inputs[1])
      

        return(group)
    
    def execute(self, context):
        name = "RoMa Separate Geometry by Factor"
        if name not in bpy.data.node_groups:
            group = self.newGroup(name)
            
        else:
            subdivision = bpy.context.scene.roma_group_node_number_of_split
        
            activeNode = get_active_node(self)
            try:
                activeNode.node_tree
                if activeNode.node_tree.bl_description == "RoMa Geometry By Factor":
                    group = activeNode.node_tree
                    previousSubdivision =  activeNode.inputs[1].default_value
                    groupNodes = group.nodes
                    group_input = groupNodes['Group Input']
                    group_output = groupNodes['Group Output']
                    random_node = groupNodes['Random Value']
                   
                    if previousSubdivision < subdivision:
                        i = previousSubdivision
                        
                        itemIndex = 0
                        # splitIndex = 0
                        for item in group.interface.items_tree:
                            if item.name == f"Split {itemIndex}":
                                itemIndex += 1
                        
                        # itemIndex = len(group.interface.items_tree) -4
                        nameIndex = itemIndex
                        while i < subdivision:
                            group.interface.new_socket(name=f'Split {nameIndex}', description='The number of subdivisions', in_out = 'INPUT', socket_type='NodeSocketInt')
                            lastItem = len(group.interface.items_tree) -1
                            group.interface.items_tree[lastItem].default_value = 0
                            group.interface.items_tree[lastItem].min_value = 0
                            group.interface.items_tree[lastItem].max_value = 100
                            group.interface.items_tree[lastItem].force_non_field = True
                            group.interface.items_tree[lastItem].subtype = 'PERCENTAGE'


                            less_than_node = group.nodes.new(type='FunctionNodeCompare')
                            less_than_node.name = f"Compare {nameIndex}"
                            less_than_node.operation = 'LESS_EQUAL'
                            less_than_node.location = (400 + 150 * nameIndex, 0)
                            
                            separate_geometry_node = group.nodes.new(type='GeometryNodeSeparateGeometry')
                            separate_geometry_node.name = f"Separate {nameIndex}"
                            separate_geometry_node.domain = 'EDGE'
                            separate_geometry_node.location = (400 + 150 * nameIndex, 200)
                            
                            socketName = f'Geometry less than Split {nameIndex+1}'
                            if i == subdivision -1:
                                socketName = f'Geometry more than Split {nameIndex+1}'
                            group.interface.new_socket(name=socketName, description='', in_out = 'OUTPUT', socket_type='NodeSocketGeometry')
                            
                            group_output.location = (600 + 150 * nameIndex, 500)

                            # links from group input to less than node
                            group.links.new(random_node.outputs['Value'], less_than_node.inputs[0])
                            group.links.new(group_input.outputs[f'Split {nameIndex}'], less_than_node.inputs[1])
                            
                            # links to separate geometry
                            group.links.new(less_than_node.outputs[0], separate_geometry_node.inputs[1])
                            previousSeparareNode = group.nodes[f"Separate {nameIndex -1}"]
                            group.links.new(previousSeparareNode.outputs[1], separate_geometry_node.inputs['Geometry'])
                            
                            # links to group output
                            group.links.new(separate_geometry_node.outputs[0], group_output.inputs[nameIndex])
                            # group_output.inputs[nameIndex].name = f"Geometry lessss than Split {nameIndex}"
                            
                            
                            i += 1
                            itemIndex += 2
                            nameIndex += 1
                        # link the inverted output from the last separate geometry node
                        group.links.new(separate_geometry_node.outputs[1], group_output.inputs[nameIndex])
                            
                            
                    elif previousSubdivision > subdivision:
                        i = previousSubdivision
                        while i >= subdivision:
                            itemsToRemove = []
                            # nodesToRemove = []
                            for item in group.interface.items_tree:
                                if item.name in [f"Split {i}", f"Geometry less than Split {i}"]:
                                    itemsToRemove.append(item)
                            for node in groupNodes:
                                if node.name in [f"Separate {i}", f"Compare {i}"]:
                                    groupNodes.remove(node)
                            for item in itemsToRemove:
                                group.interface.remove(item)
                            i -= 1
                        # create a link for the last inverted socket
                        for node in groupNodes:
                            if node.name == f'Separate {i}':
                                group.links.new(node.outputs[1], group_output.inputs[i+1])
                                break
                            
                            
                    # rename the output sockets
                    i = 0
                    for item in group.interface.items_tree:
                        if "than" in item.name:
                            item.name = f"Geometry less than Split {i}"
                            lastItem = item
                            i += 1
                    lastItem.name = f"Geometry more than Split {i-2}"
                    
                    #set what field to separate (point, edge, face)
                    groupNodes = group.nodes
                    selection = bpy.context.scene.geometryMenuSwitch
                    for node in groupNodes:
                        if "Separate" in node.name:
                            node.domain = selection
                    if selection == "FACE":
                        groupNodes['Split Edges'].mute = True
                    else:
                        groupNodes['Split Edges'].mute = False
              
                    activeNode.inputs[1].default_value = subdivision
                        
                    
            except AttributeError:
                pass
           

        return {'FINISHED'}