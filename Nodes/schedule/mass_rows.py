"""Per-object equivalent of Utils/import_export/mastro_export_utils.py's
granularData(), for the Schedule node tree's "Mass" Input Mesh category.

get_mass_data() (mastro_export_utils.py) is reused as-is - it already
produces one row per face, per object, with "_Object" set correctly.
granularData() is NOT reused: its row-aggregation step
(mastro_export_utils.py:granularData, the "first aggregate" loop)
compares Block Name/Building Name/Typology/Number of Storeys/Level/
Perimeter but never "_Object" - two different objects (e.g. a mass and a
block, or two masses) that happen to share all of those values get
silently merged into one row, summing their Floor Area/Perimeter/Wall
Area together. That's likely harmless for the CSV/print export (which
this function deliberately leaves untouched, in case the cross-object
merge is relied upon there), but is a real bug for the node tree, where
the user expects rows for different objects to never bleed into each
other - confirmed live (a mass and a block sharing the same grouping
metadata produced one merged row showing the wrong object's area)."""

from decimal import Decimal

from ...Utils.import_export.mastro_export_utils import floorToFloorLevel


def granular_rows_per_object(rough_data):
    """Same multi-storey unwrap/aggregation as
    mastro_export_utils.granularData, except grouping (and therefore
    never merging) is always scoped to a single "_Object" - rows from
    different objects are never combined, even if every other grouping
    field happens to match."""
    flat = [entry for sublist in rough_data for entry in sublist]
    if not flat:
        return []

    flat = sorted(
        flat,
        key=lambda x: (
            x["_Object"],
            x["Block Name"],
            x["Building Name"],
            x["Typology"],
            x["Level"],
        ),
    )

    # First aggregate: combine consecutive same-object rows that share
    # every other grouping field (e.g. two faces of the same storey
    # group), same as granularData - but gated on "_Object" matching too.
    data = [flat[0]]
    for el in flat[1:]:
        last = data[-1]
        if (el["_Object"] == last["_Object"] and
                el["Block Name"] == last["Block Name"] and
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
    expanded = []
    for index in reversed(range(len(data))):
        el = data[index]
        if el["Number of Storeys"] <= 1:
            continue

        edges = el["Edges"]
        use_index = 0
        accumulate_floor = int(el["Storey List"][0])
        for floor in range(1, el["Number of Storeys"] + 1):
            if accumulate_floor < floor:
                use_index += 1
                accumulate_floor += int(el["Storey List"][use_index])

            use_name = el["Use List"][use_index]
            floor_height = float(el["Height List"][use_index])
            level = el["Level"] + Decimal(floorToFloorLevel * floor)

            perimeter = 0
            for edge in edges:
                if edge.perimeter is True:
                    perimeter += edge.length
                else:
                    if floor >= (edge.topStorey - edge.storeys + 1):
                        perimeter += edge.length

            wall_area = perimeter * floorToFloorLevel

            if floor <= el.get("Undercroft", 0):
                continue

            expanded.append({
                "_Object": el["_Object"],
                "Block Name": el["Block Name"],
                "Building Name": el["Building Name"],
                "Typology": el["Typology"],
                "Number of Storeys": el["Number of Storeys"],
                "Floor Number": floor,
                "Use": use_name,
                "Floor to Floor Height": floor_height,
                "Level": level,
                "Floor Area": el["Floor Area"],
                "Perimeter": perimeter,
                "Wall Area": wall_area,
            })

        del data[index]

    data.extend(expanded)
    return data
