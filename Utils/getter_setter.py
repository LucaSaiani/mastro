import bpy
import bmesh

from .read_write_bmesh_storey_attribute import write_bmesh_storey_attribute
from .read_write_bmesh_use_attribute import write_bmesh_use_attribute

def set_attribute_mastro_mesh_storeys(self, value):
    active_object = bpy.context.view_layer.objects.active
    selected_objects = bpy.context.selected_objects

    if len(selected_objects) == 0:
        selected_objects.append(active_object)

    for obj in selected_objects:
        if (obj.type == "MESH" and 
                "MaStro object" in obj.data and
                ("MaStro mass" in obj.data or
                "MaStro block" in obj.data)):
            
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
                if (obj.type == "MESH" and 
                        "MaStro object" in obj.data and
                        ("MaStro mass" in obj.data or
                        "MaStro block" in obj.data)):
                    
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
    
            
def get_attribute_mastro_mesh(self, bm_layer):
    obj = bpy.context.view_layer.objects.active
    
    if (obj.type == "MESH" and 
        obj.mode == "EDIT" and
        "MaStro object" in obj.data and
        ("MaStro mass" in obj.data or
        "MaStro block" in obj.data)):
        
        bm = bmesh.from_edit_mesh(obj.data)
        if "MaStro mass" in obj.data:
            layer = bm.faces.layers.int[bm_layer]
            field = bm.faces
        else: # mastro block
            layer = bm.edges.layers.int[f"{bm_layer}_EDGE"]
            field = bm.edges

        if layer:
            for el in field:
                if el.select:
                    bm.free()
                    return el[layer]
        bm.free()
    return 0

