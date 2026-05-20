import bpy
import math
from bpy.types import Operator
from mathutils import Vector

from ..Utils.get_preferences import get_prefs
from ..Utils.projection.projector import _Projector
from ..Utils.projection.build_global_bvh import _build_global_bvh
from ..Utils.projection.intersection_curve_merge_projected import _merge_intersections_into_results
from ..Utils.projection.merge_per_category import _merge_category_bmeshes
from ..Utils.projection.merge_by_distance import _merge_bmeshes_by_distance
from ..Utils.projection.scene_graph_helpers import (_get_or_create_empty_keep,
                                         _get_or_create_empty,
                                         _detach_user_edits,
                                         apply_depth_offset,
                                         convert_objects_to_grease_pencil,
                                         _GP_TYPES)
from ..Utils.projection.snap_orphans import _snap_orphans_in_bmeshes
from ..Utils.projection.deduplicate_merged import _deduplicate_merged_edges
from ..Utils.projection.write_merged import _write_merged_object
from ..Utils.projection.section_outline import _compute_and_write_section_outline

class OBJECT_OT_bidimensional_Lines_Projection(Operator):
    """Creates a 2D representation of the 3D scene as shown in the camera"""
    bl_idname  = "object.mastro_bidimensional_lines_projection"
    bl_label   = "Run Projection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        import time
        t_start = time.perf_counter()

        scene  = context.scene
        camera = scene.camera

        if camera is None:
            self.report({'ERROR'}, "No active camera in the scene!")
            return {'CANCELLED'}

        props      = camera.data.mastro_projector_cl
        depsgraph  = context.evaluated_depsgraph_get()
        empty_name = camera.name + get_prefs().projection_suffix

        # ── Delete previously projected objects ───────────────────────────────
        excluded_names = set()

        # Always exclude ALL children of the projection empty — both projection
        # outputs and user-created edits — so they are never re-projected.
        if empty_name in bpy.data.objects:
            def _add_descendants(obj):
                for child in obj.children:
                    excluded_names.add(child.name)
                    _add_descendants(child)
            _add_descendants(bpy.data.objects[empty_name])

        if props.only_selected_objects:
            selected_names = {obj.name for obj in scene.objects if obj.select_get()}
            for src_name in selected_names:
                proj_name = src_name + get_prefs().projection_suffix
                obj = bpy.data.objects.get(proj_name)
                if obj is not None:
                    if obj.type == 'MESH':
                        bpy.data.meshes.remove(obj.data, do_unlink=True)
                    else:
                        bpy.data.objects.remove(obj, do_unlink=True)
                excluded_names.add(proj_name)
        else:
            to_delete = [
                obj for obj in scene.objects
                if obj.name.endswith(get_prefs().projection_suffix)
                and (obj.type == 'MESH' or obj.type in _GP_TYPES)
            ]
            for obj in to_delete:
                excluded_names.add(obj.name)
                if obj.type == 'MESH':
                    bpy.data.meshes.remove(obj.data, do_unlink=True)
                else:
                    bpy.data.objects.remove(obj, do_unlink=True)

        # ── Collect names of hidden objects / disabled collections ────────────
        def get_disabled_collections(layer_collection, disabled_set):
            if layer_collection.exclude or layer_collection.hide_viewport:
                disabled_set.add(layer_collection.collection.name)
            if layer_collection.collection.hide_viewport:
                disabled_set.add(layer_collection.collection.name)
            for child in layer_collection.children:
                get_disabled_collections(child, disabled_set)

        disabled_colls = set()
        get_disabled_collections(
            bpy.context.view_layer.layer_collection, disabled_colls
        )

        for obj in scene.objects:
            is_hidden_direct = obj.hide_get() or obj.hide_viewport
            in_disabled_coll = any(
                c.name in disabled_colls for c in obj.users_collection
            )
            if is_hidden_direct or in_disabled_coll:
                excluded_names.add(obj.name)

        # ── Build the global BVHTree ONCE ─────────────────────────────────────
        clip_bvh_kwargs = {}
        if props.camera_clipping:
            clip_bvh_kwargs = {
                'cam_location': camera.matrix_world.translation.copy(),
                'cam_fwd':      (-camera.matrix_world.col[2].xyz).normalized(),
                'clip_start':   camera.data.clip_start,
                'clip_end':     camera.data.clip_end,
            }
        global_bvh, poly_to_obj = _build_global_bvh(
            scene, depsgraph, excluded_names, **clip_bvh_kwargs
        )
        projector = _Projector(props, global_bvh=global_bvh, poly_to_obj=poly_to_obj)

        # ── STEP 1: project every visible object to 2D ────────────────────────
        wm = context.window_manager
        wm.progress_begin(0, 100)

        results, aspect = projector.build_projection_per_object(
            scene, depsgraph, camera, excluded_names
        )
        wm.progress_update(40)

        if not results:
            wm.progress_end()
            self.report({'WARNING'},
                        "No visible edges found — check the scene and the camera.")
            return {'CANCELLED'}

        view_matrix, proj_matrix, aspect = projector.get_camera_matrices(
            scene, camera, depsgraph
        )

        # ── STEP 2 (optional): merge intersection curves ──────────────────────
        if props.compute_intersections:
            _merge_intersections_into_results(
                results, scene, depsgraph, projector,
                view_matrix, proj_matrix, aspect
            )
        wm.progress_update(55)

        # ── STEP 3 (optional): merge by distance ─────────────────────────────
        # Must happen BEFORE snap so that near-coincident vertices are
        # collapsed before orphan detection — avoids snapping false orphans.
        merged_verts = 0
        if props.merge_by_distance:
            merged_verts = _merge_bmeshes_by_distance(results, props.merge_distance)
        wm.progress_update(65)

        # ── STEP 4 (optional): snap orphan endpoints ──────────────────────────
        # Operates on per-category bmeshes before they are merged, using the
        # original implementation that is known to work correctly.
        snapped = 0
        if props.snap_orphans:
            snap_bms = []
            sync_bms = []
            for data in results.values():
                # bm_visible and bm_hidden are the complete supersets — used as
                # orphan sources and ray-cast targets.
                snap_bms.append((data.bm_visible, {}))
                snap_bms.append((data.bm_hidden,  {}))
                # bm_silhouette, bm_silhouette_hidden, and bm_section are
                # subsets — their vertices must be kept in sync with any moves
                # and splits applied to the supersets, but must NOT be added as
                # snap sources or their shared vertices would be double-counted
                # in pos_degree.
                sync_bms.append((data.bm_silhouette,        {}))
                sync_bms.append((data.bm_silhouette_hidden, {}))
                sync_bms.append((data.bm_section,           {}))
            # Adaptive sampling disabled — always use uniform (max_dist=None)
            # max_dist = (props.snap_max_distance
            #             if props.sampling_method == 'ADAPTIVE' else None)
            max_dist = None
            snapped = _snap_orphans_in_bmeshes(
                snap_bms,
                sync_bm_list=sync_bms,
                max_snap_distance=max_dist,
            )
        wm.progress_update(75)

        # ── STEP 4.5: collect section edges for the global outline ────────────
        # Must happen before _merge_category_bmeshes, which frees bm_section.
        section_segs = []
        for data in results.values():
            bm_sec = data.bm_section
            if bm_sec is None:
                continue
            for edge in bm_sec.edges:
                a = Vector((edge.verts[0].co.x, edge.verts[0].co.y, 0.0))
                b = Vector((edge.verts[1].co.x, edge.verts[1].co.y, 0.0))
                if (b - a).length > 1e-7:
                    section_segs.append((a, b))

        # ── STEP 5: merge per-category bmeshes into one bmesh per object ──────
        merged = {}
        for src_name, data in results.items():
            bm_merged, category_verts = _merge_category_bmeshes(data)
            if bm_merged is None:
                continue
            merged[src_name] = (bm_merged, category_verts)

        if not merged:
            wm.progress_end()
            self.report({'WARNING'}, "No geometry produced.")
            return {'CANCELLED'}

        # ── STEP 5b: cross-object edge deduplication ──────────────────────────
        # Removes edges that appear in more than one source object's projection
        # (e.g. two walls sharing a surface both projecting the same boundary
        # edge to the same 2D position).
        dedup_removed = _deduplicate_merged_edges(merged)

        wm.progress_update(85)

        # ── STEP 6: write merged bmeshes to the scene ─────────────────────────
        bpy.ops.object.select_all(action='DESELECT')

        if props.only_selected_objects and empty_name in bpy.data.objects:
            # Incremental mode: always preserve the existing empty.
            empty = _get_or_create_empty_keep(empty_name, scene)

        elif props.place_on_camera_plane:
            # Place on camera plane: recreate and reposition the empty every run.
            # Detach user edits first so _delete_hierarchy does not remove them.
            user_edits = []
            if empty_name in bpy.data.objects:
                user_edits = _detach_user_edits(
                    bpy.data.objects[empty_name], get_prefs().projection_suffix
                )
            empty = _get_or_create_empty(empty_name, scene)
            for ch in user_edits:
                ch.parent = empty

            cam_mat  = camera.matrix_world
            cam_data = camera.data
            forward  = -cam_mat.col[2].xyz.normalized()
            near     = cam_data.clip_start + 0.01  # default for perspective
            render   = scene.render
            aspect_r = (render.resolution_x * render.pixel_aspect_x) / \
                       (render.resolution_y * render.pixel_aspect_y)

            if cam_data.type == 'PERSP':
                if cam_data.sensor_fit == 'VERTICAL' or \
                   (cam_data.sensor_fit == 'AUTO' and aspect_r < 1.0):
                    fov_y = cam_data.angle
                else:
                    fov_y = 2 * math.atan(
                        math.tan(cam_data.angle / 2) / aspect_r
                    )
                empty_scale = near * math.tan(fov_y / 2)
            else:
                half_h = cam_data.ortho_scale / 2
                if cam_data.sensor_fit == 'VERTICAL' or \
                   (cam_data.sensor_fit == 'AUTO' and aspect_r < 1.0):
                    empty_scale = half_h
                else:
                    empty_scale = half_h / aspect_r
                # For orthographic cameras, push the empty far enough from
                # clip_start so that the full extent of the scaled geometry
                # stays within the clipping volume.
                near = cam_data.clip_start + empty_scale * 0.1

            empty.location       = cam_mat.translation + forward * near
            empty.rotation_euler = camera.rotation_euler
            empty.scale          = (empty_scale,) * 3

            # Tag the empty so future runs know it was created on the camera
            # plane — used to decide whether to recreate or preserve it when
            # place_on_camera_plane is toggled off.
            empty["projector_on_camera_plane"] = True

        else:
            # Free placement mode: preserve the empty position if it exists
            # and was NOT previously created on the camera plane (so the user
            # can move it freely between runs). If it was on the camera plane,
            # recreate it at the world origin to avoid a stale camera-aligned
            # transform confusing the user.
            existing = bpy.data.objects.get(empty_name)
            if existing is not None and existing.get("projector_on_camera_plane"):
                # Previous run used place_on_camera_plane — start fresh.
                user_edits = _detach_user_edits(existing, get_prefs().projection_suffix)
                empty = _get_or_create_empty(empty_name, scene)
                for ch in user_edits:
                    ch.parent = empty
            else:
                # Preserve position so the user can place the empty freely.
                empty = _get_or_create_empty_keep(empty_name, scene)

            # Clear the tag so toggling back to camera-plane works correctly.
            if "projector_on_camera_plane" in empty:
                del empty["projector_on_camera_plane"]

        bpy.ops.object.select_all(action='DESELECT')

        created_objects = []
        for src_name, (bm_m, cat_v) in merged.items():
            obj = _write_merged_object(
                src_name, bm_m, cat_v, scene, props, parent=empty
            )
            if obj is not None:
                obj.select_set(True)
                created_objects.append(obj)

        # ── STEP 6b: write global section outline + fill ──────────────────────
        for section_obj in _compute_and_write_section_outline(
                section_segs, scene, camera.name, parent=empty):
            apply_depth_offset(section_obj, camera, get_prefs().section_offset)
            section_obj.select_set(True)
            created_objects.append(section_obj)

        wm.progress_end()

        if not created_objects:
            self.report({'WARNING'}, "No geometry produced.")
            return {'CANCELLED'}

        total_edges = sum(len(o.data.edges) for o in created_objects)

        if props.convert_to_grease_pencil:
            convert_objects_to_grease_pencil(created_objects)

        empty.select_set(True)
        context.view_layer.objects.active = empty
        t_elapsed = time.perf_counter() - t_start
        msg = (
            f"Projection done: {len(created_objects)} object(s), "
            f"{total_edges} total edge(s), "
            f"{merged_verts} vertex/vertices merged, "
            f"{snapped} orphan(s) snapped, "
            f"{dedup_removed} cross-object duplicate(s) removed "
            f"({t_elapsed:.2f}s)."
        )
        self.report({'INFO'}, msg)
        return {'FINISHED'}