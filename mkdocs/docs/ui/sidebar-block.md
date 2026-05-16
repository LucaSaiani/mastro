# Block Panel

The **Block** panel appears in the MaStro sidebar tab when the active object is a **Block** object. Like the Mass panel, its content changes depending on the current mode and selection mode.

## Object Mode

**Block**  
Assigns the block object to one of the project-level blocks.

## Edit Mode

In Edit Mode the available controls depend on which element type is currently selected.

### Edge Select Mode

**Side Rotation**  
A rotation angle (in degrees) applied to the building volume perpendicular to the edge direction. This lets you adjust the angle of the building façade relative to the street line.

### Face Select Mode

When faces are selected (available after the Block modifier generates geometry), the following controls are active:

**N° of Storeys**  
Total number of floors for the selected edges/faces.

**Typology**  
Assigns a typology to the selected elements.

**Use breakdown**  
Read-only list of uses stacked on the active element, from bottom to top.

**Depth**  
The distance from the façade edge to the back of the building volume, in metres. Controls how deep the building extends behind the street line.

**Flip Normal**  
Inverts the direction the building volume is extruded from the edge. Toggle this if the building appears on the wrong side of the street line.

## Override Sub-panel

The **Override** sub-panel (collapsed by default) provides the same **Top Floors** and **Undercroft** controls as the Mass panel. See [Mass Panel — Override](sidebar-mass.md#override-sub-panel) for details.
