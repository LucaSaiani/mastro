import bpy
import math

def write_bmesh_storey_attribute(bm, selection, numberOfStoreys, mode):
    if mode == "FACE": # mastro mass
        bMesh_storeys = bm.faces.layers.int["mastro_number_of_storeys"]
        bMesh_storey_list_A = bm.faces.layers.int["mastro_list_storey_A"]
        bMesh_storey_list_B = bm.faces.layers.int["mastro_list_storey_B"]
        bMesh_typology = bm.faces.layers.int["mastro_typology_id"]
    else: # mastro block
        bMesh_storeys = bm.edges.layers.int["mastro_number_of_storeys_EDGE"]
        bMesh_storey_list_A = bm.edges.layers.int["mastro_list_storey_A_EDGE"]
        bMesh_storey_list_B = bm.edges.layers.int["mastro_list_storey_B_EDGE"]
        bMesh_typology = bm.edges.layers.int["mastro_typology_id_EDGE"]
    
    typology_id = selection[bMesh_typology]
    
    data = read_bmesh_storey_attribute(numberOfStoreys, typology_id)

    # --- writing to bmesh ---
    selection[bMesh_storeys] = data["numberOfStoreys"]
    selection[bMesh_storey_list_A] = data["storey_list_A"]
    selection[bMesh_storey_list_B] = data["storey_list_B"]
    

def read_bmesh_storey_attribute(numberOfStoreys, typology_id):
    projectUses = bpy.context.scene.mastro_use_name_list
    
    # number of storeys
    if numberOfStoreys == 0:
        numberOfStoreys = 1
    numberOfWantedStoreys = numberOfStoreys
    
    # --- Find the typology item safely (cannot rely on list index) ---
    item = next(i for i in bpy.context.scene.mastro_typology_name_list if i["id"] == typology_id)
    use_list = item.useList
    useSplit = use_list.split(";")
    useSplit.reverse()  # uses listed top-to-bottom in UI
    
    # --- Init values ---
    storey_list_A = "1"
    storey_list_B = "1"
    liquidPosition = []
    fixedStoreys = 0
    
    # --- Build storey lists ---
    for enum, el in enumerate(useSplit):
        for use in projectUses:
            if use.id == int(el):
                if use.liquid:
                    storeys = "00"
                    liquidPosition.append(enum)
                else:
                    fixedStoreys += use.storeys
                    storeys = f"{use.storeys:02d}"
                storey_list_A += storeys[0]
                storey_list_B += storeys[1]
                break
            
    # --- Adjust storeys for "liquid" uses ---
    storeyCheck = numberOfStoreys - fixedStoreys - len(liquidPosition)
    if storeyCheck < 1:
        numberOfStoreys = fixedStoreys + len(liquidPosition)
    storeyLeft = numberOfStoreys - fixedStoreys

    if liquidPosition:
        storey_list_A = storey_list_A[1:]
        storey_list_B = storey_list_B[1:]

        n = storeyLeft / len(liquidPosition)
        liquidStoreyNumber = math.floor(n)
        insert = f"{liquidStoreyNumber:02d}"

        for idx, el in enumerate(liquidPosition):
            ins = insert
            if idx == len(liquidPosition) - 1 and math.modf(n)[0] > 0:
                ins = f"{liquidStoreyNumber + 1:02d}"
            storey_list_A = storey_list_A[:el] + ins[0] + storey_list_A[el + 1:]
            storey_list_B = storey_list_B[:el] + ins[1] + storey_list_B[el + 1:]

        storey_list_A = "1" + storey_list_A
        storey_list_B = "1" + storey_list_B
        
    # --- Clipping logic (always active) ---
    if numberOfWantedStoreys < numberOfStoreys:
        storey_list_A = list(storey_list_A)
        storey_list_B = list(storey_list_B)
        storeyDifference = numberOfStoreys - numberOfWantedStoreys
        numberOfUses = len(storey_list_A) - 1
        index_iter = numberOfUses

        while index_iter >= 0:
            currentStoreys = int(storey_list_A[index_iter]) * 10 + int(storey_list_B[index_iter])
            difference = currentStoreys - storeyDifference
            if difference > 0:
                new_val = f"{difference:02d}"
                storey_list_A[index_iter] = new_val[0]
                storey_list_B[index_iter] = new_val[1]
                break
            else:
                storey_list_A = storey_list_A[:-1]
                storey_list_B = storey_list_B[:-1]
                storeyDifference = abs(difference)
                if difference == 0:
                    break
            index_iter -= 1

        storey_list_A = "".join(storey_list_A)
        storey_list_B = "".join(storey_list_B)
        numberOfStoreys = numberOfWantedStoreys
    
    # --- Output ---
    return {
        "numberOfStoreys": int(numberOfStoreys),
        "storey_list_A": int(storey_list_A),
        "storey_list_B": int(storey_list_B)
    }
   