import bpy
import bmesh

from ...Utils.mastro_arch.read_write_bmesh_storey_attribute import read_bmesh_storey_attribute
from ...Utils.get_names_from_list import get_names_from_list
from .mastro_arch.block_extrusion import _handle_block_extrusion
from .mastro_street.street_extrusion import _handle_street_extrusion


# Rebuild the VIEW3D use/storey UIList to reflect the active face or edge's attributes.
# Called from the depsgraph handler on every selection change.
def update_view3D_panels(scene):
    obj = bpy.context.active_object

    if obj is None:
        return
    if obj.type != "MESH":
        return
    if "MaStro object" not in obj.data:
        return
    if obj.mode != 'EDIT':
        return

    mesh = obj.data
    
    # to avoid issue when opening a file which was saved in edit mode
    try:
        bm = bmesh.from_edit_mesh(mesh)
    except ValueError:
        return
        

    if ("MaStro mass" in obj.data or "MaStro block" in obj.data):
        numberOfStoreys = scene.mastro_attribute_mass_storeys
        numberOfUndercroft = scene.mastro_attribute_mass_undercroft
        if numberOfUndercroft > numberOfStoreys:
            numberOfUndercroft = numberOfStoreys

        current_value = scene.mastro_typology_names
        enum_items = get_names_from_list(scene, bpy.context, "mastro_typology_name_list")
        typology_index = next((i for i, item in enumerate(enum_items) if item[0] == current_value), 0)

        data = read_bmesh_storey_attribute(numberOfStoreys, typology_index)
        item = next((i for i in bpy.context.scene.mastro_typology_name_list if i["id"] == typology_index), None)
        if item is None:
            return

        usesUiList = bpy.context.scene.mastro_obj_typology_uses_name_list

        while len(usesUiList) > 0:
            index = bpy.context.scene.mastro_obj_typology_uses_name_list_index
            usesUiList.remove(index)
            bpy.context.scene.mastro_obj_typology_uses_name_list_index = min(max(0, index - 1), len(usesUiList) - 1)

        use_list = item.useList
        list_storey_A = str(data["storey_list_A"])[1:]
        list_storey_B = str(data["storey_list_B"])[1:]

        active = None

        if "MaStro mass" in obj.data:
            bm.faces.ensure_lookup_table()
            field = bm.faces
            suffix = ""
            if isinstance(bm.select_history.active, bmesh.types.BMFace):
                active = bm.select_history.active
        else:  # mastro block
            bm.edges.ensure_lookup_table()
            bm.verts.ensure_lookup_table()
            field = bm.edges
            suffix = "_EDGE"
            if isinstance(bm.select_history.active, bmesh.types.BMEdge):
                active = bm.select_history.active
            _handle_block_extrusion(scene, obj, bm)

        try:
            bm_use_list_A    = field.layers.int[f"mastro_list_use_id_A{suffix}"]
            bm_use_list_B    = field.layers.int[f"mastro_list_use_id_B{suffix}"]
            bm_storey_list_A = field.layers.int[f"mastro_list_storey_A{suffix}"]
            bm_storey_list_B = field.layers.int[f"mastro_list_storey_B{suffix}"]
        except KeyError:
            return

        if active is not None:
            use_id_list_A = str(active[bm_use_list_A])[1:]
            use_id_list_B = str(active[bm_use_list_B])[1:]
            use_id_list = [a + b for a, b in zip(use_id_list_A, use_id_list_B)]
            use_list = ';'.join(str(int(x)) for x in use_id_list)
            use_list = use_list[::-1]
            list_storey_A = str(active[bm_storey_list_A])[1:]
            list_storey_B = str(active[bm_storey_list_B])[1:]

            if numberOfUndercroft > 0:
                reversed_use_list = use_list[::-1].split(";")
                undercroft_levels = numberOfUndercroft
                index_to_insert = None
                index_to_stop = None
                for enum, use in enumerate(reversed_use_list):
                    try:
                        storeys = int(list_storey_A[enum] + list_storey_B[enum])
                    except IndexError:
                        storeys = 1

                    if undercroft_levels > storeys:
                        undercroft_levels = undercroft_levels - storeys
                    else:
                        if undercroft_levels < storeys:
                            index_to_insert = enum
                        index_to_stop = enum
                        break

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
                    storey_left_str = f"{storey_left:02d}"

                str_undercroft_levels = f"{numberOfUndercroft:02d}"

                list_storey_A = list_storey_A[index_to_stop+1:]
                list_storey_B = list_storey_B[index_to_stop+1:]

                new_list_storey_A = str_undercroft_levels[0]
                new_list_storey_B = str_undercroft_levels[1]

                if storey_left > 0:
                    new_list_storey_A += storey_left_str[0]
                    new_list_storey_B += storey_left_str[1]

                new_list_storey_A += new_list_storey_A + list_storey_A
                new_list_storey_B += new_list_storey_B + list_storey_B

                grouped_list.reverse()
                list_storey_A = new_list_storey_A[::-1]
                list_storey_B = new_list_storey_B[::-1]
                useSplit = list(grouped_list)
            else:
                useSplit = use_list.split(";")
                list_storey_A = list_storey_A[::-1]
                list_storey_B = list_storey_B[::-1]

            for enum, el in enumerate(useSplit):
                if el:
                    id = int(el)
                    usesUiList.add()
                    usesUiList[enum].id = enum + 1

                    if id == -1:
                        usesUiList[enum].name = "undercroft"
                        usesUiList[enum].nameId = -1
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
                                try:
                                    storeys = list_storey_A[enum] + list_storey_B[enum]
                                except IndexError:
                                    storeys = 1
                                usesUiList[enum].storeys = int(storeys)
                                break

    elif "MaStro street" in obj.data:
        bm.edges.ensure_lookup_table()
        bm.verts.ensure_lookup_table()
        _handle_street_extrusion(scene, obj, bm)
