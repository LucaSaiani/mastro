# XY Constraint

The XY Constraint is a toggle that modifies the behaviour of the **G** (Move) and **R** (Rotate) shortcuts so that transforms are automatically constrained to the horizontal plane, without having to manually press **Z** or **Shift+Z** after every operation.

This is particularly useful in architectural modelling, where almost all moves and rotations happen in the XY plane and adding a Z constraint by hand on every operation is tedious.

## The Toggle Button

A small toggle button appears in the **Tool Header** (the horizontal bar at the top of the 3D Viewport). It shows a custom icon indicating whether the constraint is active.

Click the button to enable or disable XY constraint globally. The setting is stored per scene.

## Constrained Behaviour

When XY Constraint is **enabled**:

| Shortcut | Result |
|---|---|
| **G** | Move constrained to the XY plane (Z axis locked) |
| **R** | Rotate around the Z axis only |

When XY Constraint is **disabled**, **G** and **R** behave exactly as standard Blender — no constraint is applied.

The constraint applies in both **Object Mode** and **Edit Mode**.

## Combining with Other Constraints

XY Constraint replaces the default Blender G/R shortcuts. You can still apply additional constraints manually after invoking the operator (for example, pressing **X** during a G operation to further constrain to the X axis only).

## Keyboard Shortcut

The toggle can also be activated via the **G** and **R** keys directly — the operator checks the toggle state and applies the constraint accordingly. There is no separate shortcut to toggle the button itself; use the header button.
