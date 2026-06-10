from .depsgraph_handlers import register as _register_depsgraph, unregister as _unregister_depsgraph
from .utils.open_file_detection import register as _register_file_lock, unregister as _unregister_file_lock
from .mastro_cad import depsgraph_handlers_cad as _depsgraph_handlers_cad
from .mastro_cad import cad_handles as _cad_handles
from .mastro_cad import drawing_selection_overlay as _drawing_selection_overlay


def register():
    _register_depsgraph()
    _register_file_lock()
    _depsgraph_handlers_cad.register()
    _cad_handles.register()
    _drawing_selection_overlay.register()


def unregister():
    _drawing_selection_overlay.unregister()
    _cad_handles.unregister()
    _depsgraph_handlers_cad.unregister()
    _unregister_file_lock()
    _unregister_depsgraph()
