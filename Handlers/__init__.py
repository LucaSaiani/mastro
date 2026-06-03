from .depsgraph_handlers import register as _register_depsgraph, unregister as _unregister_depsgraph
from .utils.open_file_detection import register as _register_file_lock, unregister as _unregister_file_lock


def register():
    _register_depsgraph()
    _register_file_lock()


def unregister():
    _unregister_file_lock()
    _unregister_depsgraph()
