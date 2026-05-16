# Operators

All MaStro operators accessible from the UI. The `bl_idname` is the Python identifier used to call the operator programmatically (e.g. `bpy.ops.object.mastro_add_mastro_mass()`).

---

## Object Operators

| Label | bl_idname | Description |
|---|---|---|
| Mass | `object.mastro_add_mastro_mass` | Create a new Mass object with a default rectangular footprint |
| Block | `object.mastro_add_mastro_block` | Create a new Block object with a default edge path |
| Street | `object.mastro_add_mastro_street` | Create a new Street object with a default edge network |
| Dimension | `object.mastro_add_mastro_dimension` | Create a new Dimension object |
| Convert to MaStro Mass | `object.mastro_convert_to_mastro_mass` | Add Mass attributes and node groups to selected meshes |
| Convert to MaStro Street | `object.mastro_convert_to_mastro_street` | Add Street attributes and node groups to selected meshes |
| Update | `object.update_mastro_mesh_attributes` | Recalculate and write all MaStro attributes on all objects in the scene |
| Export Data as CSV | `object.mastro_export_csv` | Export granular floor data for all visible MaStro objects to a CSV file |
| Print Data | `object.mastro_print_data` | Print aggregate or granular floor data to the console |
| Set Street Id | `object.mastro_set_street_id` | Assign the street ID attribute to all edges of a Street object |
| Update All Street Attributes | `object.mastro_update_all_street_attributes` | Recalculate street width and radius attributes on all Street objects |

---

## Transform Operators

| Label | bl_idname | Description |
|---|---|---|
| Translate XY Constraint | `transform.translate_xy_constraint` | Move with automatic XY plane constraint when XY Constraint is enabled (**G**) |
| Rotate XY Constraint | `transform.rotate_xy_constraint` | Rotate around Z axis when XY Constraint is enabled (**R**) |
| Selection | `transform.set_orientation_from_selection` | Create a custom transform orientation from the selected edge or vertex pair (**Alt+,**) |

---

## Mesh Operators

| Label | bl_idname | Description |
|---|---|---|
| Move Active Vertex (Modal) | `mesh.move_active_vertex_modal` | Move the active vertex along the direction of the previous selection, accepting a typed distance or expression (**Alt+G**) |

---

## Node Operators

| Label | bl_idname | Description |
|---|---|---|
| Rename Reroute | `node.rename_reroute_from_source_socket` | Rename a Reroute node to match its connected socket (**Shift+Ctrl+F2**) |
| Sticky Note | `node.sticky_note` | Add or edit a sticky note on a Frame node |
| Sort Multi-Input | `node.sort_multiple_input` | Re-order the inputs of a Join Geometry or Geometry to Instance node |
| Filter By (GN) | `node.mastro_gn_filter_by` | Update the MaStro GN Filter By node group |
| Separate Geometry By (GN) | `node.mastro_gn_separate_geometry_by` | Update the MaStro GN Separate Geometry By node group |
| Filter By (Shader) | `node.mastro_shader_filter_by` | Update the MaStro Shader Filter By node group |

---

## Layer Manager Operators

| Label | bl_idname | Description |
|---|---|---|
| Set Active View Layer | `layer_manager.set_active` | Switch the active view layer to the selected shadow slot |
| New View Layer | `layer_manager.add_layer` | Add a new view layer (New, Copy, or Blank) |
| New View Layer (Popup) | `layer_manager.add_layer_popup` | Open a popup to choose the type of new view layer |
| Move View Layer Slot | `layer_manager.move_item` | Move the selected layer slot Up, Down, to Top, or to Bottom |
| Sort View Layers | `layer_manager.sort_layers` | Sort all layer slots alphabetically (A→Z or Z→A) |
