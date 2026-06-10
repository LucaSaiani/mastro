import bpy
import math

def write_bmesh_storey_attribute(bm, selection, numberOfStoreys, mode):
    """Compute and write storey distribution for `selection` to the bmesh layers."""
    if mode == "FACE": # mastro mass
        field = bm.faces
        suffix = ""
    else: # mastro block
        field = bm.edges
        suffix = "_EDGE"
    
    bm_storeys = field.layers.int[f"mastro_number_of_storeys{suffix}"]
    bm_storey_list_A = field.layers.int[f"mastro_list_storey_A{suffix}"]
    bm_storey_list_B = field.layers.int[f"mastro_list_storey_B{suffix}"]
    bm_typology = field.layers.int[f"mastro_typology_id{suffix}"]
    
    typology_id = selection[bm_typology]
    
    data = read_bmesh_storey_attribute(numberOfStoreys, typology_id)

    # --- writing to bmesh ---
    selection[bm_storeys] = data["numberOfStoreys"]
    selection[bm_storey_list_A] = data["storey_list_A"]
    selection[bm_storey_list_B] = data["storey_list_B"]
    
    return data
    

def read_bmesh_storey_attribute(numberOfStoreys, typology_id):
    """Compute storey distribution for the given typology and total storey count.

    Uses marked as "liquid" fill the remaining floors after fixed uses are placed,
    distributed as evenly as possible (any remainder goes to the last liquid use).
    If the requested storey count is less than the typology minimum, top uses are
    clipped until the count fits.

    Returns a dict: {numberOfStoreys, storey_list_A, storey_list_B}.
    """
    projectUses = bpy.context.scene.mastro_use_name_list
    
    # number of storeys
    if numberOfStoreys == 0:
        numberOfStoreys = 1
    numberOfWantedStoreys = numberOfStoreys
    
    # --- Find the typology item safely (cannot rely on list index) ---
    item = next((i for i in bpy.context.scene.mastro_typology_name_list if i["id"] == typology_id), None)
    if item is None:
        return
    use_list = item.useList
    useSplit = [el for el in use_list.split(";") if el.strip()]
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
   