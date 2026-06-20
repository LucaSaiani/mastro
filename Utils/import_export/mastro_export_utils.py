import bpy
import bmesh

import csv
from decimal import Decimal, ROUND_HALF_DOWN

header_granularData = ["Block Name",
                  "Building Name",
                  "Typology",
                  "Number of Storeys",
                  "Floor Number",
                  "Use",
                  "Floor Area",
                  "Floor to Floor Height",
                  "Level",
                  "Perimeter",
                  "Wall Area"]

floorToFloorLevel = 4.5


class faceEdge():
     def __init__(self, index = None, face = None, storeys = None, topStorey = None, length = None, perimeter = None):
         self.index = index
         self.face = face
         self.storeys = storeys
         self.topStorey = topStorey
         self.length = length
         self.perimeter = perimeter


# in case of mastro block, the mesh is evaluated in order to get areas
def evaluate_mastro_obj(obj):
    # get the list of modifiers, keep on only the first one, the others
    # are switched off
    modifiers_to_restore = []
    found_first = False

    for mod in obj.modifiers:
        if mod.type == 'NODES':
            if not found_first:
                found_first = True
                continue
            else:
                modifiers_to_restore.append((mod, mod.show_viewport))
                mod.show_viewport = False

    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    # Invoke to_mesh() for evaluated object.
    object_eval = obj.evaluated_get(depsgraph)
    # a copy of the mesh is necessary to be processed as bMesh
    mesh_from_eval = bpy.data.meshes.new_from_object(object_eval)
    object_eval.to_mesh_clear()

    # modifiers are turned back on
    for mod, state in modifiers_to_restore:
        mod.show_viewport = state

    return mesh_from_eval


def get_mass_data(obj, mastro_type):
    data = []

    if mastro_type == "mass":
        mesh = obj.data
    else:
        mesh = evaluate_mastro_obj(obj)

    bm = bmesh.new()
    bm.from_mesh(mesh)

    bm_typology = bm.faces.layers.int["mastro_typology_id"]
    bm_storeys = bm.faces.layers.int["mastro_number_of_storeys"]
    bm_undercroft = bm.faces.layers.int["mastro_undercroft"]
    bm_use_list_A   = bm.faces.layers.int["mastro_list_use_id_A"]
    bm_use_list_B   = bm.faces.layers.int["mastro_list_use_id_B"]
    bm_storey_list_A = bm.faces.layers.int["mastro_list_storey_A"]
    bm_storey_list_B = bm.faces.layers.int["mastro_list_storey_B"]
    bm_height_A = bm.faces.layers.int["mastro_list_height_A"]
    bm_height_B = bm.faces.layers.int["mastro_list_height_B"]
    bm_height_C = bm.faces.layers.int["mastro_list_height_C"]
    bm_height_D = bm.faces.layers.int["mastro_list_height_D"]
    bm_height_E = bm.faces.layers.int["mastro_list_height_E"]

    face_list = list(bm.faces)

    for face in face_list:
        edges = []
        block_name = ""
        building_name = ""
        typology_name = ""

        # block name
        for block in bpy.context.scene.mastro_block_name_list:
            if block.id == obj.mastro_props['mastro_block_attribute']:
                block_name = block.name
                break

        # building name
        for building in bpy.context.scene.mastro_building_name_list:
            if building.id == obj.mastro_props['mastro_building_attribute']:
                building_name = building.name
                break

        # typology name
        for typology in bpy.context.scene.mastro_typology_name_list:
            if typology.id == face[bm_typology]:
                typology_name = typology.name
                typology_id = typology.id
                break

        # use list
        use_id_list_A = face[bm_use_list_A]
        use_id_list_B = face[bm_use_list_B]

        use_id_list_A = str(use_id_list_A)[1:]
        use_id_list_B = str(use_id_list_B)[1:]
        uses_list = [a + b for a, b in zip(use_id_list_A, use_id_list_B)]
        use_name_list = []
        for u in uses_list:
            use_id = int(u)
            use_name = ""
            for use in bpy.context.scene.mastro_use_name_list:
                if use.id == use_id:
                    use_name = use.name
                    break
            use_name_list.append(use_name)

        # storey list
        storey_list_A = face[bm_storey_list_A]
        storey_list_B = face[bm_storey_list_B]

        storey_list_A = str(storey_list_A)[1:]
        storey_list_B = str(storey_list_B)[1:]
        storey_list = [a + b for a, b in zip(storey_list_A, storey_list_B)]

        # height list
        height_list_A = face[bm_height_A]
        height_list_B = face[bm_height_B]
        height_list_C = face[bm_height_C]
        height_list_D = face[bm_height_D]
        height_list_E = face[bm_height_E]

        height_list_A = str(height_list_A)[1:]
        height_list_B = str(height_list_B)[1:]
        height_list_C = str(height_list_C)[1:]
        height_list_D = str(height_list_D)[1:]
        height_list_E = str(height_list_E)[1:]
        height_list = [a + b + c + d + e for a, b, c, d, e in zip(height_list_A, height_list_B, height_list_C, height_list_D, height_list_E)]

        # number of storeys
        number_of_storeys = face[bm_storeys]

        # Floor Area
        floor_area = face.calc_area()

        # GEA
        GEA = floor_area * number_of_storeys

        #perimeter
        perimeter = 0
        common_edges = []
        for edge in face.edges:
            edge_of_face = faceEdge()
            edge_of_face.index = edge.index
            edge_of_face.face = face.index
            edge_of_face.length = edge.calc_length()
            edge_of_face.topStorey = number_of_storeys
            edge_of_face.storeys = None
            # if there is no angle, then the edge_of_face is not a edge in common between faces
            try:
                edge.calc_face_angle()
                common_edges.append(edge.index)
                edge_of_face.perimeter = False
            except ValueError:
                perimeter += edge_of_face.length
                edge_of_face.perimeter = True
                edge_of_face.storeys = number_of_storeys
            edges.append(edge_of_face)

        #wall area
        # this is the area of the perimeter walls
        wall_area = perimeter * floorToFloorLevel *number_of_storeys
        # but if the faces having an edge in common have different storey numbers,
        # then the difference is added to the wall area
        for index in common_edges:
            for fa in bm.faces:
                if face.index != fa.index: #there is no point in evaluating the same face
                    for ed in fa.edges:
                        if index == ed.index:
                            if face[bm_storeys] > fa[bm_storeys]:
                                diff = face[bm_storeys] - fa[bm_storeys]
                                length = ed.calc_length()
                                wall_area += length * diff * floorToFloorLevel
                                for ed in edges:
                                    if ed.index == index:
                                        ed.storeys = diff
                                        break

        # removes the edges marked as not perimeter
        # and are duplicates of the edges that are visible
        for index, edge in reversed(list(enumerate(edges))):
            if edge.storeys == None:
                edges.pop(index)

        #lowest Z coordinate of the face
        obj_origin_z = obj.location[2]
        face_z = face.calc_center_median()[2]
        level = obj_origin_z + face_z

        GEA = Decimal(GEA)
        GEA = GEA.quantize(Decimal('0.01'), rounding=ROUND_HALF_DOWN)

        wall_area = Decimal(wall_area)
        wall_area = wall_area.quantize(Decimal('0.01'), rounding=ROUND_HALF_DOWN)

        perimeter = Decimal(perimeter)
        perimeter = perimeter.quantize(Decimal('0.01'), rounding=ROUND_HALF_DOWN)

        floor_area = Decimal(floor_area)
        floor_area = floor_area.quantize(Decimal('0.01'), rounding=ROUND_HALF_DOWN)

        level = Decimal(level)
        level = level.quantize(Decimal('0.001'))

        entry = {
            "Object": obj.name,
            "Block Name": block_name,
            "Building Name": building_name,
            "Typology": typology_name,
            "Typology Id" : typology_id,
            "Number of Storeys": number_of_storeys,
            "Use List" : use_name_list,
            "Storey List" : storey_list,
            "Height List" : height_list,
            "Level": level,
            "Floor Area": floor_area,
            "Perimeter": perimeter,
            "Wall Area": wall_area,
            "GEA": GEA,
            "Edges": edges,
            "Undercroft": face[bm_undercroft],
        }
        data.append(entry)

    bm.free()

    if mastro_type == "block":
        bpy.data.meshes.remove(mesh)
    return data


def granularData(roughData):
    roughData_flat = [entry for sublist in roughData for entry in sublist]
    roughData = sorted(
        roughData_flat,
        key=lambda x: (
            x["Block Name"],
            x["Building Name"],
            x["Typology"],
            x["Level"]
        )
    )

    # first aggregate
    data = [roughData[0]]

    for el in roughData[1:]:
        last = data[-1]
        if (el["Block Name"] == last["Block Name"] and
            el["Building Name"] == last["Building Name"] and
            el["Typology"] == last["Typology"] and
            el["Number of Storeys"] == last["Number of Storeys"] and
            el["Level"] == last["Level"] and
            el["Perimeter"] == last["Perimeter"]):

            last["Floor Area"] += el["Floor Area"]
            last["Perimeter"] += el["Perimeter"]
            last["Wall Area"] += el["Wall Area"]

        else:
            data.append(el)

    # Unwrap multi-storey
    expandedData = []

    for index in reversed(range(len(data))):
        el = data[index]

        if el["Number of Storeys"] > 1:
            edges = el["Edges"]
            use_index = 0
            accumulate_floor = int(el["Storey List"][0])
            for floor in range(1, el["Number of Storeys"] + 1):
                floor_group = el["Storey List"][use_index]
                if accumulate_floor < floor:
                    use_index +=1
                    accumulate_floor += int(el["Storey List"][use_index])

                # use name
                use_name = el["Use List"][use_index]

                # floor to floor height
                floor_height = float(el["Height List"][use_index])

                # level
                level = el["Level"] + Decimal(floorToFloorLevel * floor)

                # Perimeter for each floor
                perimeter = 0
                for edge in edges:
                    if edge.perimeter is True:
                        perimeter += edge.length
                    else:
                        # edge.storeys is the number of visible storeys
                        if floor >= (edge.topStorey - edge.storeys + 1):
                            perimeter += edge.length

                wallArea = perimeter * floorToFloorLevel

                if floor <= el.get("Undercroft", 0):
                    continue

                expandedData.append({
                    "Object": el["Object"],
                    "Block Name": el["Block Name"],
                    "Building Name": el["Building Name"],
                    "Typology": el["Typology"],
                    "Number of Storeys": el["Number of Storeys"],
                    "Floor Number" : floor,
                    "Use" : use_name,
                    "Floor to Floor Height" : floor_height,
                    "Level": level,
                    "Floor Area": el["Floor Area"],
                    "Perimeter": perimeter,
                    "Wall Area": wallArea
                })

            del data[index]

    # add expanded data
    data.extend(expandedData)

    data = [x for x in data if x.get("Undercroft", 0) < x["Number of Storeys"]]

    for x in data:
        if "Floor Number" not in x:
            x["Floor Number"] = x["Number of Storeys"]

    # second aggregate
    data = sorted(
        data,
        key=lambda x: (
            x["Block Name"],
            x["Building Name"],
            x["Typology"],
            x["Floor Number"],
            x["Level"]
        )
    )

    granularData = [data[0]]

    for el in data[1:]:
        last = granularData[-1]

        if (el["Block Name"] == last["Block Name"] and
            el["Building Name"] == last["Building Name"] and
            el["Typology"] == last["Typology"] and
            el["Floor Number"] == last["Floor Number"] and
            el["Level"] == last["Level"]):

            last["Floor Area"] += el["Floor Area"]
            last["Perimeter"] += el["Perimeter"]
            last["Wall Area"] += el["Wall Area"]
        else:
            granularData.append(el)

    return granularData


def get_mass_objects_for_scope(context, scope):
    """Return MaStro mass/block objects matching the given scope ('VISIBLE'/'SELECTED'/'ALL')"""
    if scope == 'SELECTED':
        candidates = context.selected_objects
    elif scope == 'ALL':
        candidates = context.scene.objects
    else:
        candidates = context.scene.objects

    objects = []
    for obj in candidates:
        if obj.type != "MESH" or "MaStro object" not in obj.data:
            continue
        if "MaStro mass" not in obj.data and "MaStro block" not in obj.data:
            continue
        if scope == 'VISIBLE' and not obj.visible_get():
            continue
        objects.append(obj)
    return objects


def get_mass_data_for_scope(context, scope):
    """Collect get_mass_data() rows for MaStro mass/block objects matching the given scope"""
    roughData = []
    for obj in get_mass_objects_for_scope(context, scope):
        mastro_type = "mass" if "MaStro mass" in obj.data else "block"
        roughData.append(get_mass_data(obj, mastro_type))
    return roughData


def get_visible_mass_data():
    """Collect get_mass_data() rows for every visible MaStro mass/block object in the scene"""
    return get_mass_data_for_scope(bpy.context, 'VISIBLE')


def write_csv(filepath, granularDataDict):
    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile,
                                fieldnames=header_granularData,
                                extrasaction="ignore"
                                )
        writer.writeheader()
        writer.writerows(granularDataDict)


# to print text in the python console
def print_ui(text):
    # Get the CONSOLE area
    for area in bpy.context.screen.areas:
        if area.type == 'CONSOLE':
            with bpy.context.temp_override(area=area):
                bpy.ops.console.scrollback_append(text=str(text), type="OUTPUT")
            return

    print(f"[System Console Fallback]: {text}")
