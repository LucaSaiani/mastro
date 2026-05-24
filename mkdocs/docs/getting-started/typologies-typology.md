# Typology

A **Typology** is an ordered stack of uses, from bottom to top. For example:

```
Typology: Mixed-Use Tower
  ├─ Ground Floor  (Retail,      4.50 m,  1 storey)
  ├─ Lower Floors  (Office,      3.60 m,  4 storeys)
  └─ Upper Floors  (Residential, 3.15 m,  variable)
```

Each face (Mass) or edge (Block) in the scene is assigned to one typology. Geometry Nodes reads the stacked use data and generates the correct floor heights automatically.
