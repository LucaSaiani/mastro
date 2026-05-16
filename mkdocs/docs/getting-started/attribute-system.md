# The Attribute System

## Why Custom Attributes

Geometry Nodes reads mesh data natively and efficiently, but it has a fundamental limitation: **it does not support Python arrays or lists as attribute values**. Each custom attribute on a mesh element (vertex, edge, face) can hold exactly one value — an integer, a float, or a boolean.

MaStro needs to store lists of data per face or edge: the sequence of use IDs for each floor, the storey count for each use, the floor-to-floor height for each use. To do this without arrays, MaStro uses a **digit-pair encoding** scheme: every list is split into two parallel integer attributes, each holding one digit position of every value in the list.

## Digit-Pair Encoding

Consider a face with three uses whose storey counts are 1, 4, and 12 (bottom to top). These are encoded as two-digit values: `01`, `04`, `12`. The two parallel strings are built by taking the tens digit of each value and concatenating them, then doing the same with the units digits:

```
storey counts:   01   04   12
                 ↓↓   ↓↓   ↓↓
storey_list_A:  "1" + "0" + "0" + "1"  →  1001   (tens digits, prefixed with "1")
storey_list_B:  "1" + "1" + "4" + "2"  →  1142   (units digits, prefixed with "1")
```

To reconstruct the original value for use *i*, GN reads `storey_list_A[i] * 10 + storey_list_B[i]`.

The leading `"1"` prefix is always added before the data. This prevents Blender from silently discarding leading zeros when storing an integer (e.g. the string `"0142"` would be read back as `142`, losing the first digit). By always starting with `1`, the prefix is stripped at read time and the rest decoded correctly.

## Height Encoding

Floor-to-floor heights are floating-point values and require more precision. A height of `3.555 m` is encoded across **five** parallel integer attributes (A through E), each storing one decimal position:

```
height = 03.555
  A = 0   (tens digit of the integer part)
  B = 3   (units digit of the integer part)
  C = 5   (first decimal place)
  D = 5   (second decimal place)
  E = 5   (third decimal place)
```

This gives sub-millimetre precision (0.001 m) without requiring float arrays.

## Attribute Domains

MaStro uses different element domains depending on the object type:

| Object type | Domain | Suffix |
|---|---|---|
| Mass | **Face** | *(none)* |
| Block | **Edge** | `_EDGE` |

The same attribute name is used for both, distinguished by suffix. For example, the typology ID is stored in `mastro_typology_id` on faces (Mass) and `mastro_typology_id_EDGE` on edges (Block).

## Attribute Lifecycle

Attributes are created when a MaStro object is first added to the scene, initialised with values derived from the currently selected typology. They are updated by:

- Editing parameters in the MaStro sidebar panels
- Running the **Update** operator
- Changing a typology or use definition in the Properties editor (propagated automatically)

If you add new faces or edges in Edit Mode, they receive the same initial values as the object's current typology. You can then select them and assign different parameters.

## Full Attribute List

For a complete table of all custom attributes, their types, domains, and meanings, see the [Custom Attributes](../reference/custom-attributes.md) reference page.
