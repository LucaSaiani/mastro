# Drawing Mesh

A **Drawing Mesh** object is a flat mesh where every **edge** represents a drawn line. It is the MaStro way to produce 2D technical drawings — floor plans, sections, elevations — without leaving the 3D viewport.

**Created with:** *Add → MaStro → Drawing (Mesh)*  
**Edit Mode geometry:** edges — extrude vertices to add new lines  
**Typical use:** architectural drawings, line-work overlays, technical annotations.

---

## How it works

Each edge carries a set of named attributes that describe its appearance: which layer it belongs to, its thickness, its dash pattern, its colour, and whether it should be rendered in black. A Geometry Nodes modifier reads these attributes and converts the mesh to a Grease Pencil object at render time.

Because the drawing is a mesh, all standard Blender mesh tools work on it: snapping, mirroring, array modifiers, and so on. The drawing can also coexist in the same file as Mass, Block, and Street objects.

---

## Layers, pens and line styles

Every edge belongs to exactly one **layer**, identified by an integer ID stored as an edge attribute. The layer references a **pen** (which controls line weight and colour) and a **line style** (which controls the dash pattern). Changing any of these in the properties panel propagates immediately to all edges on that layer across all drawing objects in the scene.

See [Layers, Pens and Line Styles](../ui/drawing-layers.md) for the full panel reference.

---

## Drawing workflow

1. Use *Add → MaStro → Drawing (Mesh)* to add a new drawing object. A single edge is created at the 3D cursor position, already tagged with the active layer's attributes.
2. Enter Edit Mode. Select the endpoint vertex and use **Extrude Vertex** (`E` or `Alt+D`) to extend the line. Each new edge is automatically assigned the currently active layer.
3. To change which layer a group of edges belongs to, select the edges and use **Assign Layer to Selected Edges** from the layer header popover.
4. To draw across multiple objects simultaneously, enter Edit Mode on several drawing meshes at once. The layer assignment operator acts on all of them.

!!! note
    The active layer is tracked by the **MaStro Layers** panel in the Properties editor. Switch layers there before extruding to assign the correct attributes.
