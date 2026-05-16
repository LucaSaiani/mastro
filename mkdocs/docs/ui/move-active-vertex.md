# Move Active Vertex

The **Move Active Vertex** operator positions the active vertex along the direction defined by the previous vertex in the selection history. It accepts a typed numeric value or an arithmetic expression, making it possible to place vertices at precise distances without using the standard G shortcut.

## Keyboard Shortcut

**Alt+G** in Edit Mode (with at least two vertices selected).

## How It Works

1. In Edit Mode, select two or more vertices in sequence — the order of selection matters.
2. Press **Alt+G**.
3. Type a distance value. The active vertex (the last one you selected) moves along the direction from the previous vertex toward it, at the typed distance from the previous vertex.
4. Press **Enter** to confirm, or **Esc** to cancel and restore the original position.

## Input

The operator accepts:

- **Integers and decimals** — e.g. `3.5`
- **Arithmetic expressions** — e.g. `3.5 + 0.15`, `12 / 4`, `2.5 * 3`
- **Negation** — prefix or suffix the value with `-` to move in the opposite direction
- **Backspace** — remove the last character
- **Real-time preview** — the vertex moves as you type; the current expression is shown in the viewport header

## Practical Use

This operator is designed for architectural precision work:

- Placing a vertex at a specific distance along a wall line: select the wall corner, then the point to move, type `3600` (if the scene unit is millimetres) or `3.6` (if metres).
- Splitting a façade at a known setback: select two edge endpoints, invoke the operator, type the setback distance.
- Quick arithmetic without a calculator: `(3.5 + 0.15) * 2` gives the exact result inline.

## Requirements

- At least **two vertices** must be selected.
- The active vertex (the one that moves) is the **last selected** in history.
- The reference vertex (the one that defines the direction) is the **second-to-last** selected.
