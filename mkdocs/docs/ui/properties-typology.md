# Properties — Typology

The **Typology** panel is a sub-panel of Mass in the Properties editor. It is the main workspace for designing the use stacks that define how buildings are programmed floor by floor.

---

## Typology List

The upper list shows all typologies defined in the project. Each typology has a name and a colour used for the viewport overlay.

- **+** — Add a new typology. A default use is added automatically.
- **Duplicate** — Copy the selected typology.
- **↑ / ↓** — Reorder typologies in the list.

---

## Use List

The lower list shows the uses assigned to the selected typology, in order from bottom to top.

- **+** — Add a new use to the current typology. The first use in the project use list is added as a default.
- **✕** — Remove the selected use. Disabled when only one use remains.
- **↑ / ↓** — Reorder uses within the typology.

Changing the order of uses immediately changes how floors are stacked in the geometry.

---

## Use Selector

Below the use list, a dropdown lets you **assign a different use** to the currently selected row. The dropdown lists all uses defined in the project use list.

---

## Use Editor

When a use is selected in the list, its properties are shown for editing:

**Name**  
The display name of the use (e.g. *Residential*, *Office*, *Retail*). Renaming here updates the use everywhere it appears.

**Floor-to-floor height**  
The vertical distance between finished floors for this use, in metres. Accepts values up to 99.999 m with millimetre precision.

**Number of storeys**  
How many floors this use occupies. Ignored when *Variable storeys* is enabled.

**Variable storeys**  
When enabled, this use fills however many floors remain after all fixed-storey uses have been placed. If multiple uses are set to variable, the remaining floors are distributed evenly. This control is disabled (greyed out) while *Variable storeys* is active.

---

## Project Uses

The **+** button at the bottom of the panel adds a new use to the **project use list** — the global pool of all available uses. This is distinct from the typology-level use list above. A new use created here can then be assigned to any typology.

---

## Update

**Update** — Recalculates the storey distribution for all MaStro objects in the scene based on the current typology and use definitions.

**Auto Update** — When enabled, the update runs automatically whenever a typology or use property is changed. Disable this for large scenes where recalculation is slow.
