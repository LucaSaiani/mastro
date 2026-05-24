# Block

A **Block** object represents a building perimeter as a path of **edges**. Each edge defines one façade line and carries parameters for typology, depth (the distance from the façade line to the back of the building), storey count, and façade normal direction.

Geometry Nodes generates the building volume by extruding along the edge direction and offsetting inward by the depth value. A Block object carries two modifiers simultaneously: *MaStro Block* (which generates the perimeter massing) and *MaStro Mass* (which reads the resulting volume for further processing).

**Created with:** *Add → MaStro → Block*  
**Edit Mode geometry:** edges — select edges to assign parameters  
**Typical use:** urban blocks where the building follows the street edge with a controlled setback depth.
