# Export Panel

The **Export** panel appears at the bottom of the MaStro sidebar tab in Object Mode. It provides tools for extracting quantitative data from all visible MaStro objects in the scene.

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
