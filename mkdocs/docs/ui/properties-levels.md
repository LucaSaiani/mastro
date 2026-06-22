# Properties — Levels

The **Levels** sub-panel of [Sets](properties-project-data.md) manages the scene's list of project elevations (the **Level List**) and groups them into named **Level Sets**. Level Sets are what the viewport [Clip Range](clip-range.md) control offers in its dropdown, and what new MaStro drawings can snap to when [created at the active level](../getting-started/object-type-drawing.md#drawing-creation-at-the-active-level).

!!! note "Reference"
    **Panel:** <span class="breadcrumbs"><span class="step">Properties editor</span><span class="sep">▸</span><span class="step">Scene Properties</span><span class="sep">▸</span><span class="step">MaStro</span><span class="sep">▸</span><span class="step">Sets</span><span class="sep">▸</span><span class="step">Levels</span></span>

## Level List

Each row in the **Level List** has:

- **Id** — a stable internal identifier, shown but not editable
- **Level** — the elevation (Z height), in scene units
- **Name** — a free-text label

The list is always kept sorted by **descending elevation**: the highest level is at the top.

A default level with id `0` (commonly used as the ground / "AOD" reference) always exists at elevation `0` and cannot be renamed or have its elevation changed — its row is greyed out. It can still be reordered relative to other levels by changing other levels' elevations around it, but it cannot be deleted.

Use the **+** / **−** buttons to add or remove a single level. The dropdown menu (▾) next to them gives access to **Add Levels...**, which opens a dialog to create several evenly-spaced levels at once:

| Option | Description |
|---|---|
| **Start Level** | Elevation of the first level created |
| **Increment** | Elevation step between consecutive levels |
| **Direction** | Whether the increment is added (Positive) or subtracted (Negative) at each step |
| **Number of Levels** | How many levels to create |
| **Name Template** | Naming pattern; must contain `{n}` as a placeholder for the level number, e.g. `level_{n}` |
| **Start Number** | First number substituted into `{n}` |
| **Digits** | Minimum digit count for `{n}`, zero-padded (e.g. `2` → `01`, `02`, …) |

## Level Sets

A **Level Set** is a named subset of the Level List, used to scope the Clip Range to only the levels relevant to a given drawing pass (e.g. "Ground Floor Plans" vs. "Roof Plans").

### Sets list

Shows every Level Set with its name and member count. Use the buttons to the right to **Add**, **Remove**, **Duplicate**, **Move Up** or **Move Down** a set.

A default set with id `0`, **All Levels**, always exists and automatically contains every level in the scene — it cannot be edited or removed, and its member count always mirrors the full Level List.

### Members list

Below the Sets list, the **Members** list shows every level in the scene with a checkbox on the right indicating whether it belongs to the active set. Click a checkbox to toggle membership; the checkbox is a real per-row toggle, so **clicking and dragging across multiple rows** assigns or unassigns several levels in a single gesture.

The **filter button** (funnel icon) next to the Members list, when enabled, hides levels that are not members of the active set. It is disabled (and has no effect) while the **All Levels** set is active, since every level is always a member.
