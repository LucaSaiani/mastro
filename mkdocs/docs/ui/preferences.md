# Preferences

MaStro preferences are accessible via **Edit → Preferences → Extensions → MaStro**. They control the visual appearance of viewport overlays and node editor annotations.

---

## Overlay Settings

### Mass Overlay

Controls the appearance of the selection overlay drawn on **Mass** objects in Edit Mode.

| Setting | Description |
|---|---|
| **Edge Size** | Thickness of the edge overlay lines (pixels) |
| **Edge Color** | Colour of the edge overlay |
| **Face Color** | Colour of selected face highlights |

### Block Overlay

| Setting | Description |
|---|---|
| **Edge Size** | Thickness of the edge overlay lines for Block objects |

### Wall Overlay

| Setting | Description |
|---|---|
| **Edge Size** | Thickness of the wall type colour lines |

### Street Overlay

| Setting | Description |
|---|---|
| **Edge Size** | Thickness of the street type colour lines |

### Font

Controls the text labels drawn over mesh elements in the viewport (typology name, storey count, etc.).

| Setting | Description |
|---|---|
| **Size** | Font size in points |
| **Color** | Text colour including alpha |

---

## Node Note Settings

Controls the appearance of **Sticky Note** annotations in the Node Editor.

| Setting | Description |
|---|---|
| **Font Size** | Size of the sticky note text |
| **Font Color** | Text colour including alpha |

---

## 2D Projection Settings

Global settings for the projection and shadow system.

| Setting | Description |
|---|---|
| **Projection Suffix** | Suffix appended to every projected output object and to the parent empty (default `_projection`). Changing this after a calculation does not rename existing objects. |
| **Section Offset** | Distance the section outline mesh is moved **toward** the camera so it masks projection lines that pass behind it. Default 10 mm. |
| **Shadow Offset** | Distance the shadow mesh is moved **away** from the camera so it does not mask projection lines in front of it. Default 10 mm. |
