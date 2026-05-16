# Custom Attributes

MaStro stores all parametric data as custom mesh attributes. These attributes are readable by Geometry Nodes and can also be accessed from Python via `mesh.attributes`.

For an explanation of the encoding scheme used for list attributes, see [The Attribute System](../getting-started/attribute-system.md).

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
| `mastro_custom_face` | FLOAT | User-defined custom value per face |

## Mass Attributes (Edge Domain)

Stored on edges of **Mass** objects.

| Attribute | Type | Description |
|---|---|---|
| `mastro_wall_id` | INT | ID of the assigned wall type |
| `mastro_inverted_normal` | BOOLEAN | Whether the wall normal is flipped |
| `mastro_custom_edge` | FLOAT | User-defined custom value per edge |

## Mass Attributes (Point Domain)

Stored on vertices of **Mass** objects.

| Attribute | Type | Description |
|---|---|---|
| `mastro_custom_vert` | FLOAT | User-defined custom value per vertex |

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
| `mastro_custom_edge` | FLOAT | User-defined custom value per edge |

---

## Street Attributes (Edge Domain)

Stored on edges of **Street** objects.

| Attribute | Type | Description |
|---|---|---|
| `mastro_street_id` | INT | ID of the assigned street type |
