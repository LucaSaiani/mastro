# Object Types

MaStro works with five types of mesh objects, each identified by a custom property on the mesh data. The type determines which Geometry Nodes modifier is applied and which attributes and panels become available.

| Type | Geometry | Description |
|---|---|---|
| [Mass](object-type-mass.md) | Faces | Building footprints |
| [Block](object-type-block.md) | Edges | Perimeter-based buildings |
| [Street](object-type-street.md) | Edges | Road networks |
| [Dimension](object-type-dimension.md) | Single edge | Annotation anchor |
| [Drawing Mesh](object-type-drawing.md) | Edges | 2D technical drawings |

If you already have a mesh you want to use as a MaStro object, use **Convert to MaStro Mass** or **Convert to MaStro Street** from the MaStro sidebar panel. The original geometry is preserved; only custom attributes and modifiers are added.
