# Architecture Panel

The **Architecture** panel appears in the MaStro sidebar tab when a **Mass** or [Plan](mastro-plan.md) object is in Edit Mode. It exposes wall and floor type assignments at the element level — the same attribute schema (`mastro_wall_id` on edges, `mastro_floor_id` on faces) is shared by both object types.

## Wall Type (Edge Select Mode)

When the mesh is in **Edge Select** mode, the panel shows:

**Wall Type**  
A dropdown listing all wall types defined in the project. Assigns the selected wall type to all selected edges. The wall type carries thickness and offset properties used by Geometry Nodes to generate the wall geometry.

**Flip Normal**  
Inverts the wall normal for the selected edges. The normal direction determines which side of the edge the wall thickness is applied to.

## Floor Type (Face Select Mode)

When the mesh is in **Face Select** mode, the panel shows:

**Floor Type**  
A dropdown listing all floor types defined in the project. Assigns the selected floor type to all selected faces.

---

!!! note
    Wall types and floor types are defined in the **Properties editor** under *Project Data → Architecture*. See [Properties — Project Data](properties-project-data.md) for the full list of controls.
