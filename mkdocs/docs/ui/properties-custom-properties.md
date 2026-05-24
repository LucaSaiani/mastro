# Properties — Custom Properties

The **Custom Properties** sub-panel of Project Data defines per-object data fields that can be attached to Mass/Block and Street objects across the scene.

Each entry in the list has:

| Property | Description |
|---|---|
| **Name** | Label shown in the 3D viewport sidebar |
| **Type** | Data type: Integer, Float, Boolean, or String. Cannot be changed after assignment. |
| **Default** | Default value applied when the property is first assigned to an object |
| **Min / Max** | Value range (Integer and Float only) |
| **Step** | Increment used by the UI slider (Integer and Float only) |
| **Precision** | Number of decimal places displayed (Float only) |
| **Description** | Optional tooltip shown in the sidebar |
| **Assign to Mass/Block** | Whether this property is assigned to Mass and Block objects |
| **Assign to Street** | Whether this property is assigned to Street objects |

---

**Workflow:**

1. Add a new entry with **+** and give it a name and type.
2. Set the default value and any constraints.
3. Press **Assign** (the icon button in the list row) to propagate the property to all matching objects. Until assigned, the property exists only in the list.
4. Once assigned, type and targets are locked. Use **Update** to re-propagate after changing the default or description.
5. To remove, use **−** — a confirmation dialog appears and the property is removed from all objects.

---

Per-object values are edited in the **Custom Properties** panel in the 3D viewport sidebar. See [Custom Properties](sidebar-custom-properties.md) for details.
