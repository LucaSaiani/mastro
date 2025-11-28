import bpy
import bmesh

from .read_write_bmesh_storey_attribute import write_bmesh_storey_attribute
from .read_write_bmesh_use_attribute import write_bmesh_use_attribute

point_only_attributes = [("mastro_side_angle","FLOAT"),
                        ("mastro_custom_vert","FLOAT")]
    
edge_only_attributes = [("mastro_block_depth","FLOAT"),
                        ("mastro_inverted_normal","BOOL"),
                        ("mastro_custom_edge","FLOAT"),
                        ("mastro_wall_id","INT"),
                        ("mastro_wall_thickness","FLOAT"),
                        ("mastro_wall_offset", "FLOAT")]
    
face_only_attributes = [("mastro_custom_face","FLOAT"),
                        ("mastro_floor_id", "INT")]

attribute_map = {
    **{name: ("verts", typ) for name, typ in point_only_attributes},
    **{name: ("edges", typ) for name, typ in edge_only_attributes},
    **{name: ("faces", typ) for name, typ in face_only_attributes}
} 
 
layer_map = {
    "mastro_wall_id": ("edges", "INT", ("MaStro mass", "MaStro block")),
    "mastro_inverted_normal": ("edges", "BOOL", ("MaStro mass", "MaStro block")),
    "mastro_block_depth": ("edges", "FLOAT", "MaStro block"),
    "mastro_side_angle": ("verts", "FLOAT", "MaStro block"),
    "mastro_floor_id": ("faces", "INT", "MaStro mass"),
    "mastro_custom_vert": ("verts", "FLOAT", ("MaStro mass", "MaStro block")),
    "mastro_custom_edge": ("edges", "FLOAT", ("MaStro mass", "MaStro block")),
    "mastro_custom_face": ("faces", "FLOAT", ("MaStro mass", "MaStro block")),
}   

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
        
        try:
            if "MaStro mass" in obj.data:
                selection_set = [f for f in bm.faces if f.select]
                mode = "FACE"
            else: # mastro block
                selection_set = [e for e in bm.edges if e.select]
                mode = "EDGE"

            for selection in selection_set:
                write_bmesh_storey_attribute(bm, selection, value, mode)
            bmesh.update_edit_mesh(obj.data)
        finally:
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
    if len(selected_objects) == 0:
        selected_objects.append(active_object)

    typology_name = bpy.context.scene.mastro_typology_names
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
                try:
                    if "MaStro mass" in obj.data:
                        selection_set = [f for f in bm.faces if f.select]
                        mode = "FACE"
                    else: #mastro block
                        selection_set = [e for e in bm.edges if e.select]
                        mode = "EDGE"

                    for selection in selection_set:
                        write_bmesh_use_attribute(bm, selection, value, mode)
                    bmesh.update_edit_mesh(obj.data)
                finally:
                    bm.free()
                
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.object.mode_set(mode='EDIT')
            
            if active_object:
                bpy.context.view_layer.objects.active = active_object
            break  
        
def set_attribute_mastro_generic(value, bm_layer):
    if bm_layer in layer_map:
        field_name, type, mastro_types = layer_map[bm_layer]
                
        active_object = bpy.context.view_layer.objects.active
        selected_objects = bpy.context.selected_objects
        
        if len(selected_objects) == 0:
            selected_objects.append(active_object)
            
        for obj in selected_objects:
            if obj is None:
                continue
            if obj.type != "MESH": 
                continue
            if not any(t in obj.data for t in mastro_types):
                continue
            bm = bmesh.from_edit_mesh(obj.data)
            try:
                field = getattr(bm, field_name)
                if type == "FLOAT":
                    layer = field.layers.float[bm_layer]
                elif type == "INT":
                    layer = field.layers.int[bm_layer]
                else:
                    layer = field.layers.bool[bm_layer]
                if layer:
                    selection_set = [s for s in field if s.select]
                    for selection in selection_set:
                        selection[layer] = value
            finally:
                bm.free()
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.mode_set(mode='EDIT')
        
        if active_object:
            bpy.context.view_layer.objects.active = active_object
        
# read attributes for both masses and blocks at mesh level          
def get_attribute_mastro_mesh(self, bm_layer):
    obj = bpy.context.view_layer.objects.active
    
    if not (obj.type == "MESH" and 
            obj.mode == "EDIT" and 
            "MaStro object" in obj.data):
        return 0
    
    if not ("MaStro mass" in obj.data or 
            "MaStro block" in obj.data):
        return 0
        
    bm = bmesh.from_edit_mesh(obj.data)
    try:
        if bm_layer in attribute_map:
            field_name, type = attribute_map[bm_layer]
            field = getattr(bm, field_name)
            if type == "FLOAT":
                layer = field.layers.float[bm_layer]
            elif type == "INT":
                layer = field.layers.int[bm_layer]
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
    finally:
        bm.free()
    
    return 0


def set_attribute_mastro_block_depth(self, value):
    set_attribute_mastro_generic(value, "mastro_block_depth")
    
        
def set_attribute_mastro_block_side_angle(self, value):
    set_attribute_mastro_generic(value, "mastro_side_angle")
        
    
def set_attribute_mastro_wall_id(self, value):
    set_attribute_mastro_generic(value, "mastro_wall_id")
    
            
def set_attribute_mastro_wall_normal(self, value):
    set_attribute_mastro_generic(value, "mastro_inverted_normal")
    
            
def set_attribute_mastro_floor_id(self, value):
    set_attribute_mastro_generic(value, "mastro_floor_id")
        
def set_attribute_custom_vert(self, value):
    set_attribute_mastro_generic(value, "mastro_custom_vert")
    
def set_attribute_custom_edge(self, value):
    set_attribute_mastro_generic(value, "mastro_custom_edge")
    
def set_attribute_custom_face(self, value):
    set_attribute_mastro_generic(value, "mastro_custom_face")

##############################
# attributes at object level #
##############################

def set_attribute_mastro_object(value, attribute):
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
        
        if attribute ==  "block":
            obj.mastro_props['mastro_block_attribute'] = value

        elif attribute == "building":
            obj.mastro_props['mastro_building_attribute'] = value
        
    if active_object:
        bpy.context.view_layer.objects.active = active_object


# read attributes for both masses and blocks at object level  
def get_attribute_mastro_object(self, attribute):
    obj = bpy.context.view_layer.objects.active
    if not (obj.type == "MESH" and 
            obj.mode == "OBJECT" and 
            "MaStro object" in obj.data):
        return 0
    
    if not ("MaStro mass" in obj.data or 
            "MaStro block" in obj.data):
        return 0
    
    if attribute ==  "block":
        return obj.mastro_props['mastro_block_attribute']
    elif attribute == "building":
        return obj.mastro_props['mastro_building_attribute']
        
    return 0

def set_attribute_mastro_object_block(self, value):
    set_attribute_mastro_object(value, "block")

    
def set_attribute_mastro_object_building(self, value):
    set_attribute_mastro_object(value, "building")

