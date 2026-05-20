# 2D Projection

MaStro can generate a 2D line-drawing representation of the 3D scene as seen through any camera, optionally including cast shadows. The system works per-camera: each camera stores its own settings and can be calculated independently or in batch.

---

## Enabling a Camera

The projection system is activated per-camera in the **Properties Editor → Object Data Properties** (camera icon). Open the **MaStro Projection** panel. The checkbox next to the panel label enables or disables the camera for projection and shadow baking.

When disabled, all sub-panels are grayed out and the camera does not appear in the Calculate panel.

---

## MaStro Projection Panel

These settings apply to both projection and shadow output for the selected camera.

| Setting | Description |
|---|---|
| **Place on Camera Plane** | Position the output empty (and all its children) in front of the camera at the near clip plane. When disabled, the empty can be moved freely in the scene. |
| **Camera Clipping** | Restrict projected geometry to the camera clipping volume. Edges beyond the far clip plane are truncated; faces that straddle it generate an additional section line. Also applied to shadow baking. |
| **Convert to Grease Pencil** | After generation, convert all projection and shadow output meshes to Grease Pencil objects. Subsequent runs automatically replace existing Grease Pencil outputs. |

---

## 2D Projection Sub-panel

Controls the line-drawing projection. Enable with the checkbox in the sub-panel header.

### Quality

| Setting | Description |
|---|---|
| **Segment Length** | Sampling precision in NDC screen space (range 0–2 per axis). Smaller values produce more accurate visibility transitions at the cost of performance. Independent of object size or distance from camera. |
| **Ray Offset** | World-space offset applied to ray origins to avoid self-intersection artefacts. |

### Output

| Setting | Description |
|---|---|
| **Only Selected Objects** | Project only the selected objects. All visible objects still participate in occlusion. Useful for incremental updates without recalculating the entire scene. |
| **Include Hidden** | Include hidden (back-facing or occluded) lines as separate edges in a dedicated vertex group on the output mesh. |
| **Flat Angle Threshold** | Edges shared by two nearly-parallel faces of the same object are hidden when the angle between their normals is below this threshold. Edges between different materials or objects are always shown. |
| **Compute Silhouette** | Identify silhouette edges (boundary between camera-facing and back-facing faces). Silhouette edges are always included regardless of the flat angle threshold and are assigned to dedicated vertex groups. |
| **Compute Intersections** | Calculate and project the intersection curves between interpenetrating objects. Enable only when objects overlap in 3D. |

### Cleanup

| Setting | Description |
|---|---|
| **Snap Orphans** | Move each orphan endpoint (a segment end with no connecting edge) to the nearest point on the projected wire of the occluder that caused the cut. Reduces gaps in the output. |
| **Merge by Distance** | Merge vertices closer than the specified threshold before snapping. Collapses near-coincident vertices produced by the projection. |
| **Merge Distance** | Maximum distance between vertices to be merged (in projection space). Visible only when Merge by Distance is enabled. |
| **Remove Overlapping Boundary** | Remove overlapping portions of boundary edges within the same object before projection. Only active when Flat Angle Threshold is greater than zero. |

---

## Shadow Sub-panel

Controls shadow baking. Enable with the checkbox in the sub-panel header.

### Light Source

By default, shadows are computed from a **virtual light source** defined by azimuth and elevation. If a real **Sun** or **Area** light is linked in the *Light* field, it overrides the virtual source automatically. Removing the link or deleting the light reverts to the virtual source — no manual switch is needed.

| Setting | Description |
|---|---|
| **Light** | Optional Sun or Area light object. When set, its direction is used and the virtual parameters below are hidden. |
| **Space** | Reference frame for the virtual light: **World** (azimuth/elevation in world space) or **Camera** (relative to the camera view — useful for consistent shadow direction across all architectural elevations). Visible only when no real light is linked. |
| **Azimuth** | Horizontal angle of the virtual light source, measured counterclockwise from North (+Y axis). Visible only when no real light is linked. |
| **Elevation** | Angle of the virtual light source above the horizon. Visible only when no real light is linked. |

### Quality

| Setting | Description |
|---|---|
| **Grid Subdivisions** | Number of tiles along the camera's longest axis. Each tile is 256 px; more tiles means higher total bake resolution. |
| **Boundary Resolution** | Target pixels on the short side when sampling the shadow boundary. Higher values produce finer border detail at the cost of more output vertices. |
| **Interior Resolution** | Target pixels on the short side when sampling the shadow interior. Lower values produce fewer interior triangles and faster baking. |

---

## Output Structure

After calculation, all outputs are parented to an **empty** object named `<CameraName><suffix>` (suffix configured in Preferences, default `_projection`). The empty is placed in a dedicated **2D Projection and Shadows** collection.

Each source object produces one output mesh named `<SourceName><suffix>`. Vertex groups on each mesh identify edge categories (visible, hidden, silhouette, section). The shadow output is a single filled mesh named `<CameraName>_shadow`.

When **Place on Camera Plane** is enabled, the empty is positioned and scaled to match the camera frustum. The section outline mesh is offset slightly toward the camera (so it masks lines behind it) and the shadow mesh is offset slightly away (so it does not mask lines). Both offset values are configurable in Preferences.

---

## Calculate Panel

Found in **Properties Editor → Scene Properties → Project Data → 2D Projection**.

This panel lists all cameras that have projection **enabled** and provides a single entry point to run calculations.

| Element | Description |
|---|---|
| Camera list | Shows all enabled cameras sorted by name. Each row displays the camera type (perspective/orthographic icon), the camera name, and icons indicating which operations are active (projection and/or shadow). |
| **Active** toggle | The checkbox at the left of each row controls whether that camera is included in the next batch calculation. |
| **Calculate (N)** | Runs projection and/or shadow baking for all active cameras in the list. The number in parentheses shows how many cameras will be processed. Disabled when no cameras are active. |
| **Cancel** | Appears while a calculation is running. Stops all active operations. |

> **Tip:** Individual camera calculations can also be triggered from each camera's own MaStro Projection panel using the **Run Projection** operator, which processes only the active camera.
