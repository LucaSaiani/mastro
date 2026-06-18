from bpy.props import (IntProperty,
                       BoolProperty,
                       CollectionProperty,
)

from .property_classes_cad import (mastro_CL_cad_pen,
                                   mastro_CL_cad_dash_pattern,
                                   mastro_CL_cad_layer,
)


# =============================================================================
# Scale / black mode update callbacks
# =============================================================================
def _on_black_mode_toggled(self, context):
    from ...Utils.mastro_cad.update_bmesh_drawing_attributes import set_black_switch
    set_black_switch(context, self.mastro_cad_drawing_black_mode)


def _on_camera_scale_changed(self, context):
    from ...Utils.mastro_cad.sync_drawing_scale import sync_drawing_scale
    sync_drawing_scale(self.mastro_cad_drawing_scale)
    scene = context.scene
    if scene:
        scene["mastro_cad_drawing_scale"] = self.mastro_cad_drawing_scale
        from ...Handlers.depsgraph_handlers import _update_scale_header
        _update_scale_header(scene)


def _on_scene_scale_changed(self, context):
    from ...Utils.mastro_cad.sync_drawing_scale import sync_drawing_scale
    sync_drawing_scale(self.mastro_cad_drawing_scale)
    # Mirror back to the active source so the value persists.
    scene = context.scene
    if scene is None:
        return
    space = getattr(context, 'space_data', None)
    in_camera_view = (space and space.type == 'VIEW_3D' and
                      space.region_3d.view_perspective == 'CAMERA')
    if in_camera_view:
        cam = scene.camera
        if cam and cam.type == 'CAMERA' and cam.data.mastro_cad_drawing_scale != self.mastro_cad_drawing_scale:
            cam.data["mastro_cad_drawing_scale"] = self.mastro_cad_drawing_scale
    else:
        if scene.mastro_cad_drawing_scale_viewport != self.mastro_cad_drawing_scale:
            scene["mastro_cad_drawing_scale_viewport"] = self.mastro_cad_drawing_scale


def _on_viewport_scale_changed(self, context):
    from ...Utils.mastro_cad.sync_drawing_scale import sync_drawing_scale
    sync_drawing_scale(self.mastro_cad_drawing_scale_viewport)
    self["mastro_cad_drawing_scale"] = self.mastro_cad_drawing_scale_viewport


def _on_auto_update_layers_toggled(self, context):
    if self.mastro_cad_auto_update_layers:
        from ...Utils.mastro_cad.sync_layer_groups import sync_layer_groups
        sync_layer_groups(context)


# =============================================================================
# Scene Properties - CAD (pens, line types, layers, drawing scale)
# =============================================================================
scene_props_cad = [
    ("mastro_cad_pens", CollectionProperty(type=mastro_CL_cad_pen)),
    ("mastro_cad_pen_index", IntProperty(default=0)),

    ("mastro_cad_dash_patterns", CollectionProperty(type=mastro_CL_cad_dash_pattern)),
    ("mastro_cad_line_type_index", IntProperty(default=0)),

    ("mastro_cad_layers", CollectionProperty(type=mastro_CL_cad_layer)),
    ("mastro_cad_layer_index", IntProperty(default=0)),

    ("mastro_cad_drawing_black_mode", BoolProperty(
        name="Black Mode",
        description="Draw all black-marked edges in black, ignoring layer colour",
        default=False,
        update=_on_black_mode_toggled,
    )),

    ("mastro_cad_drawing_previous_vert_id", IntProperty(default=-1)),
    ("mastro_cad_drawing_previous_edge_number", IntProperty(default=0)),

    ("mastro_cad_drawing_scale", IntProperty(
        name="Drawing Scale",
        description="Active drawing scale — follows camera in camera view, viewport scale otherwise",
        default=100,
        min=1,
        update=_on_scene_scale_changed,
    )),
    ("mastro_cad_drawing_scale_viewport", IntProperty(
        name="Viewport Scale",
        description="Drawing scale used in free viewport (not camera view)",
        default=100,
        min=1,
        update=_on_viewport_scale_changed,
    )),
]


# =============================================================================
# Camera Properties - CAD
# =============================================================================
camera_props_cad = [
    ("mastro_cad_drawing_scale", IntProperty(
        name="Drawing Scale",
        description="Scale denominator (e.g. 200 for 1:200). Multiplies all line thicknesses in the viewport",
        default=100,
        min=1,
        update=_on_camera_scale_changed,
    )),
]


# =============================================================================
# WindowManager Properties - CAD
# =============================================================================
window_manager_props_cad = [
    ("mastro_cad_auto_update_layers", BoolProperty(
        name="Auto Update Layers",
        description="Automatically sync drawing attributes when layers change",
        default=True,
        update=_on_auto_update_layers_toggled,
    )),
]
