import bpy
import bmesh

from .read_write_bmesh_storey_attribute import write_bmesh_storey_attribute
from .read_write_bmesh_use_attribute import write_bmesh_use_attribute

# set the number of storeys for both masses and blocks
def set_attribute_mastro_mesh_storeys(self, value):
    active_object = bpy.context.view_layer.objects.active
    selected_objects = bpy.context.selected_objects

    if len(selected_objects) == 0:
        selected_objects.append(active_object)

    for obj in selected_objects:
        if obj is None:
            continue
        if obj.type != "MESH": 
            continue
        if "MaStro object" not in obj.data: 
            continue
        if ("MaStro mass" not in obj.data and
            "MaStro block" not in obj.data):
            continue
            
        bm = bmesh.from_edit_mesh(obj.data)
        
        if "MaStro mass" in obj.data:
            selection_set = [f for f in bm.faces if f.select]
            mode = "FACE"
        else: # mastro block
            selection_set = [e for e in bm.edges if e.select]
            mode = "EDGE"

        for selection in selection_set:
            write_bmesh_storey_attribute(bm, selection, value, mode)
        bmesh.update_edit_mesh(obj.data)
        bm.free()
        
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')
            
    if active_object:
        bpy.context.view_layer.objects.active = active_object

# set the uses and relative heights for both masses and blocks
def set_attribute_mastro_mesh_uses(self, value):
    active_object = bpy.context.view_layer.objects.active
    selected_objects = bpy.context.selected_objects
    typology_name = bpy.context.scene.mastro_typology_names
    
    if len(selected_objects) == 0:
        selected_objects.append(active_object)

    for n in bpy.context.scene.mastro_typology_name_list:
        if n.name == typology_name:
            bpy.context.scene.mastro_attribute_mass_typology_id = n.id
            
            for obj in selected_objects:
                if obj is None:
                    continue
                if obj.type != "MESH": 
                    continue
                if "MaStro object" not in obj.data: 
                    continue
                if ("MaStro mass" not in obj.data and
                    "MaStro block" not in obj.data):
                    continue
                    
                bm = bmesh.from_edit_mesh(obj.data)
                
                if "MaStro mass" in obj.data:
                    selection_set = [f for f in bm.faces if f.select]
                    mode = "FACE"
                else: #mastro block
                    selection_set = [e for e in bm.edges if e.select]
                    mode = "EDGE"

                for selection in selection_set:
                    write_bmesh_use_attribute(bm, selection, value, mode)
                bmesh.update_edit_mesh(obj.data)
                bm.free()
                
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.object.mode_set(mode='EDIT')

            bpy.context.scene.mastro_typology_name_current[0].id = n.id
            bpy.context.scene.mastro_typology_name_current[0].name = typology_name
            
            if active_object:
                bpy.context.view_layer.objects.active = active_object
            break  
    
def set_attribute_mastro_block_depth(self, value):
    active_object = bpy.context.view_layer.objects.active
    selected_objects = bpy.context.selected_objects
    
    if len(selected_objects) == 0:
        selected_objects.append(active_object)
    
    for obj in selected_objects:
        if obj is None:
            continue
        if obj.type != "MESH": 
            continue
        if "MaStro object" not in obj.data: 
            continue
        if "MaStro block" not in obj.data:
            continue
        
        bm = bmesh.from_edit_mesh(obj.data)
        bMesh_block_depth = bm.edges.layers.float["mastro_block_depth"]
        
        selection_set = [e for e in bm.edges if e.select]
        
        for selection in selection_set:
            selection[bMesh_block_depth] = value

        bmesh.update_edit_mesh(obj.data)
        bm.free()
        
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')
        
    if active_object:
        bpy.context.view_layer.objects.active = active_object
    
    

# read attributes for both masses and blocks            
def get_attribute_mastro_mesh(self, bm_layer):
    point_only_attributes = [("mastro_side_angle","FLOAT"),
                             ("mastro_custom_vert","FLOAT")]
    
    edge_only_attributes = [("mastro_block_depth","FLOAT"),
                            ("mastro_inverted_normal","BOOL"),
                            ("mastro_custom_edge","FLOAT")]
    
    face_only_attributes = [("mastro_custom_face","FLOAT")]
    
    
    obj = bpy.context.view_layer.objects.active
    
    if (obj.type == "MESH" and 
        obj.mode == "EDIT" and
        "MaStro object" in obj.data and
        ("MaStro mass" in obj.data or
        "MaStro block" in obj.data)):
        
        bm = bmesh.from_edit_mesh(obj.data)
        
        attribute_map = ({name: ("verts", type)  for name, type in point_only_attributes} | 
                         {name: ("edges", type) for name, type in edge_only_attributes} | 
                         {name: ("faces", type) for name, type in face_only_attributes}
        ) 
        
        if bm_layer in attribute_map:
            field_name, type = attribute_map[bm_layer]
            field = getattr(bm, field_name)
            if type == "FLOAT":
                layer = field.layers.float[bm_layer]
            else:
                layer = field.layers.bool[bm_layer]
        # if the above is false, it means that the bm_layer can be either
        # an edge or a face layer, accordingly to the mastro type (block, or mass)
        elif "MaStro mass" in obj.data:
            field = bm.faces
            layer = field.layers.int[bm_layer]
        else: # mastro block
            field = bm.edges
            layer = field.layers.int[f"{bm_layer}_EDGE"]

        if layer:
            for el in field:
                if el.select:
                    bm.free()
                    return el[layer]
        bm.free()
    return 0

