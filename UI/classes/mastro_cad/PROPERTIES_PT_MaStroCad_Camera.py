import bpy
from bpy.types import Panel



def _draw_scale_data(self, context):
    if context.camera is None:
        return
    self.layout.prop(context.camera, "mastro_cad_drawing_scale", text="Scale 1:")


def _draw_scale_view3d(self, context):
    scene = context.scene
    if scene is None:
        return
    space = context.space_data
    in_cam = (space and space.type == 'VIEW_3D' and
              space.region_3d.view_perspective == 'CAMERA')
    col = self.layout.column(align=True)
    if in_cam and scene.camera and scene.camera.type == 'CAMERA':
        col.prop(scene.camera.data, "mastro_cad_drawing_scale", text="Scale 1:")
    else:
        col.prop(scene, "mastro_cad_drawing_scale_viewport", text="Scale 1:")


def _find_view3d_space(context):
    """Find a VIEW_3D space in the current screen.

    context.space_data during a STATUSBAR_HT_header draw call is the status
    bar's own space (type 'STATUSBAR'), not the 3D viewport — so it can't be
    used to read view_perspective/overlay state here.
    """
    screen = context.screen
    if screen is None:
        return None
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    return space
    return None


def _draw_statusbar(self, context):
    scene = context.scene
    if scene is None:
        return
    space = _find_view3d_space(context)
    if space is None:
        return
    in_cam = space.region_3d.view_perspective == 'CAMERA'
    if in_cam and scene.camera and scene.camera.type == 'CAMERA':
        scale = scene.camera.data.mastro_cad_drawing_scale
    else:
        scale = getattr(scene, "mastro_cad_drawing_scale_viewport", 100)
    self.layout.label(text=f"|  Scale 1:{scale}")


def register():
    bpy.types.DATA_PT_camera_display.append(_draw_scale_data)
    bpy.types.VIEW3D_PT_view3d_properties.append(_draw_scale_view3d)
    bpy.types.STATUSBAR_HT_header.append(_draw_statusbar)


def unregister():
    bpy.types.STATUSBAR_HT_header.remove(_draw_statusbar)
    bpy.types.VIEW3D_PT_view3d_properties.remove(_draw_scale_view3d)
    bpy.types.DATA_PT_camera_display.remove(_draw_scale_data)
