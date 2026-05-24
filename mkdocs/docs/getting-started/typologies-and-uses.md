# Typologies and Uses

The typology and use system is the core of MaStro's parametric approach. It describes **what a building contains, floor by floor**, and drives both geometry generation and area calculations.

| Concept | Description |
|---|---|
| [Use](typologies-use.md) | A single functional program occupying a contiguous set of floors |
| [Typology](typologies-typology.md) | An ordered stack of uses, from bottom to top |
| [Fixed vs Variable Storeys](typologies-storeys.md) | How floor counts are assigned |
| [Undercroft](typologies-undercroft.md) | Below-grade floors |
| [Top Floor Override](typologies-top-floor.md) | Overriding the topmost floors |

Typologies and uses are **project-level** — defined once in the Properties editor and available to every object in the scene. The assignment of a typology to a specific face or edge is stored as a mesh attribute on that object.
