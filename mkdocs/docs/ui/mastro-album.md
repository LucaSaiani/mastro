# MaStro Album

A **MaStro Album** is an Empty object that carries a single drawing **scale** shared by everything parented to it. It is the recommended way to lay out several drawings (plans, sections, elevations) at the same print scale and move or rescale them together as a group — for example to arrange a sheet of drawings, or to quickly compare the same drawing at different scales by duplicating its album.

**Created with:** *Add → MaStro → Album*

---

## How it works

The album's **Scale 1:** value is stored as its X/Y/Z scale (`1 / denominator`). Children's [drawing](../getting-started/object-type-drawing.md) Geometry Nodes read this scale from their parent album via an Object Info node, so each child renders at the scale carried by its own album rather than a value baked into the drawing itself. Changing the album's scale re-applies proportionally from the album's own origin — the same behaviour as scaling around the 3D cursor.

The album's empty display icon is compensated by the **Icon Size** setting so it keeps a constant on-screen size in world space regardless of how much the album itself is scaled.

## Adding objects to an album

Select the objects to add, then **Shift-click the album last** so it becomes the active object, and use the **+** button next to the children list (or *Add to MaStro Album* from the search menu). This:

- creates a **linked-data copy** of each selected object, parented to the album — the originals are left untouched in their original location
- positions each copy relative to the album the same way the original sits relative to the world origin, as if the album's origin were the 3D cursor

Because the children are linked-data copies (sharing the same mesh and Geometry Nodes modifiers as their source), editing the source's geometry updates every album copy of it too.

## The children list

The Object Data panel (and its sidebar counterpart) list every child currently parented to the album:

| Control | Description |
|---|---|
| **Scale 1:** | The shared scale denominator applied to this album's children |
| Children list | One row per parented object; clicking a row selects and activates that object |
| **+** button | Adds the selected objects to the album (see above) |
| 🗑 (row) | Removes that single child — deletes its linked-data copy |
| **Icon Size** | World-space size of the album's empty icon, kept constant regardless of Scale 1: |

To remove several children at once, select them in the viewport and use **Unparent from MaStro Album** — since each child only exists as the album's copy of the source object, this deletes the copies rather than leaving loose unparented duplicates.

## Where to find it

| Location | Contents |
|---|---|
| **Properties → Object Data Properties** | Same controls as below, available whenever a MaStro album Empty is the active object |
| **Viewport sidebar (N) → MaStro → Album** | Same controls, nested under the MaStro tab |
