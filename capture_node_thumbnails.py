"""
For every "MaStro *" Geometry Nodes node group, add an instance of it to a
scratch node tree, screenshot just its box, cut out the background, save the
result, then remove the node and move on to the next one.

Run from Blender's Text Editor with mastro.blend open and a Geometry Node
Editor area visible somewhere on screen (the screenshot is a real screen
grab of that area, so it must not be occluded or minimized).

Before running, manually pan/zoom that Node Editor so its top-left corner
has enough room for the largest MaStro node (no need for it to be perfectly
framed) -- the script keeps that exact view fixed for every node, it does
not move the view itself. node.view_selected/view_all both require
SpaceNode.edittree to be wired up through the UI path stack in a way that
proved impossible to satisfy reliably from a script, so panning/zooming is
left to the user instead.

Requires ImageMagick's `magick` binary on PATH for the background removal.
"""

import os
import subprocess
import tempfile

import bpy

DOCS_IMAGES_DIR = os.path.join(
    os.path.dirname(bpy.data.filepath), "mkdocs", "docs", "nodes", "images"
)
BG_COLOR = (1.0, 0.0, 1.0)  # magenta, not used elsewhere in the node editor theme
FUZZ_PERCENT = 5
PADDING = 4  # pixels of margin kept around the node box before trimming
MARGIN_GUESS = 40  # rough top header height per Blender's node header drawing


def slugify(name):
    name = name.lower().strip()
    name = name.replace("maStro ".lower(), "")
    for ch in (" ", "_"):
        name = name.replace(ch, "-")
    return "".join(c for c in name if c.isalnum() or c == "-")


def find_node_editor_area():
    """Find a Node Editor area and force it into Geometry Nodes mode, since
    MaStro node groups are GeometryNodeTree and a Shader/Compositor editor
    would otherwise reject space.path.start() silently (it just ignores trees
    of the wrong type, leaving edit_tree pointing at the old shader tree)."""
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == "NODE_EDITOR":
                space = area.spaces[0]
                space.tree_type = "GeometryNodeTree"
                return window, area
    return None, None


def make_scratch_tree():
    tree = bpy.data.node_groups.new("ThumbnailScratch", "GeometryNodeTree")
    return tree


def screenshot_area(window, area, filepath):
    region = next(r for r in area.regions if r.type == "WINDOW")
    with bpy.context.temp_override(window=window, area=area, region=region):
        bpy.ops.screen.screenshot_area(filepath=filepath)


def node_screen_bounds(node, region):
    x0, y0 = node.location
    width = node.dimensions.x
    height = node.dimensions.y
    top_left = region.view2d.view_to_region(x0, y0, clip=False)
    bottom_right = region.view2d.view_to_region(x0 + width, y0 - height, clip=False)
    return top_left, bottom_right, region


def crop_screenshot(raw_path, out_path, top_left, bottom_right, region):
    rx0, ry0 = top_left
    rx1, ry1 = bottom_right
    # Screen Y grows upward in Blender's region space but downward in image space.
    img_y0 = region.height - ry0
    img_y1 = region.height - ry1
    x0 = max(int(min(rx0, rx1)) - PADDING, 0)
    x1 = int(max(rx0, rx1)) + PADDING
    y0 = max(int(min(img_y0, img_y1)) - PADDING - MARGIN_GUESS, 0)
    y1 = int(max(img_y0, img_y1)) + PADDING
    w = x1 - x0
    h = y1 - y0
    subprocess.run(
        ["magick", raw_path, "-crop", f"{w}x{h}+{x0}+{y0}", "+repage", out_path],
        check=True,
    )


def cut_out_background(in_path, out_path):
    subprocess.run(
        [
            "magick", in_path,
            "-alpha", "set",
            "-background", "none",
            "-fuzz", f"{FUZZ_PERCENT}%",
            "-fill", "none",
            "-draw", "color 0,0 floodfill",
            "-trim", "+repage",
            out_path,
        ],
        check=True,
    )


def main():
    window, area = find_node_editor_area()
    if area is None:
        raise RuntimeError("No visible Node Editor area found; open one before running.")

    space = area.spaces[0]
    theme = bpy.context.preferences.themes[0].node_editor
    prev_color = tuple(theme.space.back)
    theme.space.back = BG_COLOR

    tree = make_scratch_tree()
    region = next(r for r in area.regions if r.type == "WINDOW")
    with bpy.context.temp_override(window=window, area=area, region=region):
        space.path.start(tree)

    mastro_groups = sorted(
        (ng for ng in bpy.data.node_groups
         if ng.bl_idname == "GeometryNodeTree" and ng.name.startswith("MaStro ")),
        key=lambda ng: ng.name,
    )

    os.makedirs(DOCS_IMAGES_DIR, exist_ok=True)
    tmp_dir = tempfile.mkdtemp(prefix="mastro_thumbs_")

    for group in mastro_groups:
        short_name = group.name[len("MaStro "):]
        slug = slugify(short_name)
        out_dir = os.path.join(DOCS_IMAGES_DIR, slug)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "node.png")

        node = tree.nodes.new("GeometryNodeGroup")
        node.node_tree = group
        node.location = (0, 0)
        node.select = True
        tree.nodes.active = node

        bpy.context.view_layer.update()
        with bpy.context.temp_override(window=window, area=area, region=region):
            bpy.ops.wm.redraw_timer(type="DRAW_WIN_SWAP", iterations=1)

        raw_path = os.path.join(tmp_dir, f"{slug}_raw.png")
        screenshot_area(window, area, raw_path)

        top_left, bottom_right, region = node_screen_bounds(node, region)
        cropped_path = os.path.join(tmp_dir, f"{slug}_cropped.png")
        crop_screenshot(raw_path, cropped_path, top_left, bottom_right, region)
        cut_out_background(cropped_path, out_path)

        print(f"  saved {out_path}")

        tree.nodes.remove(node)

    theme.space.back = prev_color
    bpy.data.node_groups.remove(tree)
    print(f"\nDone. Processed {len(mastro_groups)} node groups.")


if __name__ == "__main__":
    main()
