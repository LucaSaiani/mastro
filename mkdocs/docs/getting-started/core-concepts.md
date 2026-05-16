# Core Concepts

## The Schematic Approach

MaStro is built around a single guiding idea: **model only the essentials, and let Geometry Nodes handle the rest**.

In a traditional 3D modelling workflow, the modeller builds every wall, every floor slab, every opening by hand. MaStro takes a different approach. The user draws a schematic — a flat footprint, a path, a network of edges — and assigns a set of parameters to it: how many storeys, what program, how deep. From that minimal input, a stack of Geometry Nodes generates the full three-dimensional result automatically.

This means that:

- Changing a parameter (say, adding a floor or switching from residential to office) updates the geometry instantly, non-destructively.
- Large masterplans with hundreds of buildings become manageable, because each building is defined by a small set of data rather than thousands of manually placed polygons.
- Architectural analysis (areas, perimeters, GEA) can be extracted directly from the parametric data, without any manual counting.

## Two Layers

MaStro operates on two distinct layers that work together:

**Python layer**
The Python component handles everything that Geometry Nodes cannot do on its own: creating objects, assigning custom mesh attributes, managing project lists (typologies, uses, wall types, streets), and providing the sidebar and properties panels. When you adjust a parameter in the MaStro panel, Python writes it into the mesh's custom attributes.

**Geometry Nodes layer**
The GN layer reads those custom attributes and generates the final geometry — volumes, walls, openings, road surfaces — in real time. All GN node groups are stored in a single `.blend` file and linked into the scene. You can inspect, extend, or replace them without touching the Python code.

## Typical Workflow

1. **Create** a Mass, Block, or Street object from the **Add** menu or by converting an existing mesh.
2. **Edit** the footprint in Edit Mode — draw the outline of a building, trace a street network, sketch a block perimeter.
3. **Assign parameters** in the MaStro sidebar: typology, number of storeys, wall type, street type.
4. **Refine** in the Properties editor: define new typologies, adjust floor-to-floor heights, set wall thicknesses.
5. **Iterate** freely — all parameters can be changed at any time and the geometry updates immediately.

## Non-Destructive by Design

Because MaStro stores its data in mesh attributes rather than in the geometry itself, the design is always editable. There is no "bake" step that locks you in. The Geometry Nodes stack can be muted, adjusted, or replaced without losing the underlying parametric data.
