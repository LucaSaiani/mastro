"""
For every "MaStro *" node belonging to TREE_TYPE, add an instance of it to a
scratch node tree, screenshot just its box, cut out the background, save the
result, then remove the node and move on to the next one. Also adds any
newly seen node name to node_categories.json (empty category, for the user
to fill in by hand) so a single run keeps both the images and the category
list in sync -- no separate script needed.

Run from Blender's Text Editor with mastro.blend open and a Node Editor area
visible somewhere on screen (the screenshot is a real screen grab of that
area, so it must not be occluded or minimized).

Before running, manually set a zoom level in that Node Editor that is small
enough to fit the largest MaStro node on screen -- the script keeps that
exact zoom fixed for every node (it never calls view_selected/view_all,
since their zoom-to-fit would make the on-screen size, and therefore the
fixed pixel margins used for cropping, vary per node). What the script does
do automatically is pan the view so each node's top-left corner always
lands at the same fixed point in the editor, regardless of the node's size.

Requires ImageMagick's `magick` binary on PATH for the background removal.
"""

import datetime
import json
import os
import subprocess
import sys
import tempfile
import time

import bpy

# Lives next to this script (mkdocs/generator/), same as in generate_node_docs.py.
CATEGORIES_JSON_PATH = os.path.join(
    os.path.dirname(bpy.data.filepath), "mkdocs", "generator", "node_categories.json"
)

LOG_PATH = os.path.join(
    os.path.dirname(bpy.data.filepath), "mkdocs", "generator", "capture_node_thumbnails.log"
)


class Tee:
    """Writes to both the original stream (so Blender's console still shows
    output live) and a log file, so the full run can be reviewed afterwards
    without having to scroll back or copy-paste from the console."""

    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for stream in self.streams:
            stream.write(data)

    def flush(self):
        for stream in self.streams:
            stream.flush()

# Which editor/node family to capture. One of "GeometryNodeTree" (MaStro
# architecture/mesh/etc. node groups), "ShaderNodeTree" (MaStro material
# node groups), or "MaStroScheduleTreeType" (MaStro Schedule's native nodes,
# not node groups -- see TREE_TYPE_PROFILES below).
TREE_TYPE = "GeometryNodeTree"

# Placeholder: same folder for every TREE_TYPE, keyed only by node slug.
# Fine as long as node names stay unique across GeometryNodeTree/ShaderNodeTree/
# MaStroScheduleTreeType -- adjust per TREE_TYPE (e.g. add a subfolder) if a
# name collision between two different node families ever comes up.
DOCS_IMAGES_DIR = os.path.join(
    os.path.dirname(bpy.data.filepath), "mkdocs", "docs", "nodes", "images"
)
DEBUG_NODE_LIMIT = None  # set to an int (e.g. 5) to process only the first N nodes, or None for all
SLEEP_BETWEEN_NODES = 0.5  # seconds; gives the UI time to actually settle between nodes
FUZZ_PERCENT = 5
BREADCRUMB_HEIGHT = 80  # fixed height of the editor's toolbar + path breadcrumb strips, kept out of the crop
PADDING = 60  # generous margin kept around the node box's known bounds before trim does the real work
TARGET_TOP_LEFT_X = 80  # fixed region-space X each node's top-left corner is panned to
TARGET_TOP_MARGIN = 80 + BREADCRUMB_HEIGHT  # gap kept between the editor's actual top edge and the node


def target_top_left(region):
    """region.view2d's Y axis is region-space: 0 at the bottom, growing
    upward -- the opposite of image-space. So "near the top" means a Y
    close to region.height, not close to 0 (that's near the bottom, which
    is what put nodes off-screen below the visible area before this)."""
    return (TARGET_TOP_LEFT_X, region.height - TARGET_TOP_MARGIN)


def slugify(name):
    name = name.lower().strip()
    name = name.replace("maStro ".lower(), "")
    for ch in (" ", "_"):
        name = name.replace(ch, "-")
    return "".join(c for c in name if c.isalnum() or c == "-")


def find_node_editor_area():
    """Find a Node Editor area and force it into TREE_TYPE's mode, since a
    Node Editor showing the wrong tree type rejects space.path.start()
    silently (it just ignores trees of the wrong type, leaving edit_tree
    pointing at whatever tree the editor previously had open)."""
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == "NODE_EDITOR":
                space = area.spaces[0]
                space.tree_type = TREE_TYPE
                return window, area
    return None, None


def make_scratch_tree_and_object_geometry_nodes():
    """The Geometry Node Editor only shows a tree when it is wired through an
    active object's Nodes modifier (see get_modifier_for_node_editor() in
    space_node.cc) -- space.path.start()/space.node_tree alone are not
    enough to populate SpaceNode.edit_tree. So build a real scratch object
    with a real Nodes modifier, just like a user would."""
    tree = bpy.data.node_groups.new("ThumbnailScratch", "GeometryNodeTree")
    mesh = bpy.data.meshes.new("ThumbnailScratchMesh")
    obj = bpy.data.objects.new("ThumbnailScratchObject", mesh)
    bpy.context.scene.collection.objects.link(obj)
    modifier = obj.modifiers.new("ThumbnailScratch", "NODES")
    modifier.node_group = tree
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    return tree, obj


def make_scratch_tree_and_object_shader():
    """Same idea as the Geometry Nodes case, but the Shader Editor reads the
    tree from the active object's active material slot (shaderfrom ==
    SNODE_SHADER_OBJECT) instead of a modifier. A material owns its node
    tree outright (can't point at an external ShaderNodeTree datablock the
    way a Nodes modifier points at a GeometryNodeTree), so the tree returned
    here is material.node_tree -- cleaned up by removing the material."""
    material = bpy.data.materials.new("ThumbnailScratchMaterial")
    material.use_nodes = True
    material.node_tree.nodes.clear()
    mesh = bpy.data.meshes.new("ThumbnailScratchMesh")
    obj = bpy.data.objects.new("ThumbnailScratchObject", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(material)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    return material.node_tree, obj


def make_scratch_tree_and_object_schedule():
    """The MaStro Schedule editor (panel.py: `space.edit_tree is not None`)
    doesn't key off an object/modifier/material at all -- it's a standalone
    tree like World shader nodes, so space.path.start() alone is enough."""
    tree = bpy.data.node_groups.new("ThumbnailScratch", "MaStroScheduleTreeType")
    return tree, None


TREE_TYPE_PROFILES = {
    "GeometryNodeTree": {
        "make_scratch": make_scratch_tree_and_object_geometry_nodes,
        "group_node_idname": "GeometryNodeGroup",
        "is_native": False,
    },
    "ShaderNodeTree": {
        "make_scratch": make_scratch_tree_and_object_shader,
        "group_node_idname": "ShaderNodeGroup",
        "is_native": False,
    },
    "MaStroScheduleTreeType": {
        "make_scratch": make_scratch_tree_and_object_schedule,
        "group_node_idname": None,
        "is_native": True,
    },
}


def screenshot_area(window, area, filepath):
    region = next(r for r in area.regions if r.type == "WINDOW")
    with bpy.context.temp_override(window=window, area=area, region=region):
        bpy.ops.screen.screenshot_area(filepath=filepath)


def force_redraw(window, area, region):
    """Block until the area has actually repainted. Without this, view2d
    reads from a previous, stale redraw -- pan deltas computed against that
    stale state don't converge and the pan error compounds every iteration
    until view_to_region() returns coordinates outside int32 range."""
    with bpy.context.temp_override(window=window, area=area, region=region):
        bpy.ops.wm.redraw_timer(type="DRAW_WIN_SWAP", iterations=1)


def pan_node_to_target(window, area, region, node, short_name=""):
    """Pan (without zooming) so node's top-left corner lands near the top of
    the editor, regardless of the node's size."""
    force_redraw(window, area, region)
    target = target_top_left(region)
    x0, y0 = node.location
    current_top_left = region.view2d.view_to_region(x0, y0, clip=False)
    delta_x = current_top_left[0] - target[0]
    delta_y = current_top_left[1] - target[1]
    v2d = region.view2d
    print(f"DEBUG pan[{short_name!r}]: node.location={node.location[:]}, "
          f"node.dimensions={node.dimensions[:]}, "
          f"region=({region.width}x{region.height}), "
          f"top_left={current_top_left[:]}, delta=({delta_x:.1f}, {delta_y:.1f}), "
          f"view_to_region(0,0)={v2d.view_to_region(0, 0, clip=False)[:]}, "
          f"region_to_view(0,0)={v2d.region_to_view(0, 0)[:]}")
    # view_to_region(..., clip=False) can return huge/garbage coordinates
    # when the queried point is far outside the current view (e.g. right
    # after adding a node whose location hasn't been laid out on screen
    # yet). A pan that big means something upstream is stale -- one extra
    # redraw/re-read cycle is enough to recover instead of feeding a
    # value VIEW2D_OT_pan's int32 deltax/deltay can't accept.
    max_delta = 100_000
    if abs(delta_x) > max_delta or abs(delta_y) > max_delta:
        print(f"WARNING: pan delta out of range (dx={delta_x}, dy={delta_y}, "
              f"node at {node.location[:]}, top_left={current_top_left[:]}); "
              f"forcing an extra redraw and retrying once.")
        force_redraw(window, area, region)
        current_top_left = region.view2d.view_to_region(x0, y0, clip=False)
        delta_x = current_top_left[0] - target[0]
        delta_y = current_top_left[1] - target[1]
        print(f"DEBUG pan[{short_name!r}] retry: top_left={current_top_left[:]}, "
              f"delta=({delta_x:.1f}, {delta_y:.1f})")
        if abs(delta_x) > max_delta or abs(delta_y) > max_delta:
            raise RuntimeError(
                f"pan delta still out of range after retry (dx={delta_x}, dy={delta_y}); "
                f"node at {node.location[:]}, top_left={current_top_left[:]}"
            )
    with bpy.context.temp_override(window=window, area=area, region=region):
        bpy.ops.view2d.pan(deltax=int(delta_x), deltay=int(delta_y))
    force_redraw(window, area, region)


def node_screen_bounds(node, region):
    x0, y0 = node.location
    width = node.dimensions.x
    height = node.dimensions.y
    top_left = region.view2d.view_to_region(x0, y0, clip=False)
    bottom_right = region.view2d.view_to_region(x0 + width, y0 - height, clip=False)
    return top_left, bottom_right, region


def crop_screenshot(raw_path, out_path, top_left, bottom_right, region):
    """Generously crop around the node's known bounds (extra padding absorbs
    the node's drop shadow and any margin-of-error in the screen-space
    mapping). The top edge is clamped to BREADCRUMB_HEIGHT so the editor's
    fixed-height path breadcrumb (always at image row 0, regardless of where
    the node sits) never makes it into the crop. cut_out_background()'s
    floodfill+trim then does the precise cropping, the same way the user's
    manual ImageMagick script does."""
    rx0, ry0 = top_left
    rx1, ry1 = bottom_right
    # Screen Y grows upward in Blender's region space but downward in image space.
    img_y0 = region.height - ry0
    img_y1 = region.height - ry1
    x0 = max(int(min(rx0, rx1)) - PADDING, 0)
    x1 = int(max(rx0, rx1)) + PADDING
    y0 = max(int(min(img_y0, img_y1)) - PADDING, BREADCRUMB_HEIGHT)
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


def find_targets(profile):
    """Returns a list of (display_name, add_node_fn) pairs to capture.
    Group-based trees (Geometry Nodes, Shader) capture every MaStro node
    group of that tree type; the Schedule tree captures its own natively
    registered node classes instead, since it has no node groups to wrap."""
    if profile["is_native"]:
        targets = []
        for cls in bpy.types.Node.__subclasses__():
            bl_idname = getattr(cls, "bl_idname", "")
            if bl_idname.startswith("MaStroSchedule") and bl_idname != "MaStroScheduleGroupTreeType":
                targets.append((cls.bl_label, bl_idname))
        targets.sort(key=lambda t: t[0])
        return [(name, lambda tree, idname=idname: tree.nodes.new(idname)) for name, idname in targets]

    group_idname = profile["group_node_idname"]
    groups = sorted(
        (ng for ng in bpy.data.node_groups
         if ng.bl_idname == TREE_TYPE and ng.name.startswith("MaStro ")),
        key=lambda ng: ng.name,
    )

    def add_group_node(tree, group=None):
        node = tree.nodes.new(group_idname)
        node.node_tree = group
        # New group nodes always get the generic ~160px default width from
        # the node *type*, not from the node_tree -- group.default_group_node_width
        # is the width remembered for this specific group (what you see when
        # dragging it out of the Add menu), so use that instead.
        node.width = group.default_group_node_width
        return node

    return [(group.name[len("MaStro "):], lambda tree, g=group: add_group_node(tree, g)) for group in groups]


def update_node_categories(target_names):
    """Add any newly seen node name to node_categories.json with empty
    category/subcategory for the user to fill in by hand. Existing entries
    (and their order) are left untouched -- this only appends."""
    with open(CATEGORIES_JSON_PATH, encoding="utf-8") as f:
        categories = json.load(f)

    added = [name for name in target_names if name not in categories]
    for name in added:
        categories[name] = {"category": "", "subcategory": None}

    if added:
        with open(CATEGORIES_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(categories, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"Added {len(added)} new node(s) to node_categories.json:")
        for name in added:
            print(f"  {name}")
        print('Fill in their "category" (and "subcategory" if needed) by hand.')


def main():
    profile = TREE_TYPE_PROFILES[TREE_TYPE]

    window, area = find_node_editor_area()
    if area is None:
        raise RuntimeError("No visible Node Editor area found; open one before running.")

    space = area.spaces[0]

    tree, scratch_obj = profile["make_scratch"]()
    region = next(r for r in area.regions if r.type == "WINDOW")
    with bpy.context.temp_override(window=window, area=area, region=region):
        space.path.start(tree)

    print(f"DEBUG: space.tree_type={space.tree_type!r}, "
          f"space.node_tree={space.node_tree!r}, space.edit_tree={space.edit_tree!r}, "
          f"want tree={tree!r}")

    targets = find_targets(profile)
    update_node_categories([name for name, _ in targets])
    if DEBUG_NODE_LIMIT is not None:
        targets = targets[:DEBUG_NODE_LIMIT]
        print(f"DEBUG_NODE_LIMIT set: only processing the first {len(targets)} node(s).")

    os.makedirs(DOCS_IMAGES_DIR, exist_ok=True)
    tmp_dir = tempfile.mkdtemp(prefix="mastro_thumbs_")

    for short_name, add_node in targets:
        slug = slugify(short_name)
        out_dir = os.path.join(DOCS_IMAGES_DIR, slug)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "node.png")

        node = add_node(tree)
        node.location = (0, 0)
        node.select = True
        tree.nodes.active = node

        bpy.context.view_layer.update()
        force_redraw(window, area, region)
        time.sleep(SLEEP_BETWEEN_NODES)
        pan_node_to_target(window, area, region, node, short_name=short_name)

        raw_path = os.path.join(tmp_dir, f"{slug}_raw.png")
        screenshot_area(window, area, raw_path)

        top_left, bottom_right, region = node_screen_bounds(node, region)
        cropped_path = os.path.join(tmp_dir, f"{slug}_cropped.png")
        crop_screenshot(raw_path, cropped_path, top_left, bottom_right, region)

        cut_out_background(cropped_path, out_path)

        print(f"  saved {out_path}")

        tree.nodes.remove(node)

    if scratch_obj is not None:
        mesh = scratch_obj.data
        materials = list(scratch_obj.data.materials) if TREE_TYPE == "ShaderNodeTree" else []
        bpy.data.objects.remove(scratch_obj)
        bpy.data.meshes.remove(mesh)
        # A material's node tree is owned by the material (deleted with it);
        # for the other tree types `tree` is its own node_groups datablock.
        for material in materials:
            bpy.data.materials.remove(material)
    if TREE_TYPE != "ShaderNodeTree":
        bpy.data.node_groups.remove(tree)
    print(f"\nDone. Processed {len(targets)} node(s).")


if __name__ == "__main__":
    log_file = open(LOG_PATH, "w", encoding="utf-8")
    real_stdout, real_stderr = sys.stdout, sys.stderr
    sys.stdout = Tee(real_stdout, log_file)
    sys.stderr = Tee(real_stderr, log_file)
    print(f"=== capture_node_thumbnails run started {datetime.datetime.now().isoformat()} ===")
    try:
        main()
    finally:
        sys.stdout, sys.stderr = real_stdout, real_stderr
        log_file.close()
        print(f"Log written to {LOG_PATH}")
