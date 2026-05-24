# Attributes and Properties Reference

MaStro uses two distinct mechanisms to attach user data to objects:

- **Mesh attributes** — per-element data (vertex, edge, face) stored in `mesh.attributes`, readable by Geometry Nodes. This is where all parametric data lives.
- **Custom properties** — per-object data stored as Blender custom properties (`obj["key"]`), defined and managed from the Properties editor. These are not accessible to Geometry Nodes but can be read from Python.

For an explanation of the encoding scheme used for list attributes, see [The Attribute System](../getting-started/attribute-system.md).

---

## Custom Properties (Per-Object)

Custom properties are defined in the **Custom Properties** sub-panel of the Project Data panel in the Properties editor. Each definition applies to all MaStro objects of the selected type (mass/block, street, or both).

### Defining a Custom Property

1. Click **+** to add a new entry to the list.
2. Set **Name**, **Type** (Integer, Float, Boolean, or String), default value, and optional constraints (min, max, step, precision).
3. Choose which object types receive the property via **Assign to Mass/Block** and **Assign to Street**.
4. Click the **Assign** icon (✓) in the list row to write the property to all existing matching objects. The entry is then locked — type and assignment cannot be changed.
5. Click **Update** (↺) to propagate value changes to all objects after editing defaults.

### Storage

Each custom property is stored on the object as `mastro_custom_{id}`, where `id` is the stable integer ID assigned when the entry is created. The key never changes even if the property is renamed or reordered in the list.

### Removing a Custom Property

Click **−** in the list column next to the entry. If the property has been assigned, a confirmation dialog appears before the key is deleted from all objects and the entry removed from the list.

### Viewing and Editing Per-Object Values

In Object Mode, the **Custom Properties** panel appears in the MaStro sidebar tab when the active object has at least one assigned custom property. Values can be edited directly there.

---

---

## Mass Attributes (Face Domain)

Stored on faces of **Mass** objects.

| Attribute | Type | Description |
|---|---|---|
| `mastro_typology_id` | INT | ID of the assigned typology |
| `mastro_list_use_id_A` | INT | Tens digits of the use ID list (digit-pair encoded) |
| `mastro_list_use_id_B` | INT | Units digits of the use ID list (digit-pair encoded) |
| `mastro_list_storey_A` | INT | Tens digits of the storey count per use (digit-pair encoded) |
| `mastro_list_storey_B` | INT | Units digits of the storey count per use (digit-pair encoded) |
| `mastro_list_height_A` | INT | Tens digits of the floor-to-floor height per use |
| `mastro_list_height_B` | INT | Units digits of the floor-to-floor height per use |
| `mastro_list_height_C` | INT | First decimal of the floor-to-floor height per use |
| `mastro_list_height_D` | INT | Second decimal of the floor-to-floor height per use |
| `mastro_list_height_E` | INT | Third decimal of the floor-to-floor height per use |
| `mastro_number_of_storeys` | INT | Total number of storeys for this face |
| `mastro_overlay_top` | INT | Number of top floors to override |
| `mastro_undercroft` | INT | Number of below-grade floors |
| `mastro_floor_id` | INT | ID of the assigned floor type |
| `mastro_custom_face` | FLOAT | Free-form user value per face (see [Geometry Data](../ui/sidebar-geometry-data.md)) |

## Mass Attributes (Edge Domain)

Stored on edges of **Mass** objects.

| Attribute | Type | Description |
|---|---|---|
| `mastro_wall_id` | INT | ID of the assigned wall type |
| `mastro_inverted_normal` | BOOLEAN | Whether the wall normal is flipped |
| `mastro_custom_edge` | FLOAT | Free-form user value per edge (see [Geometry Data](../ui/sidebar-geometry-data.md)) |

## Mass Attributes (Point Domain)

Stored on vertices of **Mass** objects.

| Attribute | Type | Description |
|---|---|---|
| `mastro_custom_vert` | FLOAT | Free-form user value per vertex (see [Geometry Data](../ui/sidebar-geometry-data.md)) |

---

## Block Attributes (Edge Domain)

Block objects store most attributes on **edges** with an `_EDGE` suffix. They mirror the Mass face attributes.

| Attribute | Type | Description |
|---|---|---|
| `mastro_typology_id_EDGE` | INT | ID of the assigned typology |
| `mastro_list_use_id_A_EDGE` | INT | Tens digits of the use ID list |
| `mastro_list_use_id_B_EDGE` | INT | Units digits of the use ID list |
| `mastro_list_storey_A_EDGE` | INT | Tens digits of the storey count per use |
| `mastro_list_storey_B_EDGE` | INT | Units digits of the storey count per use |
| `mastro_list_height_A_EDGE` | INT | Tens digits of the floor-to-floor height per use |
| `mastro_list_height_B_EDGE` | INT | Units digits of the floor-to-floor height per use |
| `mastro_list_height_C_EDGE` | INT | First decimal of the floor-to-floor height per use |
| `mastro_list_height_D_EDGE` | INT | Second decimal of the floor-to-floor height per use |
| `mastro_list_height_E_EDGE` | INT | Third decimal of the floor-to-floor height per use |
| `mastro_number_of_storeys_EDGE` | INT | Total number of storeys for this edge |
| `mastro_overlay_top_EDGE` | INT | Number of top floors to override |
| `mastro_undercroft_EDGE` | INT | Number of below-grade floors |
| `mastro_floor_id_EDGE` | INT | ID of the assigned floor type |
| `mastro_block_depth` | FLOAT | Depth of the building volume from the façade edge |
| `mastro_inverted_normal_EDGE` | BOOLEAN | Whether the building extrudes in the opposite direction |
| `mastro_side_angle` | FLOAT | Side rotation angle (stored per vertex) |
| `mastro_custom_edge` | FLOAT | Free-form user value per edge (see [Geometry Data](../ui/sidebar-geometry-data.md)) |

---

## Street Attributes (Edge Domain)

Stored on edges of **Street** objects.

| Attribute | Type | Description |
|---|---|---|
| `mastro_street_id` | INT | ID of the assigned street type |
