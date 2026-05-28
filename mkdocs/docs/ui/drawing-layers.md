# Drawing: Layers, Pens and Line Styles

The **MaStro Drawing** section of the Properties editor contains three sub-panels — Layers, Pens, and Line Styles — that together define the appearance of every line in the drawing.

---

## Layers panel

The layers list shows all layers defined in the scene. Each layer is a named record that groups edges by appearance.

**Layer list**

Each row shows the layer name, a visibility toggle, and a lock toggle. The active layer (highlighted) is the one whose attributes are assigned to newly extruded edges.

Use the **+** and **−** buttons to add or remove layers. Locked layers cannot be removed.

**Layer properties** (shown below the list when a layer is selected)

- **Name** — display label; does not affect attribute storage.
- **Pen** — drop-down showing enabled pens. Determines line weight and default colour.
- **Line Style** — drop-down showing the available dash patterns.
- **Colour** — stroke colour for this layer. When *Use Pen Colour* is active (link icon next to the colour), this value is kept in sync with the selected pen's colour.
- **Visible** — when disabled, all edges on this layer produce no output in the Grease Pencil result.
- **Black** — marks edges on this layer as candidates for [Black Mode](#black-mode-toggle).

**Toolbar row** (below the list)

- **Sync** — manually triggers a full update of all drawing mesh attributes and rebuilds the Geometry Nodes group. Use this when *Auto Update* is disabled.
- **Auto Update** (refresh icon toggle) — when enabled, any change to a layer, pen, or line style propagates to the mesh attributes immediately.
- **Black Mode** (solid shading icon toggle) — global override; see [Black Mode](#black-mode-toggle) below.

**Header popover**

The layer name shown in the 3D viewport header opens a popover with a compact layer list and the **Assign Layer to Selected Edges** button, which writes the active layer's ID and attributes to all selected edges across all drawing meshes currently in Edit Mode.

---

## Pens panel

Each pen defines the physical weight and default colour of a line.

- **Thickness** — in millimetres. Stored internally as a radius in metres (`thickness / 2000`).
- **Colour** — used as the layer colour when *Use Pen Colour* is active on the layer.
- **Active** toggle — disabled pens are hidden from the pen drop-down in the layer properties.
- **Locked** toggle — prevents accidental edits.

Pens are sorted by thickness. Changing a pen's thickness or colour propagates immediately to all layers that reference it.

---

## Line Styles panel

A line style defines the dash pattern of a stroke. Up to three dash–gap pairs are available:

| Field | Meaning |
|-------|---------|
| `l1`  | Length of the first dash |
| `g1`  | Gap after the first dash |
| `l2`  | Length of the second dash |
| `g2`  | Gap after the second dash |
| `l3`  | Length of the third dash |
| `g3`  | Gap after the third dash |

A line style is **continuous** when `g1`, `l2`, `g2`, `l3`, and `g3` are all zero. In this case `l1` is ignored for resampling purposes and the edge is rendered as an unbroken stroke. All other configurations produce a **dashed** line, where the Geometry Nodes pipeline resamples the curve before applying the pattern.

---

## Black Mode toggle

The **Black Mode** toggle (solid shading icon in the layer toolbar) is a global scene switch. When enabled, it writes `True` to the `mastro_drawing_black_switch` attribute on every edge of every drawing mesh. When disabled, it writes `False`.

In the Geometry Nodes pipeline, an edge is rendered in black only when **both** conditions are true:

- The edge's `mastro_drawing_black` attribute is `True` (set because its layer has the Black flag enabled).
- `mastro_drawing_black_switch` is `True` (the global toggle is on).

This design lets you prepare layers with the Black flag in advance and switch the entire drawing to black-line mode with a single click, without losing any layer-level colour information.

The black stroke uses the `Mastro_GP_Black` material, a solid black GP material created automatically on first sync.
