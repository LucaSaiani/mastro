import bpy 
import bmesh

from ..Utils.init_lists import init_lists
from ..Utils.update_bmesh_attributes import update_bmesh_attributes

# ------------------------------
# Mastro Project Data
# ------------------------------

# ------------------------------
# Typology and uses panels
# -----------------------------

# When a typology is selected in the panel, the UIList of the related uses
# is updated in the panel below
def update_uses_of_typology(self, context):
    # empty the use name list
    index = context.scene.mastro_typology_uses_name_list_index
    use_name_list = context.scene.mastro_typology_uses_name_list
    use_name_list.clear()
    context.scene.mastro_typology_uses_name_list_index = min(max(0, index - 1), len(use_name_list) - 1)
         
    # add the uses stored in the typology to the current typology use UIList
    selected_typology_index = context.scene.mastro_typology_name_list_index
    if len(context.scene.mastro_typology_name_list) > 0:
        name_list = context.scene.mastro_typology_name_list[selected_typology_index].useList    
        split_list = name_list.split(";")
        for el in split_list:
            if el.strip() != '': # to avoid empty values which could happend when the software starts
                context.scene.mastro_typology_uses_name_list.add()
                temp_list = []    
                temp_list.append(int(el))
                last = len(context.scene.mastro_typology_uses_name_list)-1
                # search for the correspondent use name in mastro_use_name_list
                for use in context.scene.mastro_use_name_list:
                    if int(el) == use.id:
                        context.scene.mastro_typology_uses_name_list[last].id = use.id
                        context.scene.mastro_typology_uses_name_list[last].name = use.name 
                        context.scene.mastro_typology_uses_name_list_index = 0
                        break


# When a use related to the current typology is updated in the UIList,
# it is necessary to update the relative use list in Scene.mastro_typology_uses_name_list
# and also update the uses in the mastro objects
def update_typology_uses_list(context):
    selected_typology_index = context.scene.mastro_typology_name_list_index
    # the exististing list is replaced with what is in the UiList
    # the format of the list is 2;5;1 with numbers indicating the Id of the use
    tmp = ""
    for el in context.scene.mastro_typology_uses_name_list:
        tmp += str(el.id) + ";"
    # remove the last ";" in the string
    tmp = tmp[:-1]
    context.scene.mastro_typology_name_list[selected_typology_index].useList = tmp

    
# update the typology use in the UIList, in the scene panel,
# with the name selected in the drop down menu in the Typology Uses UI
def update_typology_uses_name_label(self, context):
    scene = context.scene
    name = scene.mastro_typology_uses_name
    # if the typology is newly created, the index is equal to -1 and 
    # therefore there is an out of range error
    # Also, in this case, there are no values to update
    if scene.mastro_typology_uses_name_list_index > -1:
        scene.mastro_typology_uses_name_list[scene.mastro_typology_uses_name_list_index].name = name
        for n in scene.mastro_use_name_list:
            if n.name == name:
                scene.mastro_typology_uses_name_list[scene.mastro_typology_uses_name_list_index].id = n.id
                update_typology_uses_list(context)
                return None
            

            

# from .write_storey_attribute import read_storey_attribute, write_bmesh_storey_attribute 


# def update_attributes_mastro_block_name_id(self, context):
#     scene = context.scene
#     name = scene.mastro_block_name
#     # scene.mastro_block_name_current[0].name = " " + name
#     scene.mastro_block_name_current[0].name = name
#     for n in scene.mastro_block_name_list:
#         if n.name == name:
#             scene.mastro_attribute_mass_block_id = n.id
#             scene.mastro_block_name_current[0].id = n.id
            
#             obj = context.active_object
#             obj.mastro_props['mastro_block_attribute'] = n.id
#             break 
        
        
# def update_attributes_mastro_building_name_id(self, context):
#     scene = context.scene
#     name = scene.mastro_building_name
#     scene.mastro_building_name_current[0].name = name
#     for n in scene.mastro_building_name_list:
#         if n.name == name:
#             scene.mastro_attribute_mass_building_id = n.id
#             scene.mastro_building_name_current[0].id = n.id
            
#             obj = context.active_object
#             obj.mastro_props['mastro_building_attribute'] = n.id
#             break 
        
        

            
        
# # Update the wall label in the UI and all the relative data in the selected edges
# def update_attributes_wall(self, context):
#     scene = context.scene
#     name = scene.mastro_wall_names
#     scene.mastro_wall_name_current[0].name = " " + name
#     for n in scene.mastro_wall_name_list:
#         if n.name == name:
#             scene.mastro_attribute_wall_id = n.id
#             scene.mastro_wall_name_current[0].id = n.id
#             break
        

# update the floor label in the UI and all the relative data in the selected faces
# def update_attributes_floor(self, context):
#     scene = context.scene
#     name = scene.mastro_floor_names
#     scene.mastro_floor_name_current[0].name = " " + name
#     for n in scene.mastro_floor_name_list:
#         if n.name == name:
#             scene.mastro_attribute_floor_id = n.id
#             scene.mastro_floor_name_current[0].id = n.id
#             break
        
        
# ------------------------------
# Block / Building Properties
# ------------------------------
# def update_attributes_mastro_block_side_angle(self, context):
#     bpy.ops.object.set_edge_attribute_angle() 
    
# def update_attributes_mastro_block_depth(self, context):
#     bpy.ops.object.set_edge_attribute_depth()
        
   
# ------------------------------
# Wall Properties
# ------------------------------
# def update_attributes_mastro_wall_id(self, context):
#     bpy.ops.object.set_attribute_wall_id()
    
# update the wall normal
# def update_attributes_mastro_wall_normal(self, context):
#     bpy.ops.object.set_edge_attribute_normal()
        
# ------------------------------
# Floor Properties
# ------------------------------        
# def update_attributes_mastro_floor_id(self, context):
#     bpy.ops.object.set_attribute_floor_id()

# ------------------------------
# Mastro Extras
# ------------------------------
# def update_extras_vertex(self, context):
#     bpy.ops.object.set_extras_vertex_value()

# def update_extras_edge(self, context):
#     bpy.ops.object.set_extras_edge_value()
    
# def update_extras_face(self, context):
#     bpy.ops.object.set_extras_face_value()
    
# ------------------------------
# Street Properties
# ------------------------------  
# Update the street label in the UI and all the relative data in the selected edges
def update_attributes_street(self, context):
    scene = context.scene
    name = scene.mastro_street_names
    for n in scene.mastro_street_name_list:
        if n.name == name:
            scene.mastro_attribute_street_id = n.id
            bpy.ops.object.set_attribute_street_id()
            scene.mastro_street_name_current[0].id = n.id
            scene.mastro_street_name_current[0].name = n.name
            return None 
        
        
# ------------------------------
# Classes - Generic
# ------------------------------  
# update the node "filter by use" if a new use is added or
# a use name has changed
# also update the names of mastro_typology_uses_name_list_index  
def update_mastro_nodes_by_use(self, context):
    bpy.ops.node.mastro_gn_separate_geometry_by(filter_name="use")
    bpy.ops.node.mastro_gn_filter_by(filter_name="use")
    bpy.ops.node.mastro_shader_filter_by(filter_name="use")
    
    # updating mastro_typology_uses_name_list_index
    current_list = context.scene.mastro_typology_uses_name_list
    for i, el in enumerate(current_list):
        name = context.scene.mastro_use_name_list[el.id].name
        context.scene.mastro_typology_uses_name_list[i].name = name
    # updating the names in bpy.context.scene.mastro_obj_typology_uses_name_list
    # if they are shown in the MaStro panel in the 3dView
    usesUiList = context.scene.mastro_obj_typology_uses_name_list
    subIndex = context.scene.mastro_typology_uses_name_list_index
    if  len(context.scene.mastro_typology_uses_name_list) == 0: 
        init_lists()
    subName = context.scene.mastro_typology_uses_name_list[subIndex].name
    useIndex = context.scene.mastro_use_name_list.find(subName)
    for use in usesUiList:
        if use.nameId == useIndex:
            use.name = subName
            return None
    return None


# ------------------------------
# Classes - Block Name
# ------------------------------ 
# update the node "filter by block" if a new block is added or
# a block name has changed
def update_mastro_filter_by_block(self, context):
    bpy.ops.node.mastro_shader_filter_by(filter_name="block")
    return None
# ------------------------------
# Classes - Building Name
# ------------------------------  
# update the node "filter by building" if a new building is added or
# a building name has changed
def update_mastro_filter_by_building(self, context):
    bpy.ops.node.mastro_shader_filter_by(filter_name="building")
    return None

# ------------------------------
# Classes - Typology
# ------------------------------  
# def update_all_mastro_meshes(context, attributes_to_update):
#     if context.window_manager.mastro_toggle_auto_update_mass_data:
#         print("bau")
#         update_bmesh_attributes(attributes_to_update)

# this is for the floor to floor height
def update_all_mastro_meshes_floorToFloor(self, context):
    if context.window_manager.mastro_toggle_auto_update_mass_data:
        update_bmesh_attributes(context, "floor_to_floor")
        
# this is for the number of storeys
def update_all_mastro_meshes_numberOfStoreys(self, context):
    if context.window_manager.mastro_toggle_auto_update_mass_data:
        update_bmesh_attributes(context, "number_of_storeys")
    
# this is for the useList
def update_all_mastro_meshes_useList(self, context):
    if context.window_manager.mastro_toggle_auto_update_mass_data:
        update_bmesh_attributes(context, "all")
        
        
# update the node "filter by typology" if a new typology is added or
# a typology name has changed
def update_mastro_filter_by_typology(self, context):
    bpy.ops.node.mastro_gn_filter_by(filter_name="typology")
    bpy.ops.node.mastro_shader_filter_by(filter_name="typology")
    return None



        
        


# ------------------------------
# Classes - Wall
# ------------------------------   
# update the node "filter by wall type" if a new wall type is added or
# a wall typey name has changed
def update_mastro_filter_by_wall_type(self, context):
    # nt = bpy.data.node_groups.new("MasterUpdateTMP", "GeometryNodeTree")
    # # testNode = nt.nodes.new("separateByWallType")
    # # testNode.update_all(bpy.context.scene)
    # mastro_GN_separate_by_wall_type.update_all(bpy.context.scene)
    # bpy.data.node_groups.remove(nt) 
    
    bpy.ops.node.mastro_gn_filter_by(filter_name="wall type")
    bpy.ops.node.mastro_gn_separate_geometry_by(filter_name="wall type")
    # bpy.ops.node.mastro_shader_filter_by(filter_name="wall type")
    return None
    
# ------------------------------
# Classes - Street
# ------------------------------   
# update the node "filter by street type" if a new street type is added or
# a street type name has changed
def update_mastro_filter_by_street_type(self, context):
    bpy.ops.node.mastro_gn_filter_by(filter_name="street type")
    # bpy.ops.node.mastro_shader_filter_by(filter_name="street type")
    return None

def update_all_mastro_street_width(self, context):
    updates = "width"
    bpy.ops.object.update_all_mastro_street_attributes(attribute_to_update=updates)
    
def update_all_mastro_street_radius(self, context):
    updates = "radius"
    bpy.ops.object.update_all_mastro_street_attributes(attribute_to_update=updates)
  



# #Update the typology label in the UI and all the relative data in the selected faces
# def update_attributes_mastro_mesh_typology(self, context):
#     # update the label
#     scene = context.scene
#     name = scene.mastro_typology_names
#     if "MaStro mass" in context.object.data:
#         for n in scene.mastro_typology_name_list:
#             if n.name == name:
#                 scene.mastro_attribute_mass_typology_id = n.id
#                 # update the data accordingly to the typology id
#                 bpy.ops.object.set_face_attribute_uses()
#                 scene.mastro_typology_name_current[0].id = n.id
#                 scene.mastro_typology_name_current[0].name = name
#                 break  
#     elif "MaStro block" in context.object.data:
#         for n in scene.mastro_typology_name_list:
#             if n.name == name:
#                 scene.mastro_attribute_mass_typology_id = n.id
#                 # update the data accordingly to the typology id
#                 bpy.ops.object.set_edge_attribute_uses()
#                 scene.mastro_typology_name_current[0].id = n.id
#                 scene.mastro_typology_name_current[0].name = name
#                 break     

        
        


 
            

    

    
 
