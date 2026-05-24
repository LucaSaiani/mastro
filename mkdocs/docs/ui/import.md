# Import Mastro Objects

MaStro objects can be imported from another `.blend` file via **File → Import → Mastro Objects (.blend)**. The operator transfers the selected objects together with all scene list entries they reference (typologies, uses, walls, floors, streets, buildings, blocks), remapping attribute IDs to the destination scene.

---

## Workflow

1. Open **File → Import → Mastro Objects (.blend)** and select the source file.
2. A dialog appears listing all mesh and Grease Pencil objects found in the file.
3. Tick or untick each object. All objects are selected by default.
4. Choose the import mode with the **Objects / Collection** tab at the top.
5. Click **OK**. The selected objects are linked into the active scene and their attributes are remapped automatically.

---

## Objects Mode

Shows a scrollable list of all mesh and Grease Pencil objects in the source file.

Each row shows:

| Column | Description |
|---|---|
| Checkbox | Whether the object will be imported |
| Type icon | Mesh or Grease Pencil |
| M | Present when the object is a MaStro object (has MaStro custom attributes) |
| Name | Object name |

### Filtering

The search bar at the top of the list filters by name in real time. The **M** button next to the search bar restricts the list to MaStro objects only. Use the **⋮** specials menu to **Select All** or **Deselect All** visible items.

---

## Collection Mode

Shows the collections defined in the source file. Selecting a collection imports all objects it contains (including nested collections), regardless of individual object selection.

---

## Attribute Remapping

After confirmation, MaStro reads the scene lists from the source file and merges them into the destination scene:

- If an entry with **identical parameters** already exists in the destination, the imported objects are remapped to it — no duplicate is created.
- If the parameters differ, the entry is added as a new item with a new ID.

The remapping covers all attribute types: uses, typologies, walls, floors, streets, buildings, and blocks. The process runs in this order to preserve dependencies (uses are resolved before typologies, which reference them).

Non-MaStro objects are imported as-is, without any attribute remapping.
