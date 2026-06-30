"""
Generates one MkDocs markdown page per MaStro node from export_nodes.json
(in the repo root). Run from anywhere:
    python3 mkdocs/generator/generate_node_docs.py

Run capture_node_thumbnails.py (inside Blender) first so every node's image
folder under mkdocs/docs/nodes/images/<slug>/ already has node.png before
generating pages, since each page links to that image.

Existing pages are left untouched once someone has written real content:
a page only gets (re)written if it doesn't exist yet, or if it still
contains the "*Description to be written.*" placeholder anywhere in it.
"""

import json
import os
import re

# Categorisation map: node name (without "MaStro ") -> (category, subcategory).
# Lives in node_categories.json, not here, so it can be edited without
# touching this script -- e.g. as MaStro Schedule nodes are finished, or new
# GN/material nodes are added.
CATEGORIES_JSON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "node_categories.json")
with open(CATEGORIES_JSON_PATH, encoding="utf-8") as f:
    CATEGORIES = {
        name: (entry["category"], entry["subcategory"])
        for name, entry in json.load(f).items()
    }

PLACEHOLDER = "*Description to be written.*"


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


def page_is_locked(out_path):
    """A page is considered hand-edited -- and never overwritten -- once its
    main description (the placeholder occurrence before the **Inputs**
    section) has been replaced with real text. Socket-level placeholders are
    ignored: those commonly stay unwritten long after the main description
    is done, so checking for the placeholder anywhere in the file would keep
    re-locking pages that still need their socket descriptions filled in."""
    if not os.path.exists(out_path):
        return False
    with open(out_path, encoding="utf-8") as f:
        content = f.read()
    inputs_pos = content.find("**Inputs**")
    main_section = content[:inputs_pos] if inputs_pos != -1 else content
    return PLACEHOLDER not in main_section


def write_node_page(short_name, ng, category, subcategory, docs_root):
    slug = slugify(short_name)

    if subcategory:
        rel_path = f"nodes/{category}/{subcategory}/{slug}.md"
        depth = 3
    else:
        rel_path = f"nodes/{category}/{slug}.md"
        depth = 2

    out_path = os.path.join(docs_root, rel_path)

    if page_is_locked(out_path):
        return rel_path, False

    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    img_dir_rel = f"nodes/images/{slug}"
    img_dir_abs = os.path.join(docs_root, img_dir_rel)
    icon_name = "icon.png" if os.path.exists(os.path.join(img_dir_abs, "icon.png")) else "node.png"
    thumb_name = "thumbnail.png" if os.path.exists(os.path.join(img_dir_abs, "thumbnail.png")) else "node.png"
    has_image = os.path.exists(os.path.join(img_dir_abs, thumb_name))

    lines = []

    # Icon (top-right)
    if has_image:
        icon_path = rel_image_path(depth, f"{img_dir_rel}/{icon_name}")
        lines.append(f'<img src="{icon_path}" class="node-icon" alt="{short_name} icon">\n')

    lines.append(f"# {short_name}\n")

    # Open node-body wrapper (contains thumbnail float + text + sockets)
    if has_image:
        thumb_path = rel_image_path(depth, f"{img_dir_rel}/{thumb_name}")
        lines.append(f'<div class="node-body">')
        lines.append(f'<img src="{thumb_path}" class="node-thumb" alt="{short_name} preview">\n')

    lines.append(f"{PLACEHOLDER}\n")

    # Inputs
    inputs = ng.get("inputs", [])
    if inputs:
        lines.extend(socket_list(inputs, "Inputs"))

    # Outputs
    outputs = ng.get("outputs", [])
    if outputs:
        lines.extend(socket_list(outputs, "Outputs"))

    if has_image:
        lines.append("\n</div>\n")

    # Examples
    if has_image:
        example_full = os.path.join(img_dir_abs, "example_01.png")
        if os.path.exists(example_full):
            example_path = rel_image_path(depth, f"{img_dir_rel}/example_01.png")
            lines.append(f"\n**Examples**\n")
            lines.append(f"![{short_name} example]({example_path})\n")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    return rel_path, True


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
    generator_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(os.path.dirname(generator_dir))
    json_path = os.path.join(repo_root, "export_nodes.json")
    docs_root = os.path.join(repo_root, "mkdocs", "docs")

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    pages = []
    skipped = []
    locked_count = 0

    for full_name, ng in sorted(data.items()):
        if not full_name.startswith("MaStro "):
            continue
        short_name = full_name[len("MaStro "):]
        if short_name not in CATEGORIES:
            skipped.append(full_name)
            continue
        category, subcategory = CATEGORIES[short_name]
        rel_path, written = write_node_page(short_name, ng, category, subcategory, docs_root)
        pages.append((short_name, rel_path, category, subcategory))
        if written:
            print(f"  wrote {rel_path}")
        else:
            locked_count += 1

    print(f"\nGenerated {len(pages) - locked_count} pages, "
          f"left {locked_count} hand-edited pages untouched.")
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
