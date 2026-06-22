# GIS & Basemap Import

The **GIS** sidebar panel imports georeferenced basemap imagery and 3D tile data into the scene, anchored to a real-world location.

!!! note "Reference"
    **Panel:** <span class="breadcrumbs"><span class="step">Viewport sidebar (N)</span><span class="sep">▸</span><span class="step">MaStro</span><span class="sep">▸</span><span class="step">GIS</span></span>

## Source and layer

| Setting | Description |
|---|---|
| **Source** | The map service to import from |
| **Layer** | The layer offered by that source (e.g. satellite imagery, street map, 3D tiles) |

Layers requiring a Google API key (such as **3D Tiles**) only appear in the list once a key has been entered in [Preferences → GIS → 3D Tiles](preferences.md#gis).

## Fixed-origin workflow

The project's geographic origin can be entered either as **Latitude/Longitude** or as **Projected** X/Y coordinates in a chosen CRS.

The first time a basemap is downloaded, this origin becomes **fixed**: the panel switches to showing a read-only summary with an **Unlock** button, and every subsequent import is positioned relative to that same fixed point rather than re-deriving the origin from each download. This keeps successive imports (e.g. a basemap layer followed by 3D Tiles for the same area) aligned to each other.

Click **Unlock** to release the fixed origin and edit the Latitude/Longitude or Projected fields again — for example, to start a new project area from scratch.

## Downloading

Click **Download Basemap** to fetch the chosen source/layer for the current origin and view extent.

## Google 3D Tiles

When **Source = Google** and **Layer = 3D**, a **Quality** dropdown appears (the `clip_range`-independent LOD setting from [Preferences](preferences.md#gis), `lod1`–`lod6`).

Downloading in this mode opens an interactive **selection rectangle** in the viewport, initially sized to one third of the viewport's area:

- Drag any of the **4 corner handles** to resize the area to import
- Press **Enter** or right-click to confirm and start the download
- Press **Esc** to cancel

The downloaded tiles are organized under an empty named `3D Lod{N}`, with one child object per tile; their textures are embedded directly into the `.blend` file.

## Troubleshooting

If reprojection or the basemap viewer fails — for example because a remote reprojection service requires a [MapTiler API key](preferences.md#gis) that hasn't been set — the error report names the underlying cause instead of a generic failure message.
