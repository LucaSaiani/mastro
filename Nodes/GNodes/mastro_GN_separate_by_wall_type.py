import bpy 
from bpy.types import GeometryNodeCustomGroup
from types import SimpleNamespace

from ..utils.node_utils import create_new_nodegroup

class mastro_GN_separate_by_wall_type(GeometryNodeCustomGroup):
    bl_idname = "separateByWallType"
    bl_label = "Separate by Wall Type"
    
    def init(self, context):
        # Name of the master NodeTree
        name = f"{self.bl_idname}"

        # Get the master NodeTree or create it if it doesn't exist
        ng_master = bpy.data.node_groups.get(name)
        if ng_master is None:
            ng_master = create_new_nodegroup(
                name,
                in_sockets={"Geometry": "NodeSocketGeometry"},
                out_sockets={"Wall type... ": "NodeSocketGeometry"}
            )

            # Add internal nodes
            attributeName = "mastro_wall_id"
            named_attribute_node = ng_master.nodes.new(type="GeometryNodeInputNamedAttribute")
            named_attribute_node.data_type = 'INT'
            named_attribute_node.inputs[0].default_value = attributeName

            compare_node = ng_master.nodes.new(type="FunctionNodeCompare")
            compare_node.data_type = "INT"
            compare_node.operation = "EQUAL"

            separate_geometry_node = ng_master.nodes.new(type="GeometryNodeSeparateGeometry")
            separate_geometry_node.domain = "EDGE"
            separate_geometry_node.label = "0"

            # Ensure Group Input and Group Output nodes exist
            group_input = ng_master.nodes.get("Group Input")
            group_output = ng_master.nodes.get("Group Output")

            # Get the relevant sockets
            geom_input = group_input.outputs.get("Geometry")
            geom_output_0 = group_output.inputs.get("Wall type... ")

            # Connect nodes
            ng_master.links.new(geom_input, separate_geometry_node.inputs[0])
            ng_master.links.new(named_attribute_node.outputs[0], compare_node.inputs[2])
            compare_node.inputs[3].default_value = 0
            ng_master.links.new(compare_node.outputs[0], separate_geometry_node.inputs[1])
            ng_master.links.new(separate_geometry_node.outputs[0], geom_output_0)

        # Copy the master NodeTree for this instance
        ng = ng_master.copy()
        self.node_tree = ng
        self.label = self.bl_label
   
        self.width = 160

        # Ensure the Group Input/Output nodes of the copy are updated
        for node in ng.nodes:
            if node.bl_idname in {"NodeGroupInput", "NodeGroupOutput"}:
                node.update()

        # Debug: print node names and count
        # print(f"Number of nodes in '{ng.name}': {len(ng.nodes)}")
        # for node in ng.nodes:
        #     print(node.name)

        return None
    
    def updates(self, scene):
        self.filter_name = "wall type"
        # group = bpy.data.node_groups[self.bl_idname]
        group = self.node_tree
        nodes = group.nodes
        group_output = nodes["Group Output"]
        named_attribute_node = nodes["Named Attribute"]
        
        filterNodeIds = []
        filterNodeDescriptions = []
        for node in nodes:
            if node.type == "SEPARATE_GEOMETRY":
                # tmpId = node.inputs[3].default_value
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
        
        # for e in filterNodeIds: print("filternode", e)
        lastId = filterNodeIds[-1]
        for node in nodes:
            if node.label == str(lastId):
                lastOutput = node
                break
        
        # print(lastOutput)
        for el in listToLoop:
            if hasattr(el, "id"):
                
                #a new name has been added
                if el.id not in filterNodeIds:
                    # print("adding")
                #     # if lastId >= 0:
                #     #     node_y_location = nodes["Compare " + str(lastId)].location[1] -25
                #     # else:
                #     #     node_y_location = 0
                    
                    compare_node = group.nodes.new(type="FunctionNodeCompare")
                    compare_node.data_type = 'INT'
                    compare_node.operation = 'EQUAL'
                    compare_node.inputs[3].default_value = el.id
                        
                #     # compare_node.location = (300, node_y_location-35)
                #     # compare_node.hide = True
                #     compare_node.label="="+str(el.id)
                #     compare_node.name="Compare "+str(el.id)
                #     # lastId = el.id
                    
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
            
                    # Add Links
                    
                    index = len(group_output.inputs) -2
                    group.links.new(named_attribute_node.outputs[0], compare_node.inputs[2])
                    group.links.new(compare_node.outputs[0], separate_geometry_node.inputs[1])
                    group.links.new(lastOutput.outputs[1], separate_geometry_node.inputs[0])
                    group.links.new(separate_geometry_node.outputs[0], group_output.inputs[index])
                    lastOutput = separate_geometry_node
                #     group.links.new(compare_node.outputs[0], group_output.inputs[index])

                # a name has been renamed
                elif ("id: " + str(el.id) + " - " + str(el.name)) not in filterNodeDescriptions:
                    # print("renaming")
                    for i, desc in enumerate(filterNodeDescriptions):
                        if i == int(el.id):
                            group.interface.items_tree[i].name = str(el.name)
                            group.interface.items_tree[i].description = "id: " + str(el.id) + " - " + str(el.name)
        
        self.node_tree.update_tag() # force the graphic update
        return {'FINISHED'}
   
    def copy(self, node):
        self.node_tree = node.node_tree.copy()
        return None
    
    def draw_label(self,):
        return self.bl_label

    def draw_buttons(self, context, layout):
        return None
        # row = layout.row(align=True)
        # row.label(text="ciao")
        # row.prop(self, "view_obj", text="", icon="MESH_CUBE")
        
    @classmethod
    def update_all(cls,scene):
        """search for all nodes of this type and update them"""
        
        # for n in [n for ng in bpy.data.node_groups for n in ng.nodes if (n.bl_idname==cls.bl_idname)]:
        #     n.update()
        
        # Update nodes in master NodeTrees
        for ng in bpy.data.node_groups:
            for n in ng.nodes:
                if getattr(n, "bl_idname", "") == cls.bl_idname:
                    # print("master found", n)
                    n.updates(scene)
        
        # Update nodes already instanced in modifiers
        for obj in bpy.data.objects:
            for mod in obj.modifiers:
                if hasattr(mod, "node_group"):
                    for n in mod.node_group.nodes:
                        if getattr(n, "bl_idname", "") == cls.bl_idname:
                            # print("update found", n)
                            n.updates(scene)
            
        return None 