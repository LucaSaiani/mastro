# Properties — PDF Sets

The **PDF Sets** sub-panel of Project Data (Scene Properties) organises Frame objects into named export sets. Each set can be exported to PDF in one click — either as a single merged file or as individual files per frame.

## Interface

The panel contains two lists.

### Sets list (top)

Each row shows:

- **Name** — editable directly in the list
- **Bind pages icon** (`LINKED` / `UNLINKED`) — toggles whether the frames in this set are merged into a single PDF or exported as separate files
- **Frame count** — number of frames currently assigned to this set

Use the buttons to the right of the list to **Add**, **Remove**, **Duplicate**, **Move Up**, or **Move Down** a set.

### Frames list (bottom)

Shows all Frame objects present in the scene. Each row has a checkbox on the right: click it to add or remove that frame from the active set.

The list toolbar provides:

- **Filter toggle** — show only frames already assigned to the active set
- **Search** — filter by name
- **Sort** — alphabetical, with optional reverse order

## Exporting

Click **Export PDF** to open a directory picker. The export behaviour depends on the active set's **Bind pages** setting:

| Bind pages | Output |
|---|---|
| On | All frames in the set are exported and merged into `<set name>.pdf` in the chosen directory |
| Off | Each frame is exported as a separate `<frame name>.pdf` in the chosen directory |

The directory picker sidebar exposes one option:

| Option | Default | Description |
|---|---|---|
| Open after export | On | Open the exported PDF(s) with the system default viewer immediately after saving |

!!! note
    The Frames list is kept in sync with the scene automatically: adding or deleting a Frame object updates the list without any manual action.

For exporting a single frame directly from the viewport, see [Export Panel — Export Frame PDF](sidebar-export.md#export-frame-pdf).
