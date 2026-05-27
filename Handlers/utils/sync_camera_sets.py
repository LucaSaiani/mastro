def sync_default_camera_set(scene):
    """Keep Set 0 ('All') in sync with all enabled cameras."""
    ssp = scene.mastro_projector_props

    if not ssp.camera_sets or not ssp.camera_sets[0].is_default:
        s = ssp.camera_sets.add()
        s.name = "All"
        s.is_default = True
        ssp.camera_sets.move(len(ssp.camera_sets) - 1, 0)

    default_set = ssp.camera_sets[0]
    enabled = {
        obj.name for obj in scene.objects
        if obj.type == 'CAMERA'
        and obj.data is not None
        and obj.data.mastro_projector_cl.enabled
    }
    existing = {item.camera_name for item in default_set.cameras}

    if enabled == existing:
        return

    for name in enabled - existing:
        default_set.cameras.add().camera_name = name
    to_remove = [i for i, item in enumerate(default_set.cameras)
                 if item.camera_name not in enabled]
    for i in reversed(to_remove):
        default_set.cameras.remove(i)
