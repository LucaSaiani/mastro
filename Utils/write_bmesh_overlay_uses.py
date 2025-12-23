import bpy
# from .read_write_bmesh_storey_attribute import write_bmesh_storey_attribute
from .read_write_bmesh_use_attribute import write_bmesh_use_attribute

def overlay_bmesh_uses(bm, selection, value, mode):
    if mode == "FACE":
        bMesh_typology     = bm.faces.layers.int["mastro_typology_id"]
        bmesh_overlay_top    = bm.faces.layers.int["mastro_overlay_top"]
    else:
        bMesh_typology     = bm.faces.layers.int["mastro_typology_id_EDGE"]
        bmesh_overlay_top   = bm.edges.layers.int["mastro_overlay_top_EDGE"]
    
    typology_id = selection[bMesh_typology]
    list_of_layers = write_bmesh_use_attribute(bm, selection, typology_id, mode)
        
    storey_list_A = list_of_layers["storey_list_A"]
    storey_list_B = list_of_layers["storey_list_B"]
    use_id_list_A = list_of_layers["use_id_list_A"]
    use_id_list_B = list_of_layers["use_id_list_B"]
    
    selection[bmesh_overlay_top] = value
    
    if value > 0:
        # count how many liquid uses there are, if any
        use_id_list_A = str(use_id_list_A)[1:]
        use_id_list_B = str(use_id_list_B)[1:]
        uses = [a + b for a, b in zip(use_id_list_A, use_id_list_B)]
        
        list_of_uses = bpy.context.scene.mastro_use_name_list
        liquid_ids = [item.id for item in list_of_uses if getattr(item, "liquid", False)]
        liquid_count = sum(1 for use in uses if int(use) in liquid_ids)
        
        if liquid_count > 0:
            storeys_left = value
            removed_storeys = 0
            updated_storeys_per_use = 0
            storey_list_A = str(storey_list_A)[1:]
            storey_list_B = str(storey_list_B)[1:]
            bMesh_storeys = [int(a + b) for a, b in zip(storey_list_A, storey_list_B)]
            
            # reverse the lists since we need to start from the top
            bMesh_storeys.reverse()
            storey_list_A = storey_list_A[::-1]
            storey_list_B = storey_list_B[::-1]
            uses.reverse()
            uses_to_remove = []
            for index, use in enumerate(uses):
                use_id = int(use)
                storeys_per_use = bMesh_storeys[index]
                
                if use_id in liquid_ids:
                    is_liquid = True
                else:
                    is_liquid = False
                
                if not is_liquid:
                    if storeys_per_use >= storeys_left:
                        updated_storeys_per_use = storeys_per_use - storeys_left
                        removed_storeys = removed_storeys + storeys_left
                        if storeys_per_use == storeys_left:
                            uses_to_remove.append(use)
                        override_uses(bm, 
                                      selection, 
                                      mode,
                                      uses_to_remove, 
                                      updated_storeys_per_use, 
                                      liquid_ids, 
                                      removed_storeys)
                        return
                    else:
                        uses_to_remove.append(use)
                        storeys_left = storeys_left - storeys_per_use
                        removed_storeys = removed_storeys + storeys_per_use
                if is_liquid:
                    override_uses(bm, 
                                  selection, 
                                  mode, 
                                  uses_to_remove, 
                                  updated_storeys_per_use, 
                                  liquid_ids, 
                                  removed_storeys)
                    return
                    
def override_uses(bm, selection, mode, uses_to_remove, updated_storeys_per_use, liquid_ids, removed_storeys):
    if mode == "FACE": # mastro mass
        bm.faces.ensure_lookup_table()
        bMesh_storey_list_A = bm.faces.layers.int["mastro_list_storey_A"]
        bMesh_storey_list_B = bm.faces.layers.int["mastro_list_storey_B"]
        bMesh_use_list_A   = bm.faces.layers.int["mastro_list_use_id_A"]
        bMesh_use_list_B   = bm.faces.layers.int["mastro_list_use_id_B"]
        bMesh_height_A     = bm.faces.layers.int["mastro_list_height_A"]
        bMesh_height_B     = bm.faces.layers.int["mastro_list_height_B"]
        bMesh_height_C     = bm.faces.layers.int["mastro_list_height_C"]
        bMesh_height_D     = bm.faces.layers.int["mastro_list_height_D"]
        bMesh_height_E     = bm.faces.layers.int["mastro_list_height_E"]
    else: # mastro block
        bm.edges.ensure_lookp_table()
        bMesh_storey_list_A = bm.edges.layers.int["mastro_list_storey_A_EDGE"]
        bMesh_storey_list_B = bm.edges.layers.int["mastro_list_storey_B_EDGE"]
        bMesh_use_list_A   = bm.edges.layers.int["mastro_list_use_id_A_EDGE"]
        bMesh_use_list_B   = bm.edges.layers.int["mastro_list_use_id_B_EDGE"]
        bMesh_height_A     = bm.edges.layers.int["mastro_list_height_A_EDGE"]
        bMesh_height_B     = bm.edges.layers.int["mastro_list_height_B_EDGE"]
        bMesh_height_C     = bm.edges.layers.int["mastro_list_height_C_EDGE"]
        bMesh_height_D     = bm.edges.layers.int["mastro_list_height_D_EDGE"]
        bMesh_height_E     = bm.edges.layers.int["mastro_list_height_E_EDGE"]

    use_list_A = str(selection[bMesh_use_list_A])
    use_list_B = str(selection[bMesh_use_list_B])
    height_A = str(selection[bMesh_height_A])
    height_B = str(selection[bMesh_height_B])
    height_C = str(selection[bMesh_height_C])
    height_D = str(selection[bMesh_height_D])
    height_E = str(selection[bMesh_height_E])
    storey_list_A = str(selection[bMesh_storey_list_A])
    storey_list_B = str(selection[bMesh_storey_list_B])

    uses = [a + b for a, b in zip(use_list_A, use_list_B)]

    # update the liquid storeys list
    for index, use in enumerate(uses):
        use_id = int(use)
        if use_id == liquid_ids[0]:
            liquid_storeys_A = storey_list_A[index]
            liquid_storeys_B = storey_list_B[index]
            liquid_storeys = int(liquid_storeys_A + liquid_storeys_B)
            liquid_storeys += removed_storeys
            if liquid_storeys > 9:
                new_storeys = str(liquid_storeys)
            else:
                new_storeys = "0" + str(liquid_storeys)
            storey_list_A = storey_list_A[:index] + new_storeys[0] + storey_list_A[index+1:]
            storey_list_B = storey_list_B[:index] + new_storeys[1] + storey_list_B[index+1:]
            break

    # remove the unnecessary uses and related data
    number_of_uses = len(uses_to_remove)
    if number_of_uses > 0:
        selection[bMesh_use_list_A] = int(use_list_A[:-number_of_uses])
        selection[bMesh_use_list_B] = int(use_list_B[:-number_of_uses])
        selection[bMesh_height_A] = int(height_A[:-number_of_uses])
        selection[bMesh_height_B] = int(height_B[:-number_of_uses])
        selection[bMesh_height_C] = int(height_C[:-number_of_uses])
        selection[bMesh_height_D] = int(height_D[:-number_of_uses])
        selection[bMesh_height_E] = int(height_E[:-number_of_uses])
        selection[bMesh_storey_list_A] = int(storey_list_A[:-number_of_uses])
        selection[bMesh_storey_list_B] = int(storey_list_B[:-number_of_uses])
    else:
        # still need to update the number of storeys
        selection[bMesh_storey_list_A] = int(storey_list_A)
        selection[bMesh_storey_list_B] = int(storey_list_B)

    # update the number of storeys of the use, if any
    if updated_storeys_per_use > 0:
        if updated_storeys_per_use > 9:
            new_storey_value = str(updated_storeys_per_use)
        else:
            new_storey_value = "0" + str(updated_storeys_per_use)
        
        list_A = str(selection[bMesh_storey_list_A])[:-1] + new_storey_value[0]
        list_B = str(selection[bMesh_storey_list_B])[:-1] + new_storey_value[1]
        selection[bMesh_storey_list_A] = int(list_A)
        selection[bMesh_storey_list_B] = int(list_B)
