# Properties — Typology

The **Typology** panel is a sub-panel of Mass in the Properties editor. It is the main workspace for designing the use stacks that define how buildings are programmed floor by floor.

---

**Typology List** — The upper list shows all typologies defined in the project. Each typology has a name and a colour used for the viewport overlay. Use **+** to add (a default use is added automatically), **Duplicate** to copy, and **↑ / ↓** to reorder.

---

**Use List** — The lower list shows the uses assigned to the selected typology, ordered from bottom to top. Use **+** to add a use, **✕** to remove (disabled when only one use remains), and **↑ / ↓** to reorder. Changing the order immediately changes how floors are stacked in the geometry.

---

**Use Selector** — A dropdown below the list lets you assign a different use to the selected row. The dropdown lists all uses defined in the project use list.

---

**Use Editor** — When a use is selected, its properties are shown:

| Property | Description |
|---|---|
| **Name** | Display name (e.g. *Residential*, *Office*, *Retail*). Renaming updates the use everywhere it appears. |
| **Floor-to-floor height** | Vertical distance between finished floors, in metres. |
| **Number of storeys** | How many floors this use occupies. Ignored when Variable storeys is enabled. |
| **Variable storeys** | When enabled, this use fills however many floors remain after all fixed-storey uses. If multiple uses are variable, remaining floors are distributed evenly. |

---

**Project Uses** — The **+** button at the bottom adds a new use to the global project use list. This is distinct from the typology-level use list — uses created here can then be assigned to any typology.

---

**Update** — Recalculates the storey distribution for all MaStro objects based on the current typology and use definitions.

**Auto Update** — When enabled, recalculation runs automatically on every change. Disable for large scenes where recalculation is slow.
