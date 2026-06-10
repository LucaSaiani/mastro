import bpy

from .read_write_bmesh_storey_attribute import write_bmesh_storey_attribute

def write_bmesh_use_attribute(bm, selection, value, mode):
    data = read_bmesh_use_attribute(value)
    
    if mode == "FACE": # mastro mass
        field = bm.faces
        suffix = ""
        
    else: # mastro block
        field = bm.edges
        suffix = "_EDGE"

    bm_typology     = field.layers.int[f"mastro_typology_id{suffix}"]
    bm_use_list_A   = field.layers.int[f"mastro_list_use_id_A{suffix}"]
    bm_use_list_B   = field.layers.int[f"mastro_list_use_id_B{suffix}"]
    bm_height_A     = field.layers.int[f"mastro_list_height_A{suffix}"]
    bm_height_B     = field.layers.int[f"mastro_list_height_B{suffix}"]
    bm_height_C     = field.layers.int[f"mastro_list_height_C{suffix}"]
    bm_height_D     = field.layers.int[f"mastro_list_height_D{suffix}"]
    bm_height_E     = field.layers.int[f"mastro_list_height_E{suffix}"]
    # bm_undercroft   = field.layers.int[f"mastro_undercroft{suffix}"]
    bm_storeys      = field.layers.int[f"mastro_number_of_storeys{suffix}"]

     # --- writing to bmesh ---
    selection[bm_typology] = data["typology_id"]
    selection[bm_use_list_A] = data["use_id_list_A"]
    selection[bm_use_list_B] = data["use_id_list_B"]
    selection[bm_height_A] = data["height_A"]
    selection[bm_height_B] = data["height_B"]
    selection[bm_height_C] = data["height_C"]
    selection[bm_height_D] = data["height_D"]
    selection[bm_height_E] = data["height_E"]
    # selection[bm_undercroft] = data["undercroft"]
    
    numberOfStoreys = selection[bm_storeys]
    data_storey = write_bmesh_storey_attribute(bm, selection, numberOfStoreys, mode)
    
    joined_data = {**data_storey, **data} 
    return(joined_data)
    
def read_bmesh_use_attribute(typology_id):
    projectUses = bpy.context.scene.mastro_use_name_list
    # since it is possible to sort typologies in the ui, it can be that the index of the element
    # in the list doesn't correspond to typology_id. Therefore it is necessary to find elements
    # in the way below and not with use_list = bpy.context.scene.mastro_typology_name_list[typology_id].useList
    item = next((i for i in bpy.context.scene.mastro_typology_name_list if i["id"] == typology_id), None)
    if item is None:
        return
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
    # undercroft = 0
    
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
                
                # undercroft += str(int(use.undercroft))
                
                # Heights are encoded as parallel digit strings (A–E) because GN attributes
                # don't support arrays. Each string holds one digit position of the value
                # across all uses, e.g. 3.555 → tens=3, units=5, dec1=5, dec2=5, dec3=5.
                # All strings are prefixed with "1" so they never start with a leading zero.
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
            # "undercroft" :undercroft
            }
    
    return data
    
    

    