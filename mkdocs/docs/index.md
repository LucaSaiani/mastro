# Introduction

![MaStro Logo](assets/mastro_logo.png)

MaStro is a Blender extension for architects and anyone interested in rapidly producing parametric architectural and urban models — from a single building up to a masterplan of hundreds, complete with technical drawings ready for print. The name reflects that range: it can be read as *Masterplan and Roads*, *Mass and Streets*, or simply the Italian word for a skilled craftsman or teacher.

The core idea has stayed the same since the first version: the user models only the essentials — a schematic footprint, a centreline, a floor plan — and assigns the parameters that define the rest (height, building type, usage, wall and floor types). Geometry Nodes does the modelling from there. What has grown around that core is a full pipeline for taking a project from massing study to printed plans.

---

## Parametric modelling

[**Mass**](getting-started/object-type-mass.md) and [**Block**](getting-started/object-type-block.md) objects turn a flat footprint or perimeter into a fully storeyed building, driven by [Typologies and Uses](getting-started/typologies-and-uses.md) — named presets for storey height, count, and floor usage that can be reused across an entire project. [**Street**](getting-started/object-type-street.md) objects do the same for road networks. The [Node Library](nodes/overview.md) behind all of this covers everything from façades and openings to stairs, roofs, and site annotation, and is designed to be extended with your own node groups.

## Architectural drawing

[**Plan**](ui/mastro-plan.md) objects represent a floor plan locked to a project [Level](ui/properties-levels.md), with walls and floor types assigned the same way as on a Mass. The [Clip Range](ui/clip-range.md) control sections the viewport to a chosen level for editing or reference. For drawings that aren't generated from the 3D model, the [Drawing Mesh](getting-started/object-type-drawing.md) object type and its [CAD Tools](ui/cad-tools.md) (Rectangle, Circle, Offset, Trim, Fillet…) provide a full line-drawing toolset with layers, pens, and line styles.

## 2D Projection

The [2D Projection](ui/projection.md) system generates line drawings and cast shadows directly from any camera's view of the 3D scene — plans, sections, and elevations extracted automatically, with visible/hidden/silhouette edges sorted onto the correct drawing layers.

## Output and layout

[**Album**](ui/mastro-album.md) objects group drawings under a shared print scale; [**Frame**](ui/mastro-frame.md) objects lay out a sheet at a standard paper size for [PDF export](ui/sidebar-export.md), individually or in batches via [PDF Sets](ui/properties-pdf-sets.md).

## GIS

The [GIS panel](ui/gis-basemap.md) imports georeferenced basemap imagery and Google 3D Tiles, anchored to a real-world location, to ground a project in its actual site context.

## Data and scheduling

The [Node Editor's schedule system](ui/node-editor.md#schedule-system) builds live area schedules and floor-by-floor breakdowns straight from the MaStro objects in the scene, and the [Export panel](ui/sidebar-export.md) can dump the same data to CSV or print it to the console.

---

## Under the hood

The extension is built in two layers: a Python component that manages custom parameters on geometry and drives the UI, and a library of Geometry Nodes that does the actual modelling. See [Core Concepts](getting-started/core-concepts.md) for how the two fit together, and the [Reference](reference/operators.md) section for the full list of operators and stored attributes.

Enjoy!
