import bpy 

### Block attributes ###
def update_attributes_mastro_block_depth(self, context):
    bpy.ops.object.set_edge_attribute_depth()
    
def update_attributes_mastro_block_name_id(self, context):
    scene = context.scene
    name = scene.mastro_block_names
    # scene.mastro_block_name_current[0].name = " " + name
    scene.mastro_block_name_current[0].name = name
    for n in scene.mastro_block_name_list:
        if n.name == name:
            scene.attribute_mass_block_id = n.id
            scene.mastro_block_name_current[0].id = n.id
            
            obj = context.active_object
            obj.mastro_props['mastro_block_attribute'] = n.id
            break 

# update the block normal
def update_attributes_mastro_wall_normal(self, context):
    bpy.ops.object.set_edge_attribute_normal()
        
def update_attributes_mastro_block_side_angle(self, context):
    bpy.ops.object.set_edge_attribute_angle()

### Building attributes ###    
def update_attributes_mastro_building_name_id(self, context):
    scene = context.scene
    name = scene.mastro_building_names
    scene.mastro_building_name_current[0].name = name
    for n in scene.mastro_building_name_list:
        if n.name == name:
            scene.attribute_mass_building_id = n.id
            scene.mastro_building_name_current[0].id = n.id
            
            obj = context.active_object
            obj.mastro_props['mastro_building_attribute'] = n.id
            break 
    
### Mesh Attributes ###   
def update_attributes_mastro_mesh_storeys(self, context):
    if "MaStro mass" in context.object.data: 
        bpy.ops.object.set_face_attribute_storeys()
    elif "MaStro block" in context.object.data:
        bpy.ops.object.set_edge_attribute_storeys()
        
#Update the typology label in the UI and all the relative data in the selected faces
def update_attributes_mastro_mesh_typology(self, context):
    # update the label
    scene = context.scene
    name = scene.mastro_typology_names
    if "MaStro mass" in context.object.data:
        for n in scene.mastro_typology_name_list:
            if n.name == name:
                scene.attribute_mass_typology_id = n.id
                # update the data accordingly to the typology id
                bpy.ops.object.set_face_attribute_uses()
                scene.mastro_typology_name_current[0].id = n.id
                scene.mastro_typology_name_current[0].name = name
                break  
    elif "MaStro block" in context.object.data:
        for n in scene.mastro_typology_name_list:
            if n.name == name:
                scene.attribute_mass_typology_id = n.id
                # update the data accordingly to the typology id
                bpy.ops.object.set_edge_attribute_uses()
                scene.mastro_typology_name_current[0].id = n.id
                scene.mastro_typology_name_current[0].name = name
                break  
            
def update_attributes_mastro_wall_id(self, context):
    bpy.ops.object.set_attribute_wall_id()
    
def update_attributes_mastro_floor_id(self, context):
    bpy.ops.object.set_attribute_floor_id()
    
# Update the wall label in the UI and all the relative data in the selected edges
def update_attributes_wall(self, context):
    scene = context.scene
    name = scene.mastro_wall_names
    scene.mastro_wall_name_current[0].name = " " + name
    for n in scene.mastro_wall_name_list:
        if n.name == name:
            scene.attribute_wall_id = n.id
            scene.mastro_wall_name_current[0].id = n.id
            break 
        
# def update_floor_name_label(self, context):
#     scene = context.scene
#     name = scene.mastro_floor_names
#     scene.mastro_floor_name_current[0].name = " " + name
#     for n in scene.mastro_floor_name_list:
#         if n.name == name:
#             scene.attribute_floor_id = n.id
#             scene.mastro_floor_name_current[0].id = n.id
#             break

def update_extras_vertex(self, context):
    bpy.ops.object.set_extras_vertex_value()

def update_extras_edge(self, context):
    bpy.ops.object.set_extras_edge_value()
    
def update_extras_face(self, context):
    bpy.ops.object.set_extras_face_value()
    

        

    
 