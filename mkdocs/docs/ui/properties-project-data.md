# Properties — Project Data

The **MaStro** panel in the Properties editor is where all scene-wide MaStro data lives: lists of element types, drawing pens, and the various grouping "Sets" used for batch operations. To avoid conflicting or losing data, most of these lists do not allow deleting an entry's underlying id once created — instead, reorder unwanted entries to the end of the list, or rename them for later reuse.

!!! note "Reference"
    **Panel:** <span class="breadcrumbs"><span class="step">Properties editor</span><span class="sep">▸</span><span class="step">Scene Properties</span><span class="sep">▸</span><span class="step">MaStro</span></span>

The panel is organized into sub-panels:

| Sub-panel | Description |
|---|---|
| [Building](properties-building.md) | Typology, Block and Building lists |
| [Drawing](drawing-layers.md) | MaStro CAD layers, pens and line styles |
| [Street](properties-street.md) | Street type list |
| [Custom Properties](properties-custom-properties.md) | Per-object custom data fields |
| Sets | Container for the Levels, Cameras and PDF set panels below |
| └ [Levels](properties-levels.md) | Level Sets — named groups of project levels, used by the viewport Clip Range |
| └ [Cameras](properties-camera-sets.md) | Camera Sets — camera groupings for batch projection |
| └ [PDF](properties-pdf-sets.md) | PDF Sets — frame groupings for PDF export |

The **Sets** sub-panel groups Levels, Cameras and PDF together because they all share the same interaction pattern: a list of named sets on top, and a members list below where checkboxes toggle membership for the active set. See [Levels](properties-levels.md) for the **Level List**, which lives alongside Level Sets but is not itself a set.
