import bpy

def overlay_bmesh_uses(bm, selection, value, mode):
    if mode == "FACE": # mastro mass
        # bMesh_typology     = bm.faces.layers.int["mastro_typology_id"]
        bMesh_use_list_A   = bm.faces.layers.int["mastro_list_use_id_A"]
        bMesh_use_list_B   = bm.faces.layers.int["mastro_list_use_id_B"]
        # bMesh_height_A     = bm.faces.layers.int["mastro_list_height_A"]
        # bMesh_height_B     = bm.faces.layers.int["mastro_list_height_B"]
        # bMesh_height_C     = bm.faces.layers.int["mastro_list_height_C"]
        # bMesh_height_D     = bm.faces.layers.int["mastro_list_height_D"]
        # bMesh_height_E     = bm.faces.layers.int["mastro_list_height_E"]
        bMesh_storeys      = bm.faces.layers.int["mastro_number_of_storeys"]
        bMesh_storey_list_A = bm.faces.layers.int["mastro_list_storey_A"]
        bMesh_storey_list_B = bm.faces.layers.int["mastro_list_storey_B"]
        bmesh_overlay_top    = bm.faces.layers.int["mastro_overlay_top"]
    else: # mastro block
        # bMesh_typology     = bm.edges.layers.int["mastro_typology_id_EDGE"]
        bMesh_use_list_A   = bm.edges.layers.int["mastro_list_use_id_A_EDGE"]
        bMesh_use_list_B   = bm.edges.layers.int["mastro_list_use_id_B_EDGE"]
        # bMesh_height_A     = bm.edges.layers.int["mastro_list_height_A_EDGE"]
        # bMesh_height_B     = bm.edges.layers.int["mastro_list_height_B_EDGE"]
        # bMesh_height_C     = bm.edges.layers.int["mastro_list_height_C_EDGE"]
        # bMesh_height_D     = bm.edges.layers.int["mastro_list_height_D_EDGE"]
        # bMesh_height_E     = bm.edges.layers.int["mastro_list_height_E_EDGE"]
        bMesh_storeys      = bm.edges.layers.int["mastro_number_of_storeys_EDGE"]
        bMesh_storey_list_A = bm.edges.layers.int["mastro_list_storey_A_EDGE"]
        bMesh_storey_list_B = bm.edges.layers.int["mastro_list_storey_B_EDGE"]
        bmesh_overlay_top   = bm.edges.layers.int["mastro_overlay_top_EDGE"]
    
    selection[bmesh_overlay_top] = value
    
    liquid_count = 0
    # count how many liquid uses there are, if any
    use_id_list_A = str(selection[bMesh_use_list_A])[1:]
    use_id_list_B = str(selection[bMesh_use_list_B])[1:]
    uses = [a + b for a, b in zip(use_id_list_A, use_id_list_B)]
    
    list_of_uses = bpy.context.scene.mastro_use_name_list
    liquid_ids = {item.id for item in list_of_uses if getattr(item, "liquid", False)}
    liquid_count = sum(1 for use in uses if int(use) in liquid_ids)
    
    if liquid_count >0:
        storey_left = value
        storey_list_A = str(selection[bMesh_storey_list_A])[1:]
        storey_list_B = str(selection[bMesh_storey_list_B])[1:]
        bMesh_storeys = [int(a + b) for a, b in zip(storey_list_A, storey_list_B)]
        
        # reverse the lists since we need to start from the top
        bMesh_storeys.reverse()
        storey_list_A = storey_list_A[::-1]
        storey_list_B = storey_list_B[::-1]
        uses.reverse()
        for index, use in enumerate(uses):
            use_id = int(use)
            storeys_per_use = bMesh_storeys[index]
            if use_id in liquid_ids:
                is_liquid = True
            else:
                is_liquid = False
            if not is_liquid:
                if storeys_per_use > storey_left:
                    updated_storeys = storeys_per_use - storey_left
                    if updated_storeys < 10:
                        updated_storeys = "0" + str(updated_storeys)
                    else:
                        updated_storeys = str(updated_storeys)
                    storey_list_A = storey_list_A[:index] + updated_storeys[0] + storey_list_A[index+1:]
                    storey_list_B = storey_list_B[:index] + updated_storeys[1] + storey_list_B[index+1:]
                    
                    storey_list_A += "1"
                    storey_list_B += "1"
                    storey_list_A = storey_list_A[::-1]
                    storey_list_B = storey_list_B[::-1]
                    selection[bMesh_storey_list_A] = int(storey_list_A)
                    selection[bMesh_storey_list_B] = int(storey_list_B)
                    
                    update_liquid_storeys()
                    return
                    
                    
                    
    
def update_liquid_storeys():
    pass

