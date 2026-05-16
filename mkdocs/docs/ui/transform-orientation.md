# Transform Orientation from Selection

The **Transform Orientation** tool creates a custom transform orientation aligned to the currently selected edge or pair of vertices. This lets you move, rotate, and scale objects or mesh elements along a direction defined by the geometry itself — for example, along a building façade that is not aligned to any world axis.

## Location

The tool appears in two places:

1. **Transform Orientations pop-over** — accessible from the header of the 3D Viewport by clicking the orientation label (e.g. *Global*, *Local*, *Normal*). A dedicated **Selection** button appears in Edit Mode.
2. **Keyboard shortcut** — **Alt+,** in Edit Mode.

## How It Works

1. Enter **Edit Mode** on any mesh object.
2. Select an **edge**, or select two **vertices**.
3. Press **Alt+,** (or click the Selection button in the orientation pop-over).

MaStro reads the selected edge (or the vector between the two selected vertices), projects it onto the XY plane, and computes a rotation matrix from it:

- The **Y axis** of the new orientation points along the selected edge.
- The **X axis** is derived by crossing the Y axis with the world Z axis.
- The **Z axis** is always world Z (vertical).

The orientation is created or overwritten under the name **Selection** and becomes the active transform orientation immediately.

## Practical Use

In architectural modelling, buildings are often rotated relative to the world axes. After creating an orientation from a building edge, you can:

- Move a face precisely perpendicular to the façade.
- Rotate an object to align it with the building footprint.
- Scale elements along the façade direction without manually entering rotation values.

## Notes

- The orientation is always flat (Z = world Z). It does not follow sloped surfaces.
- Only one *Selection* orientation is stored at a time; running the tool again overwrites it.
- The standard Blender **Create Orientation** button (also in the pop-over) is still available for other use cases.
