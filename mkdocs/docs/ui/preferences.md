# Preferences

MaStro preferences are accessible via **Edit → Preferences → Extensions → MaStro**. They are organized into collapsible sections.

---

## 2D Projection

| Setting | Description |
|---|---|
| **Projection Suffix** | Suffix appended to every projected output object and to the parent empty (default `_projection`). Changing this after a calculation does not rename existing objects. |
| **Section Offset** | Distance the section outline mesh is moved **toward** the camera so it masks projection lines that pass behind it. Default 10 mm. |
| **Shadow Offset** | Distance the shadow mesh is moved **away** from the camera so it does not mask projection lines in front of it. Default 10 mm. |
| **Section Color** | Initial colour set on the MaStro Section Colour node group when materials are first appended. |
| **Shadow Color** | Initial colour set on the MaStro Shadow Colour node group when materials are first appended. |

---

## File

| Setting | Description |
|---|---|
| **Open File Detection** | When opening a `.blend` file, warn if another user already has it open. Enabled by default. |

---

## GIS

| Setting | Description |
|---|---|
| **CRS** | Pick a predefined Coordinate Reference System. Use the adjacent buttons to add, edit, remove, or reset the list of predefined CRSes. |
| **Map Tiler API Key** | API key for the [MapTiler Coordinates API](https://docs.maptiler.com/cloud/api/coordinates/) (used for CRS reprojection when needed). Get a key from the [MapTiler Cloud dashboard](https://cloud.maptiler.com/account/keys/). |

**Origin**

| Setting | Description |
|---|---|
| **Zoom to mouse** | Zoom towards the mouse pointer position in the basemap viewer. |
| **Lock objects** | Retain objects' geolocation when moving the map origin. |
| **Synch. lat/long** | Keep the geo origin synchronized with the CRS origin. Can be slow with remote reprojection services. |
| **Resampling method** | GDAL resampling method used for reprojection (Nearest Neighbour, Bilinear, Cubic, Cubic Spline, Lanczos). |

**3D Tiles**

| Setting | Description |
|---|---|
| **Google API Key** | [Google Maps Platform](https://developers.google.com/maps/documentation/tile/get-api-key) API key, required to import [Google 3D Tiles](gis-basemap.md#google-3d-tiles). See the [Photorealistic 3D Tiles API overview](https://developers.google.com/maps/documentation/tile/3d-tiles-overview) for what the key grants access to. |
| **3D Tiles quality** | Level of detail for Google 3D Tiles import, from `lod1` (whole city, very low detail) to `lod6` (maximum detail, heavy download). Disabled while the Google API Key is empty. |

**Appearance**

| Setting | Description |
|---|---|
| **Adjust 3D view** | Update the 3D view's grid size and clip distances according to the imported object's size. |
| **Force Viewport Shading: Material Preview** | Switch the viewport to Material Preview shading to display the imported texture/material. |
| **Cache folder** | Folder where the GeoPackage SQLite database is stored. |

See [GIS & Basemap Import](gis-basemap.md) for the full workflow these settings support.

---

## Geometry Nodes Note

Controls the appearance of **Sticky Note** annotations in the Node Editor.

| Setting | Description |
|---|---|
| **Font Size** | Size of the sticky note text |
| **Font Color** | Text colour including alpha |

---

## Levels

| Setting | Description |
|---|---|
| **Cutting Plane Height** | Standard architectural section height above the floor (Top view) or below the ceiling (Bottom view). The [Clip Range](clip-range.md) extends this far past the active level's own elevation, on the side closest to the camera, instead of stopping exactly at it. Default 1.2 m. |
| **Create at active level** | New MaStro drawing objects are placed at the elevation of the active level in whichever Top/Bottom ortho viewport's Clip Range is active, instead of at the 3D cursor's Z position. Enabled by default. |

---

## Overlays

### Mass Overlay

Controls the appearance of the selection overlay drawn on **Mass** objects in Edit Mode.

| Setting | Description |
|---|---|
| **Edge Size** | Thickness of the edge overlay lines (pixels) |
| **Edge Color** | Colour of the edge overlay |
| **Face Color** | Colour of selected face highlights |

### Block Overlay

| Setting | Description |
|---|---|
| **Edge Size** | Thickness of the edge overlay lines for Block objects |

### Wall Overlay

| Setting | Description |
|---|---|
| **Edge Size** | Thickness of the wall type colour lines |

### Street Overlay

| Setting | Description |
|---|---|
| **Edge Size** | Thickness of the street type colour lines |

### Font

Controls the text labels drawn over mesh elements in the viewport (typology name, storey count, etc.).

| Setting | Description |
|---|---|
| **Size** | Font size in points |
| **Color** | Text colour including alpha |

---

## Pens

Lists every MaStro CAD **pen** defined across the open file's scenes, for reference and bulk inspection. See [Layers, Pens and Line Styles](drawing-layers.md) to create or edit pens from the Properties editor.
