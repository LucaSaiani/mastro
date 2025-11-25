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
    
def read_storey_attribute():
    pass

# def read_storey_attribute(context, mesh, index, element_type="FACE", storeysSet=None):
#     """
#     Updates number of storeys for a mesh element (face or edge)
#     according to its assigned typology and project uses.

#     Args:
#         context: Blender context
#         mesh: mesh data
#         index: element index (face or edge)
#         element_type: "FACE" or "EDGE"
#         storeysSet: optional manual override of storey number
#     """
    
#     projectUses = context.scene.mastro_use_name_list

#     # --- Get typology ID depending on element type ---
#     if element_type.upper() == "EDGE":
#         if len(mesh.attributes["mastro_typology_id_EDGE"].data) > 0:
#             typology_id = mesh.attributes["mastro_typology_id_EDGE"].data[index].value
#         else:
#             typology_id = context.scene.mastro_typology_name_current[0].id
#     else:  # FACE
#         typology_id = mesh.attributes["mastro_typology_id"].data[index].value

#     # --- Get number of storeys ---
#     if storeysSet is None:
#         numberOfStoreys = context.scene.mastro_attribute_mass_storeys
#         if element_type.upper() == "EDGE" and numberOfStoreys == 0:
#             numberOfStoreys = 1
#     else:
#         numberOfStoreys = storeysSet

#     numberOfWantedStoreys = numberOfStoreys

#     # --- Find the typology item safely (cannot rely on list index) ---
#     item = next(i for i in context.scene.mastro_typology_name_list if i["id"] == typology_id)
#     use_list = item.useList
#     useSplit = use_list.split(";")
#     useSplit.reverse()  # uses listed top-to-bottom in UI

#     # --- Init values ---
#     storey_list_A = "1"
#     storey_list_B = "1"
#     liquidPosition = []
#     fixedStoreys = 0

#     # --- Build storey lists ---
#     for enum, el in enumerate(useSplit):
#         for use in projectUses:
#             if use.id == int(el):
#                 if use.liquid:
#                     storeys = "00"
#                     liquidPosition.append(enum)
#                 else:
#                     fixedStoreys += use.storeys
#                     storeys = f"{use.storeys:02d}"
#                 storey_list_A += storeys[0]
#                 storey_list_B += storeys[1]
#                 break

#     # --- Adjust storeys for "liquid" uses ---
#     storeyCheck = numberOfStoreys - fixedStoreys - len(liquidPosition)
#     if storeyCheck < 1:
#         numberOfStoreys = fixedStoreys + len(liquidPosition)
#     storeyLeft = numberOfStoreys - fixedStoreys

#     if liquidPosition:
#         storey_list_A = storey_list_A[1:]
#         storey_list_B = storey_list_B[1:]

#         n = storeyLeft / len(liquidPosition)
#         liquidStoreyNumber = math.floor(n)
#         insert = f"{liquidStoreyNumber:02d}"

#         for idx, el in enumerate(liquidPosition):
#             ins = insert
#             if idx == len(liquidPosition) - 1 and math.modf(n)[0] > 0:
#                 ins = f"{liquidStoreyNumber + 1:02d}"
#             storey_list_A = storey_list_A[:el] + ins[0] + storey_list_A[el + 1:]
#             storey_list_B = storey_list_B[:el] + ins[1] + storey_list_B[el + 1:]

#         storey_list_A = "1" + storey_list_A
#         storey_list_B = "1" + storey_list_B

#     # --- Clipping logic (always active) ---
#     if numberOfWantedStoreys < numberOfStoreys:
#         storey_list_A = list(storey_list_A)
#         storey_list_B = list(storey_list_B)
#         storeyDifference = numberOfStoreys - numberOfWantedStoreys
#         numberOfUses = len(storey_list_A) - 1
#         index_iter = numberOfUses

#         while index_iter >= 0:
#             currentStoreys = int(storey_list_A[index_iter]) * 10 + int(storey_list_B[index_iter])
#             difference = currentStoreys - storeyDifference
#             if difference > 0:
#                 new_val = f"{difference:02d}"
#                 storey_list_A[index_iter] = new_val[0]
#                 storey_list_B[index_iter] = new_val[1]
#                 break
#             else:
#                 storey_list_A = storey_list_A[:-1]
#                 storey_list_B = storey_list_B[:-1]
#                 storeyDifference = abs(difference)
#                 if difference == 0:
#                     break
#             index_iter -= 1

#         storey_list_A = "".join(storey_list_A)
#         storey_list_B = "".join(storey_list_B)
#         numberOfStoreys = numberOfWantedStoreys

#     # --- Output ---
#     return {
#         "numberOfStoreys": int(numberOfStoreys),
#         "storey_list_A": int(storey_list_A),
#         "storey_list_B": int(storey_list_B)
#     }


# import math

# '''Mass: function to update number of storeys accordingly to the assigned number of storeys'''
# def set_face_attribute_storeys(context, mesh, faceIndex, storeysSet = None):
#     typology_id = mesh.attributes["mastro_typology_id"].data[faceIndex].value
#     projectUses = context.scene.mastro_use_name_list
#     # if the function is run when the user updates the number of storeys,
#     # the number of storeys is read from context.scene.mastro_attribute_mass_storeys.
#     # Else the function is run because the user is updating the typology list and
#     # in this case the number of storeys used is the one stored in each face of the mesh
#     if storeysSet == None:
#         numberOfStoreys = context.scene.mastro_attribute_mass_storeys
#     else:
#         numberOfStoreys = storeysSet
#     numberOfWantedStoreys = numberOfStoreys
#     # since it is possible to sort typologies in the ui, it can be that the index of the element
#     # in the list doesn't correspond to typology_id. Therefore it is necessary to find elements
#     # in the way below and not with use_list = bpy.context.scene.mastro_typology_name_list[typology_id].useList
#     item = next(i for i in context.scene.mastro_typology_name_list if i["id"] == typology_id)
#     use_list = item.useList
#     # uses are listed top to bottom, but they need to
#     # be added bottom to top           
#     useSplit = use_list.split(";")            
#     useSplit.reverse() 
    
#     storey_list_A = "1"
#     storey_list_B = "1"
#     liquidPosition = [] # to count how many liquid uses they are
#     fixedStoreys = 0 # to count how many fixed storeys they are

    
#     for enum, el in enumerate(useSplit):
#         ###setting the values for each use
#         for use in projectUses:
            
#             if use.id == int(el):
#                 # number of storeys for the use
#                 # if a use is "liquid" the number of storeys is set as 00
#                 if use.liquid: 
#                     storeys = "00"
#                     liquidPosition.append(enum)
#                 else:
#                     fixedStoreys += use.storeys
#                     storeys = str(use.storeys)
#                     if use.storeys < 10:
#                         storeys = "0" + storeys
                        
#                 storey_list_A += storeys[0]
#                 storey_list_B += storeys[1]
#                 break

#     # liquid storeys need to be converted to actual storeys
#     storeyCheck = numberOfStoreys - fixedStoreys - len(liquidPosition)
#     # if the typology has more storeys than the selected mass
#     # some extra storeys are added
#     if storeyCheck < 1: 
#         numberOfStoreys = fixedStoreys + len(liquidPosition)
#     storeyLeft = numberOfStoreys - fixedStoreys

#     if len(liquidPosition) > 0:
#         # the 1 at the start of the number is removed
#         storey_list_A = storey_list_A[1:]
#         storey_list_B = storey_list_B[1:]
        
#         n = storeyLeft/len(liquidPosition)
#         liquidStoreyNumber = math.floor(n)

#         insert = str(liquidStoreyNumber)
#         if liquidStoreyNumber < 10:
#             insert = "0" + insert
            
#         index = 0
#         while index < len(liquidPosition):
#             el = liquidPosition[index]
#             # if the rounding of the liquid storeys is uneven,
#             # the last liquid floor is increased of 1 storey
#             if index == len(liquidPosition) -1 and  math.modf(n)[0] > 0:
#                 insert = str(liquidStoreyNumber +1) 
#                 if liquidStoreyNumber +1 < 10:
#                     insert = "0" + insert
                
#             storey_list_A = storey_list_A[:el] + insert[0] + storey_list_A[el +1:]
#             storey_list_B = storey_list_B[:el] + insert[1] + storey_list_B[el +1:]
#             index += 1
#         # the 1 is re-added  
#         storey_list_A = "1" + storey_list_A
#         storey_list_B = "1" + storey_list_B

#     # clip the number of storeys, removing some floors and uses, in case the number of storeys
#     # inserted are less than the ones needed for all the storeys (fixed+liquid)
#     if numberOfWantedStoreys < numberOfStoreys:
#         storey_list_A = list(storey_list_A)
#         storey_list_B = list(storey_list_B)
#         # reverse_A = storey_list_A[::-1]
#         # reverse_B = storey_list_B[::-1]
#         storeyDifference = numberOfStoreys - numberOfWantedStoreys
#         numberOfUses = len(storey_list_A) -1
#         index = numberOfUses
#         while index >= 0:
#             currentStoreys = int(storey_list_A[index]) * 10 + int(storey_list_B[index])
#             difference = currentStoreys - storeyDifference
#             # print("DIFFEREnce", difference, currentStoreys, storeyDifference)
#             if difference > 0:
#                 if difference < 10:
#                     storey_list_A[index] = "0"
#                     storey_list_B[index] = str(difference)
#                 else:
#                     storey_list_A[index] = str(difference[0])
#                     storey_list_B[index] = str(difference[1])
#                 break
#             else:
#                 storey_list_A = storey_list_A[:-1]
#                 storey_list_B = storey_list_B[:-1]
#                 storeyDifference = abs(difference)
#                 if difference == 0:
#                     break
#             index -= 1
#         storey_list_A = "".join(storey_list_A)
#         storey_list_B = "".join(storey_list_B)
#         numberOfStoreys = numberOfWantedStoreys
        
    
#     data = {"numberOfStoreys" : int(numberOfStoreys),
#             "storey_list_A" : int(storey_list_A),
#             "storey_list_B" : int(storey_list_B)
#             }
    
#     # print(data)
#     return data