This folder has no code - it exists only to document where mastro's persistent timers
(bpy.app.timers.register(..., persistent=True)) actually live, since they're spread across
several other folders rather than collected in one place. Each one is registered once in its
own module's register()/unregister(), called from the addon's root __init__.py the normal way
(via Utils.modules or the module's own dedicated register/unregister hookup) - moving them here
turned out to add import-chain complexity (cross-package imports back into the modules they
were extracted from) for no real benefit, so they were left where they were and this note was
added instead.

The four persistent timers, where to find them, and what they do:

  Utils/monitor_view_rotation.py: monitor_view_rotation
      Polls 3D viewport rotation/perspective to sync the Clip Range feature's view-side state
      (Utils/mastro_levels/clip_range.py) when the user rotates into/out of Top/Bottom ortho.
      Registered via Utils/__init__.py's `modules` list.

  Handlers/mastro_cad/depsgraph_handlers_cad.py: _monitor_scale
      Polls camera/viewport state to keep the CAD drawing scale (mastro_cad_drawing_scale)
      in sync with the active viewport's scale setting. Registered via Handlers/__init__.py.

  Handlers/utils/open_file_detection.py: _refresh_marker
      Periodically refreshes a marker file's timestamp while a .blend is open, used to detect
      stale locks from a non-clean exit. Tightly coupled with this file's other marker
      read/write functions (_write_marker, _read_marker, _marker_is_stale, check_and_mark,
      on_load_post, ...) - kept together rather than split out. Registered via
      Handlers/__init__.py.

  Nodes/schedule/tree.py: _poll_pending_trees
      Runs MaStroScheduleTree.execute() and mark_mismatched_links() for any Schedule node tree
      MaStroScheduleTree.update() flagged as needing a refresh, on Blender's own schedule
      instead of synchronously inside update() (which recurses into a RecursionError - see
      that update()'s docstring for the full story). Registered via
      Nodes/schedule/__init__.py's start_polling()/stop_polling().
