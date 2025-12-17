import bpy
import bmesh

from ...Utils.read_write_bmesh_storey_attribute import read_bmesh_storey_attribute
from ...Utils.get_names_from_list import get_names_from_list

# Update the UIList in VIEW3D of uses of the selected face or edge 
def update_view3D_panels(scene):
    obj = bpy.context.active_object
    
    if obj is None:
        return
    if obj.type != "MESH":
        return
    if "MaStro object" not in obj.data:
        return

    if ("MaStro mass" in obj.data or
        "MaStro block" in obj.data):
        numberOfStoreys = scene.mastro_attribute_mass_storeys
        numberOfUndercroft = scene.mastro_attribute_mass_undercroft
        if numberOfUndercroft > numberOfStoreys:
            numberOfUndercroft = numberOfStoreys
        
        current_value = scene.mastro_typology_names
        enum_items = get_names_from_list(scene, bpy.context, "mastro_typology_name_list")
        typology_index = next(i for i, item in enumerate(enum_items) if item[0] == current_value)
        
        data = read_bmesh_storey_attribute(numberOfStoreys, typology_index)
        # typology name
        # since it is possible to sort typologies in the ui, it can be that the index of the element
        # in the list doesn't correspond to typology_id. Therefore it is necessary to find elements
        # in the way below and not with use_list = bpy.context.scene.mastro_typology_name_list[typology_id].useList
        item = next(i for i in bpy.context.scene.mastro_typology_name_list if i["id"] == typology_index)
        # bpy.context.scene.mastro_typology_name_current[0].name = item.name
                                    
        usesUiList = bpy.context.scene.mastro_obj_typology_uses_name_list 
        
        # clean the list
        while len(usesUiList) > 0:
            index = bpy.context.scene.mastro_obj_typology_uses_name_list_index
            usesUiList.remove(index)
            bpy.context.scene.mastro_obj_typology_uses_name_list_index = min(max(0, index - 1), len(usesUiList) - 1)
        
        # populate the list of uses
        use_list = item.useList
        
        
        list_storey_A = str(data["storey_list_A"])[1:]
        list_storey_B = str(data["storey_list_B"])[1:]
        
        
        mesh = obj.data
        if mesh.is_editmode:
            bm = bmesh.from_edit_mesh(mesh)
        else:
            bm = bmesh.new()
            bm.from_mesh(mesh)
       
        active = None
        
        if "MaStro mass" in obj.data:
            bm.faces.ensure_lookup_table()
            active_face_index = obj.data.polygons.active
            active = bm.faces[active_face_index]
            
            bMesh_typology     = bm.faces.layers.int["mastro_typology_id"]
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
            # bmesh_overlay_top    = bm.faces.layers.int["mastro_overlay_top"]
        else: # mastro block
            bm.edges.ensure_lookup_table()
            active_edge_index = obj.data.edges.active
            active = bm.edges[active_edge_index]
            
            bMesh_typology     = bm.edges.layers.int["mastro_typology_id_EDGE"]
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
            # bmesh_overlay_top   = bm.edges.layers.int["mastro_overlay_top_EDGE"]
   
        if active is not None:
            use_id_list_A = str(active[bMesh_use_list_A])[1:]
            use_id_list_B = str(active[bMesh_use_list_B])[1:]
            use_id_list = [a + b for a, b in zip(use_id_list_A, use_id_list_B)]
            use_list = ';'.join(str(int(x)) for x in use_id_list)
            use_list = use_list[::-1]
            list_storey_A = str(active[bMesh_storey_list_A])[1:]
            list_storey_B = str(active[bMesh_storey_list_B])[1:]
            
            bm.free()
            
            if numberOfUndercroft > 0:
                reversed_use_list = use_list[::-1].split(";")
                undercroft_levels = numberOfUndercroft
                index_to_insert = None
                index_to_stop = None
                for enum, use in enumerate(reversed_use_list):
                    
                    # when a new face is added in edit mode
                    # no storeys are assigned to the newly created face
                    # therefore the system returns an indexError
                    try:
                        storeys = int(list_storey_A[enum] + list_storey_B[enum])
                    except IndexError:
                        storeys = 1
                    
                    if undercroft_levels > storeys:
                        undercroft_levels = undercroft_levels - storeys
                    else:
                        # you insert only when the undercroft levels is not equal to 
                        # the number of storeys of that use
                        if undercroft_levels < storeys:
                            index_to_insert = enum
                        index_to_stop = enum
                        break
                        
                # set to undercroft all the uses underneath the index
                # and groups all the "undecroft uses"
                grouped_list = []
                storey_left = 0
                for i, use in enumerate(reversed_use_list):
                    if i == index_to_stop:
                        grouped_list.append(-1)
                    elif i > index_to_stop:
                        grouped_list.append(use)
                
                if index_to_insert is not None:
                    duplicate_use = reversed_use_list[index_to_insert]
                    grouped_list.insert(1, duplicate_use)
                    
                    storeys = int(list_storey_A[index_to_insert] + list_storey_B[index_to_insert])
                    storey_left = storeys - undercroft_levels
                    
                    if storey_left > 9:
                        storey_left_str = str(storey_left)
                    else:
                        storey_left_str = "0" + str(storey_left)
                
                if numberOfUndercroft > 9:
                    str_undercroft_levels = str(numberOfUndercroft)
                else:
                    str_undercroft_levels = "0" + str(numberOfUndercroft)
                    
                # clip the lists
                list_storey_A = list_storey_A[index_to_stop+1:]
                list_storey_B = list_storey_B[index_to_stop+1:]
                
                # add the number of undercroft storeys
                new_list_storey_A = str_undercroft_levels[0]
                new_list_storey_B = str_undercroft_levels[1]

                if storey_left > 0:            
                    # update the number of leftover storeys                
                    new_list_storey_A += storey_left_str[0]
                    new_list_storey_B += storey_left_str[1]
                    
                new_list_storey_A += new_list_storey_A + list_storey_A
                new_list_storey_B += new_list_storey_B + list_storey_B
                
                # invert the lists
                grouped_list.reverse()
                list_storey_A = new_list_storey_A[::-1]
                list_storey_B = new_list_storey_B[::-1]
                useSplit = list(grouped_list)
                
            else:
                useSplit = use_list.split(";") 
                # invert the lists
                list_storey_A = list_storey_A[::-1]
                list_storey_B = list_storey_B[::-1]
                
            for enum, el in enumerate(useSplit):
                id = int(el)
                usesUiList.add()
                usesUiList[enum].id = enum + 1
                
                # if the use is -1, it means it is undercroft
                if id == -1:
                    usesUiList[enum].name = "undercroft"
                    usesUiList[enum].nameId = -1
                    # when a new face is added in edit mode
                    # no storeys are assigned to the newly created face
                    # therefore the system returns an indexError
                    try:
                        storeys = list_storey_A[enum] + list_storey_B[enum]
                    except IndexError:
                        storeys = 1
                    usesUiList[enum].storeys = int(storeys)
                
                else:
                    for use in bpy.context.scene.mastro_use_name_list:
                        if id == use.id:
                            usesUiList[enum].name = use.name
                            usesUiList[enum].nameId = use.id
                            # when a new face is added in edit mode
                            # no storeys are assigned to the newly created face
                            # therefore the system returns an indexError
                            try:
                                storeys = list_storey_A[enum] + list_storey_B[enum]
                            except IndexError:
                                storeys = 1
                            usesUiList[enum].storeys = int(storeys)
                                
                            break