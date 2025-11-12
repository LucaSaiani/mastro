import bpy 
from bpy.types import Operator 

class mastro_Shader_filter_by_OT(Operator):
    """Update the shader node Filter by... based on the passed type value"""
    bl_idname = "node.mastro_shader_filter_by"
    bl_label = "Update the Shader filter by..."
    
    filter_name: bpy.props.StringProperty(name="Filter type name")
        
    #     return node_obj, node_x_location
    def newGroup (self, groupName, type):
        if self.filter_name == "block": attributeName = "mastro_block_id"
        elif self.filter_name == "building": attributeName = "mastro_building_id"
        elif self.filter_name == "use": attributeName = "mastro_use"
        elif self.filter_name == "typology": attributeName = "mastro_typology_id"
        
         # geometry nodes group
        # if type == "GN":
        #     group = bpy.data.node_groups.new(groupName,'GeometryNodeTree')
        #     #Add Group Output
        #     group_output = group.nodes.new('NodeGroupOutput')
        #     # Add named attribute
        #     named_attribute_node = group.nodes.new(type="GeometryNodeInputNamedAttribute")
        #     named_attribute_node.data_type = 'INT'
        #     named_attribute_node.inputs[0].default_value = attributeName
        
        # shader group
        group = bpy.data.node_groups.new(groupName,'ShaderNodeTree')
        #Add Group Output
        group_output = group.nodes.new('NodeGroupOutput')
        # Add named attribute
        named_attribute_node = group.nodes.new(type="ShaderNodeAttribute")
        named_attribute_node.attribute_type = 'GEOMETRY'
        named_attribute_node.attribute_name = attributeName
        named_attribute_node.name = "Named Attribute" # this to keep more generic the following code
        named_attribute_node.label = "Named Attribute"
        #Add value attribute
        # value_attribute_node = group.nodes.new(type="ShaderNodeValue")
        # value_attribute_node.label = self.filter_name + " number"
        # value_attribute_node.outputs[0].default_value = 0
        

            
        group_output.location = (600, 0)
        named_attribute_node.location = (0,-100)
        # value_attribute_node.location = (0,100)
        
        return(group)
        
        
    def execute(self, context):
        # filter is lower case to avoid clash with GN groups
        name = "MaStro filter by " + self.filter_name.title()

        if name not in bpy.data.node_groups:
            filterBy_Group = self.newGroup(name, "Shader")
        else:
            filterBy_Group = bpy.data.node_groups[name]
            
        nodes = filterBy_Group.nodes
        
        group_output = nodes["Group Output"]
        named_attribute_node = nodes["Named Attribute"]
        # nodeName = self.filter_name + " number"
        # value_attribute_node = nodes[nodeName]
                    
        filterNodeIds = []
        filterNodeDescriptions = []
        for node in nodes:
            # if node.type == "COMPARE":
            #     tmpId = node.inputs[3].default_value
            #     filterNodeIds.append(tmpId)
            #     filterNodeDescriptions.append(filterBy_Group.interface.items_tree[tmpId].description)
            if node.type == "MATH":
                tmpId = int(node.inputs[1].default_value)
                filterNodeIds.append(tmpId)
                filterNodeDescriptions.append(filterBy_Group.interface.items_tree[tmpId].description)
                
        
        if len(filterNodeIds) == 0:
            lastId = -1           
        else:
            lastId = max(filterNodeIds)
            # print(lastId, len(nodes))
        
        
        if self.filter_name == "block": listToLoop = bpy.context.scene.mastro_block_name_list
        elif self.filter_name == "building": listToLoop = bpy.context.scene.mastro_building_name_list
        elif self.filter_name == "use": listToLoop = bpy.context.scene.mastro_use_name_list
        elif self.filter_name == "typology": listToLoop = bpy.context.scene.mastro_typology_name_list
        
        # filterBy_Group.links.new(named_attribute_node.outputs[2], group_output.inputs[0])
        # filterBy_Group.links.new(value_attribute_node.outputs[0], group_output.inputs[1])
        
            
        for el in listToLoop:
            if hasattr(el, "id"):
                #a new name has been added
                if el.id not in filterNodeIds:
                    if lastId >= 0:
                        node_y_location = nodes["Compare " + str(lastId)].location[1] -25
                    else:
                        node_y_location = 0
                    
                    # if type == "GN":
                    #     compare_node = filterBy_Group.nodes.new(type="FunctionNodeCompare")
                    #     compare_node.data_type = 'INT'
                    #     compare_node.operation = 'EQUAL'
                    #     compare_node.inputs[3].default_value = el.id
                    # else:
                    compare_node = filterBy_Group.nodes.new(type="ShaderNodeMath")
                    compare_node.operation = "COMPARE"
                    compare_node.inputs[1].default_value = el.id
                    compare_node.inputs[2].default_value = 0.001
                        
                    compare_node.location = (300, node_y_location-35)
                    compare_node.hide = True
                    compare_node.label="="+str(el.id)
                    compare_node.name="Compare "+str(el.id)
                    lastId = el.id
                    
                    #Add the Output Sockets and change their Default Value
                    if el.name == "":
                        elName = self.filter_name + " name..."
                    else:
                        elName = el.name
                    descr = "id: " + str(el.id) + " - " + elName
                    filterBy_Group.interface.new_socket(name=elName,description=descr,in_out ="OUTPUT", socket_type="NodeSocketBool")
            
                    #Add Links
                    index = len(group_output.inputs) -2
                    # if type == "GN":
                    #     filterBy_Group.links.new(named_attribute_node.outputs[0], compare_node.inputs[2])
                    # else:
                    filterBy_Group.links.new(named_attribute_node.outputs[0], compare_node.inputs[0])
                    filterBy_Group.links.new(compare_node.outputs[0], group_output.inputs[index])

                # a name has been renamed
                elif ("id: " + str(el.id) + " - " + str(el.name)) not in filterNodeDescriptions:
                    for i, desc in enumerate(filterNodeDescriptions):
                        if i == int(el.id):
                            filterBy_Group.interface.items_tree[i].name = str(el.name)
                            filterBy_Group.interface.items_tree[i].description = "id: " + str(el.id) + " - " + str(el.name)
        return {'FINISHED'}