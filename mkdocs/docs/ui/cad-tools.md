# CAD Tools

MaStro adds a set of CAD-style drawing and editing tools for working with [Drawing Mesh](../getting-started/object-type-drawing.md) edges directly in the 3D viewport: Rectangle, Circle, Offset, Trim/Extend, Fillet, and Delete Segment. All of them work in Edit Mode on a mesh, drawing on the plane defined by the active [transform orientation](transform-orientation.md), and most support live numeric input and snapping.

## Where to find them

| Location | Contents |
|---|---|
| **Add → Mesh** (Object or Edit Mode) | Rectangle and Circle creation submenus |
| **Edit Mode → Edge menu** | Offset, Fillet, Trim / Extend, Delete Segment |
| **Pie menu — `Alt+C`** | Offset, Trim, Fillet, Delete Segment |
| **`Alt+G`** (edge/vertex of a tagged rectangle or circle active) | Edit Rectangle / Edit Circle, dispatched automatically based on what's selected |

## Common conventions

- **Numeric input**: while a tool is active, typing digits (and `,`/`.` as decimal separator, `+-*/` as operators) builds up an exact value for the tool's main parameter (radius, distance, length); **Backspace** deletes the last typed character.
- **Snapping**: most tools snap the mouse to nearby vertices/edges; hold **Ctrl** to temporarily disable snapping.
- **Mouse wheel**: where a tool produces curved or segmented geometry (Circle, Fillet arcs), the wheel changes the segment count.
- **RMB / Esc**: cancels the tool without modifying the mesh. **LMB / Enter**: confirms.
- Every tool preserves the layer/thickness/dash-pattern attributes of the edges it creates from, edits, or splits — new geometry is never left with default "untagged" attributes.

---

## Rectangle

Four variants, all producing a 4-edge rectangle, found under **Add → Mesh → Rectangle**:

| Variant | Clicks |
|---|---|
| **Diagonal** | Click 1: one corner. Click 2: the opposite corner. |
| **Base Line** | Click 1: base line start. Click 2: base line end (sets the rectangle's X axis). Click 3: width, perpendicular to the base line — sign follows the mouse. |
| **Center** | Click 1: center. Click 2: a corner (or type `W;H` for exact half/full dimensions). |
| **Center Line** | Click 1: center of one edge. Click 2: center of the opposite edge (sets direction and length). Mouse or typed value: half-width perpendicular to the center line. |

For **Center** and **Center Line**, press **H** to toggle whether the typed/dragged dimension is interpreted as a half-dimension or a full dimension.

Works in both Edit Mode (adds geometry to the active mesh) and Object Mode (creates a new object).

### Editing a rectangle afterwards

Select an edge or vertex of a previously created rectangle and press **Alt+G** to invoke **Edit Rectangle**: drag any of its 4 corner handles to resize/reshape it, with the same snapping as creation. Click to confirm, Esc to cancel.

---

## Circle

Two variants, found under **Add → Mesh → Circle**:

### Center + Radius

Click 1 sets the center; moving the mouse previews the radius (drawn as a closed polyline with the current segment count); click 2 or Enter confirms.

| Control | Effect |
|---|---|
| Mouse wheel | Increase/decrease segment count (3–256) |
| **Tab** | Cycle the snap target between **Vertex** (vertices placed on the circle) and **Midpoint** (edge midpoints on the circle, vertices slightly outside — useful when drawing a regular polygon with a given *inscribed* radius) |
| Digits | Type an exact radius |

### 3 Inputs

A more general circle/arc constructor: each click adds a geometric constraint to a pool — clicking empty space adds a point constraint, clicking an edge adds a tangent-line constraint, clicking a vertex adds a point constraint plus all its incident edges as tangent constraints. Typing a number adds a floating radius constraint that replaces the mouse as the third input.

At every moment, MaStro solves all valid triples of constraints from the pool (point/point/point, point/point/edge, point/edge/edge, edge/edge/edge, or any pair plus a radius) and previews every valid solution as a white dotted circle, highlighting the one nearest the mouse in orange. Click (away from an edge/vertex) or press Enter/Space to confirm the highlighted solution. Backspace removes the last click (or the last digit of a typed radius).

### Editing a circle or arc afterwards

Select an edge or vertex of a previously created circle/arc and press **Alt+G** to invoke **Edit Circle**:

| Handle | Effect |
|---|---|
| Radius handle | Mouse changes radius and rotation; wheel changes segment count |
| Center handle | Mouse translates the whole shape |
| Arc handles (`<` `>`, arcs only) | Mouse extends/trims the arc endpoint step by step (the arc's span stays fixed; only how far around the circle it reaches changes); wheel changes segment count |

Hold **Ctrl** to disable snapping while dragging.

---

## Offset

**Edge menu / pie menu → Offset.** Select one or more connected edges (a "chain") and run Offset to create a parallel copy at a typed or mouse-controlled distance.

- If a chain has an active edge, only the edges reachable from it without crossing a junction (a vertex shared by more than 2 edges) are offset as one chain — so offsetting one wall of a closed room only needs that wall selected, even if the whole room is selected.
- The offset plane is detected automatically from the geometry: the local axis with the smallest spread is used as the plane normal, so flat geometry is offset within its own plane regardless of orientation.
- Corners are mitred automatically.
- A dotted guide line is drawn from the mouse to the point on the source edge that the current distance is being measured from, making clear which segment is driving the calculation.

| Control | Effect |
|---|---|
| Mouse / digits | Offset distance |
| **C** | Toggle **Connect Ends**: add edges joining the endpoints of the original and offset chains, closing the gap |

---

## Trim / Extend

**Edge menu / pie menu → Trim / Extend.** Cuts or extends a set of selected edges against one reference edge (the **knife**).

1. Make the knife edge the active edge (Shift-click it last).
2. Select the candidate edges to trim or extend against it (the knife itself does not need to stay selected as a candidate).
3. Run Trim / Extend. Each candidate is classified as:
    - **Cross** — physically crosses the knife: the candidate is split at the intersection, and the part on the opposite side from the mouse is discarded.
    - **Extend** — entirely on one side of the knife: if it's on the same side as the mouse, its nearer endpoint is extended to meet the knife (shown as a dotted preview); if not, nothing happens.
4. Move the mouse to choose which side is kept (for Cross) or which edges extend (for Extend) — the preview updates live (white = kept, red = removed, dotted = extension). Click to confirm.

| Key | Effect |
|---|---|
| **I** | Toggle **Infinite Knife** — treat the knife as an infinite line rather than stopping at its own endpoints |
| **C** | Toggle **Coplanar Only** — only trim edges that are truly coplanar with the knife in 3D; off uses apparent (screen-space projected) intersections instead |

---

## Fillet

**Edge menu / pie menu → Fillet.** Joins two edges (or two open profile endpoints) at a sharp corner, a chamfer, or a rounded arc.

Select either the two edges directly, or — to fillet the loose ends of an open profile — the two endpoint vertices, each the sole endpoint of exactly one edge. If the two edges already share a vertex, Fillet defaults straight to an 8-segment arc; otherwise it starts as a sharp corner.

Move the mouse to choose which sector of the two lines' intersection to fillet (relevant when the edges don't already meet).

| Control | Effect |
|---|---|
| Mouse wheel + **Ctrl** | Change segment count: `0` = sharp corner, `1` = chamfer, `2+` = arc |
| Digits | Typed radius (arc) or length (chamfer); without typing, radius/length follows the mouse |
| **L** | Toggle **Limit** — clamp the fillet so its tangent points never go past the segment's own endpoints, shrinking the radius if necessary |
| **Alt+G** while a Circle/Arc handle preview is visible | Jump straight to editing the resulting arc (see [Editing a circle or arc afterwards](#editing-a-circle-or-arc-afterwards)) |

---

## Delete Segment

**Edge menu / pie menu → Delete Segment.** Removes the portion of an edge that lies between its intersections with other edges — useful for breaking a line at a crossing without manually splitting it first.

Three sub-modes, cycled with **Q**:

| Mode | Behaviour |
|---|---|
| **Click** | Hover over an edge (silent snap, no indicator) and click to delete the sub-segment under the cursor. Stays active for repeated clicks; RMB exits. |
| **Polyline** | Click to place polyline points; every mesh edge crossed by the polyline has its crossed sub-segment deleted. RMB/Enter confirms and exits. An edge with no intersections at all is deleted entirely. |
| **Box** | Click once to set the first corner, click again to confirm the box; edges fully inside are deleted, edges crossing the border lose only their portion inside the box. |

In all modes, the segment that would be removed is previewed live in red, scaled to the edge's actual line thickness. Press **C** to toggle **Coplanar Only** (same meaning as in Trim/Extend). Esc cancels without applying.
