import bpy
import bmesh


def _layer_data(scene, layer_id):
    """Return a dict of edge attribute values for the given layer_id.

    seq is [l1, g1, l2, g2, l3, g3] trimmed of trailing zeros (fallback [1.0]).
    Returns None if no layer with that id exists.
    """
    layer = next((l for l in scene.mastro_cad_layers if l.layer_id == layer_id), None)
    if layer is None:
        return None

    pen = next((p for p in scene.mastro_cad_pens if p.pen_id == layer.pen_id), None)
    thickness = (pen.thickness if pen else 0.2) / 2000.0

    pattern = next((p for p in scene.mastro_cad_dash_patterns if p.pattern_id == layer.pattern_id), None)
    seq = pattern.to_sequence() if pattern else [1.0]

    slots = [pattern.l1, pattern.g1, pattern.l2, pattern.g2, pattern.l3, pattern.g3] if pattern else [1.0, 0, 0, 0, 0, 0]
    resample = not (slots[1] == 0.0 and slots[2] == 0.0 and slots[3] == 0.0 and slots[4] == 0.0 and slots[5] == 0.0)

    return {
        "thickness": thickness,
        "seq":       seq,
        "black":     layer.black,
        "visible":   layer.visible,
        "resample":  resample,
    }


def update_all_bmesh_drawing_attributes(context):
    """Update all layers on all drawing mesh objects (e.g. on file load)."""
    scene = context.scene
    all_ids = {l.layer_id for l in scene.mastro_cad_layers}
    update_bmesh_drawing_attributes(context, all_ids)


def set_black_switch(context, value: bool):
    """Write value to mastro_drawing_black_switch on every edge of every drawing mesh."""
    scene = context.scene
    for obj in scene.objects:
        if obj.type != 'MESH' or not obj.data.get("MaStro drawing mesh"):
            continue
        mesh = obj.data
        object_mode = obj.mode

        if object_mode == 'EDIT':
            bm = bmesh.from_edit_mesh(mesh)
        else:
            bm = bmesh.new()
            bm.from_mesh(mesh)

        bm.edges.ensure_lookup_table()
        sw_attr = bm.edges.layers.bool.get("mastro_drawing_black_switch")
        if sw_attr is not None:
            for edge in bm.edges:
                edge[sw_attr] = value

        if object_mode == 'EDIT':
            bmesh.update_edit_mesh(mesh)
        else:
            bm.to_mesh(mesh)
            bm.free()
            mesh.update()
            mesh.update()
            obj.update_tag()


def update_bmesh_drawing_attributes(context, layer_ids):
    """Push layer-derived values onto every MaStro drawing mesh edge.

    layer_ids: set of layer_id ints to update.
    Respects the mastro_cad_auto_update_layers toggle.
    """
    if not context.window_manager.mastro_cad_auto_update_layers:
        return

    scene = context.scene

    # Build a cache: layer_id → attribute dict (avoid repeated scene lookups)
    cache = {}

    for obj in scene.objects:
        if obj.type != 'MESH':
            continue
        if not obj.data.get("MaStro drawing mesh"):
            continue

        mesh = obj.data
        object_mode = obj.mode

        if object_mode == 'EDIT':
            bm = bmesh.from_edit_mesh(mesh)
        else:
            bm = bmesh.new()
            bm.from_mesh(mesh)

        bm.edges.ensure_lookup_table()

        try:
            layer_attr   = bm.edges.layers.int.get("mastro_drawing_layer")
            thick_attr   = bm.edges.layers.float.get("mastro_drawing_thickness")
            sl1_attr     = bm.edges.layers.float.get("mastro_drawing_style_l1")
            sg1_attr     = bm.edges.layers.float.get("mastro_drawing_style_g1")
            sl2_attr     = bm.edges.layers.float.get("mastro_drawing_style_l2")
            sg2_attr     = bm.edges.layers.float.get("mastro_drawing_style_g2")
            sl3_attr     = bm.edges.layers.float.get("mastro_drawing_style_l3")
            sg3_attr     = bm.edges.layers.float.get("mastro_drawing_style_g3")
            black_attr       = bm.edges.layers.bool.get("mastro_drawing_black")
            vis_attr         = bm.edges.layers.bool.get("mastro_drawing_visibile")
            resample_attr = bm.edges.layers.bool.get("mastro_drawing_resample")
        except Exception:
            if object_mode != 'EDIT':
                bm.free()
            continue

        if layer_attr is None:
            if object_mode != 'EDIT':
                bm.free()
            continue

        for edge in bm.edges:
            lid = edge[layer_attr]
            if lid not in layer_ids:
                continue

            if lid not in cache:
                cache[lid] = _layer_data(scene, lid)
            data = cache[lid]
            if data is None:
                continue

            seq = data["seq"]
            # Pad to 6 slots [l1,g1,l2,g2,l3,g3] and convert mm → m
            padded = [(v / 1000.0) for v in (seq + [0.0] * 6)[:6]]

            if thick_attr  is not None: edge[thick_attr]  = data["thickness"]
            if sl1_attr    is not None: edge[sl1_attr]    = padded[0]
            if sg1_attr    is not None: edge[sg1_attr]    = padded[1]
            if sl2_attr    is not None: edge[sl2_attr]    = padded[2]
            if sg2_attr    is not None: edge[sg2_attr]    = padded[3]
            if sl3_attr    is not None: edge[sl3_attr]    = padded[4]
            if sg3_attr    is not None: edge[sg3_attr]    = padded[5]
            if black_attr    is not None: edge[black_attr]    = data["black"]
            if vis_attr      is not None: edge[vis_attr]      = data["visible"]
            if resample_attr is not None: edge[resample_attr] = data["resample"]

        if object_mode == 'EDIT':
            bmesh.update_edit_mesh(mesh)
        else:
            bm.to_mesh(mesh)
            bm.free()
            mesh.update()
