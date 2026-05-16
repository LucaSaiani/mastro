# Object Types

MaStro works with four types of mesh objects, each identified by a custom property on the mesh data. The type determines which Geometry Nodes modifier is applied and which attributes and panels become available.

## Mass

A **Mass** object represents the footprint of one or more buildings as a flat mesh of **faces**. Each face is an independent building surface that can carry its own parameters: typology, number of storeys, wall type, floor type.

Geometry Nodes extrudes each face vertically according to the storey data, generating the massing volume. When multiple faces share an edge, the system handles the shared wall correctly.

**Created with:** *Add → MaStro → Mass*  
**Edit Mode geometry:** faces (select faces to assign parameters)  
**Typical use:** individual buildings, groups of buildings, masterplan massing studies.

## Block

A **Block** object represents a building perimeter as a path of **edges**. Each edge defines one façade line and carries parameters for typology, depth (the distance from the façade line to the back of the building), storey count, and façade normal direction.

Geometry Nodes generates the building volume by extruding along the edge direction and offsetting inward by the depth value. A Block object carries two modifiers simultaneously: *MaStro Block* (which generates the perimeter massing) and *MaStro Mass* (which reads the resulting volume for further processing).

**Created with:** *Add → MaStro → Block*  
**Edit Mode geometry:** edges (select edges to assign parameters)  
**Typical use:** urban blocks where the building follows the street edge with a controlled setback depth.

## Street

A **Street** object represents a road network as a graph of **edges**. Each edge is assigned a street type, which carries width and corner radius. Geometry Nodes generates the road surface, intersections, and lane geometry from this edge graph.

**Created with:** *Add → MaStro → Street*  
**Edit Mode geometry:** edges (select edges to assign a street type)  
**Typical use:** road networks, pedestrian paths, urban infrastructure.

## Dimension

A **Dimension** object is a single vertical edge used as an anchor for an architectural dimension annotation. Geometry Nodes generates the dimension graphic — line, ticks, and label — from this minimal input.

**Created with:** *Add → MaStro → Dimension*  
**Typical use:** floor-to-floor dimensions, section heights, annotated drawings.

## Converting Existing Meshes

If you already have a mesh you want to use as a MaStro object, you do not need to recreate it. Use the conversion operators in the MaStro sidebar panel:

- **Convert to MaStro Mass** — adds Mass attributes and node groups to all selected meshes.
- **Convert to MaStro Street** — adds Street attributes and node groups to all selected meshes.

The original geometry is preserved; only the custom attributes and modifiers are added.
