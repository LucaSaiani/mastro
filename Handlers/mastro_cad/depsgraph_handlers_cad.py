import bpy
import bmesh


def _assign_layer_to_edge(scene, bm, edge):
    """Write the active layer's attributes onto edge. Skipped if already assigned."""
    from ...Utils.mastro_cad.update_bmesh_drawing_attributes import _layer_data

    layer_attr = bm.edges.layers.int.get("mastro_drawing_layer")
    if layer_attr is None:
        return
    if edge[layer_attr] != 0:
        return  # already assigned — don't overwrite

    layers = scene.mastro_cad_layers
    idx    = scene.mastro_cad_layer_index
    if not (0 <= idx < len(layers)):
        return
    layer_id = layers[idx].layer_id

    thick_attr    = bm.edges.layers.float.get("mastro_drawing_thickness")
    sl1_attr      = bm.edges.layers.float.get("mastro_drawing_style_l1")
    sg1_attr      = bm.edges.layers.float.get("mastro_drawing_style_g1")
    sl2_attr      = bm.edges.layers.float.get("mastro_drawing_style_l2")
    sg2_attr      = bm.edges.layers.float.get("mastro_drawing_style_g2")
    sl3_attr      = bm.edges.layers.float.get("mastro_drawing_style_l3")
    sg3_attr      = bm.edges.layers.float.get("mastro_drawing_style_g3")
    black_attr    = bm.edges.layers.bool.get("mastro_drawing_black")
    vis_attr      = bm.edges.layers.bool.get("mastro_drawing_visibile")
    resample_attr = bm.edges.layers.bool.get("mastro_drawing_resample")

    data = _layer_data(scene, layer_id)
    if data is None:
        return

    padded = [(v / 1000.0) for v in (data["seq"] + [0.0] * 6)[:6]]

    edge[layer_attr] = layer_id
    if thick_attr    is not None: edge[thick_attr]    = data["thickness"]
    if sl1_attr      is not None: edge[sl1_attr]      = padded[0]
    if sg1_attr      is not None: edge[sg1_attr]      = padded[1]
    if sl2_attr      is not None: edge[sl2_attr]      = padded[2]
    if sg2_attr      is not None: edge[sg2_attr]      = padded[3]
    if sl3_attr      is not None: edge[sl3_attr]      = padded[4]
    if sg3_attr      is not None: edge[sg3_attr]      = padded[5]
    if black_attr    is not None: edge[black_attr]    = data["black"]
    if vis_attr      is not None: edge[vis_attr]      = data["visible"]
    if resample_attr is not None: edge[resample_attr] = data["resample"]


def _handle_drawing_extrusion(scene, obj, bm):
    """Detect vertex extrusion (E) and new-edge (F) on a MaStro drawing mesh.

    Mirrors the pattern used in mastro's _handle_block_extrusion:
    - state tracked as scene properties
    - vertex select mode required
    - same active vert → check F key (edge count grew by 1, 2 verts selected)
    - new active vert → check extrusion (1 vert selected, 1 linked edge)
    - sentinel: layer == 0 means unassigned
    """
    if not bpy.context.scene.tool_settings.mesh_select_mode[0]:
        return
    if not isinstance(bm.select_history.active, bmesh.types.BMVert):
        return

    active_vert      = bm.select_history.active
    number_of_edges  = len(bm.edges)

    if scene.mastro_cad_drawing_previous_vert_id != active_vert.index:
        # Active vertex changed → extrusion (E key)
        scene.mastro_cad_drawing_previous_vert_id = active_vert.index
        selected_verts = [v for v in bm.verts if v.select]
        if len(selected_verts) == 1 and len(active_vert.link_edges) == 1:
            new_edge = active_vert.link_edges[0]
            _assign_layer_to_edge(scene, bm, new_edge)
    else:
        # Same active vertex → check for F key (new edge between two selected verts)
        selected_verts = [v for v in bm.verts if v.select]
        if len(selected_verts) == 2 and scene.mastro_cad_drawing_previous_edge_number == number_of_edges - 1:
            _assign_layer_to_edge(scene, bm, bm.edges[-1])

    scene.mastro_cad_drawing_previous_edge_number = number_of_edges
    bmesh.update_edit_mesh(obj.data)


def _check_drawing_objects(context):
    seen = set()
    candidates = []

    if hasattr(context, 'objects_in_mode_unique_data'):
        candidates.extend(context.objects_in_mode_unique_data)
    if context.active_object:
        candidates.append(context.active_object)

    for obj in candidates:
        if obj.name in seen:
            continue
        seen.add(obj.name)
        if obj.type != 'MESH' or not obj.data.get("MaStro drawing mesh") or obj.mode != 'EDIT':
            continue
        bm = bmesh.from_edit_mesh(obj.data)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        _handle_drawing_extrusion(context.scene, obj, bm)


_prev_camera_name  = None
_prev_in_cam_view  = None


def _detect_camera_view():
    """Return True if any 3D viewport is in camera view."""
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        if space.region_3d.view_perspective == 'CAMERA':
                            return True
    return False


def _monitor_scale():
    """Timer callback — syncs drawing scale when camera or view perspective changes."""
    global _prev_camera_name, _prev_in_cam_view
    context = bpy.context
    if context is None or context.scene is None:
        return 0.2

    scene        = context.scene
    cam          = scene.camera
    cam_name     = cam.name if cam else None
    in_cam_view  = _detect_camera_view()

    _prev_camera_name = cam_name
    _prev_in_cam_view = in_cam_view

    # Always sync from the current source so scale changes are picked up.
    if in_cam_view and cam and cam.type == 'CAMERA':
        new_scale = cam.data.mastro_cad_drawing_scale
    else:
        new_scale = scene.mastro_cad_drawing_scale_viewport

    if scene.mastro_cad_drawing_scale != new_scale:
        scene.mastro_cad_drawing_scale = new_scale

    _update_scale_header(scene)
    return 0.2


def _update_scale_header(scene):
    """Tag the viewport and statusbar for redraw so the scale label stays current."""
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type in ('VIEW_3D', 'INFO'):
                area.tag_redraw()


def register():
    bpy.app.timers.register(_monitor_scale, first_interval=0.2, persistent=True)


def unregister():
    if bpy.app.timers.is_registered(_monitor_scale):
        bpy.app.timers.unregister(_monitor_scale)
