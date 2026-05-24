# Move Active Vertex

The **Move Active Vertex** operator positions the active vertex along the direction defined by the previous vertex in the selection history. It accepts a typed numeric value or an arithmetic expression, making it possible to place vertices at precise distances without using the standard G shortcut.

**Keyboard shortcut:** **Alt+G** in Edit Mode (with at least two vertices selected).

In Edit Mode, select two or more vertices in sequence — order matters. Press **Alt+G**, then type a distance value. The active vertex (last selected) moves along the direction from the previous vertex toward it. Press **Enter** to confirm or **Esc** to cancel.

The operator accepts integers, decimals (`3.5`), arithmetic expressions (`3.5 + 0.15`, `12 / 4`), and negation (prefix `-` to move in the opposite direction). The vertex moves in real time as you type; the current expression is shown in the viewport header.

**Requirements:** at least two vertices must be selected. The active vertex (last selected) is the one that moves; the second-to-last defines the direction.
