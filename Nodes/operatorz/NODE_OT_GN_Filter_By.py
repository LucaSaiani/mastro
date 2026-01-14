import bpy
from bpy.types import Operator
from types import SimpleNamespace

import re

class NODE_OT_mastro_filter_by(Operator):
    """Update the Geometry Nodes 'Filter By' node group outputs"""
    bl_idname = "node.mastro_gn_filter_by"
    bl_label = "Update the GN filter by group"

    filter_name: bpy.props.StringProperty(name="Filter type name")
    output_id: bpy.props.IntProperty(name="Neighbor")
    output_direction: bpy.props.StringProperty(name="Direction", default = "None")
            
    def newGroup (self, groupName, type):
        # if self.filter_name == "block": attributeName = "mastro_block_id"
        # elif self.filter_name == "building": attributeName = "mastro_building_id"
        if self.filter_name == "use": attributeName = "mastro_use"
        elif self.filter_name == "typology": attributeName = "mastro_typology_id"
        elif self.filter_name == "wall type": attributeName = "mastro_wall_id"
        elif self.filter_name == "street type": attributeName = "mastro_street_id"
        elif self.filter_name == "block side": attributeName = "mastro_block_side"

        # GN group
        group = bpy.data.node_groups.new(groupName,'GeometryNodeTree')
        
        group_input = group.nodes.new("NodeGroupInput")
        group_output = group.nodes.new('NodeGroupOutput')
        
        # Add named attribute
        named_attribute_node = group.nodes.new(type="GeometryNodeInputNamedAttribute")
        named_attribute_node.data_type = 'INT'
        named_attribute_node.inputs[0].default_value = attributeName
            
        return(group)
        
        
    def execute(self, context):
        name = "MaStro Filter by " + self.filter_name.title()
        pattern = r"id: (.*?) -"

        if name not in bpy.data.node_groups:
            filterBy_Group = self.newGroup(name, "GN")
        else:
            filterBy_Group = bpy.data.node_groups[name]
                
        nodes = filterBy_Group.nodes
        
        # group_input = nodes["Group Input"]
        group_output = nodes["Group Output"]
        named_attribute_node = nodes["Named Attribute"]
                    
        filterNodeIds = []
        # filterNodeDescriptions = []
        for node in nodes:
            if node.type == "COMPARE":
                tmpId = node.inputs[3].default_value
                filterNodeIds.append(tmpId)
                # filterNodeDescriptions.append(filterBy_Group.interface.items_tree[tmpId].description)
            
        # if len(filterNodeIds) == 0:
        #     lastId = -1           
        # else:
        #     lastId = max(filterNodeIds)
            
        if self.filter_name == "use": listToLoop = bpy.context.scene.mastro_use_name_list
        elif self.filter_name == "typology": listToLoop = bpy.context.scene.mastro_typology_name_list
        elif self.filter_name == "wall type": listToLoop = bpy.context.scene.mastro_wall_name_list
        elif self.filter_name == "street type": listToLoop = bpy.context.scene.mastro_street_name_list
        elif self.filter_name == "block side": listToLoop = [
                                                            SimpleNamespace(id=0, name="External Side"),
                                                            SimpleNamespace(id=1, name="Internal Side"),
                                                            SimpleNamespace(id=2, name="Lateral Side")
                                                        ]
        
        for el in listToLoop:
            if hasattr(el, "id"):
                #a new name has been added
                if el.id not in filterNodeIds:
                    
                    compare_node = filterBy_Group.nodes.new(type="FunctionNodeCompare")
                    compare_node.data_type = 'INT'
                    compare_node.operation = 'EQUAL'
                    compare_node.inputs[3].default_value = el.id
                        
                    compare_node.hide = True
                    compare_node.label="="+str(el.id)
                    compare_node.name="Compare "+str(el.id)
                    # lastId = el.id
                    
                    #Add the Output Sockets and change their Default Value
                    if el.name == "":
                        if self.filter_name == "use": elName = "Use name"
                        elif self.filter_name == "typology": elName = "Typology name"
                        elif self.filter_name == "wall type": elName = "Wall name"
                        elif self.filter_name == "steet type": elName = "Street name"
                    else:
                        elName = el.name
                    descr = "id: " + str(el.id) + " - " + elName
                    # filterBy_Group.interface.new_socket(name=elName,description=descr,in_out ="OUTPUT", socket_type="NodeSocketBool")
                    socket = filterBy_Group.interface.new_socket(name=elName,
                                                                 description=descr,
                                                                 in_out ="OUTPUT", 
                                                                 socket_type="NodeSocketBool"
                    )
            
            
                    #Add Links
                    # index = len(group_output.inputs) -2
                    filterBy_Group.links.new(named_attribute_node.outputs[0], 
                                             compare_node.inputs[2])
                    filterBy_Group.links.new(compare_node.outputs[0], 
                                             group_output.inputs[socket.name])

                # a name has been renamed
                # elif ("id: " + str(el.id) + " - " + str(el.name)) not in filterNodeDescriptions:
                #     for i, desc in enumerate(filterNodeDescriptions):
                #         if i == int(el.id):
                #             filterBy_Group.interface.items_tree[i].name = str(el.name)
                #             filterBy_Group.interface.items_tree[i].description = "id: " + str(el.id) + " - " + str(el.name)
                expected_descr = f"id: {el.id} - {el.name}"
                for socket in filterBy_Group.interface.items_tree:
                    match = re.search(pattern, socket.description)
                    if match and int(match.group(1)) == el.id:
                        if socket.description != expected_descr:
                            socket.name = el.name
                            socket.description = expected_descr
                        break
        
        # the name has been moven up and down in the list
        if self.output_direction != "None":
            

            interface = filterBy_Group.interface
            sockets = interface.items_tree
                           
            for socket in sockets:
                socket_description = socket.description
                regex = re.search(pattern,socket_description)
                if regex:
                    socket_id = int(regex.groups()[0])
                    if socket_id == self.output_id:
                        if self.output_direction == "UP":
                            new_position = socket.position -1
                        else:
                            new_position = socket.position +2
                        interface.move(socket, to_position=new_position)
                        return {'FINISHED'}
                    

        return {'FINISHED'}
