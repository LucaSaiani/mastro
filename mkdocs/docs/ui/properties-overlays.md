# Viewport Overlays — MaStro

The **MaStro** section appears inside Blender's **Viewport Overlays** popover (the overlapping circles icon in the 3D viewport header). It controls the text and colour overlays drawn directly in the 3D viewport over MaStro objects.

The section header contains a **master toggle**. When disabled, all MaStro overlays are hidden. Blender's global **Show Overlays** toggle also hides them. When enabled, the individual sections below become active.

---

## Edit Mode Overlays

**Edit Mode Overlays**  
When enabled, selection overlays are shown while a MaStro object is in Edit Mode. These overlays colour the edges and faces of the object according to their assigned type (typology colour for mass faces, wall type colour for mass edges, etc.).

---

## Block & Mass

Overlays drawn on Mass and Block objects:

| Toggle | What it shows |
|---|---|
| **Storey Number** | Number of storeys on each face or edge |
| **Typology Name** | Name of the assigned typology on each face or edge |
| **Typology Color** | Colours Block object edges by their typology |
| **Inverted Normal** | Marks edges whose normal has been flipped with a symbol |
| **Building Name** | Name of the building assigned to each face |
| **Block Name** | Name of the block assigned to each face |

---

## Wall

| Toggle | What it shows |
|---|---|
| **Type** | Colours Mass object edges by their wall type |
| **Inverted Normal** | Marks wall edges with an inverted normal |

---

## Floor

| Toggle | What it shows |
|---|---|
| **Type** | Shows the floor type name on each face |

---

## Street

| Toggle | What it shows |
|---|---|
| **Type** | Colours Street object edges by their street type |

---

!!! tip
    Overlay colours and text size are configured in **Preferences → Overlays**. See [Preferences](preferences.md) for details.
