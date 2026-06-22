# MaStro Frame

A **MaStro Frame** is an Empty object representing a printable sheet — it defines the paper size used when [exporting to PDF](sidebar-export.md#export-frame-pdf), either individually or as part of a [PDF Set](properties-pdf-sets.md).

**Created with:** *Add → MaStro → Frame*

---

## How it works

The frame's footprint in the viewport is its X/Y scale, set from a chosen paper format. Exporting to PDF renders whatever Grease Pencil geometry intersects the frame's footprint, at the frame's paper size.

## Paper size

| Setting | Description |
|---|---|
| **Format** | ISO 216 paper size: A0–A4, or **Custom** |
| **Orientation** | Landscape or Portrait — swaps width/height |
| **Width / Height** | Size in millimetres; only editable when Format is **Custom** |

Switching Format to one of the standard ISO sizes overwrites Width/Height with that size's dimensions (oriented per the Orientation setting); switching back to Custom keeps whatever Width/Height were last set.

## Where to edit it

Both panels show the same Format/Orientation/Width/Height controls:

| Location |
|---|
| **Properties → Object Data Properties** (when a MaStro frame Empty is the active object) |
| **Viewport sidebar (N) → MaStro → Frame** |
