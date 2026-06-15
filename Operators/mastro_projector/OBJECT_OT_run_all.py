import bpy
import math
import time
from bpy.types import Operator

from ...Utils.mastro_preferences.get_preferences import get_prefs

from ...Utils.mastro_projector.shadow_helpers  import (get_light_source, sun_direction,
                                      sun_direction_from_props,
                                      scene_mesh_objects, collect_world_vertices,
                                      build_sun_visible_faces, get_scene_extent,
                                      purge_shadow_helpers, _clear_header,
                                      stash_children, restore_stash, clear_stash,
                                      unhide_empty_children,
                                      collect_projector_empty_children,
                                      collect_collection_objects)
# from ...Utils.mastro_projector.ss_shadow_grid       import build_plane_axes, make_base_grid     # Adaptive Grid disabled
# from ...Utils.mastro_projector.ss_shadow_timer      import _state as _shadow_state, _tick_grid  # Adaptive Grid disabled
from ...Utils.mastro_projector.shadow_render     import run_render_shadow, _state as _render_state
from ...Utils.mastro_projector.proj_timer        import _proj_state, _tick_projection
from ...Utils.mastro_projector.scene_graph_helpers import (_get_or_create_empty,
                                          _get_or_create_empty_keep,
                                          _detach_user_edits,
                                          delete_projection_outputs)


def _setup_shared_empty(camera, scene, proj_props):
    """Create/position the shared empty for this camera, return it."""
    empty_name = camera.name + get_prefs().projection_suffix

    if proj_props.place_on_camera_plane:
        user_edits = []
        if empty_name in bpy.data.objects:
            user_edits = _detach_user_edits(bpy.data.objects[empty_name])
        empty = _get_or_create_empty(empty_name, scene)
        for ch in user_edits:
            ch.parent = empty

        cam_mat  = camera.matrix_world
        cam_data = camera.data
        forward  = -cam_mat.col[2].xyz.normalized()
        render   = scene.render
        aspect_r = (render.resolution_x * render.pixel_aspect_x) / \
                   (render.resolution_y * render.pixel_aspect_y)
        near     = cam_data.clip_start + 0.01

        if cam_data.type == 'PERSP':
            if cam_data.sensor_fit == 'VERTICAL' or \
               (cam_data.sensor_fit == 'AUTO' and aspect_r < 1.0):
                fov_y = cam_data.angle
            else:
                fov_y = 2 * math.atan(math.tan(cam_data.angle / 2) / aspect_r)
            empty_scale = near * math.tan(fov_y / 2)
        else:
            # The projector already emits orthographic geometry in world
            # units (see Projector.ortho_world_scale), so the empty itself
            # must not re-scale it. ortho_extent is only used below to keep
            # the empty within the clipping volume.
            half_h = cam_data.ortho_scale / 2
            if cam_data.sensor_fit == 'VERTICAL' or \
               (cam_data.sensor_fit == 'AUTO' and aspect_r < 1.0):
                ortho_extent = half_h
            else:
                ortho_extent = half_h / aspect_r
            near = cam_data.clip_start + ortho_extent * 0.1
            empty_scale = 1.0

        empty.location       = cam_mat.translation + forward * near
        empty.rotation_euler = camera.rotation_euler
        empty.scale          = (empty_scale,) * 3
        empty["projector_on_camera_plane"] = True

    else:
        existing = bpy.data.objects.get(empty_name)
        if existing is not None and existing.get("projector_on_camera_plane"):
            user_edits = _detach_user_edits(existing)
            empty = _get_or_create_empty(empty_name, scene)
            for ch in user_edits:
                ch.parent = empty
        else:
            empty = _get_or_create_empty_keep(empty_name, scene)

        if "projector_on_camera_plane" in empty:
            del empty["projector_on_camera_plane"]

    return empty


def _collect_excluded_names(scene, camera, proj_props, allowed_names=None):
    # Children of ALL projector empties are always excluded from projection.
    excluded = collect_projector_empty_children(scene)

    def _get_disabled(lc, out):
        if lc.exclude or lc.hide_viewport or lc.collection.hide_viewport:
            out.add(lc.collection.name)
        for child in lc.children:
            _get_disabled(child, out)

    disabled = set()
    _get_disabled(bpy.context.view_layer.layer_collection, disabled)
    for o in scene.objects:
        if o.hide_get() or o.hide_viewport or any(c.name in disabled for c in o.users_collection):
            excluded.add(o.name)

    # Objects explicitly chosen via source_collection bypass view-layer visibility.
    if allowed_names:
        excluded -= allowed_names

    return excluded


class OBJECT_OT_RunAll(Operator):
    bl_idname      = "object.mastro_projector_run_all"
    bl_label       = "Run"
    bl_description = "Run enabled operations (2D Projection and/or Shadow Bake)"
    bl_options     = {"REGISTER", "UNDO"}

    def execute(self, context):
        props  = context.scene.mastro_projector_props
        camera = context.scene.camera

        if camera is None:
            self.report({"ERROR"}, "No active camera in the scene.")
            return {"CANCELLED"}

        proj_props = camera.data.mastro_projector_cl

        if not proj_props.run_shadows and not proj_props.run_projection:
            self.report({"WARNING"}, "Enable at least one operation.")
            return {"CANCELLED"}
        scene      = context.scene

        # ── Set up shared empty ───────────────────────────────────────────────
        empty = _setup_shared_empty(camera, scene, proj_props)
        delete_projection_outputs(empty)
        stash_children(empty)

        # ── Resolve source collection filter ──────────────────────────────────
        src_coll = proj_props.source_collection
        allowed_objects = (
            collect_collection_objects(src_coll) if src_coll is not None else None
        )
        allowed_names = (
            {o.name for o in allowed_objects} if allowed_objects is not None else None
        )

        # ── Shadow ────────────────────────────────────────────────────────────
        if proj_props.run_shadows:
            sun     = get_light_source(context)
            sun_dir = sun_direction_from_props(proj_props, camera=camera)
            mesh_objs = scene_mesh_objects(context, sun, allowed_objects=allowed_objects)
            if not mesh_objs:
                self.report({"ERROR"}, "No visible mesh found.")
                return {"CANCELLED"}

            purge_shadow_helpers(empty)

            # Exclude children of ALL projector empties (results of any camera).
            proj_children = collect_projector_empty_children(scene)
            mesh_objs = [o for o in mesh_objs if o.name not in proj_children]

            depsgraph   = context.evaluated_depsgraph_get()
            eval_objs   = [obj.evaluated_get(depsgraph) for obj in mesh_objs]
            world_verts = collect_world_vertices(eval_objs)
            if not world_verts:
                self.report({"ERROR"}, "No visible mesh found.")
                return {"CANCELLED"}

            extent  = get_scene_extent(world_verts, sun_dir)
            sun_vis = build_sun_visible_faces(eval_objs, sun_dir)

            try:
                run_render_shadow(context, sun, empty, camera, light_dir=sun_dir)
            except Exception as exc:
                self.report({"ERROR"}, f"Shadow failed: {exc}")
                return {"CANCELLED"}
            if not props.proj_is_running:
                clear_stash(empty)
                unhide_empty_children(empty)

        # ── 2D Projection ─────────────────────────────────────────────────────
        if proj_props.run_projection:
            excluded = _collect_excluded_names(scene, camera, proj_props, allowed_names=allowed_names)
            _proj_state.clear()
            _proj_state.update({
                "running":        True,
                "phase":          "setup",
                "scene":          scene,
                "camera":         camera,
                "empty":          empty,
                "excluded_names": excluded,
                "allowed_names":  allowed_names,
            })
            props.proj_is_running = True
            # If render shadow is running concurrently, it temporarily changes
            # render.resolution_x/y for the bake. Starting the projection timer
            # immediately would read the wrong resolution and produce a distorted
            # result. Instead we do nothing here: shadow_render._finish() calls
            # bpy.app.timers.register(_tick_projection) once the bake is complete.
            if not proj_props.run_shadows:
                bpy.app.timers.register(_tick_projection, first_interval=0.0, persistent=False)

        return {"FINISHED"}


class OBJECT_OT_CancelAll(Operator):
    bl_idname      = "object.mastro_projector_cancel_all"
    bl_label       = "Cancel"
    bl_description = "Stop all running operations."
    bl_options     = {"INTERNAL"}

    def execute(self, context):
        _render_state["running"] = False
        _proj_state["running"]   = False
        props = context.scene.mastro_projector_props
        props.is_running      = False
        props.proj_is_running = False
        props.batch_queue.clear()
        props.batch_cursor = 0
        _clear_header()
        empty = _proj_state.get("empty")
        if empty:
            restore_stash(empty)
        return {"FINISHED"}
