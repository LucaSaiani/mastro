# Mass

A **Mass** object represents the footprint of one or more buildings as a flat mesh of **faces**. Each face is an independent building surface that can carry its own parameters: typology, number of storeys, wall type, floor type.

Geometry Nodes extrudes each face vertically according to the storey data, generating the massing volume. When multiple faces share an edge, the system handles the shared wall correctly.

**Created with:** *Add → MaStro → Mass*  
**Edit Mode geometry:** faces — select faces to assign parameters  
**Typical use:** individual buildings, groups of buildings, masterplan massing studies.
