# Viewport Clip Range

The **Clip Range** control lets you restrict an orthographic Top or Bottom viewport to show only a chosen span of [Levels](properties-levels.md) — cutting away everything above (Top view) or below (Bottom view) the selection, like a horizontal section through the model. It is built into Blender's native **View** panel, right next to **Clip Start / Clip End**, since it is really just a level-aware way of driving those same values.

!!! note "Reference"
    **Panel:** <span class="breadcrumbs"><span class="step">Viewport sidebar (N)</span><span class="sep">▸</span><span class="step">View</span></span> — only visible while the active viewport is in an **orthographic Top or Bottom** view, and at least one [Level Set](properties-levels.md#level-sets) exists.

## How it works

The control offers:

| Control | Description |
|---|---|
| **Clip Range** dropdown | Chooses which Level Set to draw levels from |
| Levels list | The levels belonging to the chosen set, in descending elevation order |
| Up / Down arrows | Move the active level one row at a time |
| **Top Unlimited** / **Bottom Unlimited** | Extends the range to cover every level on the far side of the active one |

Selecting a level (clicking a row, or moving with the arrows) makes it the **active level** for that side. The visible Z-slab in the viewport is rebuilt from the active level outward; this is reflected immediately by overriding the viewport's `Clip Start` / `Clip End` and recentring the view, with no further action needed.

### Independent Top/Bottom state

A Top viewport and a Bottom viewport open at the same time each keep their **own** chosen Level Set, active level and range — changing one does not affect the other. Switching an existing viewport between Top and Bottom ortho automatically re-applies whichever clip range was last used on that new side.

### Unlimited

The **Unlimited** button — labelled for the *opposite* end of the range from the one you're viewing (**Top Unlimited** appears while in Bottom view, and vice versa) — extends the clip range from the active level all the way to the far end of the level set, instead of stopping at the next level. Pressing it again restores exactly the selection that was active before.

### Cutting Plane Height

The clip plane closest to the camera does not stop exactly at the active level's own elevation — it is pushed out by the **Cutting Plane Height** preference (default 1.2 m, the standard architectural section height above a floor or below a ceiling). Otherwise the drawing geometry sitting *at* the active level's elevation would itself be clipped away. This preference is set in **Preferences → Extensions → MaStro → Levels**; see [Preferences](preferences.md#levels).

### Drawing creation at the active level

When the **Create Drawings at Active Level** preference is enabled (the default), new [MaStro drawings](../getting-started/object-type-drawing.md) are placed at the elevation of the active level of whichever Top/Bottom viewport's Clip Range is active, instead of at the 3D cursor's Z position. See [Preferences](preferences.md#levels).

!!! note
    The Clip Range only affects the viewport's own near/far clipping in that Top/Bottom view — it has no effect on rendering, on other viewports, or on the 2D Projection.
