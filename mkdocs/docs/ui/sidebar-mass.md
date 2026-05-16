# Mass Panel

The **Mass** panel appears in the MaStro sidebar tab when the active object is a **Mass** object. Its content changes depending on whether the object is in Object Mode or Edit Mode.

## Object Mode

In Object Mode the panel shows the assignment of the mass object to project-level categories:

**Block**  
Assigns the object to one of the blocks defined in the Project Data. A block groups multiple buildings into a named urban unit.

**Building**  
Assigns the object to one of the buildings defined in the Project Data. A building may contain multiple mass objects (e.g. separate footprints for different parts of the same building).

## Edit Mode

In Edit Mode the panel shows **face-level parameters**. The panel is fully enabled only when the mesh is in **Face Select** mode; it is greyed out in Vertex or Edge Select mode.

Select one or more faces and the panel reflects the parameters stored on the active face. Changing a value writes it to all selected faces.

**N° of Storeys**  
The total number of floors for the selected faces. This value drives how the typology's uses are distributed vertically. If the typology contains variable-storey uses, they expand or contract to reach this total.

**Typology**  
A dropdown listing all typologies defined in the project. Selecting a typology assigns its use stack to the selected faces and recalculates the storey distribution.

**Use breakdown**  
A read-only list showing the uses stacked on the active face, from bottom to top. Each row shows the use name and the number of storeys it occupies. This list is rebuilt automatically whenever the typology or storey count changes.

## Override Sub-panel

The **Override** sub-panel (collapsed by default) exposes two additional controls for fine-tuning individual faces:

**Top Floors**  
Forces the topmost *N* floors to match the use immediately below them. Useful for penthouses or mechanical floors.

**Undercroft**  
Designates *N* floors from the ground level downward as below-grade volume. These floors are grouped under a single *undercroft* entry in the breakdown.
