# MaStro Plan

A **MaStro Plan** is a single flat-face mesh representing a floor plan, kept in sync with the project's [Levels](properties-levels.md). It carries the same wall/floor attribute schema as [Mass](../getting-started/object-type-mass.md), so the same [Architecture](sidebar-architecture.md) sidebar panel is used to draw walls and assign floor types directly on the plan.

**Created with:** *Add → MaStro → Plan*

---

## How it works

A new plan is a flat rectangular quad (**Width** / **Depth** at creation) sized and positioned at the 3D cursor's X/Y. Its elevation, however, is never left at the 3D cursor's Z: a plan is always created **locked to a project level** — the level whose [Clip Range](clip-range.md) is currently active in whichever Top/Bottom ortho viewport — and its Z position is taken from that level's elevation instead.

While locked, two values are driven automatically and shown read-only in the sidebar panel:

| Value | Driven by |
|---|---|
| **FFL** (Finished Floor Level) | The locked level's elevation — written to the object's Z location |
| **Height** (floor-to-floor) | The distance to the next level up — written to the **MaStro Plan** Geometry Nodes modifier |

Because these are object-level properties (not stored on the mesh), two plans can share the same mesh data and still sit at different elevations.

If the project's Level List changes — a level is added, removed, or its elevation edited — every locked plan recalculates its FFL and Height automatically; no manual update is needed.

The plan's Z location is locked (`obj.lock_location[2]`) so it can't be accidentally dragged off its level in the viewport.

## Locking and unlocking

The **Plan** sidebar panel (Viewport sidebar (N) → MaStro → Plan) shows the lock state and lets you change it:

| Control | Available when | Effect |
|---|---|---|
| **FFL**, **Height** | Always shown; editable only when unlocked | Elevation and floor-to-floor height. Read-only while locked, since they're driven by the level lock |
| **Unlock** | Locked | Removes the drivers — FFL and Height become freely editable, independent of the project's levels |
| **Lock to Active Level** | Unlocked | Re-locks the plan to whichever level is active in the Clip Range |
| Level dropdown (▾, next to Lock to Active Level) | Unlocked | Locks the plan to a specific level chosen from the full Level List, instead of the active one |

## Walls and floors

A plan uses the exact same edge/face attributes as Mass (`mastro_wall_id`, `mastro_floor_id`) — see [Plan Attributes](../reference/custom-attributes.md#plan-attributes). Assign them the same way as on a Mass object: select edges or faces in Edit Mode and use the **Architecture** sidebar panel's Wall Type / Floor Type dropdowns.

## Custom properties

Plan is one of the object types that scene-level [Custom Properties](../reference/custom-attributes.md#custom-properties-per-object) can target — toggle **Plan** when defining a property to have it added to every plan object in the scene.
