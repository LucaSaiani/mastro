# Transform Orientation from Selection

The **Transform Orientation** tool creates a custom transform orientation aligned to the currently selected edge or pair of vertices. This lets you move, rotate, and scale objects or mesh elements along a direction defined by the geometry itself — for example, along a building façade that is not aligned to any world axis.

The tool appears in the **Transform Orientations pop-over** (click the orientation label in the 3D Viewport header) and via the keyboard shortcut **Alt+,** in Edit Mode.

**How to use:**

1. Enter Edit Mode on any mesh object.
2. Select an edge, or select two vertices.
3. Press **Alt+,**.

MaStro reads the selected edge (or the vector between the two vertices), projects it onto the XY plane, and computes a rotation matrix:

- The **Y axis** points along the selected edge.
- The **X axis** is derived by crossing Y with world Z.
- The **Z axis** is always world Z (vertical).

The orientation is created or overwritten under the name **Selection** and becomes active immediately.

**Notes:** the orientation is always flat (Z = world Z) and does not follow sloped surfaces. Only one *Selection* orientation is stored at a time — running the tool again overwrites it.
