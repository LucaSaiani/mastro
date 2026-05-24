# MaStro

**MaStro** is a Blender extension for architects and urban designers who need to rapidly create parametric 3D models of masterplans and streets.

The workflow is intentionally minimal: you sketch footprints, assign parameters (height, typology, usage), and Geometry Nodes generates the full volumetric model. The same logic applies to road networks. MaStro has been tested on projects ranging from single buildings to masterplans with hundreds of objects.

The name can be read as *Masterplan and Roads*, *Mass and Streets*, or simply the Italian word for a skilled craftsman.

## Features

- **Parametric mass modelling** — define buildings by footprint, height, and typology; Geometry Nodes handles the geometry
- **Street tracing** — assign lane counts, widths, and typology to curve-based street objects
- **Custom properties** — attach per-object data fields (integer, float, boolean, text) to masses and streets for program management and export
- **Layer manager** — organise objects into named layers with visibility and lock controls
- **2D projection and shadow baking** — generate plan-view projections and shadow studies
- **Node library** — a curated set of Geometry Nodes for walls, facades, openings, and custom extensions
- **Import** — bring MaStro objects from another `.blend` file with automatic reconciliation of typologies, layers, and custom properties
- **Export** — export object data to external formats for further analysis

## Requirements

- Blender 5.0 or later
- SciPy (bundled — no internet connection required)

## Installation

1. Download the `.zip` for your platform from the [latest release](https://github.com/LucaSaiani/mastro/releases/tag/latest-mastro).
2. In Blender, go to **Edit → Preferences → Extensions**.
3. Click **Install from Disk…** and select the downloaded `.zip`, or drag and drop it into the Blender window.
4. Enable the extension if it is not enabled automatically.

After installation, open the **3D Viewport** sidebar (**N**) — a **MaStro** tab should appear.

> **Asset Library setup required:** MaStro ships with a `.blend` file containing its Geometry Nodes. Add the extension folder as an Asset Library in **Edit → Preferences → File Paths → Asset Libraries** so that node groups are available.

## Documentation

Full documentation is available at [lucasaiani.github.io/mastro](https://lucasaiani.github.io/mastro/).

## License

GPL-3.0-or-later
