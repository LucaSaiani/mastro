import bpy


def guard_light_sources(scene):
    """Clear stale light_source pointers on cameras whose light was deleted."""
    for cam_obj in scene.objects:
        if cam_obj.type != 'CAMERA':
            continue
        try:
            props = cam_obj.data.mastro_projector_cl
        except AttributeError:
            continue
        light = props.light_source
        if light is not None and light.name not in scene.objects:
            props.light_source = None
