# Node documentation generator

Scripts that generate the MaStro node reference under `mkdocs/docs/nodes/`.

## Files

- `capture_node_thumbnails.py` -- run inside Blender. Screenshots every
  MaStro node's box, cuts out the background, and saves it to
  `mkdocs/docs/nodes/images/<slug>/node.png`. Also appends any newly seen
  node name to `node_categories.json` (with an empty category for you to
  fill in by hand).
- `generate_node_docs.py` -- run from a plain terminal (no Blender). Reads
  `export_nodes.json` (repo root) and `node_categories.json`, and writes one
  Markdown page per node under `mkdocs/docs/nodes/`.
- `node_categories.json` -- maps each node name (without the "MaStro "
  prefix) to `{"category": ..., "subcategory": ...}`. This is the only
  place that decides which section of the docs site a node belongs to --
  nothing in `export_nodes.json` or in Blender can derive that automatically,
  so it's a plain editable JSON file rather than hardcoded in a script.
  Edit it by hand to add new nodes or fix a node's category.

## Workflow

1. **Capture thumbnails.** Open `mastro.blend` in Blender, with a Node
   Editor area visible on screen. In `capture_node_thumbnails.py`:
   - Set `TREE_TYPE` to the editor/node family you want to capture:
     `"GeometryNodeTree"` (MaStro architecture/mesh/etc. node groups),
     `"ShaderNodeTree"` (MaStro material node groups), or
     `"MaStroScheduleTreeType"` (MaStro Schedule's native nodes).
   - Manually zoom/pan that Node Editor so the largest node of that family
     fits on screen -- the script keeps the zoom level fixed for every node
     it captures (it never zoom-to-fits), so the crop margins stay
     consistent across all the generated images.
   - Leave `DEBUG_STOP_AFTER_FIRST_NODE = True` for a first run: the script
     captures only the first node and stops, so you can check the result in
     `mkdocs/docs/nodes/images/<slug>/node.png` before committing to a full
     run. Once the framing looks right, set it to `False` and run again to
     process every node of that TREE_TYPE.
   - Repeat for each TREE_TYPE you need images for.
   - Requires ImageMagick's `magick` binary on `PATH`.

2. **Edit `node_categories.json`.** The capture script appends any node
   name it doesn't recognize yet, with `"category": ""`. Fill in the
   category (and subcategory, if the category has one -- see existing
   entries for the list in use, e.g. `architecture`/`annotation`) for any
   new entries.

3. **Generate the pages.** From the repo root (or anywhere):
   ```
   python3 mkdocs/generator/generate_node_docs.py
   ```
   This writes one page per node under `mkdocs/docs/nodes/<category>/
   [<subcategory>/]<slug>.md`, and prints a nav block to paste into
   `mkdocs/mkdocs.yml` under `Nodes:`.

   Pages are never blindly overwritten: a page is left untouched once its
   main description (the text right under the title, before the **Inputs**
   section) no longer contains the `*Description to be written.*`
   placeholder -- that's the signal that someone has written real content
   for it. Socket-level placeholders don't count, since those commonly stay
   unwritten long after the main description is done.
