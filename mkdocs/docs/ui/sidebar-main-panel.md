# MaStro Panel

The **MaStro** panel appears in the sidebar of the 3D Viewport (press **N** to toggle it) under the **MaStro** tab.

This panel is visible when the active object is **not** a MaStro object — either because no object is selected, the selected object is not a mesh, or the mesh has not yet been assigned a MaStro type. It provides the entry point for bringing existing geometry into the MaStro workflow.

## Convert to MaStro Mass

Converts all selected mesh objects into **Mass** objects by adding the necessary custom attributes and Geometry Nodes modifier. The original geometry is preserved.

Use this when you have already modelled a footprint (for example, imported from a DXF or drawn manually) and want to assign MaStro parameters to it.

## Convert to MaStro Street

Converts all selected mesh objects into **Street** objects by adding the street custom attributes and Geometry Nodes modifier.

Use this when you have an edge network representing roads and want to assign street types to it.

---

!!! note
    To create a new MaStro object from scratch, use the **Add** menu in the 3D Viewport (**Shift+A → MaStro**). This panel is only shown when the active object is not already a MaStro object.
