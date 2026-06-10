def sync_pdf_frames(scene):
    """Keep all_frames in sync with frame objects in the scene."""
    if not hasattr(scene, "mastro_pdf_props"):
        return
    pp = scene.mastro_pdf_props
    scene_frame_names = sorted(
        o.name for o in scene.objects
        if o.type == 'MESH' and o.data.get("MaStro frame")
    )
    current = [item.frame_name for item in pp.all_frames]
    if current == scene_frame_names:
        return
    pp.all_frames.clear()
    for name in scene_frame_names:
        pp.all_frames.add().frame_name = name
