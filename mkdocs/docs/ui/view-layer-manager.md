# View Layer Manager

The **View Layer Manager** replaces the default Blender view layer selector in the **topbar** (the horizontal bar at the very top of the Blender window). It adds the ability to **reorder view layers** — something Blender does not support natively.

## Topbar Controls

The topbar now shows, from left to right:

| Element | Description |
|---|---|
| **Scene selector** | Unchanged from standard Blender |
| **List button** (Render Layers icon) | Opens the View Layer pop-over |
| **Active layer name** | Shows and edits the name of the currently active view layer |
| **Duplicate** button | Adds a new view layer (with type options) |
| **Delete** button (**X**) | Removes the active view layer |

## View Layer Pop-over

Clicking the list button opens a floating panel containing the full view layer list. From here you can:

**Rename**  
Click on any layer name in the list to rename it inline. The rename propagates immediately to the actual Blender view layer.

**Reorder**  
Use the arrow buttons on the right side of the panel:

| Button | Action |
|---|---|
| ↑↑ (top bar) | Move selected layer to the top |
| ↑ | Move selected layer one position up |
| ↓ | Move selected layer one position down |
| ↓↓ (bottom bar) | Move selected layer to the bottom |

**Sort**  
The A→Z button opens a menu to sort all layers alphabetically, either ascending or descending.

**Add new layer**  
The Duplicate button in the pop-over opens a menu with three options:

- **New** — creates a new empty view layer.
- **Copy** — copies the settings of the current layer.
- **Blank** — creates a new layer with all collections disabled.

**Delete**  
The **X** button removes the selected view layer. Standard Blender restrictions apply (you cannot delete the last remaining layer).

## Shadow List

Blender does not expose an API for reordering view layers directly. MaStro maintains a **shadow list** — a copy of the layer names stored in the scene — and uses the order of this shadow list to present layers in the UI. Reordering in the pop-over reorders the shadow list; the actual Blender view layers remain in their original order but are displayed and activated through the shadow list.

Synchronisation between the shadow list and the actual layers happens automatically whenever layers are added, removed, or renamed from outside MaStro.
