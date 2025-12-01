import bpy

from .read_write_bmesh_storey_attribute import write_bmesh_storey_attribute

def write_bmesh_use_attribute(bm, selection, value, mode):
    data = read_bmesh_use_attribute(value)
    
    if mode == "FACE": # mastro mass
        bMesh_typology     = bm.faces.layers.int["mastro_typology_id"]
        bMesh_use_list_A   = bm.faces.layers.int["mastro_list_use_id_A"]
        bMesh_use_list_B   = bm.faces.layers.int["mastro_list_use_id_B"]
        bMesh_height_A     = bm.faces.layers.int["mastro_list_height_A"]
        bMesh_height_B     = bm.faces.layers.int["mastro_list_height_B"]
        bMesh_height_C     = bm.faces.layers.int["mastro_list_height_C"]
        bMesh_height_D     = bm.faces.layers.int["mastro_list_height_D"]
        bMesh_height_E     = bm.faces.layers.int["mastro_list_height_E"]
        bMesh_void         = bm.faces.layers.int["mastro_list_void"]
        bMesh_storeys      = bm.faces.layers.int["mastro_number_of_storeys"]
    else: # mastro block
        bMesh_typology     = bm.edges.layers.int["mastro_typology_id_EDGE"]
        bMesh_use_list_A   = bm.edges.layers.int["mastro_list_use_id_A_EDGE"]
        bMesh_use_list_B   = bm.edges.layers.int["mastro_list_use_id_B_EDGE"]
        bMesh_height_A     = bm.edges.layers.int["mastro_list_height_A_EDGE"]
        bMesh_height_B     = bm.edges.layers.int["mastro_list_height_B_EDGE"]
        bMesh_height_C     = bm.edges.layers.int["mastro_list_height_C_EDGE"]
        bMesh_height_D     = bm.edges.layers.int["mastro_list_height_D_EDGE"]
        bMesh_height_E     = bm.edges.layers.int["mastro_list_height_E_EDGE"]
        bMesh_void         = bm.edges.layers.int["mastro_list_void_EDGE"]
        bMesh_storeys      = bm.edges.layers.int["mastro_number_of_storeys_EDGE"]

     # --- writing to bmesh ---
    selection[bMesh_typology] = data["typology_id"]
    selection[bMesh_use_list_A] = data["use_id_list_A"]
    selection[bMesh_use_list_B] = data["use_id_list_B"]
    selection[bMesh_height_A] = data["height_A"]
    selection[bMesh_height_B] = data["height_B"]
    selection[bMesh_height_C] = data["height_C"]
    selection[bMesh_height_D] = data["height_D"]
    selection[bMesh_height_E] = data["height_E"]
    selection[bMesh_void] = data["void"]
    
    numberOfStoreys = selection[bMesh_storeys]
    write_bmesh_storey_attribute(bm, selection, numberOfStoreys, mode)
    
def read_bmesh_use_attribute(typology_id):
    projectUses = bpy.context.scene.mastro_use_name_list
    # since it is possible to sort typologies in the ui, it can be that the index of the element
    # in the list doesn't correspond to typology_id. Therefore it is necessary to find elements
    # in the way below and not with use_list = bpy.context.scene.mastro_typology_name_list[typology_id].useList
    item = next(i for i in bpy.context.scene.mastro_typology_name_list if i["id"] == typology_id)
    use_list = item.useList
    # uses are listed top to bottom, but they need to
    # be added bottom to top           
    useSplit = use_list.split(";")            
    useSplit.reverse() 
    
    use_id_list_A = "1"
    use_id_list_B = "1"
    height_A = "1"
    height_B = "1"
    height_C = "1"
    height_D = "1"
    height_E = "1"
    void = 0
    
    for enum, el in enumerate(useSplit):
        ### list_use_id
        if int(el) < 10:
            tmpUse = "0" + el
        else:
            tmpUse = el
        use_id_list_A += tmpUse[0]
        use_id_list_B += tmpUse[1]
                                        
        ###setting the values for each use
        for use in projectUses:
            if use.id == int(el):
                
                # void += str(int(use.void))
                
                #### floor to floor height for each use, stored in A, B, C, ...
                #### due to the fact that arrays can't be used
                #### and array like (3.555, 12.664, 0.123)
                #### is saved as
                #### A (1010) tens
                #### B (1320) units
                #### C (1561) first decimal
                #### D (1562) second decimal
                #### E (1543) third decimal
                #### each array starting with 1 since a number can't start with 0
                height = str(round(use.floorToFloor,3))
                if use.floorToFloor < 10:
                    height = "0" + height
                height_A += height[0]
                height_B += height[1]
                try:
                    height_C += height[3]
                    try:
                        height_D += height[4]
                        try:
                            height_E += height[5]
                        except:
                            height_E += "0"
                    except:
                        height_D += "0"
                        height_E += "0"
                except:
                    height_C += "0"
                    height_D += "0"
                    height_E += "0"
                break
            
    data = {"typology_id" : typology_id,
            "use_id_list_A" : int(use_id_list_A),
            "use_id_list_B" : int(use_id_list_B),
            "height_A" : int(height_A),
            "height_B" : int(height_B),
            "height_C" : int(height_C),
            "height_D" : int(height_D),
            "height_E" : int(height_E),
            "void" :void
            }
    
    return data
    
    

    