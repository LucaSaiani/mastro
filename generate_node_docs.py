"""
Generates one MkDocs markdown page per MaStro node from export_nodes.json.
Run from the repo root:
    python3 generate_node_docs.py
"""

import json
import os
import re

# ---------------------------------------------------------------------------
# Categorisation map: node name (without "MaStro ") -> (category, subcategory)
# ---------------------------------------------------------------------------
CATEGORIES = {
    # Architecture > Annotation
    "Dimension":               ("architecture", "annotation"),
    "Read Slope":              ("architecture", "annotation"),
    "Attribute Visualiser":    ("architecture", "annotation"),
    "Ruler":                   ("architecture", "annotation"),
    "Reference Grid":          ("architecture", "annotation"),
    "Brick Dimension":         ("architecture", "annotation"),

    # Architecture > Facade
    "Façade":                  ("architecture", "facade"),
    "Façade Corner":           ("architecture", "facade"),
    "Façade Pattern":          ("architecture", "facade"),
    "Facade Line Based":       ("architecture", "facade"),
    "Line Based Sum Height":   ("architecture", "facade"),
    "Opening":                 ("architecture", "facade"),
    "Opening.002":             ("architecture", "facade"),
    "Arched Opening":          ("architecture", "facade"),
    "Triangle Opening":        ("architecture", "facade"),
    "Triangular Grid":         ("architecture", "facade"),
    "Window":                  ("architecture", "facade"),
    "Awning":                  ("architecture", "facade"),
    "Folding Shutter":         ("architecture", "facade"),
    "Pivot Edge":              ("architecture", "facade"),

    # Architecture > Mass
    "Mass":                    ("architecture", "mass"),
    "Mass Walls":              ("architecture", "mass"),
    "Block":                   ("architecture", "mass"),
    "Generate Floors":         ("architecture", "mass"),
    "Generate Topology":       ("architecture", "mass"),
    "Separate Mass":           ("architecture", "mass"),
    "Convert Mass to Floor Lines": ("architecture", "mass"),
    "Line Based Building":     ("architecture", "mass"),
    "Footprint":               ("architecture", "mass"),
    "Parapet":                 ("architecture", "mass"),
    "Floor Grid":              ("architecture", "mass"),
    "Perimeter":               ("architecture", "mass"),
    "Rooms":                   ("architecture", "mass"),

    # Architecture > Elements
    "Adaptive Stair":          ("architecture", "elements"),
    "Stair":                   ("architecture", "elements"),
    "Pitch Roof":              ("architecture", "elements"),
    "Nave":                    ("architecture", "elements"),
    "Vault":                   ("architecture", "elements"),
    "Catenary":                ("architecture", "elements"),
    "Elements - Flag":         ("architecture", "elements"),
    "Elements - Pergola":      ("architecture", "elements"),
    "Rails":                   ("architecture", "elements"),
    "Steel Profile":           ("architecture", "elements"),
    "Building Shadow":         ("architecture", "elements"),
    "Visbility Study":         ("architecture", "elements"),

    # Curve
    "Curve Noise":             ("curve", None),
    "Fill Curve":              ("curve", None),
    "Move Points along Curve": ("curve", None),
    "Sine Wave":               ("curve", None),
    "Instances Along Curve":   ("curve", None),
    "Stretch Edge":            ("curve", None),
    "Loft Curves":             ("curve", None),
    "Loft Profiles":           ("curve", None),
    "Mitered Mesh":            ("curve", None),
    "Bevel 2D":                ("curve", None),
    "Bevel 3D":                ("curve", None),

    # Indices
    "Flip Indices":            ("indices", None),
    "Offset Indices":          ("indices", None),
    "Highest/Lowest Edge Index": ("indices", None),
    "Highest/Lowest Boolean":  ("indices", None),
    "Shuffle Indices":         ("indices", None),
    "Sort Elements":           ("indices", None),
    "Point Siblings":          ("indices", None),
    "Is Edge Cyclic":          ("indices", None),
    "Is Point on Edge":        ("indices", None),
    "Random Points along Edge":("indices", None),
    "Set Edge ID":             ("indices", None),
    "Instance Packer":         ("indices", None),

    # Instances
    "Distribute Instances":    ("instances", None),
    "Split to Instances":      ("instances", None),
    "Collection info +":       ("instances", None),

    # Materials (filter nodes)
    "Filter by Block Side":    ("materials", None),
    "Filter by Street Type":   ("materials", None),
    "Filter by Typology":      ("materials", None),
    "Filter by Use":           ("materials", None),
    "Filter by Wall Type":     ("materials", None),
    "Separate Geometry by Block Side":    ("materials", None),
    "Separate Geometry by Street Type":   ("materials", None),
    "Separate Geometry by Typology":      ("materials", None),
    "Separate Geometry by Use":           ("materials", None),
    "Separate Geometry by Wall Type":     ("materials", None),
    "Separate Geometry by Factor.001":    ("materials", None),

    # Mesh
    "Grid":                    ("mesh", None),
    "Grid Diagonals":          ("mesh", None),
    "Hexagonal Grid":          ("mesh", None),
    "Delaunay":                ("mesh", None),
    "Tartan":                  ("mesh", None),
    "UV Mapping":              ("mesh", None),
    "Face UV Map":             ("mesh", None),
    "Plane UV Map":            ("mesh", None),
    "UV Visualiser":           ("mesh", None),
    "Inset Faces":             ("mesh", None),
    "Solidify":                ("mesh", None),
    "Extrude":                 ("mesh", None),
    "Edge Offset 2D":          ("mesh", None),
    "Edge Offset 3D":          ("mesh", None),
    "Shear":                   ("mesh", None),
    "Mirror":                  ("mesh", None),
    "Fix Normals":             ("mesh", None),
    "Dissolve Aligned":        ("mesh", None),
    "Unify Normals":           ("mesh", None),
    "Contour Mesh":            ("mesh", None),
    "Flat Projection":         ("mesh", None),
    "Grease Pencil":           ("mesh", None),
    "Grease Pencil to Landscape": ("mesh", None),
    "Set Edge Position":       ("mesh", None),
    "Set Position":            ("mesh", None),
    "Custom Corners":          ("mesh", None),

    # Street
    "Street":                  ("street", None),
    "Street Elements":         ("street", None),
    "Offset Street Edges":     ("street", None),

    # Utilities
    "Angle between Edges":     ("utilities", None),
    "Edge Vectors":            ("utilities", None),
    "Ellipse":                 ("utilities", None),
    "Intersection 2D":         ("utilities", None),
    "Intersection Between Line and Plane": ("utilities", None),
    "Shortest Line Between Lines in 3D":   ("utilities", None),
    "Perpendicular Point on a Line":       ("utilities", None),
    "Tangent Tangent Center":  ("utilities", None),
    "Random Value":            ("utilities", None),
    "Round Value":             ("utilities", None),
    "Camera Culling":          ("utilities", None),
    "Vector":                  ("utilities", None),
    "Vectors":                 ("utilities", None),
}

IMAGE_BASE = {
    ("architecture", "annotation", "dimension"):   "nodes/images/dimension",
    ("architecture", "annotation", "read-slope"):  "nodes/images/read_slope",
}


def slugify(name):
    name = name.lower()
    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"[\s_]+", "-", name)
    return name.strip("-")


def rel_image_path(depth, img_path):
    """Return relative path from a doc at given depth to docs root."""
    ups = "/".join([".."] * depth)
    return f"{ups}/{img_path}"


SOCKET_CSS = {
    "NodeSocketGeometry":   "sock-geometry",
    "NodeSocketFloat":      "sock-float",
    "NodeSocketInt":        "sock-int",
    "NodeSocketBool":       "sock-bool",
    "NodeSocketVector":     "sock-vector",
    "NodeSocketColor":      "sock-color",
    "NodeSocketMaterial":   "sock-material",
    "NodeSocketShader":     "sock-shader",
    "NodeSocketString":     "sock-string",
    "NodeSocketMenu":       "sock-menu",
    "NodeSocketImage":      "sock-image",
    "NodeSocketObject":     "sock-object",
    "NodeSocketCollection": "sock-collection",
    "NodeSocketTexture":    "sock-texture",
    "NodeSocketRotation":   "sock-rotation",
    "NodeSocketMatrix":     "sock-matrix",
}


def socket_list(sockets, label):
    rows = []
    rows.append(f'\n**{label}**\n')
    rows.append('<dl class="node-sockets">')
    current_panel = "__none__"
    for s in sockets:
        panel = s.get("panel")
        if panel != current_panel:
            current_panel = panel
            if panel:
                rows.append(f'<div class="socket-panel">{panel}</div>')
        css = SOCKET_CSS.get(s.get("type", ""), "sock-unknown")
        name = s.get("name", "")
        desc = s.get("description", "") or "*Description to be written.*"
        rows.append(
            f'<dt><span class="socket-dot {css}"></span>{name}</dt>'
            f'<dd>{desc}</dd>'
        )
    rows.append('</dl>')
    return rows


def write_node_page(short_name, ng, category, subcategory, docs_root):
    slug = slugify(short_name)

    if subcategory:
        rel_path = f"nodes/{category}/{subcategory}/{slug}.md"
        depth = 4
    else:
        rel_path = f"nodes/{category}/{slug}.md"
        depth = 3

    out_path = os.path.join(docs_root, rel_path)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    lines = []

    # Icon (top-right)
    img_key = (category, subcategory, slug) if subcategory else (category, None, slug)
    img_dir = IMAGE_BASE.get(img_key)
    if img_dir:
        icon_path = rel_image_path(depth, f"{img_dir}/icon.png")
        lines.append(f'<img src="{icon_path}" class="node-icon" alt="{short_name} icon">\n')

    lines.append(f"# {short_name}\n")

    # Open node-body wrapper (contains thumbnail float + text + sockets)
    if img_dir:
        thumb_path = rel_image_path(depth, f"{img_dir}/thumbnail.png")
        lines.append(f'<div class="node-body">')
        lines.append(f'<img src="{thumb_path}" class="node-thumb" alt="{short_name} preview">\n')

    lines.append("*Description to be written.*\n")

    # Inputs
    inputs = ng.get("inputs", [])
    if inputs:
        lines.extend(socket_list(inputs, "Inputs"))

    # Outputs
    outputs = ng.get("outputs", [])
    if outputs:
        lines.extend(socket_list(outputs, "Outputs"))

    if img_dir:
        lines.append("\n</div>\n")

    # Examples
    if img_dir:
        example_path = rel_image_path(depth, f"{img_dir}/example_01.png")
        example_full = os.path.join(docs_root, img_dir.lstrip("/"), "example_01.png")
        if os.path.exists(example_full):
            lines.append(f"\n**Examples**\n")
            lines.append(f"![{short_name} example]({example_path})\n")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    return rel_path


def build_nav_tree(pages):
    """Build nested nav structure from list of (short_name, rel_path, category, subcategory)."""
    tree = {}
    for short_name, rel_path, category, subcategory in pages:
        if subcategory:
            tree.setdefault(category, {}).setdefault(subcategory, []).append((short_name, rel_path))
        else:
            tree.setdefault(category, {}).setdefault("__root__", []).append((short_name, rel_path))
    return tree


def main():
    repo_root = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(repo_root, "export_nodes.json")
    docs_root = os.path.join(repo_root, "mkdocs", "docs")

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    pages = []
    skipped = []

    for full_name, ng in sorted(data.items()):
        if not full_name.startswith("MaStro "):
            continue
        short_name = full_name[len("MaStro "):]
        if short_name not in CATEGORIES:
            skipped.append(full_name)
            continue
        category, subcategory = CATEGORIES[short_name]
        rel_path = write_node_page(short_name, ng, category, subcategory, docs_root)
        pages.append((short_name, rel_path, category, subcategory))
        print(f"  wrote {rel_path}")

    print(f"\nGenerated {len(pages)} pages.")
    if skipped:
        print(f"Skipped (not in CATEGORIES): {skipped}")

    # Print nav block for mkdocs.yml
    tree = build_nav_tree(pages)
    print("\n--- Paste into mkdocs.yml under 'Nodes:' ---")
    print("  - Nodes:")
    print("    - Overview: nodes/overview.md")
    for cat, sub_dict in sorted(tree.items()):
        cat_title = cat.title()
        has_root = "__root__" in sub_dict
        has_subs = any(k != "__root__" for k in sub_dict)
        if has_subs:
            print(f"    - {cat_title}:")
            if has_root:
                for name, path in sorted(sub_dict["__root__"]):
                    print(f"      - {name}: {path}")
            for subcat, node_list in sorted(
                (k, v) for k, v in sub_dict.items() if k != "__root__"
            ):
                print(f"      - {subcat.title()}:")
                for name, path in sorted(node_list):
                    print(f"        - {name}: {path}")
        else:
            print(f"    - {cat_title}:")
            for name, path in sorted(sub_dict.get("__root__", [])):
                print(f"      - {name}: {path}")


if __name__ == "__main__":
    main()
