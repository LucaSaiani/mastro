# MaStro Panel

The **MaStro** panel appears in the sidebar of the 3D Viewport (**N** to toggle) under the **MaStro** tab. It is visible when the active object is **not** a MaStro object — no object selected, not a mesh, or not yet assigned a MaStro type. It provides the entry point for bringing existing geometry into the MaStro workflow.

**Convert to MaStro Mass** — Converts all selected mesh objects into Mass objects by adding the necessary custom attributes and Geometry Nodes modifier. The original geometry is preserved. Use this when you have already modelled a footprint (e.g. imported from DXF) and want to assign MaStro parameters to it.

**Convert to MaStro Street** — Converts all selected mesh objects into Street objects by adding the street custom attributes and Geometry Nodes modifier. Use this when you have an edge network representing roads.

!!! note
    To create a new MaStro object from scratch, use **Shift+A → MaStro** in the 3D Viewport. This panel is only shown when the active object is not already a MaStro object.
