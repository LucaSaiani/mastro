# Core Concepts

MaStro is built around a single guiding idea: **model only the essentials, and let Geometry Nodes handle the rest**.

In a traditional 3D modelling workflow, the modeller builds every wall, every floor slab, every opening by hand. MaStro takes a different approach. The user draws a schematic — a flat footprint, a path, a network of edges — and assigns a set of parameters to it: how many storeys, what program, how deep. From that minimal input, a stack of Geometry Nodes generates the full three-dimensional result automatically. This means changing a parameter (adding a floor, switching from residential to office) updates the geometry instantly and non-destructively.

**Two layers**

MaStro operates on two distinct layers. The **Python layer** handles everything Geometry Nodes cannot do on its own: creating objects, assigning custom mesh attributes, managing project lists (typologies, uses, wall types, streets), and providing the sidebar and properties panels. When you adjust a parameter in the MaStro panel, Python writes it into the mesh's custom attributes. The **Geometry Nodes layer** reads those attributes and generates the final geometry — volumes, walls, openings, road surfaces — in real time.

**Typical workflow**

1. **Create** a Mass, Block, or Street object from the Add menu or by converting an existing mesh.
2. **Edit** the footprint in Edit Mode — draw the outline of a building, trace a street network, sketch a block perimeter.
3. **Assign parameters** in the MaStro sidebar: typology, number of storeys, wall type, street type.
4. **Refine** in the Properties editor: define typologies, adjust floor-to-floor heights, set wall thicknesses.
5. **Iterate** freely — all parameters can be changed at any time and the geometry updates immediately.

**Non-destructive by design**

Because MaStro stores its data in mesh attributes rather than in the geometry itself, the design is always editable. There is no bake step that locks you in. The Geometry Nodes stack can be muted, adjusted, or replaced without losing the underlying parametric data.
