import bpy 

from bpy.types import Panel, Operator, PropertyGroup
from bpy.props import StringProperty

# def get_active_node(self):
#     space_data = bpy.context.space_data

#     if space_data and space_data.tree_type == 'GeometryNodeTree':
#         node_tree = space_data.node_tree
#         if node_tree:
#             if space_data.node_tree.nodes.active:
#                 return space_data.node_tree.nodes.active
#     return None

def updateGroup(self, context):
    bpy.ops.node.separate_geometry_by_factor()
    
# to open a new window, the preferences window 
# is opened and then the area type is changed to text editor
def openTextEditor(text):
    bpy.ops.screen.userpref_show("INVOKE_DEFAULT")
    window = bpy.context.window_manager.windows[-1]
    area = window.screen.areas[0]
    area.type = "TEXT_EDITOR"
    area.spaces[0].show_region_header = False
    area.spaces[0].show_region_footer = False
    area.spaces[0].show_line_numbers = False
    area.spaces[0].show_syntax_highlight = False
    area.spaces[0].show_word_wrap = True
    area.spaces[0].text = text
    
# to create a sticky note
class NODE_OT_sticky_note(Operator):
    bl_idname = "node.sticky_note"
    bl_label = "sticky Note"
    bl_description = "MaStro Sticky Note"
    bl_options = {'REGISTER', 'UNDO'}


    def execute(self, context):
        #get the list of all selected nodes
        node_tree = bpy.context.space_data.edit_tree
        print(node_tree)
        if node_tree:
            # selected_nodes = [node for node in node_tree.nodes if node.select]
            activeNode = node_tree.nodes.active
            # edit existing note
            if activeNode and activeNode.select and "customNote" in activeNode:
                postIt = activeNode
                textName = postIt.text.name
                note_text = bpy.data.texts[textName]
                openTextEditor(note_text)
            # create a new note
            else:
                postIt = node_tree.nodes.new("NodeFrame")
                # postIt.select = False
                postIt.name = "MaStro note"
                postIt.label = "Note"
                postIt["customNote"] = True
                postIt.use_custom_color = True
                postIt.color = bpy.context.preferences.addons[__package__].preferences.noteColor
                postIt.label_size = bpy.context.preferences.addons[__package__].preferences.noteSize
                postIt.shrink = False
                if activeNode and activeNode.select:
                    postIt.location = activeNode.location
                    postIt.location.y = activeNode.height + 20
                else:
                    postIt.location = node_tree.view_center
                postIt.width = 200
                postIt.height = 200
                note_text = bpy.data.texts.new("MaStro note")
                note_text.use_fake_user = False
      
                postIt.text = bpy.data.texts[note_text.name]
                openTextEditor(note_text)
            
        return {'FINISHED'}


class VIEW_PT_MaStro_Node_Panel(Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = "UI"
    bl_category = "Node"
    bl_label = "MaStro Note"
  
    # @classmethod
    # def poll(cls, context):
    #     return context.space_data.tree_type == 'GeometryNodeTree'    
    
    def draw(self, context):
        # scene = context.scene
        layout = self.layout
        node_tree = bpy.context.space_data.edit_tree
        if node_tree:
            activeNode = node_tree.nodes.active
            # activeNode = get_active_node(self)
            if activeNode and activeNode.select and "customNote" in activeNode:
                layout.operator("node.sticky_note", text="Edit the Sticky Note")
            else:
                layout.operator("node.sticky_note", text="Add a Sticky Note")

    
class VIEW_PT_MaStro_GN_Panel(Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = "UI"
    bl_category = "MaStro"
    bl_label = "MaStro Note"
  
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'GeometryNodeTree'
    
    def draw(self, context):
        scene = context.scene
        layout = self.layout
        node_tree = bpy.context.space_data.node_tree
        if node_tree:
            node_tree = bpy.context.space_data.node_tree
            activeNode = node_tree.nodes.active
            # activeNode = get_active_node(self)

            # if activeNode and activeNode.select and "customNote" in activeNode:
            #     selectedNote = activeNode.name
            #     layout.label(text=selectedNote)
            #     # mastro_props.noteText = readText
            # else:
            #     # layout.operator("node.post_it_note", text="Add a sticky note")
            #     # row = layout.row()
            #     # row.enabled = bool(mastro_props.noteText.strip())
                
            #     layout.operator("node.sticky_note", text="Add a sticky note")
                    
            if activeNode and hasattr(activeNode, "node_tree"):
                if activeNode.node_tree.bl_description == "MaStro Geometry By Factor":
                        layout.label(text="Subdivision:")
                        row = layout.row()
                        row.label(text="Subdivide by:")
                        row.prop(scene, "geometryMenuSwitch", text="")
                        row = layout.row()
                        row.label(text="Number of subdivision:")
                        row.prop(context.scene, "mastro_group_node_number_of_split", text="")
            
                
       

class separate_geometry_by_factor_OT(Operator):
    '''Separate geometry in geometry node by factor'''
    bl_idname = "node.separate_geometry_by_factor"
    bl_label = "Separate geometry by factor"

    def newGroup (self, groupName):
        group = bpy.data.node_groups.new(groupName,'GeometryNodeTree')
        group.bl_description = "MaStro Geometry By Factor"
        
        group.interface.new_socket(name='Geometry', description='', in_out = 'INPUT', socket_type='NodeSocketGeometry')
        
        group.interface.new_socket(name='Seed', description='Seed for the random value', in_out = 'INPUT', socket_type='NodeSocketInt')
        
        group.interface.new_socket(name='Subdivisions', description='The number of subdivisions. This is used only to store data. To plug the socket does nothing. If you want to change the number of subdivisions use the panel Node->MaStro', in_out = 'INPUT', socket_type='NodeSocketInt')
        group.interface.items_tree[2].default_value = bpy.context.scene.mastro_group_node_number_of_split
        group.interface.items_tree[2].min_value = 2
        group.interface.items_tree[2].force_non_field = True
        group.interface.items_tree[2].hide_value = True
        
        group.interface.new_socket(name='Split 0', description='The number of subdivisions', in_out = 'INPUT', socket_type='NodeSocketInt')
        group.interface.items_tree[3].default_value = 0
        group.interface.items_tree[3].min_value = 0
        group.interface.items_tree[3].max_value = 100
        group.interface.items_tree[3].force_non_field = True
        group.interface.items_tree[3].subtype = 'PERCENTAGE'
        
        group.interface.new_socket(name='Selection 0', description='', in_out = 'OUTPUT', socket_type='NodeSocketGeometry')
        group.interface.new_socket(name='Remaining', description='', in_out = 'OUTPUT', socket_type='NodeSocketGeometry')
       
        group_input = group.nodes.new('NodeGroupInput')
        group_input.location = (-100, -300)
       
        group_output = group.nodes.new('NodeGroupOutput')
        group_output.location = (600, 450)
        
        split_edges = group.nodes.new(type='GeometryNodeSplitEdges')
        split_edges.location = (150, 0)

        capture_attribute = group.nodes.new(type='GeometryNodeCaptureAttribute')
        capture_attribute.domain = "EDGE"
        capture_attribute.name = "Capture"
        capture_attribute.capture_items.new(socket_type="INT", name="RND")
        capture_attribute.location = (150, -150)        

        random_value = group.nodes.new(type='FunctionNodeRandomValue')
        random_value.data_type = 'INT'
        random_value.inputs[4].default_value = 0
        random_value.inputs[5].default_value = 100
        random_value.location = (150, -300)
        
        less_than_node = group.nodes.new(type='FunctionNodeCompare')
        less_than_node.name = "Compare 0"
        less_than_node.operation = 'LESS_EQUAL'
        less_than_node.location = (400, 0)

        # not_node = group.nodes.new(type='FunctionNodeBooleanMath')
        # not_node.operation = 'NOT'
        # not_node.name = "Boolean not 0"
        # not_node.location = (400, 150)

        separate_geometry_node = group.nodes.new(type='GeometryNodeSeparateGeometry')
        separate_geometry_node.name = "Separate 0"
        separate_geometry_node.domain = 'EDGE'
        separate_geometry_node.location = (400, 150)

        # delete_geometry_node = group.nodes.new(type='GeometryNodeDeleteGeometry')
        # delete_geometry_node.name = "Separate 0"
        # delete_geometry_node.domain = 'EDGE'
        # delete_geometry_node.location = (400, 300)
        
        merge_node = group.nodes.new(type='GeometryNodeMergeByDistance')
        merge_node.name = "Merge 0"
        merge_node.location = (400, 300)
        
        leftover_greater_than_node = group.nodes.new(type='FunctionNodeCompare')
        leftover_greater_than_node.name = "Leftover compare"
        leftover_greater_than_node.operation = 'GREATER_THAN'
        leftover_greater_than_node.location = (600, 0)
        
        # leftover_not_node = group.nodes.new(type='FunctionNodeBooleanMath')
        # leftover_not_node.operation = 'NOT'
        # leftover_not_node.name = "Leftover not"
        # leftover_not_node.location = (600, 150)
        
        leftover_separate_geometry_node = group.nodes.new(type='GeometryNodeSeparateGeometry')
        leftover_separate_geometry_node.name = "Leftover"
        leftover_separate_geometry_node.domain = 'EDGE'
        leftover_separate_geometry_node.location = (600, 150)
        
        # leftover_delete_geometry_node = group.nodes.new(type='GeometryNodeDeleteGeometry')
        # leftover_delete_geometry_node.name = "Leftover"
        # leftover_delete_geometry_node.domain = 'EDGE'
        # leftover_delete_geometry_node.location = (600, 300)
        
        leftover_merge_node = group.nodes.new(type='GeometryNodeMergeByDistance')
        leftover_merge_node.name = "Leftover merge"
        leftover_merge_node.location = (600, 300)
        
        # group input links
        group.links.new(group_input.outputs['Geometry'], capture_attribute.inputs['Geometry'])
        group.links.new(group_input.outputs['Seed'], random_value.inputs[8])
        group.links.new(group_input.outputs['Split 0'], less_than_node.inputs[1])
        group.links.new(group_input.outputs['Split 0'], leftover_greater_than_node.inputs[1])
        
        # random node links
        group.links.new(random_value.outputs['Value'], capture_attribute.inputs['RND'])
        
        # capture node links
        group.links.new(capture_attribute.outputs['Geometry'], split_edges.inputs['Mesh'])
        group.links.new(capture_attribute.outputs['RND'], less_than_node.inputs[0])
        group.links.new(capture_attribute.outputs['RND'], leftover_greater_than_node.inputs[0])
        
        # split edges links
        group.links.new(split_edges.outputs['Mesh'], separate_geometry_node.inputs['Geometry'])
        # group.links.new(split_edges.outputs['Mesh'], leftover_separate_geometry_node.inputs['Geometry'])
        
        # less than links
        group.links.new(less_than_node.outputs[0], separate_geometry_node.inputs[1])
        
        # not links
        # group.links.new(not_node.outputs[0], delete_geometry_node.inputs[1])
        
        # separate geometry links
        group.links.new(separate_geometry_node.outputs[0], merge_node.inputs[0])
        group.links.new(separate_geometry_node.outputs[1], leftover_separate_geometry_node.inputs[0])
        
        # merge links
        group.links.new(merge_node.outputs[0], group_output.inputs[0])
        
        # leftover more than links
        group.links.new(leftover_greater_than_node.outputs[0], leftover_separate_geometry_node.inputs[1])
        
        # leftover not links
        # group.links.new(leftover_not_node.outputs[0], leftover_delete_geometry_node.inputs[1])
        
        # leftover geometry links
        group.links.new(leftover_separate_geometry_node.outputs[0], leftover_merge_node.inputs[0])
        
        # leftover merge links
        group.links.new(leftover_merge_node.outputs[0], group_output.inputs["Remaining"])
      

        return(group)
    
    def execute(self, context):
        name = "MaStro Separate Geometry by Factor"
        if name not in bpy.data.node_groups:
            group = self.newGroup(name)
            
        else:
            subdivision = bpy.context.scene.mastro_group_node_number_of_split
        
            # node_tree = bpy.context.space_data.node_tree
            # activeNode = node_tree.nodes.active
            if bpy.context.space_data and bpy.context.space_data.node_tree:
                node_tree = bpy.context.space_data.node_tree
                activeNode = node_tree.nodes.active
                # activeNode = get_active_node(self)
                try:
                    activeNode.node_tree
                    if activeNode.node_tree.bl_description == "MaStro Geometry By Factor":
                        group = activeNode.node_tree
                        previousSubdivision =  activeNode.inputs[1].default_value
                        groupNodes = group.nodes
                        group_input = groupNodes['Group Input']
                        group_output = groupNodes['Group Output']
                        # random_node = groupNodes['Random Value']
                        capture_node = groupNodes['Capture']
                    
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

                                greater_than_node = group.nodes.new(type='FunctionNodeCompare')
                                greater_than_node.name = f"Compare more {nameIndex}"
                                greater_than_node.operation = "GREATER_THAN"
                                greater_than_node.location = (400 + 150 * nameIndex, -150)

                                less_than_node = group.nodes.new(type='FunctionNodeCompare')
                                less_than_node.name = f"Compare less {nameIndex}"
                                less_than_node.operation = 'LESS_EQUAL'
                                less_than_node.location = (400 + 150 * nameIndex, -300)
                                
                                and_node = group.nodes.new(type='FunctionNodeBooleanMath')
                                and_node.name = f"Boolean and {nameIndex}"
                                and_node.location = (400 + 150 * nameIndex, 0)
                                
                                # not_node = group.nodes.new(type='FunctionNodeBooleanMath')
                                # not_node.operation = 'NOT'
                                # not_node.name = f"Boolean not {nameIndex}"
                                # not_node.location = (400 + 150 * nameIndex, 150)
                                
                                math_node = group.nodes.new(type='ShaderNodeMath')
                                math_node.name = f"Math {nameIndex}"
                                math_node.location = (400 + 150 * nameIndex, -450)
                                
                                separate_geometry_node = group.nodes.new(type='GeometryNodeSeparateGeometry')
                                separate_geometry_node.name = f"Separate {nameIndex}"
                                separate_geometry_node.domain = 'EDGE'
                                separate_geometry_node.location = (400 + 150 * nameIndex, 150)
                                
                                # delete_geometry_node = group.nodes.new(type='GeometryNodeDeleteGeometry')
                                # delete_geometry_node.name = f"Separate {nameIndex}"
                                # delete_geometry_node.domain = 'EDGE'
                                # delete_geometry_node.location = (400 + 150 * nameIndex, 300)
                                
                                merge_node = group.nodes.new(type='GeometryNodeMergeByDistance')
                                merge_node.name = f"Merge {nameIndex}"
                                merge_node.location = (400 + 150 * nameIndex, 300)
        
                                group.interface.new_socket(name=f'Selection {nameIndex}', description='', in_out = 'OUTPUT', socket_type='NodeSocketGeometry')
                            
                                group_output.location = (800 + 150 * nameIndex, 500)
                                
                                # group input links
                                if nameIndex == 1:
                                    group.links.new(group_input.outputs[f'Split {nameIndex-1}'], math_node.inputs[0])
                                    group.links.new(group_input.outputs[f'Split {nameIndex-1}'], greater_than_node.inputs[1])
                                else:
                                    group.links.new(group.nodes[f'Math {nameIndex-1}'].outputs[0], greater_than_node.inputs[1])
                                    group.links.new(group.nodes[f'Math {nameIndex-1}'].outputs[0], math_node.inputs[0])
                                group.links.new(group_input.outputs[f'Split {nameIndex}'], math_node.inputs[1])
                                
                                # capture node links
                                group.links.new(capture_node.outputs['RND'], greater_than_node.inputs[0])
                                group.links.new(capture_node.outputs['RND'], less_than_node.inputs[0])
                                
                                # Split edges links
                                # group.links.new(group.nodes['Split Edges'].outputs[0], delete_geometry_node.inputs['Geometry'])
                                
                                # math node links
                                group.links.new(math_node.outputs[0], less_than_node.inputs[1])
                                
                                # less than and greater than links
                                group.links.new(greater_than_node.outputs[0], and_node.inputs[0])
                                group.links.new(less_than_node.outputs[0], and_node.inputs[1])
                                
                                # and node links
                                group.links.new(and_node.outputs[0], separate_geometry_node.inputs[1])
                                
                                # # not node links
                                # group.links.new(not_node.outputs[0], delete_geometry_node.inputs[1])
                                
                                # separate geometry to merge links
                                group.links.new(groupNodes[f'Separate {nameIndex -1}'].outputs[1], separate_geometry_node.inputs[0])
                                group.links.new(separate_geometry_node.outputs[0], merge_node.inputs[0])
                                
                                # merge to group output links
                                group.links.new(merge_node.outputs[0], group_output.inputs[nameIndex])
                                
                                i += 1
                                itemIndex += 2
                                nameIndex += 1
                                
                            # change the link of the remaining greater than with the latest math node output
                            # and moves the delete geometry output to the last group output inputs
                            lastSocket = len(group_output.inputs) -2
                            group.links.new(groupNodes[f"Math {nameIndex-1}"].outputs[0], groupNodes["Leftover compare"].inputs[1])
                            group.links.new(groupNodes[f'Separate {nameIndex -1}'].outputs[1], groupNodes["Leftover"].inputs[0])
                            group.links.new(groupNodes["Leftover merge"].outputs[0], group_output.inputs[lastSocket])
                                
                                
                        elif previousSubdivision > subdivision:
                            i = previousSubdivision
                            while i >= subdivision:
                                itemsToRemove = []
                                # nodesToRemove = []
                                for item in group.interface.items_tree:
                                    if item.name in [f"Split {i}", f"Selection {i}"]:
                                        itemsToRemove.append(item)
                                for node in groupNodes:
                                    if node.name in [f"Separate {i}", 
                                                    f"Compare more {i}", 
                                                    f"Math {i}", 
                                                    f"Compare less {i}", 
                                                    f"Boolean and {i}", 
                                                    f"Boolean not {i}",
                                                    f"Merge {i}",
                                                    ]:
                                        groupNodes.remove(node)
                                for item in itemsToRemove:
                                    group.interface.remove(item)
                                i -= 1
                                
                            # create a link for the leftover socket
                            if i == 0:
                                group.links.new(group_input.outputs['Split 0'], groupNodes["Leftover compare"].inputs[1])
                            else:
                                group.links.new(groupNodes[f"Math {1}"].outputs[0], groupNodes["Leftover compare"].inputs[1])
                            # for node in groupNodes:
                            #     if node.name == f'Separate {i}':
                            #         group.links.new(node.outputs[1], group_output.inputs[i+1])
                            #         break
                                
                        group_output.location = (800 + 150 * subdivision, 500)
                        groupNodes["Leftover merge"].location = (600 + 150 * subdivision, 300)
                        groupNodes["Leftover"].location = (600 + 150 * subdivision, 150)
                        # groupNodes["Leftover not"].location = (600 + 150 * subdivision, 100)
                        groupNodes["Leftover compare"].location = (600 + 150 * subdivision, 0)
                        
                        
                        
                        # rename the output sockets
                        i = 0
                        for item in group.interface.items_tree:
                            if "Selection" in item.name or "Remaining" in item.name:
                                item.name = f"Selection {i}"
                                lastItem = item
                                i += 1
                        lastItem.name = "Remaining"
                        
                        # set what field to separate (point, edge, face)
                        groupNodes = group.nodes
                        selection = bpy.context.scene.geometryMenuSwitch
                        for node in groupNodes:
                            if "Separate" in node.name or "Capture" in node.name or node.name == "Leftover":
                                node.domain = selection
                        group.links.new(groupNodes[f'Separate {i -2}'].outputs[1], groupNodes["Leftover"].inputs[0])
                        # if selection == "FACE":
                        #     groupNodes['Split Edges'].mute = True
                        # else:
                        #     groupNodes['Split Edges'].mute = False
                
                        activeNode.inputs[1].default_value = subdivision
                            
                        
                except AttributeError:
                    pass
           

        return {'FINISHED'}