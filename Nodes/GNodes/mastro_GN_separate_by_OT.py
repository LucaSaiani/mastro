import bpy
from bpy.types import Operator
from types import SimpleNamespace

from ..utils.node_utils import create_new_nodegroup

class mastro_GN_separate_by_OT(Operator):
    """Update the Geometry Nodes 'Separate By' node group outputs"""
    bl_idname = "node.mastro_gn_separate_by"
    bl_label = "Update the GN separate by group"

    filter_name: bpy.props.StringProperty(name="Filter type name")
            
    def newGroup (self, groupName, type):
        if self.filter_name == "use": attributeName = "mastro_use"
        elif self.filter_name == "typology": attributeName = "mastro_typology_id"
        elif self.filter_name == "wall type": attributeName = "mastro_wall_id"
        elif self.filter_name == "street type": attributeName = "mastro_street_id"
        elif self.filter_name == "block side": attributeName = "mastro_block_side"

        # group = bpy.data.node_groups.new(groupName,'GeometryNodeTree')
        
        
        group = create_new_nodegroup(
                groupName,
                in_sockets={"Geometry": "NodeSocketGeometry"},
                out_sockets={"Wall type... ": "NodeSocketGeometry"}
            )
       
        named_attribute_node = group.nodes.new(type="GeometryNodeInputNamedAttribute")
        named_attribute_node.data_type = 'INT'
        named_attribute_node.inputs[0].default_value = attributeName
        
        compare_node = group.nodes.new(type="FunctionNodeCompare")
        compare_node.data_type = "INT"
        compare_node.operation = "EQUAL"
        
        separate_geometry_node = group.nodes.new(type="GeometryNodeSeparateGeometry")
        separate_geometry_node.domain = "EDGE"
        separate_geometry_node.label = "0"
        
        # Ensure Group Input and Group Output nodes exist
        group_input = group.nodes.get("Group Input")
        group_output = group.nodes.get("Group Output")
        
        # Get the relevant sockets
        geom_input = group_input.outputs.get("Geometry")
        geom_output_0 = group_output.inputs.get("Wall type... ")
        
         # Connect nodes
        group.links.new(geom_input, separate_geometry_node.inputs[0])
        group.links.new(named_attribute_node.outputs[0], compare_node.inputs[2])
        compare_node.inputs[3].default_value = 0
        group.links.new(compare_node.outputs[0], separate_geometry_node.inputs[1])
        group.links.new(separate_geometry_node.outputs[0], geom_output_0)
        
        group.default_group_node_width = 160
        
        return(group)
        
        
    def execute(self, context):
        name = "MaStro Separate Geometry by " + self.filter_name.title()
                    
        if name not in bpy.data.node_groups:
            group = self.newGroup(name, "GN")
        else:
            group = bpy.data.node_groups[name]
                
        nodes = group.nodes
        
        # group_input = nodes["Group Input"]
        group_output = nodes["Group Output"]
        named_attribute_node = nodes["Named Attribute"]
                    
        filterNodeIds = []
        filterNodeDescriptions = []
        for node in nodes:
            if node.type == "SEPARATE_GEOMETRY":
                tmpId = int(node.label)
                filterNodeIds.append(tmpId)
                filterNodeDescriptions.append(group.interface.items_tree[tmpId].description)
            
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
        
        lastId = filterNodeIds[-1]
        for node in nodes:
            if node.label == str(lastId):
                lastOutput = node
                break
            
        listToLoop = sorted(listToLoop, key=lambda x: x.id)
        
        for el in listToLoop:
            if hasattr(el, "id"):
                #a new name has been added
                if el.id not in filterNodeIds:
                    
                    compare_node = group.nodes.new(type="FunctionNodeCompare")
                    compare_node.data_type = 'INT'
                    compare_node.operation = 'EQUAL'
                    compare_node.inputs[3].default_value = el.id
                        
                    separate_geometry_node = group.nodes.new(type="GeometryNodeSeparateGeometry")
                    separate_geometry_node.domain = "EDGE"
                    separate_geometry_node.label = str(el.id)
                    
                    #Add the Output Sockets and change their Default Value
                    if el.name == "":
                        if self.filter_name == "use": elName = "Use name..."
                        elif self.filter_name == "typology": elName = "Typology name..."
                        elif self.filter_name == "wall type": elName = "Wall name..."
                        elif self.filter_name == "steet type": elName = "Street name..."
                    else:
                        elName = el.name
                    descr = "id: " + str(el.id) + " - " + elName
                    group.interface.new_socket(name=elName, 
                                               description=descr, 
                                               in_out ="OUTPUT", 
                                               socket_type="NodeSocketGeometry")
            
                    #Add Links
                    index = len(group_output.inputs) -2
                    group.links.new(named_attribute_node.outputs[0], compare_node.inputs[2])
                    group.links.new(compare_node.outputs[0], separate_geometry_node.inputs[1])
                    group.links.new(lastOutput.outputs[1], separate_geometry_node.inputs[0])
                    group.links.new(separate_geometry_node.outputs[0], group_output.inputs[index])
                    lastOutput = separate_geometry_node

                # a name has been renamed
                elif ("id: " + str(el.id) + " - " + str(el.name)) not in filterNodeDescriptions:
                    for i, desc in enumerate(filterNodeDescriptions):
                        if i == int(el.id):
                            group.interface.items_tree[i].name = str(el.name)
                            group.interface.items_tree[i].description = "id: " + str(el.id) + " - " + str(el.name)

        return {'FINISHED'}
