# Node Editor

MaStro adds a **MaStro** tab to the sidebar of the **Node Editor** when a Geometry Nodes or Shader Nodes tree is open. It provides utilities for managing nodes and a data-analysis scheduling system.

---

## MaStro Panel

The MaStro panel appears when a node is selected. The available controls depend on the type of active node.

### Rename Reroute

Available when the active node is a **Reroute** node.

**Rename Reroute from Source Socket**  
Automatically renames the reroute node to match the name of the socket it is connected to. Useful for keeping complex node trees readable without manually typing names.

Keyboard shortcut: **Shift+Ctrl+F2**.

### Sort Multi-Input

Available when the active node is a **Join Geometry** or **Geometry to Instance** node.

**Sort Multi-Input**  
Re-orders the inputs of the selected node. This is useful when the order of geometry inputs matters for subsequent operations and the automatic wiring order is not what you need.

### Sticky Note

Available when the active node is a **Frame** node.

If the frame already has a sticky note attached:  
**Edit the Sticky Note** — opens an editor to modify the note text and appearance.

If the frame does not have a sticky note:  
**Add a Sticky Note** — converts the frame into a styled sticky note with editable text.

Sticky notes are a lightweight annotation system for documenting node trees directly inside the node editor.

---

## Note Sub-panel

The **Note** sub-panel appears below the MaStro panel when a Frame node is selected. It provides the same sticky note controls in a dedicated collapsible section.

---

## Schedule System

MaStro includes a **custom node tree** type (the MaStro Schedule) for building data analysis and area schedules directly inside Blender's Node Editor. Open the Node Editor, switch the tree type to **MaStro**, and the schedule nodes become available.

The schedule system provides nodes for:

- **Input nodes** — read data from all MaStro objects in the scene, or from the current selection only.
- **Attribute nodes** — extract specific attributes (area, use, storey level, perimeter, etc.) from the input objects.
- **Math nodes** — perform arithmetic operations on the extracted data.
- **Table nodes** — aggregate and format data into a table structure.
- **Viewer node** — display the computed table directly in the node editor.

This system allows you to build live area schedules, floor-by-floor breakdowns, and custom aggregations without leaving Blender. The schedule updates automatically when the selection or the MaStro object parameters change.

!!! note
    Detailed documentation of each schedule node is provided in the [Nodes — Utilities](../nodes/utilities.md) section.
