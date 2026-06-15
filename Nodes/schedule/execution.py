import bpy
import bmesh
import math

# Cache of the last evaluated tables, keyed by tree name then node name.
# Used by the Viewer node to read the table produced by its input node.
_schedule_cache = {}


def update_node(self, context):
    """Property update callback: re-run the tree this node belongs to."""
    tree = self.id_data
    if hasattr(tree, "execute"):
        tree.execute()


def get_node_table(tree_name, node_name):
    return _schedule_cache.get(tree_name, {}).get(node_name)


def extract_mesh_rows(objs):
    """Build the schedule table rows (one per floor/level) for the given
    MaStro mass objects, decoding the per-face BMesh attribute layers
    written by add_mass_attributes()."""
    rows = []

    use_names = {u.id: u.name for u in bpy.context.scene.mastro_use_name_list}
    typology_names = {t.id: t.name for t in bpy.context.scene.mastro_typology_name_list}
    block_names = {b.id: b.name for b in bpy.context.scene.mastro_block_name_list}
    building_names = {b.id: b.name for b in bpy.context.scene.mastro_building_name_list}

    for obj in objs:
        block_name = block_names.get(obj.mastro_props.mastro_block_attribute, "")
        building_name = building_names.get(obj.mastro_props.mastro_building_attribute, "")

        bm = bmesh.new()
        bm.from_mesh(obj.data)

        bm_typology = bm.faces.layers.int["mastro_typology_id"]
        bm_use_A = bm.faces.layers.int["mastro_list_use_id_A"]
        bm_use_B = bm.faces.layers.int["mastro_list_use_id_B"]
        bm_storeys = bm.faces.layers.int["mastro_number_of_storeys"]
        bm_storey_A = bm.faces.layers.int["mastro_list_storey_A"]
        bm_storey_B = bm.faces.layers.int["mastro_list_storey_B"]
        bm_height_A = bm.faces.layers.int["mastro_list_height_A"]
        bm_height_B = bm.faces.layers.int["mastro_list_height_B"]
        bm_height_C = bm.faces.layers.int["mastro_list_height_C"]
        bm_height_D = bm.faces.layers.int["mastro_list_height_D"]
        bm_height_E = bm.faces.layers.int["mastro_list_height_E"]
        bm_undercroft = bm.faces.layers.int["mastro_undercroft"]

        for f in bm.faces:
            storeys = f[bm_storeys]
            typology_name = typology_names.get(f[bm_typology], "")
            area_total = round(f.calc_area(), 2)

            storey_group = 0
            index_list = 1
            for level in range(storeys):
                length = int(math.log10(f[bm_storey_A])) + 1 if f[bm_storey_A] else 1
                pos = length - index_list - 1

                storey_A = int((f[bm_storey_A] / 10 ** pos) % 10)
                storey_B = int((f[bm_storey_B] / 10 ** pos) % 10)

                use_A = int((f[bm_use_A] / 10 ** pos) % 10)
                use_B = int((f[bm_use_B] / 10 ** pos) % 10)
                use_name = use_names.get(use_A * 10 + use_B, "")

                height_A = int((f[bm_height_A] / 10 ** pos) % 10)
                height_B = int((f[bm_height_B] / 10 ** pos) % 10)
                height_C = int((f[bm_height_C] / 10 ** pos) % 10)
                height_D = int((f[bm_height_D] / 10 ** pos) % 10)
                height_E = int((f[bm_height_E] / 10 ** pos) % 10)
                height = height_A * 10 + height_B + height_C * 0.1 + height_D * 0.01 + height_E * 0.001

                undercroft = int((f[bm_undercroft] / 10 ** pos) % 10)
                area = 0 if undercroft == 1 else area_total

                storey_group_new = storey_A * 10 + storey_B + storey_group
                if storey_group_new == level + 1:
                    storey_group = storey_group_new
                    index_list += 1

                rows.append({
                    "Object": obj.name,
                    "Block": block_name,
                    "Building": building_name,
                    "Typology": typology_name,
                    "Use": use_name,
                    "Storey": storey_group_new,
                    "Height": height,
                    "Undercroft": undercroft,
                    "Area": area,
                    "Level": level,
                    "Face": f.index,
                })

        bm.free()

    return rows


def evaluate_tree(tree):
    """Topologically evaluate every node of the tree, caching each node's
    output values (a list of tables, one per output socket)."""
    cache = {}

    def eval_node(node):
        if node.name in cache:
            return cache[node.name]

        input_values = []
        for socket in node.inputs:
            value = None
            if socket.is_linked:
                link = socket.links[0]
                from_node = link.from_node
                outputs = eval_node(from_node)
                try:
                    index = list(from_node.outputs).index(link.from_socket)
                    value = outputs[index]
                except (ValueError, IndexError):
                    value = None
            input_values.append(value)

        result = node.evaluate(input_values) if hasattr(node, "evaluate") else []
        cache[node.name] = result
        return result

    for node in tree.nodes:
        eval_node(node)

    _schedule_cache[tree.name] = cache
    return cache
