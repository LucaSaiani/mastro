import bpy

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
        list_storey_A = list_storey_A[::-1]
        list_storey_B = list_storey_B[::-1]
        
        useSplit = use_list.split(";") 
        for enum, el in enumerate(useSplit):
            id = int(el)
            usesUiList.add()
            usesUiList[enum].id = enum + 1
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