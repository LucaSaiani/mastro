import bpy
from bpy.types import Operator
from types import SimpleNamespace

class mastro_GN_filter_by_OT(Operator):
    """Update the Geometry Nodes 'Filter By' node group outputs"""
    bl_idname = "node.mastro_gn_filter_by"
    bl_label = "Update the GN filter by group"

    filter_name: bpy.props.StringProperty(name="Filter type name")
            
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
        group.default_group_node_width = 200
        
        group_input = group.nodes.new("NodeGroupInput")
        group_output = group.nodes.new('NodeGroupOutput')
        
        # group_menu = group.nodes.new("GeometryNodeMenuSwitch")
        # group_evaluate_point = group.nodes.new("GeometryNodeFieldOnDomain")
        # group_evaluate_edge = group.nodes.new("GeometryNodeFieldOnDomain")
        # group_evaluate_face = group.nodes.new("GeometryNodeFieldOnDomain")
        # group_evaluate_spline = group.nodes.new("GeometryNodeFieldOnDomain")
        # group_evaluate_instance = group.nodes.new("GeometryNodeFieldOnDomain")


        
        # Add named attribute
        named_attribute_node = group.nodes.new(type="GeometryNodeInputNamedAttribute")
        named_attribute_node.data_type = 'INT'
        named_attribute_node.inputs[0].default_value = attributeName
            
        group_input.location = (-600,0)
        # group_menu.location = (-300,0)
        group_output.location = (600, 0)
        named_attribute_node.location = (0,-100)
        return(group)
        
        
    def execute(self, context):
        name = "MaStro Filter by " + self.filter_name.title()
                    
        if name not in bpy.data.node_groups:
            filterBy_Group = self.newGroup(name, "GN")
        else:
            filterBy_Group = bpy.data.node_groups[name]
                
        nodes = filterBy_Group.nodes
        
        # group_input = nodes["Group Input"]
        group_output = nodes["Group Output"]
        named_attribute_node = nodes["Named Attribute"]
                    
        filterNodeIds = []
        filterNodeDescriptions = []
        for node in nodes:
            if node.type == "COMPARE":
                tmpId = node.inputs[3].default_value
                filterNodeIds.append(tmpId)
                filterNodeDescriptions.append(filterBy_Group.interface.items_tree[tmpId].description)
            
        if len(filterNodeIds) == 0:
            lastId = -1           
        else:
            lastId = max(filterNodeIds)
            
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
                    if lastId >= 0:
                        node_y_location = nodes["Compare " + str(lastId)].location[1] -25
                    else:
                        node_y_location = 0
                    
                    compare_node = filterBy_Group.nodes.new(type="FunctionNodeCompare")
                    compare_node.data_type = 'INT'
                    compare_node.operation = 'EQUAL'
                    compare_node.inputs[3].default_value = el.id
                        
                    compare_node.location = (300, node_y_location-35)
                    compare_node.hide = True
                    compare_node.label="="+str(el.id)
                    compare_node.name="Compare "+str(el.id)
                    lastId = el.id
                    
                    #Add the Output Sockets and change their Default Value
                    if el.name == "":
                        if self.filter_name == "use": elName = "Use name..."
                        elif self.filter_name == "typology": elName = "Typology name..."
                        elif self.filter_name == "wall type": elName = "Wall name..."
                        elif self.filter_name == "steet type": elName = "Street name..."
                    else:
                        elName = el.name
                    descr = "id: " + str(el.id) + " - " + elName
                    filterBy_Group.interface.new_socket(name=elName,description=descr,in_out ="OUTPUT", socket_type="NodeSocketBool")
            
                    #Add Links
                    index = len(group_output.inputs) -2
                    filterBy_Group.links.new(named_attribute_node.outputs[0], compare_node.inputs[2])
                    filterBy_Group.links.new(compare_node.outputs[0], group_output.inputs[index])

                # a name has been renamed
                elif ("id: " + str(el.id) + " - " + str(el.name)) not in filterNodeDescriptions:
                    for i, desc in enumerate(filterNodeDescriptions):
                        if i == int(el.id):
                            filterBy_Group.interface.items_tree[i].name = str(el.name)
                            filterBy_Group.interface.items_tree[i].description = "id: " + str(el.id) + " - " + str(el.name)

        return {'FINISHED'}
