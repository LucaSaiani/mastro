# Geometry Data Panel

The **Geometry Data** panel appears in the MaStro sidebar tab for any MaStro object in **Edit Mode**. It is collapsed by default.

The panel provides a single custom floating-point value per element type. These values have no fixed meaning — they are free-form user data that can be read by custom Geometry Nodes or used for any purpose that requires a per-element float value.

The active field depends on the current mesh select mode: only the field matching the active mode is enabled.

## Vertex Select Mode

**Vertex**  
A float attribute stored per vertex (`mastro_custom_vert`).

## Edge Select Mode

**Edge**  
A float attribute stored per edge (`mastro_custom_edge`).

## Face Select Mode

**Face**  
A float attribute stored per face (`mastro_custom_face`).
