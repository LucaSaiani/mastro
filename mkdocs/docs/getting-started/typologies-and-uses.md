# Typologies and Uses

The typology and use system is the core of MaStro's parametric approach. It describes **what a building contains, floor by floor**, and drives both the geometry generation and the area calculations.

## Uses

A **Use** is the basic building block: a single functional program occupying a contiguous set of floors. Each use is defined by three properties:

| Property | Description |
|---|---|
| **Name** | A label, e.g. *Residential*, *Office*, *Retail*, *Parking* |
| **Floor-to-floor height** | The vertical distance from one finished floor to the next, in metres |
| **Number of storeys** | How many floors this use occupies |
| **Variable storeys** | When enabled, the storey count is determined dynamically (see below) |

Uses are defined once per project in the Properties editor and can be reused across any number of typologies.

## Typologies

A **Typology** is an ordered stack of uses, from bottom to top. For example:

```
Typology: Mixed-Use Tower
  ├─ Ground Floor  (Retail,      4.50 m,  1 storey)
  ├─ Lower Floors  (Office,      3.60 m,  4 storeys)
  └─ Upper Floors  (Residential, 3.15 m,  variable)
```

Each face (Mass) or edge (Block) in the scene is assigned to one typology. Geometry Nodes reads the stacked use data and generates the correct floor heights.

## Fixed vs Variable Storeys

By default a use has a **fixed** storey count. The building height is the sum of all floor-to-floor heights multiplied by their respective storey counts.

When **Variable storeys** is enabled on a use, MaStro treats it as *liquid*: it automatically fills however many floors remain after all fixed-storey uses have been placed. This lets you set the total building height (via the *Number of Storeys* control in Edit Mode) and have one or more uses expand or contract to fill the gap.

If multiple uses are marked as variable, the remaining floors are distributed evenly between them.

## Undercroft

The **Undercroft** parameter (in the Override panel) designates a number of floors from the ground level downward as below-grade volume. These floors are grouped under a single *undercroft* entry in the face breakdown and can be treated differently by Geometry Nodes (e.g. rendered as a podium or basement).

## Top Floor Override

The **Top Floors** parameter overrides the topmost uses of a face or edge. When set to a value greater than zero, that many floors from the top of the stack are forced to match the use immediately below them. This is useful for penthouses, setbacks, or mechanical floors that share a program with the floors below.

## Project-Level vs Per-Object

Typologies and uses are **project-level** — they are defined once in the Properties editor and are available to every object in the scene. The assignment of a typology to a specific face or edge is stored as a mesh attribute on that object.

This separation means you can update a typology definition (for example, change the floor-to-floor height of the residential use) and the change propagates automatically to every face that uses that typology.
