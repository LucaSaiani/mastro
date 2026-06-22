# Export Panel

The **Export** panel appears at the bottom of the MaStro sidebar tab in Object Mode. It provides tools for extracting quantitative data from all visible MaStro objects in the scene, and for exporting the active frame to PDF.

## Export Data as CSV

Opens a file browser to choose a save location, then exports a **granular** breakdown of all visible Mass and Block objects to a `.csv` file.

The granular export expands every building storey by storey. For each floor it records:

- Block and building assignment
- Typology and use name
- Floor level (storey number from ground)
- Floor area (m²)
- Perimeter (m)
- Wall area (m²)
- GEA (Gross External Area, m²)

This format is suitable for detailed area schedules and compliance calculations.

## Print Data

Prints a formatted summary table to the **Blender console**. Two output modes are available (controlled by the `text` property, which defaults to `aggregate`):

**Aggregate mode**  
Groups data by Block / Building / Typology / Level and sums the areas. Useful for a quick overview of the project totals.

**Granular mode**  
Same as the CSV export but printed to the console rather than saved to a file.

Both modes display totals for Perimeter, Wall Area, and GEA at the bottom of the table.

---

!!! tip
    To see the printed output, open the **Blender System Console** (Window → Toggle System Console on Windows, or launch Blender from a terminal on macOS/Linux) before clicking Print Data.

## Export Frame PDF

Visible only when a [MaStro Frame](mastro-frame.md) object is the active selection. Opens a file browser to choose a save path and exports the active frame — together with all Grease Pencil objects whose geometry intersects it — to a single-page PDF.

The file browser sidebar exposes one option:

| Option | Default | Description |
|---|---|---|
| Open after export | On | Open the exported PDF with the system default viewer immediately after saving |

For exporting multiple frames at once, or binding several frames into a single PDF, use the [PDF Sets](properties-pdf-sets.md) panel in the Scene Properties.
