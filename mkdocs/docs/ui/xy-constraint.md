# XY Constraint

The XY Constraint is a toggle that modifies the behaviour of the **G** (Move) and **R** (Rotate) shortcuts so that transforms are automatically constrained to the horizontal plane, without having to manually press **Z** or **Shift+Z** after every operation. This is particularly useful in architectural modelling, where almost all moves and rotations happen in the XY plane.

A small toggle button appears in the **Tool Header** (the horizontal bar at the top of the 3D Viewport). Click it to enable or disable the constraint globally. The setting is stored per scene.

When XY Constraint is **enabled**:

| Shortcut | Result |
|---|---|
| **G** | Move constrained to the XY plane (Z axis locked) |
| **R** | Rotate around the Z axis only |

When **disabled**, **G** and **R** behave as standard Blender. The constraint applies in both Object Mode and Edit Mode.

You can still apply additional constraints manually after invoking the operator (e.g. pressing **X** during a move to further constrain to the X axis only).
