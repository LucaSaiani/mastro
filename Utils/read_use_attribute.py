# function to update the uses and their relative heights accordingly to the assigned typologySet:
# if the function is run by the user when in edit mode the typologyId is read from 
# context.scene.attribute_mass_typology_id, else the typology is updated from the
# typology panel and the typologyId used is the one stored in the face
# def read_mesh_attributes_uses(context, mesh, faceIndex, typologySet=None):
def read_use_attribute(context, typologySet=None):
    if typologySet == None:
        typology_id = context.scene.attribute_mass_typology_id
    else:
      typology_id = typologySet
    projectUses = context.scene.mastro_use_name_list
    # since it is possible to sort typologies in the ui, it can be that the index of the element
    # in the list doesn't correspond to typology_id. Therefore it is necessary to find elements
    # in the way below and not with use_list = bpy.context.scene.mastro_typology_name_list[typology_id].useList
    item = next(i for i in context.scene.mastro_typology_name_list if i["id"] == typology_id)
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
    void = "1"
    
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
                void += str(int(use.void))
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
            "void" : int(void)
            }
    return data