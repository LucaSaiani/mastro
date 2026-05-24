# Custom Properties Panel

The **Custom Properties** panel appears in the MaStro sidebar tab in **Object Mode** when the active object has at least one custom property assigned to it. It is not visible in Edit Mode.

Custom properties are defined in the Properties editor (see [Project Data](properties-project-data.md)) and then assigned to all matching objects in the scene. This panel is where you view and edit the per-object values.

## Fields

Each assigned custom property appears as a labelled field. The label is the property name as defined in the Project Data panel. The field type (integer, float, boolean, or text input) matches the property type.

Changes made here affect only the active object. To reset a property to its default value, edit it directly.

## Visibility

The panel is hidden when:

- The object is not a MaStro object (mass, block, or street)
- The object is in Edit Mode
- No custom properties have been assigned to this object
