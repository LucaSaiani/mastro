import bpy 
import math 

block_attribute_set = [
            {
            "attr" :  "mastro_typology_id",
            "attr_type" :  "INT",
            "attr_domain" :  ("EDGE","FACE")
            },
            {
            "attr" :  "mastro_list_use_id_A",
            "attr_type" :  "INT",
            "attr_domain" :  ("EDGE","FACE")
            },
             {
            "attr" :  "mastro_list_use_id_B",
            "attr_type" :  "INT",
            "attr_domain" :  ("EDGE","FACE")
            },
            {
            "attr" :  "mastro_list_storey_A",
            "attr_type" :  "INT",
            "attr_domain" :  ("EDGE","FACE")
            },
            {
            "attr" :  "mastro_list_storey_B",
            "attr_type" :  "INT",
            "attr_domain" :  ("EDGE","FACE")
            },
            {
            "attr" :  "mastro_list_height_A",
            "attr_type" :  "INT",
            "attr_domain" :  ("EDGE","FACE")
            },
            {
            "attr" :  "mastro_list_height_B",
            "attr_type" :  "INT",
            "attr_domain" :  ("EDGE","FACE")
            },
            {
            "attr" :  "mastro_list_height_C",
            "attr_type" :  "INT",
            "attr_domain" :  ("EDGE","FACE")
            },
            {
            "attr" :  "mastro_list_height_D",
            "attr_type" :  "INT",
            "attr_domain" :  ("EDGE","FACE")
            },
            {
            "attr" :  "mastro_list_height_E",
            "attr_type" :  "INT",
            "attr_domain" :  ("EDGE","FACE")
            },
            {
            "attr" :  "mastro_list_void",
            "attr_type" :  "INT",
            "attr_domain" :  ("EDGE","FACE")
            },
            {
            "attr" :  "mastro_floor_id",
            "attr_type" :  "INT",
            "attr_domain" :  ("EDGE","FACE"),
            "attr_default" : 0
            },
            {
            "attr" :  "mastro_number_of_storeys",
            "attr_type" :  "INT",
            "attr_domain" :  ("EDGE","FACE"),
            "attr_default" : 1
            },
            {
            "attr" :  "mastro_block_depth",
            "attr_type" :  "FLOAT",
            "attr_domain" :  "EDGE",
            "attr_default" : 18
            },
            {
            "attr" :  "mastro_inverted_normal",
            "attr_type" :  "BOOLEAN",
            "attr_domain" :  "EDGE",
            "attr_default" : 0
            },
            {
            "attr" :  "mastro_side_angle",
            "attr_type" :  "FLOAT",
            "attr_domain" :  "POINT",
            "attr_default" : 0
            },
            {
            "attr" : "mastro_custom_vert",
            "attr_type" :  "FLOAT",
            "attr_domain" :  "POINT",
            "attr_default" : 0
            },
            {
            "attr" : "mastro_custom_edge",
            "attr_type" :  "FLOAT",
            "attr_domain" :  "EDGE",
            "attr_default" : 0
            },
            {
            "attr" : "mastro_custom_face",
            "attr_type" :  "FLOAT",
            "attr_domain" :  "FACE",
            "attr_default" : 0
            }
]

def add_block_attributes(obj):
    obj.mastro_props['mastro_block_attribute'] = 0
    obj.mastro_props['mastro_building_attribute'] = 0
    mesh = obj.data
    mesh["MaStro object"] = True
    mesh["MaStro block"] = True
    
    typology_id = bpy.context.scene.mastro_typology_name_list_index
    projectUses = bpy.context.scene.mastro_use_name_list
    
    use_list = bpy.context.scene.mastro_typology_name_list[typology_id].useList
    useSplit = use_list.split(";")

    use_id_list_A = "1"
    use_id_list_B = "1"
    storey_list_A = "1"
    storey_list_B = "1"
    height_A = "1"
    height_B = "1"
    height_C = "1"
    height_D = "1"
    height_E = "1"
    liquidPosition = []
    fixedStoreys = 0
    numberOfStoreys = 3 # default value for initial number of storeys
    void = 0
    
    for enum,el in enumerate(useSplit):
        if int(el) < 10:
            tmpUse = "0" + el
        else:
            tmpUse = str(el)
       
        # print(el[0], el[1])
        use_id_list_A += tmpUse[0]
        use_id_list_B += tmpUse[1]
        
        
            
        for use in projectUses:
            if use.id == int(el):
                # number of storeys for the use
                # if a use is "liquid" the number of storeys is set as 00
                if use.liquid: 
                    storeys = "00"
                    liquidPosition.append(enum)
                else:
                    fixedStoreys += use.storeys
                    storeys = str(use.storeys)
                    if use.storeys < 10:
                        storeys = "0" + storeys

                storey_list_A += storeys[0]
                storey_list_B += storeys[1]
                
                # void += str(int(use.void))
                
                height = str(round(use.floorToFloor,3))
                if use.floorToFloor < 10:
                    height = "0" + height
                height_A += height[0]
                height_B += height[1]
                try:
                    # height[3]
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
            
        storeyCheck = numberOfStoreys - fixedStoreys - len(liquidPosition)
        # if the typology has more storeys than the selected mass
        # some extra storeys are added
        if storeyCheck < 1: 
            bpy.context.scene.mastro_attribute_mass_storeys = fixedStoreys + len(liquidPosition)
        storeyLeft = numberOfStoreys - fixedStoreys
        
        # the 1 at the start of the number is removed
        storey_list_A = storey_list_A[1:]
        storey_list_B = storey_list_B[1:]  
        if len(liquidPosition) > 0:
            n = storeyLeft/len(liquidPosition)
            liquidStoreyNumber = math.floor(n)

            insert = str(liquidStoreyNumber)
            if liquidStoreyNumber < 10:
                insert = "0" + insert
                
            index = 0
            while index < len(liquidPosition):
                el = liquidPosition[index]
                # if the rounding of the liquid storeys is uneven,
                # the last liquid floor is increased of 1 storeyx
                if index == len(liquidPosition) -1 and  math.modf(n)[0] > 0:
                    insert = str(liquidStoreyNumber +1) 
                    if liquidStoreyNumber +1 < 10:
                        insert = "0" + insert

                storey_list_A = storey_list_A[:el] + insert[0] + storey_list_A[el +1:]
                storey_list_B = storey_list_B[:el] + insert[1] + storey_list_B[el +1:]
                # print("el", el)
                index += 1
        # the 1 is readded
        storey_list_A = "1" + storey_list_A  
        storey_list_B = "1" + storey_list_B
            
    for a in block_attribute_set:
        try:
            mesh.attributes[a["attr"]]
        except:
            if a["attr_domain"] is None: # to set custom attributes to the object, not to vertex, edge or face
                obj[a["attr"]] = a["attr_default"]
            else:
                if "POINT" in a["attr_domain"]:
                    vert_attr_name = a['attr']
                    mesh.attributes.new(name=vert_attr_name, type=a["attr_type"], domain="POINT")
                    attribute = mesh.attributes[vert_attr_name].data.items()
                    for vert in mesh.vertices:
                        index = vert.index
                        for mesh_attribute in attribute:
                            if mesh_attribute[0]  == index:
                                if a["attr"] == "mastro_side_angle":
                                    mesh_attribute[1].value = 0
                if "EDGE" in a['attr_domain']:
                    if "FACE" in a['attr_domain']:
                        edge_attr_name = f"{a['attr']}_EDGE"
                    else:
                        edge_attr_name = a['attr']
                    mesh.attributes.new(name=edge_attr_name, type=a["attr_type"], domain="EDGE")
                
                    attribute = mesh.attributes[edge_attr_name].data.items()
                    for edge in mesh.edges:
                        index = edge.index
                        for mesh_attribute in attribute:
                            if mesh_attribute[0]  == index:
                                if a["attr"] == "mastro_typology_id":
                                    mesh_attribute[1].value = bpy.context.scene.mastro_typology_name_list[typology_id].id
                                elif a["attr"] == "mastro_list_use_id_A": 
                                    mesh_attribute[1].value = int(use_id_list_A)
                                elif a["attr"] == "mastro_list_use_id_B": 
                                    mesh_attribute[1].value = int(use_id_list_B)
                                elif a["attr"] == "mastro_list_storey_A":
                                    mesh_attribute[1].value = int(storey_list_A)
                                elif a["attr"] == "mastro_list_storey_B":
                                    mesh_attribute[1].value = int(storey_list_B)
                                elif a["attr"] == "mastro_list_height_A":
                                    mesh_attribute[1].value = int(height_A)
                                elif a["attr"] == "mastro_list_height_B":
                                    mesh_attribute[1].value = int(height_B)
                                elif a["attr"] == "mastro_list_height_C":
                                    mesh_attribute[1].value = int(height_C)
                                elif a["attr"] == "mastro_list_height_D":
                                    mesh_attribute[1].value = int(height_D)
                                elif a["attr"] == "mastro_list_height_E":
                                    mesh_attribute[1].value = int(height_E)
                                elif a["attr"] == "mastro_list_void":
                                    mesh_attribute[1].value = void
                                else:
                                    mesh_attribute[1].value = a["attr_default"]
                                break
                if "FACE" in a['attr_domain']:
                    face_attr_name = a['attr']
                    mesh.attributes.new(name=face_attr_name, type=a["attr_type"], domain="FACE")