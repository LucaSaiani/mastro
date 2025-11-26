import bpy
import bmesh

from ..Utils.read_write_bmesh_use_attribute import write_bmesh_use_attribute
from ..Utils.read_write_bmesh_storey_attribute import write_bmesh_storey_attribute

# Function to update the attributes that
# masses and blocks have in common
def update_bmesh_attributes(self, attribute_to_update):
    objects = bpy.data.objects
    for obj in objects:
        if obj is None:
            continue
        if obj.type != "MESH": 
            continue
        if "MaStro object" not in obj.data: 
            continue
        if ("MaStro mass" not in obj.data and
            "MaStro block" not in obj.data):
            continue
        
        mesh = obj.data
        object_mode = obj.mode
        
        if object_mode == "EDIT":
            bm = bmesh.from_edit_mesh(obj.data)
        else:
            bm = bmesh.new()
            bm.from_mesh(mesh)
        
        
        if "MaStro mass" in obj.data:
            mode = "FACE"
            field = bm.faces
            bMesh_typology = field.layers.int["mastro_typology_id"]
            bMesh_storeys = field.layers.int["mastro_number_of_storeys"]
            
        else:
            mode="EGDE"
            field = bm.edges
            bMesh_typology = field.layers.int["mastro_typology_id_EDGE"]
            bMesh_storeys = field.layers.int["mastro_number_of_storeys_EDGE"]
        
        for selection in field:
            if attribute_to_update == "all":
                typology_id = selection[bMesh_typology]
                write_bmesh_use_attribute(bm, selection, typology_id, mode)
            elif attribute_to_update == "floor_to_floor":
                typology_id = selection[bMesh_typology]
                write_bmesh_use_attribute(bm, selection, typology_id, mode)
            elif attribute_to_update == "number_of_storeys":
                numberOfStoreys = selection[bMesh_storeys]
                write_bmesh_storey_attribute(bm, selection, numberOfStoreys, mode)

        if object_mode == "EDIT":
            bmesh.update_edit_mesh(mesh)
        else:
            bm.to_mesh(mesh)
            
        bm.free
        
